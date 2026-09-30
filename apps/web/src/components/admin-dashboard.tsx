"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AdminAccountDeletion } from "@/components/admin-account-deletion";
import { AdminDiagnosticReset } from "@/components/admin-diagnostic-reset";
import { Button } from "@/components/ui/button";
import { ApiRequestError } from "@/lib/api/errors";
import {
  adminRequest,
  type Overview,
  type Students,
  type StudentDetail,
  type Diagnostics,
  type Questions,
  type Users,
  type Role,
  type Preview,
  type MigrationInput,
  type Operations,
  type ContentStatus,
  type Audit,
  type Reports,
  type Report,
} from "@/lib/api/admin-dashboard";

function useResource<T>(path: string) {
  const [revision, setRevision] = useState(0);
  const key = path + ":" + revision;
  const [state, setState] = useState<{ key: string; data?: T; error?: string }>(
    { key: "" },
  );
  useEffect(() => {
    let active = true;
    void adminRequest<T>(path).then(
      (data) => {
        if (active) setState({ key, data });
      },
      (error: unknown) => {
        if (active) setState({ key, error: message(error) });
      },
    );
    return () => {
      active = false;
    };
  }, [path, key]);
  return {
    data: state.key === key ? state.data : undefined,
    error: state.key === key ? state.error : undefined,
    reload: () => setRevision((n) => n + 1),
  };
}
function message(error: unknown) {
  if (error instanceof ApiRequestError)
    return `${error.message}${error.requestId ? ` Request ID: ${error.requestId}` : ""}`;
  return error instanceof Error
    ? error.message
    : "The operation could not be completed.";
}
function pretty(key: string) {
  return key.replaceAll("_", " ");
}
function date(value: string | null) {
  return value ? new Date(value).toLocaleString("en-SG") : "No activity";
}
function State({ error, reload }: { error?: string; reload: () => void }) {
  return (
    <div className="status-card" role={error ? "alert" : "status"}>
      {error ?? "Loading administrator data…"}
      {error && (
        <Button variant="outline" onClick={reload}>
          Retry
        </Button>
      )}
    </div>
  );
}
function Metrics({ values }: { values: Record<string, number | string> }) {
  return (
    <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {Object.entries(values).map(([key, value]) => (
        <div
          className="rounded-2xl border border-slate-200 bg-white p-5"
          key={key}
        >
          <dt className="text-sm capitalize text-slate-600">{pretty(key)}</dt>
          <dd className="mt-2 text-3xl font-bold">{value}</dd>
        </div>
      ))}
    </dl>
  );
}
function Table({
  headers,
  children,
}: {
  headers: string[];
  children: React.ReactNode;
}) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white">
      <table className="w-full text-left text-sm">
        <thead className="bg-slate-100">
          <tr>
            {headers.map((title) => (
              <th className="p-4 font-semibold" scope="col" key={title}>
                {title}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="[&_td]:p-4 [&_tr]:border-t [&_tr]:border-slate-100">
          {children}
        </tbody>
      </table>
    </div>
  );
}
function Pager({
  offset,
  total,
  onChange,
}: {
  offset: number;
  total: number;
  onChange: (offset: number) => void;
}) {
  return (
    <div className="flex items-center justify-between gap-3">
      <Button
        variant="outline"
        disabled={offset === 0}
        onClick={() => onChange(Math.max(0, offset - 25))}
      >
        Previous
      </Button>
      <span>
        {total ? offset + 1 : 0}–{Math.min(offset + 25, total)} of {total}
      </span>
      <Button
        variant="outline"
        disabled={offset + 25 >= total}
        onClick={() => onChange(offset + 25)}
      >
        Next
      </Button>
    </div>
  );
}
function Search({ onSearch }: { onSearch: (value: string) => void }) {
  return (
    <form
      className="flex flex-wrap gap-3"
      onSubmit={(event) => {
        event.preventDefault();
        onSearch(
          String(new FormData(event.currentTarget).get("search") ?? "").trim(),
        );
      }}
    >
      <label className="grow">
        Search name or email
        <input
          className="mt-1 block w-full rounded-lg border bg-white p-3"
          name="search"
          maxLength={100}
          type="search"
        />
      </label>
      <Button className="self-end" type="submit">
        Search
      </Button>
    </form>
  );
}
export function OverviewPanel() {
  const { data, error, reload } = useResource<Overview>("analytics/overview");
  if (!data) return <State error={error} reload={reload} />;
  return (
    <div className="space-y-6">
      <p>
        Aggregate student activity. An attempt is one submitted answer; accuracy
        is not a mastery score.
      </p>
      <Metrics values={data} />
      <Button variant="outline" onClick={reload}>
        Refresh metrics
      </Button>
    </div>
  );
}
export function StudentsPanel() {
  const [search, setSearch] = useState("");
  const [offset, setOffset] = useState(0);
  const query = new URLSearchParams({
    limit: "25",
    offset: String(offset),
    ...(search ? { search } : {}),
  });
  const { data, error, reload } = useResource<Students>(`students?${query}`);
  return (
    <div className="space-y-5">
      <Search
        onSearch={(value) => {
          setSearch(value);
          setOffset(0);
        }}
      />
      {!data ? (
        <State error={error} reload={reload} />
      ) : (
        <>
          {!data.total ? (
            <p>
              No students match this search. Administrators appear under Users &
              roles.
            </p>
          ) : (
            <Table
              headers={[
                "Student",
                "Enrolment",
                "Attempts / accuracy",
                "Mastered",
                "Retries",
                "Last activity",
              ]}
            >
              {data.students.map((student) => (
                <tr key={student.learner_id}>
                  <td>
                    <Link
                      className="font-semibold text-teal-800 underline"
                      href={`/admin/students/${student.learner_id}`}
                    >
                      {student.display_name ?? student.email}
                    </Link>
                    <p>{student.email}</p>
                  </td>
                  <td>{pretty(student.enrolment_status)}</td>
                  <td>
                    {student.attempts} /{" "}
                    {student.attempts
                      ? `${student.accuracy_percentage}%`
                      : "No attempts"}
                  </td>
                  <td>{student.lessons_mastered}</td>
                  <td>{student.retry_question_count}</td>
                  <td>{date(student.last_activity_at)}</td>
                </tr>
              ))}
            </Table>
          )}
          <Pager offset={offset} total={data.total} onChange={setOffset} />
        </>
      )}
    </div>
  );
}
export function StudentPanel({
  learnerId,
  academic = false,
}: {
  learnerId: string;
  academic?: boolean;
}) {
  const { data, error, reload } = useResource<StudentDetail>(
    `students/${encodeURIComponent(learnerId)}`,
  );
  const diagnostics = useResource<Diagnostics>(
    `students/${encodeURIComponent(learnerId)}/diagnostics`,
  );
  if (!data) return <State error={error} reload={reload} />;
  return (
    <div className="space-y-5">
      <Link className="text-teal-800 underline" href="/admin/students">
        Back to students
      </Link>
      <h2 className="text-2xl font-bold">
        {data.student.display_name ?? data.student.email}
      </h2>
      <p>{data.student.email}</p>
      <Metrics
        values={{
          attempts: data.student.attempts,
          accuracy: data.student.attempts
            ? `${data.student.accuracy_percentage}%`
            : "No attempts",
          mastered: data.student.lessons_mastered,
          retries: data.student.retry_question_count,
        }}
      />
      <h3 className="text-xl font-bold">Mathematics readiness evidence</h3>
      {!diagnostics.data ? (
        <State error={diagnostics.error} reload={diagnostics.reload} />
      ) : !diagnostics.data.baseline && !diagnostics.data.endline ? (
        <p>No submitted diagnostic evidence yet.</p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {(["baseline", "endline"] as const).map((purpose) => {
            const result = diagnostics.data?.[purpose];
            return (
              <div
                className="rounded-2xl border border-slate-200 bg-white p-5"
                key={purpose}
              >
                <p className="mb-1 text-sm font-bold uppercase tracking-wide text-teal-700">
                  {purpose}
                </p>
                {result ? (
                  <>
                    <p className="my-1 text-3xl font-black">
                      {result.percentage}%
                    </p>
                    <p className="m-0 capitalize text-slate-600">
                      {pretty(result.band)}
                    </p>
                    <p className="mb-0 mt-3 text-sm text-slate-500">
                      Priorities:{" "}
                      {result.priorities.length
                        ? result.priorities.join(", ")
                        : "none"}
                    </p>
                    {academic ? (
                      <AdminDiagnosticReset
                        learnerId={learnerId}
                        purpose={purpose}
                        onReset={diagnostics.reload}
                      />
                    ) : null}
                  </>
                ) : (
                  <p className="mb-0 text-slate-500">Not completed</p>
                )}
              </div>
            );
          })}
        </div>
      )}
      <h3 className="text-xl font-bold">Lesson progress</h3>
      {!data.lessons.length ? (
        <p>No lesson progress yet.</p>
      ) : (
        <Table
          headers={[
            "Lesson",
            "State",
            "Resolved",
            "Eventual accuracy",
            "Checkpoint",
            "Updated",
          ]}
        >
          {data.lessons.map((lesson) => (
            <tr key={lesson.lesson_key}>
              <td>{lesson.lesson_title}</td>
              <td>{pretty(lesson.state)}</td>
              <td>
                {lesson.resolved_count}/{lesson.question_count}
              </td>
              <td>{lesson.eventual_correct_percentage}%</td>
              <td>{lesson.checkpoint_passed ? "Passed" : "Not passed"}</td>
              <td>{date(lesson.updated_at)}</td>
            </tr>
          ))}
        </Table>
      )}
      <h3 className="text-xl font-bold">Performance by difficulty</h3>
      {!data.difficulty_performance.length ? (
        <p>No attempts yet.</p>
      ) : (
        <Table headers={["Difficulty", "Attempts", "Correct", "Accuracy"]}>
          {data.difficulty_performance.map((item) => (
            <tr key={item.difficulty}>
              <td>{item.difficulty}</td>
              <td>{item.attempts}</td>
              <td>{item.correct_attempts}</td>
              <td>{item.accuracy_percentage}%</td>
            </tr>
          ))}
        </Table>
      )}
      {academic ? (
        <AdminAccountDeletion
          learnerId={learnerId}
          studentEmail={data.student.email}
        />
      ) : null}
    </div>
  );
}
export function QuestionsPanel() {
  const [difficulty, setDifficulty] = useState("");
  const [outcome, setOutcome] = useState("");
  const [offset, setOffset] = useState(0);
  const query = new URLSearchParams({
    limit: "25",
    offset: String(offset),
    ...(difficulty ? { difficulty } : {}),
    ...(outcome ? { outcome } : {}),
  });
  const { data, error, reload } = useResource<Questions>(
    `analytics/questions?${query}`,
  );
  return (
    <div className="space-y-5">
      <form
        className="flex flex-wrap items-end gap-4"
        onSubmit={(event) => {
          event.preventDefault();
          const form = new FormData(event.currentTarget);
          setDifficulty(String(form.get("difficulty") ?? ""));
          setOutcome(String(form.get("outcome") ?? "").trim());
          setOffset(0);
        }}
      >
        <label>
          Difficulty
          <select
            className="ml-2 rounded border bg-white p-3"
            name="difficulty"
          >
            <option value="">All</option>
            {[1, 2, 3].map((n) => (
              <option key={n}>{n}</option>
            ))}
          </select>
        </label>
        <label>
          Outcome
          <input
            className="ml-2 rounded border bg-white p-3"
            name="outcome"
            placeholder="e.g. 1.1"
            maxLength={40}
          />
        </label>
        <Button type="submit">Apply filters</Button>
      </form>
      {!data ? (
        <State error={error} reload={reload} />
      ) : (
        <>
          {!data.total ? (
            <p>No matching questions.</p>
          ) : (
            <Table
              headers={[
                "Question",
                "Difficulty / outcome",
                "Attempts",
                "Accuracy",
                "Hints",
                "Give-ups",
                "Retries",
              ]}
            >
              {data.questions.map((question) => (
                <tr key={question.question_key}>
                  <td>
                    <strong>{question.title}</strong>
                    <p>{question.question_key}</p>
                  </td>
                  <td>
                    {question.difficulty} / {question.outcome_code}
                  </td>
                  <td>
                    {question.attempt_count} ({question.unique_students}{" "}
                    students)
                  </td>
                  <td>
                    {question.attempt_count
                      ? `${question.accuracy_percentage}%`
                      : "No attempts"}
                  </td>
                  <td>{question.hint_reveals}</td>
                  <td>{question.give_up_count}</td>
                  <td>{question.queued_for_retry_students}</td>
                </tr>
              ))}
            </Table>
          )}
          <Pager offset={offset} total={data.total} onChange={setOffset} />
        </>
      )}
    </div>
  );
}
function UserActions({
  user,
  selfId,
  reload,
}: {
  user: Users["users"][number];
  selfId: string;
  reload: () => void;
}) {
  const [role, setRole] = useState<Role>(user.role);
  const [confirm, setConfirm] = useState(false);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("");
  async function act(
    action: () => Promise<unknown>,
    done: string,
    refresh = true,
  ) {
    setBusy(true);
    setStatus("");
    try {
      await action();
      setStatus(done);
      if (refresh) reload();
    } catch (error) {
      setStatus(message(error));
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <select
          aria-label={`Role for ${user.email}`}
          className="rounded border p-2"
          disabled={busy || user.learner_id === selfId}
          value={role}
          onChange={(event) => {
            setRole(event.target.value as Role);
            setConfirm(false);
          }}
        >
          {(["student", "content_admin", "academic_admin"] as const).map(
            (value) => (
              <option key={value} value={value}>
                {pretty(value)}
              </option>
            ),
          )}
        </select>
        <Button
          variant="outline"
          disabled={busy || role === user.role || user.learner_id === selfId}
          onClick={() => setConfirm(true)}
        >
          Review role change
        </Button>
      </div>
      {user.learner_id === selfId && (
        <p className="text-sm text-slate-600">
          Your own role cannot be changed here.
        </p>
      )}
      {confirm && (
        <div className="rounded border border-amber-300 bg-amber-50 p-3">
          <p>
            Change {user.email} from {pretty(user.role)} to {pretty(role)}?
          </p>
          <Button
            disabled={busy}
            onClick={() =>
              void act(
                () =>
                  adminRequest(
                    `users/${user.learner_id}/role`,
                    { role },
                    "PATCH",
                  ),
                "Role updated.",
              )
            }
          >
            Confirm role change
          </Button>
          <Button
            variant="outline"
            disabled={busy}
            onClick={() => setConfirm(false)}
          >
            Cancel
          </Button>
        </div>
      )}
      {user.enrolments.map((enrolment) => (
        <div key={enrolment.course_key}>
          <p>
            {enrolment.course_key} · revision {enrolment.course_revision} ·{" "}
            {enrolment.status}
          </p>
          {enrolment.status === "active" && (
            <Button
              variant="outline"
              disabled={busy}
              onClick={() => {
                setPreview(null);
                void act(
                  async () =>
                    setPreview(
                      await adminRequest<Preview>(
                        `users/${user.learner_id}/curriculum-preview?course_key=${encodeURIComponent(enrolment.course_key)}`,
                      ),
                    ),
                  "",
                  false,
                );
              }}
            >
              Preview course update
            </Button>
          )}
        </div>
      ))}
      {preview && (
        <div className="rounded border bg-slate-50 p-4">
          <p className="font-semibold">
            Course revision {preview.from_revision} → {preview.target_revision}
          </p>
          <p>
            Active sessions: {preview.active_sessions}. Progress needing review:{" "}
            {preview.incompatible_lessons.join(", ") || "none"}.
          </p>
          {preview.blockers.map((blocker) => (
            <p key={blocker} className="text-amber-900">
              {blocker}
            </p>
          ))}
          {preview.allowed && (
            <>
              <label className="block">
                Reason for update
                <input
                  aria-label="Reason for course update"
                  className="my-2 block w-full rounded border bg-white p-2"
                  minLength={10}
                  maxLength={500}
                  value={reason}
                  onChange={(event) => setReason(event.target.value)}
                />
              </label>
              <Button
                disabled={busy || reason.trim().length < 10}
                onClick={() => {
                  const body: MigrationInput = {
                    course_key: preview.course_key,
                    from_revision: preview.from_revision,
                    target_revision: preview.target_revision,
                    target_hash: preview.target_hash,
                    reason: reason.trim(),
                  };
                  void act(
                    () =>
                      adminRequest(
                        `users/${user.learner_id}/curriculum-migration`,
                        body,
                      ),
                    "Course updated.",
                  );
                }}
              >
                Confirm course update
              </Button>
            </>
          )}
        </div>
      )}
      {status && (
        <p role="status" className="text-sm">
          {status}
        </p>
      )}
    </div>
  );
}
export function UsersPanel({ selfId }: { selfId: string }) {
  const [search, setSearch] = useState("");
  const [offset, setOffset] = useState(0);
  const query = new URLSearchParams({
    limit: "25",
    offset: String(offset),
    ...(search ? { search } : {}),
  });
  const { data, error, reload } = useResource<Users>(`users?${query}`);
  return (
    <div className="space-y-5">
      <Search
        onSearch={(value) => {
          setSearch(value);
          setOffset(0);
        }}
      />
      {!data ? (
        <State error={error} reload={reload} />
      ) : (
        <>
          {!data.total ? (
            <p>No registered profiles match.</p>
          ) : (
            <Table headers={["User", "Role and course access"]}>
              {data.users.map((user) => (
                <tr key={user.learner_id}>
                  <td>
                    <strong>{user.display_name ?? "Unnamed user"}</strong>
                    <p>{user.email}</p>
                  </td>
                  <td>
                    <UserActions user={user} selfId={selfId} reload={reload} />
                  </td>
                </tr>
              ))}
            </Table>
          )}
          <Pager offset={offset} total={data.total} onChange={setOffset} />
        </>
      )}
    </div>
  );
}
export function OperationsPanel() {
  const service = useResource<Operations>("operations/status");
  const content = useResource<ContentStatus>("operations/content");
  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold">Service and database</h2>
      {!service.data ? (
        <State error={service.error} reload={service.reload} />
      ) : (
        <>
          <Metrics
            values={{
              database: service.data.database.state,
              environment: service.data.environment,
              uptime_seconds: Math.round(service.data.uptime_seconds),
              database_latency_ms: service.data.database.latency_ms,
            }}
          />
          <p className="break-all">
            Release: {service.data.release.sha} · schema:{" "}
            {service.data.release.required_schema_revision}
          </p>
          <p>Checked {date(service.data.checked_at)}</p>
          <Metrics values={service.data.database.resources} />
        </>
      )}
      <h2 className="text-xl font-bold">Imported content</h2>
      {!content.data ? (
        <State error={content.error} reload={content.reload} />
      ) : (
        <Metrics
          values={{
            status: content.data.status,
            revision: content.data.course_revision,
            lessons: content.data.lessons,
            questions: content.data.questions,
          }}
        />
      )}
      <Button
        variant="outline"
        onClick={() => {
          service.reload();
          content.reload();
        }}
      >
        Refresh status
      </Button>
      <p className="text-sm text-slate-600">
        This page checks the current API and database. Request logs and
        historical availability are available in the hosting platform and GitHub
        workflow runs.
      </p>
    </div>
  );
}
export function AuditPanel() {
  const { data, error, reload } = useResource<Audit>("audit-events?limit=100");
  if (!data) return <State error={error} reload={reload} />;
  return (
    <div className="space-y-5">
      <p>Latest 100 administrative events. Entries are append-only.</p>
      {!data.events.length ? (
        <p>No administrative events yet.</p>
      ) : (
        <Table
          headers={["When", "Event", "Actor / target", "Details", "Request"]}
        >
          {data.events.map((event) => (
            <tr key={event.event_id}>
              <td>{date(event.created_at)}</td>
              <td>{pretty(event.event_type)}</td>
              <td className="break-all">
                {event.actor_user_id ?? "System"}
                <p>{event.target_user_id ?? event.invitation_id ?? ""}</p>
              </td>
              <td>
                <pre className="max-w-md whitespace-pre-wrap break-all text-xs">
                  {JSON.stringify(event.metadata, null, 2)}
                </pre>
              </td>
              <td className="break-all">{event.request_id}</td>
            </tr>
          ))}
        </Table>
      )}
      <Button variant="outline" onClick={reload}>
        Refresh audit trail
      </Button>
    </div>
  );
}

export function ReportsPanel() {
  const [status, setStatus] = useState("open");
  const [offset, setOffset] = useState(0);
  const [revision, setRevision] = useState(0);
  const [decision, setDecision] = useState<{
    reportId: string;
    status: "resolved" | "dismissed";
  } | null>(null);
  const [resolution, setResolution] = useState("");
  const [busyReportId, setBusyReportId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const query = new URLSearchParams({
    status,
    limit: "25",
    offset: String(offset),
    revision: String(revision),
  });
  const { data, error, reload } = useResource<Reports>(
    "question-reports?" + query.toString(),
  );

  async function update(
    reportId: string,
    nextStatus: "in_review" | "resolved" | "dismissed",
    resolutionText: string | null = null,
  ) {
    setBusyReportId(reportId);
    setActionError(null);
    try {
      await adminRequest<Report>(
        "question-reports/" + encodeURIComponent(reportId),
        { status: nextStatus, resolution: resolutionText },
        "PATCH",
      );
      setDecision(null);
      setResolution("");
      setRevision((value) => value + 1);
      reload();
    } catch (caught) {
      setActionError(message(caught));
    } finally {
      setBusyReportId(null);
    }
  }

  return (
    <div className="space-y-5">
      <p className="max-w-3xl text-sm leading-6 text-slate-600">
        Review learner reports against the immutable question revision. A
        resolution is shown to the learner and recorded in the audit trail.
      </p>
      <label className="block max-w-xs text-sm font-bold">
        Status
        <select
          className="mt-1 block w-full rounded-lg border bg-white p-3"
          onChange={(event) => {
            setStatus(event.target.value);
            setOffset(0);
            setDecision(null);
            setActionError(null);
          }}
          value={status}
        >
          <option value="open">Open</option>
          <option value="in_review">In review</option>
          <option value="resolved">Resolved</option>
          <option value="dismissed">Dismissed</option>
        </select>
      </label>
      {actionError ? (
        <p
          className="rounded-xl bg-rose-50 p-3 text-sm text-rose-800"
          role="alert"
        >
          {actionError}
        </p>
      ) : null}
      {!data ? (
        <State error={error} reload={reload} />
      ) : !data.reports.length ? (
        <p>No reports in this state.</p>
      ) : (
        <div className="space-y-4">
          {data.reports.map((report) => {
            const deciding = decision?.reportId === report.report_id;
            return (
              <article
                className="rounded-2xl border border-slate-200 bg-white p-5"
                key={report.report_id}
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="m-0 text-xs font-bold uppercase text-teal-700">
                      {pretty(report.category)} · {report.question_key} r
                      {report.question_revision}
                    </p>
                    <h2 className="mt-1 text-xl font-bold">
                      {report.question_title}
                    </h2>
                  </div>
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-sm font-semibold capitalize">
                    {pretty(report.status)}
                  </span>
                </div>
                <p className="text-sm text-slate-500">
                  {report.learner_email} · {date(report.created_at)}
                </p>
                <p className="whitespace-pre-wrap">{report.comment}</p>
                {report.resolution ? (
                  <p className="rounded-xl bg-emerald-50 p-3">
                    <strong>Resolution:</strong> {report.resolution}
                  </p>
                ) : null}
                {report.status === "open" ? (
                  <Button
                    disabled={busyReportId === report.report_id}
                    onClick={() => void update(report.report_id, "in_review")}
                  >
                    {busyReportId === report.report_id
                      ? "Updating…"
                      : "Start review"}
                  </Button>
                ) : null}
                {report.status === "in_review" && !deciding ? (
                  <div className="flex flex-wrap gap-2">
                    <Button
                      onClick={() => {
                        setDecision({
                          reportId: report.report_id,
                          status: "resolved",
                        });
                        setResolution("");
                        setActionError(null);
                      }}
                    >
                      Resolve
                    </Button>
                    <Button
                      onClick={() => {
                        setDecision({
                          reportId: report.report_id,
                          status: "dismissed",
                        });
                        setResolution("");
                        setActionError(null);
                      }}
                      variant="outline"
                    >
                      Dismiss
                    </Button>
                  </div>
                ) : null}
                {report.status === "in_review" && deciding ? (
                  <div className="mt-4 space-y-3 rounded-xl border border-amber-200 bg-amber-50 p-4">
                    <p className="m-0 font-bold capitalize">
                      {decision.status === "resolved"
                        ? "Resolve report"
                        : "Dismiss report"}
                    </p>
                    <label
                      className="block text-sm font-bold"
                      htmlFor={"report-resolution-" + report.report_id}
                    >
                      Resolution shown to the learner
                    </label>
                    <textarea
                      className="block min-h-24 w-full rounded-lg border bg-white p-3"
                      id={"report-resolution-" + report.report_id}
                      maxLength={2000}
                      onChange={(event) => setResolution(event.target.value)}
                      value={resolution}
                    />
                    <div className="flex flex-wrap gap-2">
                      <Button
                        disabled={
                          resolution.trim().length < 3 ||
                          busyReportId === report.report_id
                        }
                        onClick={() =>
                          void update(
                            report.report_id,
                            decision.status,
                            resolution.trim(),
                          )
                        }
                      >
                        {busyReportId === report.report_id
                          ? "Saving…"
                          : decision.status === "resolved"
                            ? "Confirm resolution"
                            : "Confirm dismissal"}
                      </Button>
                      <Button
                        disabled={busyReportId === report.report_id}
                        onClick={() => {
                          setDecision(null);
                          setResolution("");
                        }}
                        variant="outline"
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                ) : null}
              </article>
            );
          })}
          <Pager offset={offset} total={data.total} onChange={setOffset} />
        </div>
      )}
    </div>
  );
}
