"""Server-owned allowance and cost reservations for future live essay feedback."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from threading import Lock
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .english_essay_repository import EnglishEssayError


@dataclass(frozen=True, slots=True)
class EssayFeedbackLimits:
    enabled: bool
    monthly_feedback: int
    monthly_cost_micros_sgd: int
    academy_monthly_cost_micros_sgd: int
    max_feedback_cost_micros_sgd: int


@dataclass(frozen=True, slots=True)
class EssayFeedbackQuote:
    max_cost_micros_sgd: int


@dataclass(frozen=True, slots=True)
class EssayFeedbackActual:
    cost_micros_sgd: int


@dataclass(frozen=True, slots=True)
class EssayFeedbackReservation:
    reservation_id: str
    learner_id: str
    submission_id: str
    usage_month: date
    status: str = "reserved"


@dataclass(frozen=True, slots=True)
class EssayFeedbackAllowanceSnapshot:
    enabled: bool
    monthly_feedback_limit: int
    monthly_feedback_remaining: int
    resets_at: datetime
    availability: str


def _month_start(moment: datetime | None = None) -> date:
    current = moment or datetime.now(UTC)
    return date(current.year, current.month, 1)


def _next_month(month: date) -> datetime:
    if month.month == 12:
        return datetime(month.year + 1, 1, 1, tzinfo=UTC)
    return datetime(month.year, month.month + 1, 1, tzinfo=UTC)


def _validate_quote(quote: EssayFeedbackQuote, limits: EssayFeedbackLimits) -> None:
    if (
        quote.max_cost_micros_sgd <= 0
        or quote.max_cost_micros_sgd > limits.max_feedback_cost_micros_sgd
    ):
        raise EnglishEssayError(
            "essay_feedback_reservation_invalid",
            "Live essay feedback could not be reserved within the configured boundary.",
            503,
        )


def _disabled_error() -> EnglishEssayError:
    return EnglishEssayError(
        "essay_feedback_not_released",
        "Live essay feedback has not been released. Self-review and fixture feedback remain available.",
        503,
    )


def _allowance_error(boundary: str) -> EnglishEssayError:
    return EnglishEssayError(
        "essay_feedback_allowance_exhausted",
        "The live essay-feedback allowance is currently unavailable. Self-review remains available.",
        429,
    )


def _snapshot(
    *,
    limits: EssayFeedbackLimits,
    usage_month: date,
    reserved_feedback: int,
    committed_feedback: int,
    learner_reserved_cost: int,
    learner_actual_cost: int,
    academy_reserved_cost: int,
    academy_actual_cost: int,
) -> EssayFeedbackAllowanceSnapshot:
    remaining = max(
        0, limits.monthly_feedback - reserved_feedback - committed_feedback
    )
    if not limits.enabled:
        availability = "provider_not_released"
    elif remaining == 0:
        availability = "allowance_exhausted"
    elif learner_reserved_cost + learner_actual_cost >= limits.monthly_cost_micros_sgd:
        availability = "cost_ceiling_reached"
    elif academy_reserved_cost + academy_actual_cost >= limits.academy_monthly_cost_micros_sgd:
        availability = "academy_circuit_breaker"
    else:
        availability = "available"
    return EssayFeedbackAllowanceSnapshot(
        enabled=limits.enabled,
        monthly_feedback_limit=limits.monthly_feedback,
        monthly_feedback_remaining=remaining if limits.enabled else 0,
        resets_at=_next_month(usage_month),
        availability=availability,
    )


class InMemoryEssayFeedbackAllowanceRepository:
    """Test/development adapter mirroring the PostgreSQL reservation lifecycle."""

    def __init__(self, essay_repository):
        self.essay_repository = essay_repository
        self.learner_usage: dict[tuple[str, date], dict[str, int]] = {}
        self.academy_usage: dict[date, dict[str, int]] = {}
        self.reservations: dict[str, dict] = {}
        self.idempotency: dict[tuple[str, str], str] = {}
        self.events: list[dict] = []
        self._lock = Lock()

    @staticmethod
    def _empty_usage() -> dict[str, int]:
        return {
            "reserved_feedback": 0,
            "committed_feedback": 0,
            "released_feedback": 0,
            "reserved_cost_micros_sgd": 0,
            "actual_cost_micros_sgd": 0,
        }

    @staticmethod
    def _empty_academy_usage() -> dict[str, int]:
        return {"reserved_cost_micros_sgd": 0, "actual_cost_micros_sgd": 0}

    def allowance(
        self, learner_id: str, limits: EssayFeedbackLimits, *, at: datetime | None = None
    ) -> EssayFeedbackAllowanceSnapshot:
        usage_month = _month_start(at)
        with self._lock:
            learner = self.learner_usage.get(
                (learner_id, usage_month), self._empty_usage()
            )
            academy = self.academy_usage.get(
                usage_month, self._empty_academy_usage()
            )
            return _snapshot(
                limits=limits,
                usage_month=usage_month,
                reserved_feedback=learner["reserved_feedback"],
                committed_feedback=learner["committed_feedback"],
                learner_reserved_cost=learner["reserved_cost_micros_sgd"],
                learner_actual_cost=learner["actual_cost_micros_sgd"],
                academy_reserved_cost=academy["reserved_cost_micros_sgd"],
                academy_actual_cost=academy["actual_cost_micros_sgd"],
            )

    def reserve(
        self,
        learner_id: str,
        submission_id: str,
        *,
        quote: EssayFeedbackQuote,
        limits: EssayFeedbackLimits,
        idempotency_key: str,
        request_id: str,
        provider_name: str,
        model_name: str,
        policy_version: str,
        at: datetime | None = None,
    ) -> EssayFeedbackReservation:
        if not limits.enabled:
            raise _disabled_error()
        _validate_quote(quote, limits)
        usage_month = _month_start(at)
        with self._lock:
            prior_id = self.idempotency.get((learner_id, idempotency_key))
            if prior_id:
                prior = self.reservations[prior_id]
                if prior["submission_id"] != submission_id:
                    raise EnglishEssayError(
                        "idempotency_conflict",
                        "That idempotency key was already used for another essay feedback reservation.",
                        409,
                    )
                return self._reservation(prior)
            self.essay_repository.get_submission(learner_id, submission_id)
            if not self.essay_repository.get_self_review(learner_id, submission_id):
                raise EnglishEssayError(
                    "essay_self_review_required",
                    "Complete the learner self-review before requesting live feedback.",
                    409,
                )
            if any(
                row["learner_id"] == learner_id and row["status"] == "reserved"
                for row in self.reservations.values()
            ):
                raise EnglishEssayError(
                    "essay_feedback_in_progress",
                    "Wait for the current essay feedback request to finish.",
                    409,
                )
            learner = self.learner_usage.setdefault(
                (learner_id, usage_month), self._empty_usage()
            )
            academy = self.academy_usage.setdefault(
                usage_month, self._empty_academy_usage()
            )
            if (
                learner["reserved_feedback"] + learner["committed_feedback"] + 1
                > limits.monthly_feedback
            ):
                raise _allowance_error("monthly_feedback")
            if (
                learner["reserved_cost_micros_sgd"]
                + learner["actual_cost_micros_sgd"]
                + quote.max_cost_micros_sgd
                > limits.monthly_cost_micros_sgd
            ):
                raise _allowance_error("monthly_cost")
            if (
                academy["reserved_cost_micros_sgd"]
                + academy["actual_cost_micros_sgd"]
                + quote.max_cost_micros_sgd
                > limits.academy_monthly_cost_micros_sgd
            ):
                raise _allowance_error("academy_circuit_breaker")
            reservation_id = str(uuid4())
            row = {
                "reservation_id": reservation_id,
                "learner_id": learner_id,
                "submission_id": submission_id,
                "usage_month": usage_month,
                "status": "reserved",
                "reserved_cost_micros_sgd": quote.max_cost_micros_sgd,
                "actual_cost_micros_sgd": None,
                "provider_name": provider_name,
                "model_name": model_name,
                "policy_version": policy_version,
            }
            self.reservations[reservation_id] = row
            self.idempotency[(learner_id, idempotency_key)] = reservation_id
            learner["reserved_feedback"] += 1
            learner["reserved_cost_micros_sgd"] += quote.max_cost_micros_sgd
            academy["reserved_cost_micros_sgd"] += quote.max_cost_micros_sgd
            self._event(row, "reserved", request_id, quote.max_cost_micros_sgd)
            return self._reservation(row)

    def commit(
        self,
        reservation: EssayFeedbackReservation,
        actual: EssayFeedbackActual,
        limits: EssayFeedbackLimits,
        *,
        request_id: str,
    ) -> EssayFeedbackAllowanceSnapshot:
        if actual.cost_micros_sgd < 0:
            raise EnglishEssayError(
                "essay_feedback_provider_usage_invalid",
                "The feedback provider reported invalid usage.",
                503,
            )
        with self._lock:
            row = self.reservations.get(reservation.reservation_id)
            if row is None:
                raise EnglishEssayError(
                    "essay_feedback_reservation_invalid",
                    "Essay feedback usage could not be committed.",
                    503,
                )
            if row["status"] == "committed":
                if row["actual_cost_micros_sgd"] != actual.cost_micros_sgd:
                    raise EnglishEssayError(
                        "essay_feedback_reservation_invalid",
                        "Essay feedback usage was already committed with different evidence.",
                        409,
                    )
                return self.allowance_without_lock(row["learner_id"], limits, row["usage_month"])
            if row["status"] != "reserved" or actual.cost_micros_sgd > row[
                "reserved_cost_micros_sgd"
            ]:
                raise EnglishEssayError(
                    "essay_feedback_provider_usage_invalid",
                    "The feedback provider reported usage outside the reserved boundary.",
                    503,
                )
            learner = self.learner_usage[(row["learner_id"], row["usage_month"])]
            academy = self.academy_usage[row["usage_month"]]
            learner["reserved_feedback"] -= 1
            learner["committed_feedback"] += 1
            learner["reserved_cost_micros_sgd"] -= row["reserved_cost_micros_sgd"]
            learner["actual_cost_micros_sgd"] += actual.cost_micros_sgd
            academy["reserved_cost_micros_sgd"] -= row["reserved_cost_micros_sgd"]
            academy["actual_cost_micros_sgd"] += actual.cost_micros_sgd
            row["status"] = "committed"
            row["actual_cost_micros_sgd"] = actual.cost_micros_sgd
            self._event(row, "committed", request_id, actual.cost_micros_sgd)
            return self.allowance_without_lock(row["learner_id"], limits, row["usage_month"])

    def release(
        self,
        reservation: EssayFeedbackReservation,
        limits: EssayFeedbackLimits,
        *,
        request_id: str,
        reason: str,
    ) -> EssayFeedbackAllowanceSnapshot:
        with self._lock:
            row = self.reservations.get(reservation.reservation_id)
            if row is None:
                raise EnglishEssayError(
                    "essay_feedback_reservation_invalid",
                    "Essay feedback usage could not be released.",
                    503,
                )
            if row["status"] == "reserved":
                learner = self.learner_usage[(row["learner_id"], row["usage_month"])]
                academy = self.academy_usage[row["usage_month"]]
                learner["reserved_feedback"] -= 1
                learner["released_feedback"] += 1
                learner["reserved_cost_micros_sgd"] -= row["reserved_cost_micros_sgd"]
                academy["reserved_cost_micros_sgd"] -= row["reserved_cost_micros_sgd"]
                row["status"] = "released"
                self._event(row, "released", request_id, 0, reason=reason)
            return self.allowance_without_lock(row["learner_id"], limits, row["usage_month"])

    def allowance_without_lock(
        self, learner_id: str, limits: EssayFeedbackLimits, usage_month: date
    ) -> EssayFeedbackAllowanceSnapshot:
        learner = self.learner_usage.get((learner_id, usage_month), self._empty_usage())
        academy = self.academy_usage.get(usage_month, self._empty_academy_usage())
        return _snapshot(
            limits=limits,
            usage_month=usage_month,
            reserved_feedback=learner["reserved_feedback"],
            committed_feedback=learner["committed_feedback"],
            learner_reserved_cost=learner["reserved_cost_micros_sgd"],
            learner_actual_cost=learner["actual_cost_micros_sgd"],
            academy_reserved_cost=academy["reserved_cost_micros_sgd"],
            academy_actual_cost=academy["actual_cost_micros_sgd"],
        )

    def _event(
        self, row: dict, event_type: str, request_id: str, cost: int, *, reason: str | None = None
    ) -> None:
        self.events.append(
            {
                "reservation_id": row["reservation_id"],
                "learner_id": row["learner_id"],
                "submission_id": row["submission_id"],
                "event_type": event_type,
                "request_id": request_id,
                "cost_micros_sgd": cost,
                "reason": reason,
            }
        )

    @staticmethod
    def _reservation(row: dict) -> EssayFeedbackReservation:
        return EssayFeedbackReservation(
            reservation_id=row["reservation_id"],
            learner_id=row["learner_id"],
            submission_id=row["submission_id"],
            usage_month=row["usage_month"],
            status=row["status"],
        )


class PostgresEssayFeedbackAllowanceRepository:
    def __init__(self, database_url: str):
        self.database_url = database_url

    def _connect(self):
        return psycopg.connect(self.database_url, row_factory=dict_row)

    def allowance(
        self, learner_id: str, limits: EssayFeedbackLimits, *, at: datetime | None = None
    ) -> EssayFeedbackAllowanceSnapshot:
        usage_month = _month_start(at)
        with self._connect() as connection:
            learner = connection.execute(
                "select * from english_essay_feedback_monthly_usage where student_id=%s and usage_month=%s",
                (learner_id, usage_month),
            ).fetchone() or {}
            academy = connection.execute(
                "select * from english_essay_feedback_academy_monthly_usage where usage_month=%s",
                (usage_month,),
            ).fetchone() or {}
        return _snapshot(
            limits=limits,
            usage_month=usage_month,
            reserved_feedback=learner.get("reserved_feedback", 0),
            committed_feedback=learner.get("committed_feedback", 0),
            learner_reserved_cost=learner.get("reserved_cost_micros_sgd", 0),
            learner_actual_cost=learner.get("actual_cost_micros_sgd", 0),
            academy_reserved_cost=academy.get("reserved_cost_micros_sgd", 0),
            academy_actual_cost=academy.get("actual_cost_micros_sgd", 0),
        )

    def reserve(
        self,
        learner_id: str,
        submission_id: str,
        *,
        quote: EssayFeedbackQuote,
        limits: EssayFeedbackLimits,
        idempotency_key: str,
        request_id: str,
        provider_name: str,
        model_name: str,
        policy_version: str,
        at: datetime | None = None,
    ) -> EssayFeedbackReservation:
        if not limits.enabled:
            raise _disabled_error()
        _validate_quote(quote, limits)
        usage_month = _month_start(at)
        reservation_id = str(uuid4())
        with self._connect() as connection:
            connection.execute(
                "select pg_advisory_xact_lock(hashtextextended(%s, 0))",
                (f"english-essay-feedback:{learner_id}",),
            )
            connection.execute(
                "select pg_advisory_xact_lock(hashtextextended(%s, 0))",
                (f"english-essay-feedback:academy:{usage_month.isoformat()}",),
            )
            prior = connection.execute(
                """
                select reservations.*
                  from english_essay_feedback_reservation_idempotency_keys keys
                  join english_essay_feedback_reservations reservations
                    on reservations.id = keys.reservation_id
                 where keys.student_id=%s and keys.idempotency_key=%s
                """,
                (learner_id, idempotency_key),
            ).fetchone()
            if prior:
                if str(prior["submission_id"]) != submission_id:
                    raise EnglishEssayError(
                        "idempotency_conflict",
                        "That idempotency key was already used for another essay feedback reservation.",
                        409,
                    )
                return self._reservation(prior)
            eligible = connection.execute(
                """
                select 1
                  from english_essay_submissions submissions
                  join english_essay_self_reviews reviews
                    on reviews.submission_id = submissions.id
                   and reviews.student_id = submissions.student_id
                 where submissions.id=%s and submissions.student_id=%s
                """,
                (submission_id, learner_id),
            ).fetchone()
            if not eligible:
                raise EnglishEssayError(
                    "essay_feedback_submission_ineligible",
                    "An owned submission with completed self-review is required for live feedback.",
                    409,
                )
            if connection.execute(
                "select 1 from english_essay_feedback_reservations where student_id=%s and status='reserved'",
                (learner_id,),
            ).fetchone():
                raise EnglishEssayError(
                    "essay_feedback_in_progress",
                    "Wait for the current essay feedback request to finish.",
                    409,
                )
            connection.execute(
                "insert into english_essay_feedback_monthly_usage (student_id, usage_month) values (%s, %s) on conflict do nothing",
                (learner_id, usage_month),
            )
            connection.execute(
                "insert into english_essay_feedback_academy_monthly_usage (usage_month) values (%s) on conflict do nothing",
                (usage_month,),
            )
            learner = connection.execute(
                "select * from english_essay_feedback_monthly_usage where student_id=%s and usage_month=%s for update",
                (learner_id, usage_month),
            ).fetchone()
            academy = connection.execute(
                "select * from english_essay_feedback_academy_monthly_usage where usage_month=%s for update",
                (usage_month,),
            ).fetchone()
            if learner["reserved_feedback"] + learner["committed_feedback"] + 1 > limits.monthly_feedback:
                raise _allowance_error("monthly_feedback")
            if learner["reserved_cost_micros_sgd"] + learner["actual_cost_micros_sgd"] + quote.max_cost_micros_sgd > limits.monthly_cost_micros_sgd:
                raise _allowance_error("monthly_cost")
            if academy["reserved_cost_micros_sgd"] + academy["actual_cost_micros_sgd"] + quote.max_cost_micros_sgd > limits.academy_monthly_cost_micros_sgd:
                raise _allowance_error("academy_circuit_breaker")
            connection.execute(
                """
                insert into english_essay_feedback_reservations (
                    id, student_id, submission_id, usage_month, policy_version,
                    provider_name, model_name, reserved_cost_micros_sgd
                ) values (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (reservation_id, learner_id, submission_id, usage_month, policy_version,
                 provider_name, model_name, quote.max_cost_micros_sgd),
            )
            connection.execute(
                "insert into english_essay_feedback_reservation_idempotency_keys (student_id, idempotency_key, reservation_id) values (%s, %s, %s)",
                (learner_id, idempotency_key, reservation_id),
            )
            connection.execute(
                """
                update english_essay_feedback_monthly_usage
                   set reserved_feedback=reserved_feedback+1,
                       reserved_cost_micros_sgd=reserved_cost_micros_sgd+%s,
                       updated_at=now()
                 where student_id=%s and usage_month=%s
                """,
                (quote.max_cost_micros_sgd, learner_id, usage_month),
            )
            connection.execute(
                """
                update english_essay_feedback_academy_monthly_usage
                   set reserved_cost_micros_sgd=reserved_cost_micros_sgd+%s,
                       updated_at=now()
                 where usage_month=%s
                """,
                (quote.max_cost_micros_sgd, usage_month),
            )
            self._event(connection, reservation_id, learner_id, submission_id, "reserved", request_id,
                        {"reserved_cost_micros_sgd": quote.max_cost_micros_sgd})
        return EssayFeedbackReservation(reservation_id, learner_id, submission_id, usage_month)

    def commit(
        self,
        reservation: EssayFeedbackReservation,
        actual: EssayFeedbackActual,
        limits: EssayFeedbackLimits,
        *,
        request_id: str,
    ) -> EssayFeedbackAllowanceSnapshot:
        if actual.cost_micros_sgd < 0:
            raise EnglishEssayError(
                "essay_feedback_provider_usage_invalid",
                "The feedback provider reported invalid usage.",
                503,
            )
        with self._connect() as connection:
            row = connection.execute(
                "select * from english_essay_feedback_reservations where id=%s for update",
                (reservation.reservation_id,),
            ).fetchone()
            if row is None:
                raise EnglishEssayError("essay_feedback_reservation_invalid", "Essay feedback usage could not be committed.", 503)
            if row["status"] == "committed":
                if row["actual_cost_micros_sgd"] != actual.cost_micros_sgd:
                    raise EnglishEssayError("essay_feedback_reservation_invalid", "Essay feedback usage was already committed with different evidence.", 409)
                return self.allowance(reservation.learner_id, limits)
            if row["status"] != "reserved" or actual.cost_micros_sgd > row["reserved_cost_micros_sgd"]:
                raise EnglishEssayError("essay_feedback_provider_usage_invalid", "The feedback provider reported usage outside the reserved boundary.", 503)
            connection.execute(
                """
                update english_essay_feedback_monthly_usage
                   set reserved_feedback=reserved_feedback-1,
                       committed_feedback=committed_feedback+1,
                       reserved_cost_micros_sgd=reserved_cost_micros_sgd-%s,
                       actual_cost_micros_sgd=actual_cost_micros_sgd+%s,
                       updated_at=now()
                 where student_id=%s and usage_month=%s
                """,
                (row["reserved_cost_micros_sgd"], actual.cost_micros_sgd,
                 reservation.learner_id, reservation.usage_month),
            )
            connection.execute(
                """
                update english_essay_feedback_academy_monthly_usage
                   set reserved_cost_micros_sgd=reserved_cost_micros_sgd-%s,
                       actual_cost_micros_sgd=actual_cost_micros_sgd+%s,
                       updated_at=now()
                 where usage_month=%s
                """,
                (row["reserved_cost_micros_sgd"], actual.cost_micros_sgd, reservation.usage_month),
            )
            connection.execute(
                "update english_essay_feedback_reservations set status='committed', actual_cost_micros_sgd=%s, completed_at=now() where id=%s",
                (actual.cost_micros_sgd, reservation.reservation_id),
            )
            self._event(connection, reservation.reservation_id, reservation.learner_id,
                        reservation.submission_id, "committed", request_id,
                        {"actual_cost_micros_sgd": actual.cost_micros_sgd})
        return self.allowance(reservation.learner_id, limits)

    def release(
        self,
        reservation: EssayFeedbackReservation,
        limits: EssayFeedbackLimits,
        *,
        request_id: str,
        reason: str,
    ) -> EssayFeedbackAllowanceSnapshot:
        with self._connect() as connection:
            row = connection.execute(
                "select * from english_essay_feedback_reservations where id=%s for update",
                (reservation.reservation_id,),
            ).fetchone()
            if row is None:
                raise EnglishEssayError("essay_feedback_reservation_invalid", "Essay feedback usage could not be released.", 503)
            if row["status"] == "reserved":
                connection.execute(
                    """
                    update english_essay_feedback_monthly_usage
                       set reserved_feedback=reserved_feedback-1,
                           released_feedback=released_feedback+1,
                           reserved_cost_micros_sgd=reserved_cost_micros_sgd-%s,
                           updated_at=now()
                     where student_id=%s and usage_month=%s
                    """,
                    (row["reserved_cost_micros_sgd"], reservation.learner_id, reservation.usage_month),
                )
                connection.execute(
                    """
                    update english_essay_feedback_academy_monthly_usage
                       set reserved_cost_micros_sgd=reserved_cost_micros_sgd-%s,
                           updated_at=now()
                     where usage_month=%s
                    """,
                    (row["reserved_cost_micros_sgd"], reservation.usage_month),
                )
                connection.execute(
                    "update english_essay_feedback_reservations set status='released', completed_at=now() where id=%s",
                    (reservation.reservation_id,),
                )
                self._event(connection, reservation.reservation_id, reservation.learner_id,
                            reservation.submission_id, "released", request_id,
                            {"reason": reason[:120]})
        return self.allowance(reservation.learner_id, limits)

    @staticmethod
    def _event(connection, reservation_id, learner_id, submission_id, event_type, request_id, usage):
        connection.execute(
            """
            insert into english_essay_feedback_usage_events (
                reservation_id, student_id, submission_id, event_type, request_id, usage
            ) values (%s, %s, %s, %s, %s, %s)
            """,
            (reservation_id, learner_id, submission_id, event_type, request_id, Jsonb(usage)),
        )

    @staticmethod
    def _reservation(row: dict) -> EssayFeedbackReservation:
        return EssayFeedbackReservation(
            str(row["id"]), str(row["student_id"]), str(row["submission_id"]),
            row["usage_month"], row["status"]
        )
