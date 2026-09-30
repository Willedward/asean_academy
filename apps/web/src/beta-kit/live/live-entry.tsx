import {
  AlertCircle,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  LoaderCircle,
  LogOut,
  Mail,
  ShieldCheck,
  TicketCheck,
} from "lucide-react";
import type { FormEventHandler, ReactNode } from "react";

import { Hornbill } from "../components/hornbill";
import {
  Avatar,
  Button,
  Callout,
  Divider,
  Eyebrow,
  Field,
  H1,
  Muted,
} from "../components/ui";
import { BareShell, Logo, TopBar } from "../shell/app-shell";

type FormAction = (formData: FormData) => void | Promise<void>;

function SignOutButton({ compact = false }: { compact?: boolean }) {
  return (
    <form action="/auth/signout" method="post">
      <Button
        type="submit"
        size="sm"
        variant="ghost"
        icon={LogOut}
        ariaLabel="Sign out and use another account"
      >
        {compact ? "Switch" : "Sign out"}
      </Button>
    </form>
  );
}

export function LiveSignInScreen({
  error,
  googleAction,
  next,
  configured,
}: {
  error: string | null;
  googleAction: FormAction;
  next: string;
  configured: boolean;
}) {
  return (
    <BareShell className="lg:flex lg:items-center lg:justify-center lg:bg-ns-sunken lg:p-16">
      <div className="lg:hidden">
        <TopBar backHref="/" />
      </div>
      <main className="flex flex-col gap-5 px-6 pt-6 pb-10 lg:w-[520px] lg:rounded-2xl lg:border lg:border-ns-line lg:bg-ns-raised lg:p-10 lg:shadow-ns-md">
        <div className="animate-ns-float self-start">
          <Hornbill
            size={96}
            mood={error ? "kind" : "happy"}
            pose={error ? "perch" : "cheer"}
            outfit="scarf"
            branch={false}
            label="NextScholar hornbill"
          />
        </div>
        <div className="flex flex-col gap-2">
          <Eyebrow>INVITATION-ONLY BETA</Eyebrow>
          <H1 className="text-[28px] leading-9 lg:text-[28px] lg:leading-9">
            Sign in to NextScholar
          </H1>
          <Muted className="text-base leading-6">
            Use the Google account that received your invitation.
          </Muted>
        </div>

        {error ? (
          <div role="alert">
            <Callout tone="danger" icon={AlertCircle}>
              <strong>{error}</strong>
            </Callout>
          </div>
        ) : null}

        {configured ? (
          <form action={googleAction} className="flex">
            <input type="hidden" name="next" value={next} />
            <Button type="submit" full icon={Mail}>
              Continue with Google
            </Button>
          </form>
        ) : (
          <Callout tone="amber" icon={AlertCircle}>
            <strong>Hosted authentication is not configured.</strong>
            <span>
              Add the Supabase public URL and publishable key before testing
              Google sign-in.
            </span>
          </Callout>
        )}

        <Callout tone="brand" icon={ShieldCheck}>
          <strong>Invitation-bound access</strong>
          <span>
            Your Google identity and invitation email are verified before a
            learner profile or course enrolment is created.
          </span>
        </Callout>
        <Muted>
          Google handles your password. NextScholar receives only the account
          information needed to identify your learner profile.
        </Muted>
        <Divider />
        <Muted>
          No invitation yet? Access is currently limited to invited beta
          students.
        </Muted>
      </main>
    </BareShell>
  );
}

export function LiveEntryUnavailable({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <BareShell className="flex items-center justify-center px-5 py-12">
      <main className="flex w-full max-w-lg flex-col gap-5 rounded-2xl border border-ns-line bg-ns-raised p-6 shadow-ns-md lg:p-8">
        <Logo height={28} />
        <Callout tone="amber" icon={AlertCircle}>
          <strong>{title}</strong>
          <span>{description}</span>
        </Callout>
        <Button href="/" variant="secondary">
          Return home
        </Button>
      </main>
    </BareShell>
  );
}

export function LiveOnboardingShell({ children }: { children: ReactNode }) {
  return (
    <BareShell className="lg:flex">
      <aside className="hidden w-[500px] shrink-0 bg-ns-ink text-ns-on-brand lg:block">
        <div className="sticky top-0 flex h-dvh flex-col justify-between overflow-hidden p-14">
          <Logo height={30} reversed />
          <div className="flex flex-col gap-5">
            <div className="flex size-56 animate-ns-float items-center justify-center rounded-full bg-[radial-gradient(circle,rgb(227_164_75/0.32),rgb(227_164_75/0)_70%)]">
              <Hornbill
                size={205}
                mood="happy"
                pose="cheer"
                branch={false}
                label="NextScholar hornbill welcoming a beta student"
              />
            </div>
            <h1 className="m-0 text-[40px] leading-[46px] font-bold tracking-[-0.015em]">
              Welcome to the beta.
            </h1>
            <p className="m-0 text-lg leading-7 text-ns-on-brand/85">
              Connect the invitation sent to your Google account. It assigns the
              reviewed course revision and keeps your progress attached to one
              learner profile.
            </p>
            <div className="grid gap-2 text-sm text-ns-on-brand/90">
              <span className="flex items-center gap-2">
                <CheckCircle2 size={18} className="text-ns-gold" aria-hidden />
                Verified Google identity
              </span>
              <span className="flex items-center gap-2">
                <CheckCircle2 size={18} className="text-ns-gold" aria-hidden />
                Invitation-controlled beta access
              </span>
              <span className="flex items-center gap-2">
                <CheckCircle2 size={18} className="text-ns-gold" aria-hidden />
                Individual attempt and progress history
              </span>
            </div>
          </div>
          <p className="m-0 text-sm text-ns-on-brand/85">
            Made for ASEAN Scholarship preparation.
          </p>
        </div>
      </aside>

      <div className="flex min-w-0 grow flex-col">
        <div className="lg:hidden">
          <TopBar logo right={<SignOutButton compact />} />
        </div>
        <div className="hidden justify-end px-8 pt-6 lg:flex">
          <SignOutButton />
        </div>
        <main className="flex grow justify-center px-5 pt-6 pb-10 lg:px-16 lg:pt-4 lg:pb-16">
          <div className="w-full max-w-[500px]">{children}</div>
        </main>
      </div>
    </BareShell>
  );
}

export function LiveOnboardingFormView({
  email,
  displayName,
  invitationCode,
  codeFromLink,
  submitting,
  error,
  onDisplayNameChange,
  onInvitationCodeChange,
  onSubmit,
}: {
  email: string | null;
  displayName: string;
  invitationCode: string;
  codeFromLink: boolean;
  submitting: boolean;
  error: string | null;
  onDisplayNameChange: (value: string) => void;
  onInvitationCodeChange: (value: string) => void;
  onSubmit: FormEventHandler<HTMLFormElement>;
}) {
  const accountLabel = email ?? "Verified Google account";

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <Eyebrow>ONE FINAL STEP</Eyebrow>
        <H1 className="text-[28px] leading-9 lg:text-[32px] lg:leading-10">
          Activate student access
        </H1>
        <Muted className="text-base leading-6">
          Your invitation determines the course and revision you can access.
        </Muted>
      </div>

      <form className="flex flex-col gap-6" onSubmit={onSubmit}>
        <div className="flex items-center gap-3 rounded-2xl border border-ns-line bg-ns-sunken px-3 py-3">
          <Avatar initials={accountLabel.charAt(0).toUpperCase()} size={36} />
          <div className="flex min-w-0 grow flex-col">
            <span className="text-sm text-ns-muted">Signed in as</span>
            <span className="truncate text-[15px] font-semibold">
              {accountLabel}
            </span>
          </div>
        </div>

        <Field
          id="display-name"
          name="display_name"
          label="Name shown in the academy"
          value={displayName}
          onChange={onDisplayNameChange}
          autoComplete="name"
          maxLength={80}
          minLength={1}
          placeholder="Your preferred name"
          required
          hint="Shown in your learner account and the administrator dashboard."
        />

        <Field
          id="invitation-code"
          name="invitation_code"
          label="Beta invitation code"
          value={invitationCode}
          onChange={onInvitationCodeChange}
          autoCapitalize="none"
          autoComplete="one-time-code"
          maxLength={300}
          minLength={16}
          placeholder="Paste the code you received"
          required
          spellCheck={false}
          mono
          hint={
            codeFromLink
              ? "Filled in securely from your invitation link."
              : "Use the code from your beta invitation."
          }
        />

        {error ? (
          <div role="alert">
            <Callout tone="danger" icon={AlertCircle}>
              <strong>Invitation could not be accepted</strong>
              <span>{error}</span>
            </Callout>
          </div>
        ) : null}

        <Callout tone="brand" icon={BookOpen}>
          <strong>What happens next</strong>
          <span>
            After access is activated, you will begin the mathematics readiness
            check assigned to this beta course.
          </span>
        </Callout>

        <Button
          type="submit"
          variant="primary"
          full
          disabled={submitting}
          icon={submitting ? LoaderCircle : TicketCheck}
          iconRight={submitting ? undefined : ArrowRight}
        >
          {submitting ? "Checking invitation…" : "Join the beta course"}
        </Button>
      </form>
    </div>
  );
}
