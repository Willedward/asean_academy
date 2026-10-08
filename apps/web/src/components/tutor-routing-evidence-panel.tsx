"use client";

import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { adminRequest } from "@/lib/api/admin-dashboard";
import { ApiRequestError } from "@/lib/api/errors";
import type { components } from "@/lib/api/schema";

type RoutingStatus = components["schemas"]["TutorRoutingStatusAdminResponse"];
type TutorUsage = components["schemas"]["TutorUsageAdminResponse"];
type RouteDecision = components["schemas"]["TutorRouteDecisionAdminResponse"];
type RouteDecisionList =
  components["schemas"]["TutorRouteDecisionListAdminResponse"];

type Filters = {
  routingMode: string;
  recommendedTier: string;
  executedTier: string;
  tutorMode: string;
  questionDifficulty: string;
  reservationStatus: string;
};

type LoadError = {
  title: string;
  detail: string;
  expiredSession: boolean;
};

type SummaryState = {
  key: string;
  status: RoutingStatus;
  usage: TutorUsage;
};

type DecisionState = {
  key: string;
  items: RouteDecision[];
  nextCursor?: string;
};

const EMPTY_FILTERS: Filters = {
  routingMode: "",
  recommendedTier: "",
  executedTier: "",
  tutorMode: "",
  questionDifficulty: "",
  reservationStatus: "",
};

const TUTOR_MODES = [
  "clarify_question",
  "diagnose_misconception",
  "socratic_prompt",
  "alternative_explanation",
  "analogous_example",
  "solution_explanation",
  "lesson_recommendation",
] as const;

function currentMonth() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

function label(value: string) {
  return value.replaceAll("_", " ");
}

function formatCost(value: number) {
  return new Intl.NumberFormat("en-SG", {
    style: "currency",
    currency: "SGD",
    currencyDisplay: "code",
    minimumFractionDigits: 4,
    maximumFractionDigits: 4,
  }).format(value / 1_000_000);
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-SG", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function loadError(cause: unknown): LoadError {
  if (cause instanceof ApiRequestError) {
    const suffix = cause.requestId ? ` Request ID: ${cause.requestId}` : "";
    if (cause.status === 401) {
      return {
        title: "Your administrator session expired",
        detail: `Sign in again before loading routing evidence.${suffix}`,
        expiredSession: true,
      };
    }
    if (
      cause.code.toLowerCase().includes("schema") ||
      cause.message.toLowerCase().includes("schema")
    ) {
      return {
        title: "Routing evidence is not ready",
        detail: `The required database migration has not finished. Check System status before retrying.${suffix}`,
        expiredSession: false,
      };
    }
    if ([502, 503, 504].includes(cause.status)) {
      return {
        title: "The learning service is unavailable",
        detail: `The service may be waking from a Render cold start. Wait briefly, then retry.${suffix}`,
        expiredSession: false,
      };
    }
    return {
      title: "Routing evidence could not be loaded",
      detail: `${cause.message}${suffix}`,
      expiredSession: false,
    };
  }
  return {
    title: "Routing evidence could not be loaded",
    detail:
      cause instanceof Error
        ? cause.message
        : "The operation could not be completed.",
    expiredSession: false,
  };
}

function Cost({ value }: { value: number }) {
  return (
    <div className="inline-block">
      <span title={`${value.toLocaleString()} micro-SGD`}>
        {formatCost(value)}
      </span>
      <details className="mt-1 text-xs font-normal text-slate-500">
        <summary className="cursor-pointer">Raw micro-SGD</summary>
        <span>{value.toLocaleString()} micro-SGD</span>
      </details>
    </div>
  );
}

function MetricCard({
  label: title,
  value,
  detail,
}: {
  label: string;
  value: React.ReactNode;
  detail?: string;
}) {
  return (
    <div className="rounded-xl border bg-white p-4">
      <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
        {title}
      </p>
      <div className="mt-1 text-2xl font-bold">{value}</div>
      {detail ? <p className="mt-1 text-xs text-slate-600">{detail}</p> : null}
    </div>
  );
}

function ErrorState({ error, retry }: { error: LoadError; retry: () => void }) {
  return (
    <div
      role="alert"
      className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-900"
    >
      <p className="font-bold">{error.title}</p>
      <p className="mt-1 text-sm">{error.detail}</p>
      <div className="mt-3 flex flex-wrap gap-3">
        {error.expiredSession ? (
          <Button asChild>
            <a href="/login">Sign in again</a>
          </Button>
        ) : null}
        <Button type="button" variant="outline" onClick={retry}>
          Retry evidence
        </Button>
      </div>
    </div>
  );
}

function decisionPath(month: string, filters: Filters, cursor?: string) {
  const query = new URLSearchParams({ month, limit: "25" });
  if (cursor) query.set("cursor", cursor);
  if (filters.routingMode) query.set("routing_mode", filters.routingMode);
  if (filters.recommendedTier)
    query.set("recommended_tier", filters.recommendedTier);
  if (filters.executedTier) query.set("executed_tier", filters.executedTier);
  if (filters.tutorMode) query.set("tutor_mode", filters.tutorMode);
  if (filters.questionDifficulty)
    query.set("question_difficulty", filters.questionDifficulty);
  if (filters.reservationStatus)
    query.set("reservation_status", filters.reservationStatus);
  return `tutor-routing/decisions?${query.toString()}`;
}

export function TutorRoutingEvidencePanel() {
  const [month, setMonth] = useState(currentMonth);
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
  const [summary, setSummary] = useState<SummaryState>();
  const [decisionPage, setDecisionPage] = useState<DecisionState>();
  const [loadingMore, setLoadingMore] = useState(false);
  const [summaryFailure, setSummaryFailure] = useState<{
    key: string;
    error: LoadError;
  }>();
  const [decisionFailure, setDecisionFailure] = useState<{
    key: string;
    error: LoadError;
  }>();
  const [summaryRefresh, setSummaryRefresh] = useState(0);
  const [decisionsRefresh, setDecisionsRefresh] = useState(0);
  const summaryKey = `${month}:${summaryRefresh}`;
  const decisionsKey = `${month}:${JSON.stringify(filters)}:${decisionsRefresh}`;

  useEffect(() => {
    let current = true;
    void Promise.all([
      adminRequest<RoutingStatus>("tutor-routing/status"),
      adminRequest<TutorUsage>(`tutor-usage?month=${month}`),
    ])
      .then(([statusValue, usageValue]) => {
        if (!current) return;
        if (typeof usageValue.shadow_premium_executions !== "number") {
          throw new ApiRequestError(
            "Routing evidence schema revision is not ready.",
            503,
            "tutor_routing_schema_not_ready",
          );
        }
        setSummary({
          key: summaryKey,
          status: statusValue,
          usage: usageValue,
        });
      })
      .catch((cause: unknown) => {
        if (current)
          setSummaryFailure({ key: summaryKey, error: loadError(cause) });
      });
    return () => {
      current = false;
    };
  }, [month, summaryKey]);

  useEffect(() => {
    let current = true;
    void adminRequest<RouteDecisionList>(decisionPath(month, filters))
      .then((value) => {
        if (!current) return;
        setDecisionPage({
          key: decisionsKey,
          items: value.items,
          nextCursor: value.next_cursor ?? undefined,
        });
      })
      .catch((cause: unknown) => {
        if (current)
          setDecisionFailure({
            key: decisionsKey,
            error: loadError(cause),
          });
      });
    return () => {
      current = false;
    };
  }, [decisionsKey, filters, month]);

  const activeSummary = summary?.key === summaryKey ? summary : undefined;
  const status = activeSummary?.status;
  const usage = activeSummary?.usage;
  const summaryError =
    summaryFailure?.key === summaryKey ? summaryFailure.error : undefined;
  const activeDecisionPage =
    decisionPage?.key === decisionsKey ? decisionPage : undefined;
  const decisions = activeDecisionPage?.items ?? [];
  const nextCursor = activeDecisionPage?.nextCursor;
  const decisionsError =
    decisionFailure?.key === decisionsKey ? decisionFailure.error : undefined;
  const summaryLoading = !activeSummary && !summaryError;
  const decisionsLoading = !activeDecisionPage && !decisionsError;

  const recommendationRate = useMemo(() => {
    if (!usage?.route_decisions) return 0;
    return (usage.recommended_premium_routes / usage.route_decisions) * 100;
  }, [usage]);

  async function loadMore() {
    if (!nextCursor) return;
    setLoadingMore(true);
    setDecisionFailure(undefined);
    try {
      const value = await adminRequest<RouteDecisionList>(
        decisionPath(month, filters, nextCursor),
      );
      setDecisionPage((current) =>
        current?.key === decisionsKey
          ? {
              ...current,
              items: [...current.items, ...value.items],
              nextCursor: value.next_cursor ?? undefined,
            }
          : current,
      );
    } catch (cause) {
      setDecisionFailure({ key: decisionsKey, error: loadError(cause) });
    } finally {
      setLoadingMore(false);
    }
  }

  function updateFilter(key: keyof Filters, value: string) {
    setFilters((current) => ({ ...current, [key]: value }));
  }

  return (
    <section
      aria-labelledby="routing-evidence-title"
      className="space-y-5 rounded-2xl border bg-slate-50 p-4 sm:p-5"
    >
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-wide text-teal-700">
            Academic administrator evidence
          </p>
          <h2 id="routing-evidence-title" className="text-xl font-bold">
            Hybrid tutor routing
          </h2>
          <p className="mt-1 max-w-3xl text-sm text-slate-600">
            Review server-recorded recommendations, executions and reconciled
            costs. This panel never exposes learner prompts or answers.
          </p>
        </div>
        <label className="text-sm">
          Evidence month
          <input
            aria-label="Evidence month"
            type="month"
            value={month}
            onChange={(event) => setMonth(event.target.value)}
            className="mt-1 block rounded-lg border px-3 py-2"
          />
        </label>
      </div>

      {summaryError ? (
        <ErrorState
          error={summaryError}
          retry={() => setSummaryRefresh((value) => value + 1)}
        />
      ) : null}

      {summaryLoading && !status && !usage ? (
        <p
          role="status"
          className="rounded-xl border bg-white p-4 text-slate-600"
        >
          Loading routing status and monthly evidence…
        </p>
      ) : null}

      {status ? (
        <div className="grid gap-4 rounded-xl border bg-white p-4 md:grid-cols-[1.15fr_1fr_1fr]">
          <div>
            <p className="text-xs font-bold uppercase text-slate-500">
              Resolved routing mode
            </p>
            <p className="mt-1 text-lg font-bold capitalize">
              {status.resolved_mode}
            </p>
            <p className="text-sm text-slate-600">
              Configured {status.configured_mode} · cohort {status.cohort}
            </p>
          </div>
          <div>
            <p className="text-xs font-bold uppercase text-slate-500">
              Policy and schema
            </p>
            <p className="mt-1 font-semibold">{status.policy_version}</p>
            <p className="text-sm text-slate-600">
              Schema {status.schema_revision}
            </p>
          </div>
          <div>
            <p className="text-xs font-bold uppercase text-slate-500">
              Provider targets
            </p>
            <p className="mt-1 text-sm">
              Economy: {status.economy_provider} / {status.economy_model}
            </p>
            <p className="text-sm">
              Premium:{" "}
              {status.premium_provider && status.premium_model
                ? `${status.premium_provider} / ${status.premium_model}`
                : "not configured"}
            </p>
          </div>
        </div>
      ) : null}

      {usage ? (
        <>
          <div
            role={usage.shadow_premium_executions === 0 ? "status" : "alert"}
            className={`rounded-xl border p-4 ${
              usage.shadow_premium_executions === 0
                ? "border-green-200 bg-green-50 text-green-900"
                : "border-red-300 bg-red-50 text-red-900"
            }`}
          >
            <p className="font-bold">
              Shadow premium executions: {usage.shadow_premium_executions}
            </p>
            <p className="mt-1 text-sm">
              {usage.shadow_premium_executions === 0
                ? "The shadow-routing isolation invariant holds for this month."
                : "Stop the evidence run: at least one shadow decision executed the premium tier."}
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              label="Route decisions"
              value={usage.route_decisions.toLocaleString()}
              detail={`${usage.shadow_route_decisions.toLocaleString()} recorded in shadow mode`}
            />
            <MetricCard
              label="Premium recommended"
              value={usage.recommended_premium_routes.toLocaleString()}
              detail={`${recommendationRate.toFixed(1)}% of route decisions`}
            />
            <MetricCard
              label="Premium executed"
              value={usage.executed_premium_routes.toLocaleString()}
              detail="Across every routing mode"
            />
            <MetricCard
              label="Actual cost"
              value={<Cost value={usage.actual_cost_micros_sgd} />}
              detail={`${usage.actual_requests.toLocaleString()} reconciled requests`}
            />
            <MetricCard
              label="Projected recommended cost"
              value={
                <Cost value={usage.projected_recommended_cost_micros_sgd} />
              }
              detail="Server-priced recommendation projection"
            />
            <MetricCard
              label="Projected difference"
              value={
                <Cost
                  value={
                    usage.projected_recommended_cost_micros_sgd -
                    usage.actual_cost_micros_sgd
                  }
                />
              }
              detail="Projected recommendation minus actual cost"
            />
            <MetricCard
              label="Token usage"
              value={(
                usage.input_tokens + usage.output_tokens
              ).toLocaleString()}
              detail={`${usage.input_tokens.toLocaleString()} input · ${usage.output_tokens.toLocaleString()} output`}
            />
            <MetricCard
              label="Reservations"
              value={usage.active_reservations.toLocaleString()}
              detail={`${formatCost(usage.reserved_cost_micros_sgd)} currently reserved`}
            />
          </div>
        </>
      ) : null}

      <div className="space-y-4 rounded-xl border bg-white p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="font-bold">Decision evidence</h3>
            <p className="text-sm text-slate-600">
              Newest decisions first. Filters are applied by the server.
            </p>
          </div>
          <Button
            type="button"
            variant="outline"
            onClick={() => setFilters(EMPTY_FILTERS)}
            disabled={Object.values(filters).every((value) => value === "")}
          >
            Clear filters
          </Button>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
          <label className="text-xs">
            Routing mode
            <select
              aria-label="Routing mode"
              value={filters.routingMode}
              onChange={(event) =>
                updateFilter("routingMode", event.target.value)
              }
              className="mt-1 w-full rounded-lg border p-2"
            >
              <option value="">All</option>
              {["legacy", "off", "shadow", "live"].map((value) => (
                <option key={value} value={value}>
                  {label(value)}
                </option>
              ))}
            </select>
          </label>
          <label className="text-xs">
            Recommended tier
            <select
              aria-label="Recommended tier"
              value={filters.recommendedTier}
              onChange={(event) =>
                updateFilter("recommendedTier", event.target.value)
              }
              className="mt-1 w-full rounded-lg border p-2"
            >
              <option value="">All</option>
              <option value="economy">Economy</option>
              <option value="premium">Premium</option>
            </select>
          </label>
          <label className="text-xs">
            Executed tier
            <select
              aria-label="Executed tier"
              value={filters.executedTier}
              onChange={(event) =>
                updateFilter("executedTier", event.target.value)
              }
              className="mt-1 w-full rounded-lg border p-2"
            >
              <option value="">All</option>
              <option value="economy">Economy</option>
              <option value="premium">Premium</option>
            </select>
          </label>
          <label className="text-xs">
            Tutor mode
            <select
              aria-label="Tutor mode"
              value={filters.tutorMode}
              onChange={(event) =>
                updateFilter("tutorMode", event.target.value)
              }
              className="mt-1 w-full rounded-lg border p-2"
            >
              <option value="">All</option>
              {TUTOR_MODES.map((value) => (
                <option key={value} value={value}>
                  {label(value)}
                </option>
              ))}
            </select>
          </label>
          <label className="text-xs">
            Difficulty
            <select
              aria-label="Question difficulty"
              value={filters.questionDifficulty}
              onChange={(event) =>
                updateFilter("questionDifficulty", event.target.value)
              }
              className="mt-1 w-full rounded-lg border p-2"
            >
              <option value="">All</option>
              {[1, 2, 3, 4, 5].map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
          <label className="text-xs">
            Reservation status
            <select
              aria-label="Reservation status"
              value={filters.reservationStatus}
              onChange={(event) =>
                updateFilter("reservationStatus", event.target.value)
              }
              className="mt-1 w-full rounded-lg border p-2"
            >
              <option value="">All</option>
              {["reserved", "reconciled", "released"].map((value) => (
                <option key={value} value={value}>
                  {label(value)}
                </option>
              ))}
            </select>
          </label>
        </div>

        {decisionsError ? (
          <ErrorState
            error={decisionsError}
            retry={() => setDecisionsRefresh((value) => value + 1)}
          />
        ) : null}

        {decisionsLoading ? (
          <p
            role="status"
            className="rounded-lg bg-slate-50 p-4 text-slate-600"
          >
            Loading routing decisions…
          </p>
        ) : null}

        {!decisionsLoading && !decisionsError && decisions.length === 0 ? (
          <div className="rounded-lg border border-dashed p-5 text-center">
            <p className="font-semibold">No routing decisions found</p>
            <p className="mt-1 text-sm text-slate-600">
              Run an eligible tutor conversation or clear the current filters.
            </p>
          </div>
        ) : null}

        {decisions.length ? (
          <div className="overflow-x-auto rounded-lg border">
            <table className="w-full min-w-[78rem] text-left text-sm">
              <thead>
                <tr>
                  <th className="p-3">Created</th>
                  <th className="p-3">Context</th>
                  <th className="p-3">Score and reasons</th>
                  <th className="p-3">Recommended</th>
                  <th className="p-3">Executed</th>
                  <th className="p-3">Actual usage</th>
                  <th className="p-3">Projected cost</th>
                  <th className="p-3">Result</th>
                </tr>
              </thead>
              <tbody>
                {decisions.map((decision) => (
                  <tr key={decision.decision_id} className="border-t">
                    <td className="p-3">
                      <time dateTime={decision.created_at}>
                        {formatDate(decision.created_at)}
                      </time>
                      <span className="mt-1 block text-xs text-slate-500">
                        {decision.policy_version}
                      </span>
                    </td>
                    <td className="p-3">
                      <span className="font-semibold capitalize">
                        {decision.routing_mode}
                      </span>
                      <span className="block">
                        {label(decision.tutor_mode)}
                      </span>
                      <span className="block text-xs text-slate-500">
                        Difficulty {decision.question_difficulty}
                      </span>
                    </td>
                    <td className="p-3">
                      <span className="font-bold">{decision.route_score}</span>
                      <details className="mt-1">
                        <summary className="cursor-pointer text-xs font-semibold text-teal-800">
                          {decision.reason_codes.length} reason code
                          {decision.reason_codes.length === 1 ? "" : "s"}
                        </summary>
                        <ul className="mt-1 list-disc pl-4 text-xs text-slate-600">
                          {decision.reason_codes.map((reason) => (
                            <li key={reason}>{reason}</li>
                          ))}
                        </ul>
                      </details>
                    </td>
                    <td className="p-3">
                      <span className="font-semibold capitalize">
                        {decision.recommended_tier}
                      </span>
                      <span className="block text-xs text-slate-600">
                        {decision.recommended_provider} /{" "}
                        {decision.recommended_model}
                      </span>
                    </td>
                    <td className="p-3">
                      <span className="font-semibold capitalize">
                        {decision.executed_tier}
                      </span>
                      <span className="block text-xs text-slate-600">
                        {decision.executed_provider} / {decision.executed_model}
                      </span>
                    </td>
                    <td className="p-3">
                      {decision.actual_cost_micros_sgd == null ? (
                        <span className="text-slate-500">Pending</span>
                      ) : (
                        <>
                          <Cost value={decision.actual_cost_micros_sgd} />
                          <span className="block text-xs text-slate-600">
                            {(
                              decision.actual_input_tokens ?? 0
                            ).toLocaleString()}{" "}
                            in ·{" "}
                            {(
                              decision.actual_output_tokens ?? 0
                            ).toLocaleString()}{" "}
                            out
                          </span>
                        </>
                      )}
                    </td>
                    <td className="p-3">
                      {decision.projected_recommended_cost_micros_sgd ==
                      null ? (
                        <span className="text-slate-500">Pending</span>
                      ) : (
                        <Cost
                          value={decision.projected_recommended_cost_micros_sgd}
                        />
                      )}
                    </td>
                    <td className="p-3">
                      <span className="font-semibold">
                        {label(decision.reservation_status)}
                      </span>
                      <span className="block text-xs text-slate-600">
                        {decision.safety_outcome
                          ? label(decision.safety_outcome)
                          : "No assistant response"}
                      </span>
                      {decision.latency_ms == null ? null : (
                        <span className="block text-xs text-slate-500">
                          {decision.latency_ms.toLocaleString()} ms
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        {nextCursor ? (
          <Button
            type="button"
            disabled={loadingMore}
            onClick={() => void loadMore()}
          >
            {loadingMore ? "Loading more…" : "Load more decisions"}
          </Button>
        ) : null}
      </div>
    </section>
  );
}
