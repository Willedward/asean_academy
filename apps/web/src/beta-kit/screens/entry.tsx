import Link from "next/link";
import type { ReactNode } from "react";
import { AlertCircle, ArrowRight, BookOpen, Mail, RotateCcw, Users } from "lucide-react";

import { cn } from "@/lib/utils";

import { Hornbill } from "../components/hornbill";
import { GameIcon } from "../components/icons";
import { MascotSays, RewardLine, XpPill } from "../components/rewards";
import { Avatar, Button, Callout, Card, Divider, Eyebrow, Field, H1, H3, Muted, Tag, focusRing } from "../components/ui";
import { BareShell, Logo, TopBar } from "../shell/app-shell";
import type { Href, Outfit } from "../types";

/**
 * A form target: a URL, or a server action. Screens stay server-component
 * safe, so the page passes the action in and the kit renders a plain <form>.
 */
export type FormAction = string | ((formData: FormData) => void | Promise<void>);

/* ------------------------------------------------------------------ */
/* Landing                                                             */
/* ------------------------------------------------------------------ */

function FloatPill({ children, className }: { children: ReactNode; className: string }) {
  return (
    <div
      className={cn(
        "absolute inline-flex animate-ns-float items-center gap-1.5 rounded-full bg-ns-raised px-3 py-2 text-sm font-extrabold whitespace-nowrap text-ns-ink shadow-ns-md",
        className,
      )}
    >
      {children}
    </div>
  );
}

/** Decorative hero: cheering hornbill with floating streak, XP and badge pills. */
function HeroArt() {
  return (
    <div
      aria-hidden="true"
      className="relative h-[280px] overflow-hidden rounded-3xl border border-ns-line bg-[radial-gradient(circle_at_50%_55%,var(--color-ns-amber-soft)_0%,var(--color-ns-sunken)_70%)] lg:h-[440px]"
    >
      <div className="absolute bottom-11 left-1/2 -translate-x-1/2 lg:bottom-[26px]">
        <Hornbill size={250} mood="happy" pose="cheer" outfit="scarf" className="size-[150px] lg:size-[250px]" />
      </div>
      <FloatPill className="top-[18px] left-4 lg:top-14 lg:left-12">
        <GameIcon name="flame" size={20} className="text-ns-amber" />
        12 day streak
      </FloatPill>
      <FloatPill className="top-16 right-4 [animation-delay:0.8s] lg:top-[110px] lg:right-14">
        <GameIcon name="bolt" size={20} className="text-ns-amber" />
        +10 XP
      </FloatPill>
      <FloatPill className="bottom-2.5 left-[84px] [animation-delay:1.6s] lg:bottom-[60px] lg:left-10">
        <GameIcon name="star" size={20} className="text-ns-gold" />
        Badge: First-try ace
      </FloatPill>
    </div>
  );
}

const SELLING_POINTS: { icon: ReactNode; title: string; text: string }[] = [
  {
    icon: <BookOpen size={22} aria-hidden />,
    title: "Learn one lesson at a time",
    text: "Short lessons with worked examples, then practice on the same idea.",
  },
  {
    icon: <RotateCcw size={22} aria-hidden />,
    title: "Try again before the answer",
    text: "Wrong answers get a hint, not the solution. The solution waits until you choose to see it.",
  },
  {
    icon: <GameIcon name="flame" size={22} className="text-ns-amber" />,
    title: "Streaks, XP and badges",
    text: "Every right answer earns XP. Keep your streak, climb the weekly league and dress up your hornbill.",
  },
  {
    icon: <Users size={22} aria-hidden />,
    title: "Built by former scholars",
    text: "Written by two ASEAN scholars who went through the same tests.",
  },
];

export interface LandingProps {
  /** e.g. "Private beta · December 2026" */
  betaLabel: string;
  signInHref: Href;
}

/** Canvas: Landing.m, Landing.d */
export function LandingScreen({ betaLabel, signInHref }: LandingProps) {
  return (
    <BareShell>
      <header className="flex h-[60px] items-center justify-between gap-3 border-b border-ns-line px-4 lg:h-20 lg:px-20">
        <span className="lg:hidden">
          <Logo height={22} />
        </span>
        <span className="hidden lg:block">
          <Logo height={30} />
        </span>
        <Button variant="ghost" size="sm" href={signInHref} className="lg:hidden">
          Sign in
        </Button>
        <Button variant="secondary" href={signInHref} className="hidden lg:inline-flex">
          Sign in
        </Button>
      </header>

      <main className="flex flex-col gap-7 px-5 pt-6 pb-10 lg:gap-0 lg:px-20 lg:pt-0 lg:pb-24">
        <section className="grid gap-7 lg:grid-cols-2 lg:items-center lg:gap-16 lg:pt-[88px] lg:pb-16">
          <div className="flex max-w-[560px] flex-col gap-4 lg:gap-6">
            <div>
              <Tag tone="amber">{betaLabel}</Tag>
            </div>
            <h1 className="m-0 text-[36px] leading-[42px] font-bold tracking-[-0.015em] lg:text-[56px] lg:leading-[60px]">
              <span className="font-extrabold">Your next</span> <span className="font-normal">scholarship starts here</span>
            </h1>
            <p className="m-0 text-[17px] leading-[26px] text-ns-muted lg:text-[19px] lg:leading-[30px]">
              Structured Mathematics practice for the Singapore ASEAN Scholarship, built by former scholars. The beta is by
              invitation only.
            </p>
            <div className="hidden items-center gap-5 lg:flex">
              <Button variant="primary" href={signInHref}>
                Sign in with your invitation
              </Button>
              <p className="m-0 text-[15px] leading-[22px] text-ns-muted">No invitation yet? Places are limited.</p>
            </div>
          </div>
          <HeroArt />
          <div className="flex flex-col gap-3 lg:hidden">
            <Button variant="primary" full href={signInHref}>
              Sign in with your invitation
            </Button>
            <Muted>
              No invitation yet? We are opening a small number of places. Ask the person who told you about NextScholar.
            </Muted>
          </div>
        </section>

        <section aria-label="What you get" className="flex flex-col gap-3 lg:flex-row lg:gap-5">
          {SELLING_POINTS.map((point) => (
            <Card key={point.title} className="flex-row items-start gap-4 lg:flex-1">
              <span className="inline-flex size-11 shrink-0 items-center justify-center rounded-full bg-ns-brand-soft text-ns-ink">
                {point.icon}
              </span>
              <div className="flex min-w-0 flex-col gap-1">
                <H3>{point.title}</H3>
                <Muted className="text-[15px] leading-[22px]">{point.text}</Muted>
              </div>
            </Card>
          ))}
        </section>
      </main>
    </BareShell>
  );
}

/* ------------------------------------------------------------------ */
/* Sign in                                                             */
/* ------------------------------------------------------------------ */

export interface SignInProps {
  /**
   * Shown when sign-in failed. Map from the /login?error= codes
   * (auth_callback_failed, oauth_start_failed, ...). Null for the normal state.
   */
  error: string | null;
  /** Server action that starts Google OAuth (today: signInWithGoogle in app/login/actions.ts). */
  googleAction?: FormAction;
  /** Passed to googleAction as the "next" form field. */
  next?: string;
  /** Used instead of googleAction in the preview. */
  continueHref?: Href;
  landingHref: Href;
}

/** Canvas: SignIn.m (normal), SignIn.d (error) */
export function SignInScreen({ error, googleAction, next = "", continueHref, landingHref }: SignInProps) {
  const google = googleAction ? (
    <form action={googleAction} className="flex">
      <input type="hidden" name="next" defaultValue={next} />
      <Button type="submit" full icon={Mail}>
        Continue with Google
      </Button>
    </form>
  ) : (
    <Button full icon={Mail} href={continueHref}>
      Continue with Google
    </Button>
  );

  return (
    <BareShell className="lg:flex lg:items-center lg:justify-center lg:bg-ns-sunken lg:p-16">
      <div className="lg:hidden">
        <TopBar backHref={landingHref} />
      </div>
      <main className="flex flex-col gap-5 px-6 pt-6 pb-10 lg:w-[520px] lg:rounded-2xl lg:border lg:border-ns-line lg:bg-ns-raised lg:p-10 lg:shadow-ns-md">
        <div className="animate-ns-float self-start">
          {error ? (
            <Hornbill size={96} mood="kind" outfit="scarf" branch={false} />
          ) : (
            <Hornbill size={96} mood="happy" pose="cheer" outfit="scarf" branch={false} />
          )}
        </div>
        <div className="flex flex-col gap-2">
          <H1 className="text-[28px] leading-9 lg:text-[28px] lg:leading-9">Sign in to NextScholar</H1>
          <Muted className="text-base leading-6">Use the Google account your invitation was sent to.</Muted>
        </div>
        {error ? (
          <Callout tone="danger" icon={AlertCircle}>
            <span className="text-[15px] leading-[22px] font-semibold text-ns-danger">{error}</span>
          </Callout>
        ) : null}
        {google}
        <div className="flex items-start gap-1.5 text-sm leading-5 font-semibold text-ns-amber-text">
          <GameIcon name="flame" size={16} className="mt-0.5 text-ns-amber" />
          <span>Your streak, XP and badges are saved to this account.</span>
        </div>
        <Muted>We only use your Google account to sign you in. We never see your password.</Muted>
        <Divider />
        <Muted>
          No invitation yet? NextScholar is in a private beta.{" "}
          <Link href={landingHref} className={cn("rounded-sm text-ns-amber-text underline", focusRing)}>
            Learn more
          </Link>
        </Muted>
      </main>
    </BareShell>
  );
}

/* ------------------------------------------------------------------ */
/* Onboarding                                                          */
/* ------------------------------------------------------------------ */

/** NEW. One intake the learner can prepare for. */
export interface TrackOption {
  /** Stored as ProfileResponse.target_track. */
  value: string;
  label: string;
  description: string;
}

/** NEW. Rewards granted when onboarding finishes. */
export interface StarterPack {
  welcomeXp: number;
  firstOutfit: { outfit: Outfit; name: string; level: number };
}

export interface OnboardingProps {
  /** API: ProfileResponse.email (from the verified session). */
  email: string;
  /** API: AcceptInvitationRequest.display_name. Prefilled from Google if known. */
  displayName: string;
  /** API: AcceptInvitationRequest.invitation_code. From the ?code= link. */
  invitationCode: string;
  /** True when the code came from the invitation link. */
  codeFromLink: boolean;
  /** API: ErrorDetail.message from POST /onboarding/accept-invitation. */
  codeError?: string | null;
  /** NEW: AcceptInvitationRequest.target_track (today only ProfileResponse.target_track exists). */
  tracks: TrackOption[];
  selectedTrack: string;
  /** e.g. "Singapore Secondary 1 G3 Mathematics, unit N1 Numbers and their operations." */
  startingCourse: string;
  /** NEW */
  starterPack: StarterPack;
  /** Server action that calls POST /api/v1/onboarding/accept-invitation. */
  action?: FormAction;
  /** Used instead of action in the preview. */
  continueHref?: Href;
  /** Signs out and returns to sign in. */
  switchAccountHref: Href;
}

function TrackChoice({ tracks, selected }: { tracks: TrackOption[]; selected: string }) {
  return (
    <fieldset className="m-0 flex min-w-0 flex-col gap-2 border-0 p-0">
      <legend className="mb-2 p-0 text-[15px] leading-5 font-semibold">Which intake are you preparing for?</legend>
      {tracks.map((track) => (
        <label
          key={track.value}
          className="group flex cursor-pointer items-start gap-3 rounded-xl border-[1.5px] border-ns-line-strong bg-ns-raised px-4 py-3.5 has-checked:border-ns-ink has-checked:bg-ns-brand-soft has-focus-visible:outline-3 has-focus-visible:outline-offset-2 has-focus-visible:outline-ns-success"
        >
          <input
            type="radio"
            name="target_track"
            value={track.value}
            defaultChecked={track.value === selected}
            className="sr-only"
          />
          <span className="mt-0.5 inline-flex size-5 shrink-0 items-center justify-center rounded-full border-2 border-ns-line-strong group-has-checked:border-ns-ink">
            <span className="size-2.5 rounded-full bg-ns-ink opacity-0 group-has-checked:opacity-100" />
          </span>
          <span className="flex flex-col gap-0.5">
            <span className="text-base font-semibold">{track.label}</span>
            <span className="text-sm leading-5 text-ns-muted">{track.description}</span>
          </span>
        </label>
      ))}
    </fieldset>
  );
}

function StarterPackCard({ pack }: { pack: StarterPack }) {
  return (
    <Card tone="amber" className="gap-3">
      <div className="flex items-center justify-between gap-3">
        <H3>Your starter pack</H3>
        <XpPill xp={pack.welcomeXp} />
      </div>
      <RewardLine
        icon={<GameIcon name="bolt" size={20} className="text-ns-amber" />}
        title={`+${pack.welcomeXp} XP welcome bonus`}
        sub="Added when you start Lesson 1."
      />
      <RewardLine
        icon={<GameIcon name="flame" size={20} className="text-ns-amber" />}
        title="Day 1 of your streak"
        sub="Answer one question a day to keep it alive."
      />
      <RewardLine
        icon={<Hornbill size={30} crop="head" outfit={pack.firstOutfit.outfit} />}
        title={`${pack.firstOutfit.name} at Level ${pack.firstOutfit.level}`}
        sub="Your hornbill’s first outfit."
      />
    </Card>
  );
}

function OnboardingForm(props: OnboardingProps) {
  const {
    email,
    displayName,
    invitationCode,
    codeFromLink,
    codeError,
    tracks,
    selectedTrack,
    startingCourse,
    starterPack,
    action,
    continueHref,
    switchAccountHref,
  } = props;
  const fields = (
    <>
      <div className="flex items-center gap-3 rounded-2xl border border-ns-line bg-ns-sunken px-3 py-3">
        <Avatar initials={email.charAt(0).toUpperCase()} size={32} />
        <div className="flex min-w-0 grow flex-col">
          <span className="text-sm text-ns-muted">Signed in as</span>
          <span className="truncate text-[15px] font-semibold">{email}</span>
        </div>
        <Button variant="ghost" size="sm" href={switchAccountHref}>
          Switch
        </Button>
      </div>
      {/* Ids match the AcceptInvitationRequest field names. */}
      <Field
        id="display_name"
        name="display_name"
        label="What should we call you?"
        value={displayName}
        hint="Shown only to you and the NextScholar team."
      />
      <Field
        id="invitation_code"
        name="invitation_code"
        label="Invitation code"
        value={invitationCode}
        mono
        hint={codeFromLink ? "Filled in from your invitation link." : "It is in your invitation email."}
        error={codeError ?? undefined}
      />
      <TrackChoice tracks={tracks} selected={selectedTrack} />
      <Callout tone="brand" icon={BookOpen}>
        <p className="m-0 text-[15px] leading-[22px] text-ns-muted">
          <b className="text-ns-ink">You will start with:</b> {startingCourse}
        </p>
      </Callout>
      <StarterPackCard pack={starterPack} />
      {action ? (
        <Button type="submit" variant="primary" full iconRight={ArrowRight}>
          Start learning · +{starterPack.welcomeXp} XP
        </Button>
      ) : (
        <Button variant="primary" full iconRight={ArrowRight} href={continueHref}>
          Start learning · +{starterPack.welcomeXp} XP
        </Button>
      )}
    </>
  );

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <Eyebrow>Step 1 of 1</Eyebrow>
        <H1 className="text-[28px] leading-9 lg:text-[28px] lg:leading-9">Set up your account</H1>
      </div>
      <MascotSays size={72} mood={codeError ? "kind" : "happy"} pose={codeError ? "perch" : "cheer"}>
        Hi! I am your study buddy. Two quick details and your first lesson unlocks.
      </MascotSays>
      {action ? (
        <form action={action} className="flex flex-col gap-6">
          {fields}
        </form>
      ) : (
        <div className="flex flex-col gap-6">{fields}</div>
      )}
    </div>
  );
}

/** Desktop only: the dark welcome panel on the left. */
function WelcomePanel() {
  return (
    <aside className="hidden w-[520px] shrink-0 bg-ns-ink text-ns-on-brand lg:block">
      <div className="sticky top-0 flex h-dvh flex-col justify-between overflow-hidden p-16">
        <Logo height={30} reversed />
        <div className="flex flex-col gap-[18px]">
          <div className="flex size-60 animate-ns-float items-center justify-center rounded-full bg-[radial-gradient(circle,rgb(227_164_75/0.35),rgb(227_164_75/0)_70%)]">
            <Hornbill size={210} mood="happy" pose="cheer" branch={false} />
          </div>
          <h2 className="m-0 text-[40px] leading-[46px] font-bold tracking-[-0.015em]">Welcome to the beta.</h2>
          <p className="m-0 text-lg leading-7 text-ns-on-brand/85">
            You are one of a small group of students testing NextScholar before anyone else. Earn XP, keep your streak and climb
            the Beta League together.
          </p>
          <div className="flex gap-2">
            {(
              [
                ["flame", "Streaks"],
                ["bolt", "XP"],
                ["trophy", "League"],
              ] as const
            ).map(([icon, label]) => (
              <span
                key={label}
                className="inline-flex h-[34px] items-center gap-1.5 rounded-full bg-ns-on-brand/12 px-3 text-sm font-extrabold"
              >
                <GameIcon name={icon} size={18} className="text-ns-gold" />
                {label}
              </span>
            ))}
          </div>
        </div>
        <p className="m-0 text-sm text-ns-on-brand/85">Made by former ASEAN scholars.</p>
      </div>
    </aside>
  );
}

/** Canvas: Onboarding.m, Onboarding.d, OnboardingError.m (codeError set) */
export function OnboardingScreen(props: OnboardingProps) {
  return (
    <BareShell className="lg:flex">
      <WelcomePanel />
      <div className="flex min-w-0 grow flex-col">
        <div className="lg:hidden">
          <TopBar logo />
        </div>
        <main className="flex justify-center px-5 pt-6 pb-10 lg:p-16">
          <div className="w-full max-w-[480px]">
            <OnboardingForm {...props} />
          </div>
        </main>
      </div>
    </BareShell>
  );
}
