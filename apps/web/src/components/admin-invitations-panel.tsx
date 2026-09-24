"use client";

import {
  Ban,
  Check,
  CircleAlert,
  Clipboard,
  LoaderCircle,
  RefreshCw,
  Send,
  type LucideIcon,
  Users,
} from "lucide-react";
import { type FormEvent, useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  createInvitation,
  getOperationsSummary,
  listAuditEvents,
  listInvitations,
  revokeInvitation,
  type AuditEventList,
  type CreatedInvitation,
  type Invitation,
  type InvitationList,
  type OperationsSummary,
} from "@/lib/api/admin";
import { ApiRequestError } from "@/lib/api/errors";

type AdminApi = {
  listInvitations: () => Promise<InvitationList>;
  createInvitation: typeof createInvitation;
  revokeInvitation: typeof revokeInvitation;
  getOperationsSummary: () => Promise<OperationsSummary>;
  listAuditEvents: () => Promise<AuditEventList>;
};

const defaultApi: AdminApi = {
  listInvitations,
  createInvitation,
  revokeInvitation,
  getOperationsSummary,
  listAuditEvents,
};

const statusClasses: Record<Invitation["status"], string> = {
  active: "bg-emerald-100 text-emerald-800",
  expired: "bg-slate-100 text-slate-700",
  exhausted: "bg-violet-100 text-violet-800",
  revoked: "bg-rose-100 text-rose-800",
};

const eventLabels = {
  invitation_created: "Invitation created",
  invitation_revoked: "Invitation revoked",
  invitation_accepted: "Student onboarded",
} as const;

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en-SG", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function errorMessage(caught: unknown): string {
  if (caught instanceof ApiRequestError && caught.requestId) {
    return `${caught.message} Request ID: ${caught.requestId}`;
  }
  return caught instanceof Error ? caught.message : "The beta operation could not be completed.";
}

export function AdminInvitationsPanel({ api = defaultApi }: { api?: AdminApi }) {
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [summary, setSummary] = useState<OperationsSummary | null>(null);
  const [audit, setAudit] = useState<AuditEventList["events"]>([]);
  const [created, setCreated] = useState<CreatedInvitation | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [revoking, setRevoking] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [invitationResult, summaryResult, auditResult] = await Promise.all([
        api.listInvitations(),
        api.getOperationsSummary(),
        api.listAuditEvents(),
      ]);
      setInvitations(invitationResult.invitations);
      setSummary(summaryResult);
      setAudit(auditResult.events);
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    let cancelled = false;
    void Promise.all([
      api.listInvitations(),
      api.getOperationsSummary(),
      api.listAuditEvents(),
    ])
      .then(([invitationResult, summaryResult, auditResult]) => {
        if (cancelled) return;
        setInvitations(invitationResult.invitations);
        setSummary(summaryResult);
        setAudit(auditResult.events);
      })
      .catch((caught: unknown) => {
        if (!cancelled) setError(errorMessage(caught));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [api]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    setSubmitting(true);
    setCreated(null);
    setCopied(false);
    setError(null);
    try {
      const result = await api.createInvitation({
        email: String(form.get("email") ?? "").trim(),
        course_key: "g3-sec1-math",
        expires_days: Number(form.get("expires_days")),
        max_uses: Number(form.get("max_uses")),
      });
      setCreated(result);
      formElement.reset();
      await load();
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setSubmitting(false);
    }
  }

  async function revoke(invitationId: string) {
    setRevoking(invitationId);
    setError(null);
    try {
      await api.revokeInvitation(invitationId);
      await load();
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setRevoking(null);
    }
  }

  async function copyOnboardingLink() {
    if (!created) return;
    const url = new URL("/onboarding", window.location.origin);
    url.searchParams.set("code", created.invitation_code);
    try {
      await navigator.clipboard.writeText(url.toString());
      setCopied(true);
    } catch {
      setError("The onboarding link could not be copied. Copy the invitation code manually.");
    }
  }

  const summaryCards: Array<{
    label: string;
    value: number | undefined;
    icon: LucideIcon;
  }> = [
    { label: "Active students", value: summary?.active_students, icon: Users },
    { label: "Joined in 7 days", value: summary?.enrolments_last_7_days, icon: Check },
    { label: "Active invitations", value: summary?.invitations_active, icon: Send },
    {
      label: "Expired or revoked",
      value: summary
        ? summary.invitations_expired + summary.invitations_revoked
        : undefined,
      icon: Ban,
    },
  ];

  return (
    <div className="space-y-8">
      {error ? (
        <div className="flex gap-3 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-950" role="alert">
          <CircleAlert aria-hidden="true" className="size-5 shrink-0" />
          <span className="grow">{error}</span>
          <button className="font-bold underline" onClick={() => setError(null)} type="button">Dismiss</button>
        </div>
      ) : null}

      <section aria-label="Beta operations summary" className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {summaryCards.map(({ label, value, icon: Icon }) => (
          <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm" key={label}>
            <Icon aria-hidden="true" className="mb-3 size-5 text-teal-700" />
            <strong className="block text-3xl font-black">{loading ? "—" : String(value ?? 0)}</strong>
            <span className="text-sm text-slate-500">{label}</span>
          </article>
        ))}
      </section>

      <section className="grid gap-6 lg:grid-cols-[0.8fr_1.2fr]" aria-labelledby="issue-invitation-title">
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="mt-0 text-2xl font-extrabold" id="issue-invitation-title">Issue an invitation</h2>
          <form className="space-y-4" onSubmit={(event) => void submit(event)}>
            <div>
              <label className="mb-2 block text-sm font-bold" htmlFor="invitation-email">Student email</label>
              <input className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-teal-600 focus:ring-2 focus:ring-teal-100" id="invitation-email" name="email" placeholder="student@example.com" required type="email" />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-2 block text-sm font-bold" htmlFor="expires-days">Expires after</label>
                <select className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3" defaultValue="14" id="expires-days" name="expires_days">
                  <option value="7">7 days</option>
                  <option value="14">14 days</option>
                  <option value="30">30 days</option>
                </select>
              </div>
              <div>
                <label className="mb-2 block text-sm font-bold" htmlFor="max-uses">Usage limit</label>
                <input className="w-full rounded-xl border border-slate-300 px-4 py-3" defaultValue="1" id="max-uses" max="100" min="1" name="max_uses" required type="number" />
              </div>
            </div>
            <Button className="w-full py-3" disabled={submitting} type="submit">
              {submitting ? <><LoaderCircle aria-hidden="true" className="mr-2 size-4 animate-spin" />Creating…</> : <><Send aria-hidden="true" className="mr-2 size-4" />Create invitation</>}
            </Button>
          </form>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="mt-0 text-2xl font-extrabold">New invitation handoff</h2>
          {created ? (
            <div className="space-y-4">
              <p className="rounded-xl border border-amber-300 bg-amber-50 p-3 text-sm leading-6 text-amber-950">
                Copy this now. The raw code cannot be retrieved after this screen is cleared or reloaded.
              </p>
              <div>
                <span className="text-sm font-semibold text-slate-500">For {created.email}</span>
                <code className="mt-2 block break-all rounded-xl bg-slate-950 p-4 text-sm text-teal-200">{created.invitation_code}</code>
              </div>
              <Button onClick={() => void copyOnboardingLink()} type="button" variant="outline">
                {copied ? <Check aria-hidden="true" className="mr-2 size-4" /> : <Clipboard aria-hidden="true" className="mr-2 size-4" />}
                {copied ? "Onboarding link copied" : "Copy onboarding link"}
              </Button>
            </div>
          ) : (
            <div className="flex min-h-48 items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center text-sm leading-6 text-slate-500">
              A newly created invitation code will appear here once. Existing invitation codes cannot be recovered.
            </div>
          )}
        </div>
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white shadow-sm" aria-labelledby="invitations-title">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 p-6">
          <div><h2 className="m-0 text-2xl font-extrabold" id="invitations-title">Recent invitations</h2><p className="mb-0 mt-1 text-sm text-slate-500">Codes are deliberately excluded from this list.</p></div>
          <Button disabled={loading} onClick={() => void load()} type="button" variant="outline"><RefreshCw aria-hidden="true" className={`mr-2 size-4 ${loading ? "animate-spin" : ""}`} />Refresh</Button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-3xl border-collapse text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500"><tr><th className="px-6 py-3">Student</th><th className="px-6 py-3">Course</th><th className="px-6 py-3">Status</th><th className="px-6 py-3">Usage</th><th className="px-6 py-3">Expires</th><th className="px-6 py-3"><span className="sr-only">Actions</span></th></tr></thead>
            <tbody>
              {invitations.map((invitation) => (
                <tr className="border-t border-slate-100" key={invitation.invitation_id}>
                  <td className="px-6 py-4 font-semibold">{invitation.email}</td>
                  <td className="px-6 py-4 text-slate-600">{invitation.course_key} · r{invitation.course_revision}</td>
                  <td className="px-6 py-4"><span className={`rounded-full px-2.5 py-1 text-xs font-bold capitalize ${statusClasses[invitation.status]}`}>{invitation.status}</span></td>
                  <td className="px-6 py-4 text-slate-600">{invitation.use_count}/{invitation.max_uses}</td>
                  <td className="px-6 py-4 text-slate-600">{formatDate(invitation.expires_at)}</td>
                  <td className="px-6 py-4 text-right">{invitation.status === "active" ? <Button disabled={revoking === invitation.invitation_id} onClick={() => void revoke(invitation.invitation_id)} type="button" variant="outline">{revoking === invitation.invitation_id ? "Revoking…" : "Revoke"}</Button> : null}</td>
                </tr>
              ))}
              {!loading && invitations.length === 0 ? <tr><td className="px-6 py-8 text-center text-slate-500" colSpan={6}>No invitations have been issued.</td></tr> : null}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm" aria-labelledby="audit-title">
        <h2 className="mt-0 text-2xl font-extrabold" id="audit-title">Recent audit trail</h2>
        <ol className="m-0 grid list-none gap-3 p-0">
          {audit.map((event) => (
            <li className="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-slate-50 p-4" key={event.event_id}>
              <div><strong>{eventLabels[event.event_type]}</strong><p className="mb-0 mt-1 font-mono text-xs text-slate-500">Request {event.request_id}</p></div>
              <time className="text-sm text-slate-500" dateTime={event.created_at}>{formatDate(event.created_at)}</time>
            </li>
          ))}
          {!loading && audit.length === 0 ? <li className="text-sm text-slate-500">No beta operations have been recorded.</li> : null}
        </ol>
      </section>
    </div>
  );
}
