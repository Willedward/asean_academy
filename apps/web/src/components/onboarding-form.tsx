"use client";

import { CircleAlert, LoaderCircle, TicketCheck } from "lucide-react";
import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";

import { Button } from "@/components/ui/button";
import { acceptBetaInvitation, type InvitationAcceptanceResponse } from "@/lib/api/identity";
import { ApiRequestError } from "@/lib/api/errors";

type Props = {
  email: string | null;
  initialCode?: string;
  acceptInvitation?: (
    invitationCode: string,
    displayName: string,
  ) => Promise<InvitationAcceptanceResponse>;
};

export function OnboardingForm({
  email,
  initialCode = "",
  acceptInvitation = acceptBetaInvitation,
}: Props) {
  const router = useRouter();
  const [displayName, setDisplayName] = useState("");
  const [invitationCode, setInvitationCode] = useState(initialCode);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await acceptInvitation(invitationCode.trim(), displayName.trim());
      router.replace("/learn");
      router.refresh();
    } catch (caught) {
      const suffix = caught instanceof ApiRequestError && caught.requestId
        ? ` Request ID: ${caught.requestId}`
        : "";
      setError(
        `${caught instanceof Error ? caught.message : "The invitation could not be accepted."}${suffix}`,
      );
      setSubmitting(false);
    }
  }

  return (
    <form className="space-y-5" onSubmit={(event) => void submit(event)}>
      <div>
        <label className="mb-2 block text-sm font-bold text-slate-800" htmlFor="student-email">
          Signed-in email
        </label>
        <input
          className="w-full rounded-xl border border-slate-200 bg-slate-100 px-4 py-3 text-slate-600"
          id="student-email"
          readOnly
          value={email ?? "Verified Google account"}
        />
        <p className="mb-0 mt-2 text-xs leading-5 text-slate-500">
          This must match the email address on the beta invitation.
        </p>
      </div>

      <div>
        <label className="mb-2 block text-sm font-bold text-slate-800" htmlFor="display-name">
          Name shown in the academy
        </label>
        <input
          autoComplete="name"
          className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 outline-none focus:border-teal-600 focus:ring-2 focus:ring-teal-100"
          id="display-name"
          maxLength={80}
          minLength={1}
          onChange={(event) => setDisplayName(event.target.value)}
          placeholder="Your preferred name"
          required
          value={displayName}
        />
      </div>

      <div>
        <label className="mb-2 block text-sm font-bold text-slate-800" htmlFor="invitation-code">
          Beta invitation code
        </label>
        <input
          autoCapitalize="none"
          autoComplete="one-time-code"
          className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 font-mono outline-none focus:border-teal-600 focus:ring-2 focus:ring-teal-100"
          id="invitation-code"
          maxLength={300}
          minLength={16}
          onChange={(event) => setInvitationCode(event.target.value)}
          placeholder="Paste the code you received"
          required
          spellCheck={false}
          value={invitationCode}
        />
      </div>

      {error ? (
        <div className="flex gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-900" role="alert">
          <CircleAlert aria-hidden="true" className="size-5 shrink-0" />
          <span>{error}</span>
        </div>
      ) : null}

      <Button className="w-full py-3" disabled={submitting} type="submit">
        {submitting ? (
          <><LoaderCircle aria-hidden="true" className="mr-2 size-4 animate-spin" />Checking invitation…</>
        ) : (
          <><TicketCheck aria-hidden="true" className="mr-2 size-4" />Join the beta course</>
        )}
      </Button>
    </form>
  );
}
