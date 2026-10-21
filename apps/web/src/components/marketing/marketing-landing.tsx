import Link from "next/link";
import {
  ArrowRight,
  BarChart3,
  BookOpenCheck,
  BrainCircuit,
  Check,
  ClipboardCheck,
  FileText,
  Languages,
  LockKeyhole,
  MessageCircleQuestion,
  Quote,
  Route,
  Sparkles,
  Target,
  UserRound,
  UsersRound,
} from "lucide-react";

import { Hornbill } from "@/beta-kit/components/hornbill";
import { Button, focusRing } from "@/beta-kit/components/ui";
import { Logo } from "@/beta-kit/shell/app-shell";
import { cn } from "@/lib/utils";

const FEATURES = [
  {
    icon: Route,
    title: "A clear learning path",
    body: "Move from concise lesson notes to guided practice, checkpoints and retry work without losing your place.",
  },
  {
    icon: ClipboardCheck,
    title: "Exam-shaped practice",
    body: "Build Mathematics and English skills through reviewed questions designed around scholarship-test demands.",
  },
  {
    icon: BrainCircuit,
    title: "Help when you are stuck",
    body: "Ask for a hint, inspect a worked method and use guided tutor support without immediately revealing the answer.",
  },
  {
    icon: BarChart3,
    title: "Progress you can act on",
    body: "See which skills are secure, which need another attempt and what to study next.",
  },
] as const;

const STEPS = [
  {
    number: "01",
    title: "Find your starting point",
    body: "A diagnostic identifies the Mathematics topics that deserve attention first.",
  },
  {
    number: "02",
    title: "Learn one skill at a time",
    body: "Short explanations and worked examples build the method before independent practice.",
  },
  {
    number: "03",
    title: "Practise and reflect",
    body: "Submit answers, study precise feedback and classify the mistake when a retry is useful.",
  },
  {
    number: "04",
    title: "Return with a purpose",
    body: "Your course view keeps the next lesson, unresolved retry and progress evidence together.",
  },
] as const;

const TESTIMONIAL_SLOTS = [
  {
    icon: UserRound,
    audience: "Student experience",
    placeholder:
      "Reserved for a consented student quote after the private beta interviews.",
  },
  {
    icon: UsersRound,
    audience: "Parent perspective",
    placeholder:
      "Reserved for an approved parent quote about clarity, confidence or study habits.",
  },
  {
    icon: Quote,
    audience: "Learning evidence",
    placeholder:
      "Reserved for a verified outcome or educator observation with its source and context.",
  },
] as const;

const FAQ = [
  {
    question: "Who is NextScholar for?",
    answer:
      "The current course is for secondary-school students in Indonesia and Southeast Asia preparing for ASEAN Scholarship selection tests.",
  },
  {
    question: "Which subjects are included?",
    answer:
      "Layer 1 focuses on Mathematics and English. Other subjects and gamification features are outside the first academic beta.",
  },
  {
    question: "Can anyone create an account?",
    answer:
      "The current beta is invitation-only. Invited students sign in with the same Google account that received access.",
  },
] as const;

function SectionHeading({
  eyebrow,
  title,
  body,
  centered = false,
}: {
  eyebrow: string;
  title: string;
  body: string;
  centered?: boolean;
}) {
  return (
    <div className={cn("max-w-3xl", centered && "mx-auto text-center")}>
      <p className="mb-3 text-sm font-extrabold tracking-[0.14em] text-ns-amber-text uppercase">
        {eyebrow}
      </p>
      <h2 className="m-0 text-3xl leading-tight font-bold tracking-[-0.03em] text-ns-ink sm:text-5xl">
        {title}
      </h2>
      <p className="mt-5 text-base leading-7 text-ns-muted sm:text-lg sm:leading-8">
        {body}
      </p>
    </div>
  );
}

function ProductPreview() {
  return (
    <div
      aria-label="Preview of the NextScholar learning experience"
      className="relative mx-auto min-h-[420px] w-full max-w-[620px] overflow-hidden rounded-[2rem] border border-white/70 bg-[linear-gradient(145deg,#dcebe7_0%,#f8ecd8_48%,#f7d3bf_100%)] p-5 shadow-[0_28px_80px_rgb(15_61_64/0.18)] sm:min-h-[520px] sm:p-8"
    >
      <div
        aria-hidden="true"
        className="absolute -top-24 -right-20 size-72 rounded-full bg-white/50 blur-2xl"
      />
      <div
        aria-hidden="true"
        className="absolute -bottom-24 -left-16 size-72 rounded-full bg-[#8fd3c8]/45 blur-2xl"
      />

      <div className="relative z-10 flex items-center justify-between rounded-2xl border border-white/80 bg-white/80 px-4 py-3 shadow-ns-sm backdrop-blur">
        <div>
          <p className="m-0 text-xs font-bold text-ns-muted">
            TODAY&apos;S PLAN
          </p>
          <p className="mt-1 mb-0 text-sm font-extrabold text-ns-ink sm:text-base">
            Ratios, reading and one retry
          </p>
        </div>
        <span className="rounded-full bg-ns-brand-soft px-3 py-1.5 text-xs font-bold text-ns-ink">
          3 activities
        </span>
      </div>

      <div className="relative z-10 mt-5 grid gap-3 sm:grid-cols-[1fr_0.8fr]">
        <div className="rounded-3xl bg-ns-ink p-5 text-white shadow-ns-md">
          <span className="inline-flex size-10 items-center justify-center rounded-full bg-white/12">
            <Target size={20} aria-hidden />
          </span>
          <p className="mt-6 mb-1 text-xs font-bold tracking-[0.12em] text-[#b7cecc] uppercase">
            Continue learning
          </p>
          <h3 className="m-0 text-2xl leading-7 font-bold">
            Ratios and proportional reasoning
          </h3>
          <div className="mt-5 h-2 overflow-hidden rounded-full bg-white/15">
            <div className="h-full w-[58%] rounded-full bg-ns-gold-light" />
          </div>
          <p className="mt-2 mb-0 text-xs text-[#d6e4e2]">
            3 of 5 lessons complete
          </p>
        </div>

        <div className="flex min-h-48 items-center justify-center rounded-3xl border border-white/80 bg-white/75 p-3 backdrop-blur">
          <Hornbill
            size={170}
            mood="happy"
            pose="cheer"
            outfit="scarf"
            label="NextScholar hornbill celebrating a study plan"
            className="size-36 sm:size-40"
          />
        </div>
      </div>

      <div className="relative z-10 mt-3 grid grid-cols-3 gap-2 sm:gap-3">
        {[
          { icon: BookOpenCheck, label: "Mathematics", tone: "bg-[#e4f1f5]" },
          { icon: Languages, label: "English", tone: "bg-[#f8ecd8]" },
          {
            icon: MessageCircleQuestion,
            label: "Tutor help",
            tone: "bg-[#fbeae7]",
          },
        ].map(({ icon: Icon, label, tone }) => (
          <div
            className="rounded-2xl border border-white/80 bg-white/80 p-3 shadow-ns-sm backdrop-blur sm:p-4"
            key={label}
          >
            <span
              className={cn(
                "inline-flex size-9 items-center justify-center rounded-xl text-ns-ink",
                tone,
              )}
            >
              <Icon size={18} aria-hidden />
            </span>
            <p className="mt-3 mb-0 text-xs font-bold text-ns-ink sm:text-sm">
              {label}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

export function MarketingLanding({
  signInHref = "/login",
  registerHref = "/register",
}: {
  signInHref?: string;
  registerHref?: string;
}) {
  return (
    <div className="ns-root min-h-screen overflow-x-hidden bg-ns-surface font-ns text-ns-ink">
      <a
        href="#main-content"
        className={cn(
          "fixed top-3 left-3 z-50 -translate-y-20 rounded-full bg-ns-ink px-4 py-2 text-sm font-bold text-white transition-transform focus:translate-y-0",
          focusRing,
        )}
      >
        Skip to content
      </a>

      <header className="sticky top-0 z-40 border-b border-ns-line bg-ns-surface/92 backdrop-blur-xl">
        <div className="mx-auto flex h-16 w-full max-w-[1280px] items-center gap-6 px-5 lg:h-20 lg:px-8">
          <Link
            href="/marketing-preview"
            aria-label="NextScholar marketing preview home"
          >
            <Logo height={25} />
          </Link>
          <nav
            aria-label="Marketing"
            className="ml-auto hidden items-center gap-7 lg:flex"
          >
            <a
              className={cn(
                "text-sm font-semibold no-underline hover:text-ns-amber-text",
                focusRing,
              )}
              href="#features"
            >
              Features
            </a>
            <a
              className={cn(
                "text-sm font-semibold no-underline hover:text-ns-amber-text",
                focusRing,
              )}
              href="#subjects"
            >
              Subjects
            </a>
            <a
              className={cn(
                "text-sm font-semibold no-underline hover:text-ns-amber-text",
                focusRing,
              )}
              href="#how-it-works"
            >
              How it works
            </a>
            <a
              className={cn(
                "text-sm font-semibold no-underline hover:text-ns-amber-text",
                focusRing,
              )}
              href="#families"
            >
              For families
            </a>
            <a
              className={cn(
                "text-sm font-semibold no-underline hover:text-ns-amber-text",
                focusRing,
              )}
              href="#testimonials"
            >
              Testimonials
            </a>
            <a
              className={cn(
                "text-sm font-semibold no-underline hover:text-ns-amber-text",
                focusRing,
              )}
              href="#faq"
            >
              FAQ
            </a>
          </nav>
          <div className="ml-auto flex items-center gap-2 lg:ml-3">
            <Button
              href={signInHref}
              variant="ghost"
              size="sm"
              className="hidden sm:inline-flex"
            >
              Sign in
            </Button>
            <Button
              href={registerHref}
              variant="primary"
              size="sm"
              iconRight={ArrowRight}
            >
              Register
            </Button>
          </div>
        </div>
      </header>

      <main id="main-content">
        <section className="relative isolate overflow-hidden px-5 pt-14 pb-20 sm:pt-20 lg:px-8 lg:pt-24 lg:pb-28">
          <div
            aria-hidden="true"
            className="absolute inset-x-0 top-0 -z-10 h-[780px] bg-[radial-gradient(circle_at_12%_10%,#f8ecd8_0%,transparent_32%),radial-gradient(circle_at_85%_25%,#dcebe7_0%,transparent_34%)]"
          />
          <div className="mx-auto grid w-full max-w-[1280px] gap-14 lg:grid-cols-[0.95fr_1.05fr] lg:items-center">
            <div className="max-w-2xl">
              <div className="inline-flex items-center gap-2 rounded-full border border-ns-amber-line bg-ns-amber-soft px-3 py-1.5 text-xs font-bold text-ns-amber-text">
                <Sparkles size={15} aria-hidden />
                Private beta for ASEAN Scholarship preparation
              </div>
              <h1 className="mt-6 mb-0 text-[clamp(3rem,7vw,6rem)] leading-[0.98] font-bold tracking-[-0.055em]">
                Build the skills to face the test with confidence.
              </h1>
              <p className="mt-7 max-w-xl text-lg leading-8 text-ns-muted sm:text-xl sm:leading-9">
                Structured Mathematics and English lessons, exam-shaped practice
                and guided help for secondary students across Southeast Asia.
              </p>
              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <Button
                  href={registerHref}
                  variant="primary"
                  iconRight={ArrowRight}
                  className="h-12 px-7 text-base"
                >
                  Register for access
                </Button>
                <Button
                  href="#how-it-works"
                  variant="secondary"
                  className="h-12 px-7 text-base"
                >
                  See how learning works
                </Button>
              </div>
              <div className="mt-7 flex flex-wrap gap-x-6 gap-y-3 text-sm font-semibold text-ns-muted">
                <span className="inline-flex items-center gap-2">
                  <Check size={17} className="text-ns-success" aria-hidden />{" "}
                  Mathematics and English
                </span>
                <span className="inline-flex items-center gap-2">
                  <Check size={17} className="text-ns-success" aria-hidden />{" "}
                  Progress saved automatically
                </span>
                <span className="inline-flex items-center gap-2">
                  <LockKeyhole
                    size={16}
                    className="text-ns-success"
                    aria-hidden
                  />{" "}
                  Invitation-only beta
                </span>
              </div>
            </div>
            <ProductPreview />
          </div>
        </section>

        <section className="border-y border-ns-line bg-white px-5 py-8 lg:px-8">
          <div className="mx-auto grid w-full max-w-[1100px] gap-6 text-center sm:grid-cols-3">
            <div>
              <strong className="block text-3xl tracking-[-0.03em]">
                2 subjects
              </strong>
              <span className="mt-1 block text-sm text-ns-muted">
                Mathematics and English in Layer 1
              </span>
            </div>
            <div className="border-ns-line sm:border-x">
              <strong className="block text-3xl tracking-[-0.03em]">
                1 connected path
              </strong>
              <span className="mt-1 block text-sm text-ns-muted">
                Learn, practise, retry and progress
              </span>
            </div>
            <div>
              <strong className="block text-3xl tracking-[-0.03em]">
                Built for the goal
              </strong>
              <span className="mt-1 block text-sm text-ns-muted">
                ASEAN Scholarship test preparation
              </span>
            </div>
          </div>
        </section>

        <section
          id="features"
          className="scroll-mt-24 px-5 py-20 lg:px-8 lg:py-28"
        >
          <div className="mx-auto w-full max-w-[1280px]">
            <SectionHeading
              eyebrow="Why NextScholar"
              title="Everything in the learning loop stays connected."
              body="The course links what a student studies, attempts, misses and revisits, so the next action is clearer than opening another folder of random worksheets."
              centered
            />
            <div className="mt-12 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {FEATURES.map(({ icon: Icon, title, body }) => (
                <article
                  className="rounded-3xl border border-ns-line bg-white p-6 shadow-ns-sm"
                  key={title}
                >
                  <span className="inline-flex size-12 items-center justify-center rounded-2xl bg-ns-brand-soft text-ns-ink">
                    <Icon size={23} aria-hidden />
                  </span>
                  <h3 className="mt-6 mb-0 text-xl font-bold">{title}</h3>
                  <p className="mt-3 mb-0 text-[15px] leading-6 text-ns-muted">
                    {body}
                  </p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section
          id="subjects"
          className="scroll-mt-24 bg-ns-ink px-5 py-20 text-white lg:px-8 lg:py-28"
        >
          <div className="mx-auto w-full max-w-[1280px]">
            <div className="max-w-3xl">
              <p className="mb-3 text-sm font-extrabold tracking-[0.14em] text-ns-gold-light uppercase">
                Layer 1 academics
              </p>
              <h2 className="m-0 text-3xl leading-tight font-bold tracking-[-0.03em] sm:text-5xl">
                Focused on the two subjects students need.
              </h2>
              <p className="mt-5 text-lg leading-8 text-[#c5d7d5]">
                A structured syllabus gives Mathematics depth while skill-based
                modules make English practice deliberate and repeatable.
              </p>
            </div>
            <div className="mt-12 grid gap-5 lg:grid-cols-2">
              <article className="overflow-hidden rounded-[2rem] bg-[#e4f1f5] p-7 text-ns-ink sm:p-9">
                <span className="inline-flex size-12 items-center justify-center rounded-2xl bg-white">
                  <Target size={23} aria-hidden />
                </span>
                <p className="mt-7 mb-2 text-sm font-extrabold tracking-[0.12em] text-ns-success uppercase">
                  Mathematics
                </p>
                <h3 className="m-0 text-3xl font-bold tracking-[-0.02em]">
                  Understand the method, then use it under pressure.
                </h3>
                <ul className="mt-6 mb-0 grid gap-3 pl-0 text-sm leading-6 text-ns-muted">
                  <li className="flex gap-3">
                    <Check
                      className="mt-1 size-4 shrink-0 text-ns-success"
                      aria-hidden
                    />
                    Concept notes and worked examples
                  </li>
                  <li className="flex gap-3">
                    <Check
                      className="mt-1 size-4 shrink-0 text-ns-success"
                      aria-hidden
                    />
                    Difficulty-calibrated practice and diagnostics
                  </li>
                  <li className="flex gap-3">
                    <Check
                      className="mt-1 size-4 shrink-0 text-ns-success"
                      aria-hidden
                    />
                    Typed answers, hints and guided tutor support
                  </li>
                </ul>
              </article>
              <article className="overflow-hidden rounded-[2rem] bg-[#f8ecd8] p-7 text-ns-ink sm:p-9">
                <span className="inline-flex size-12 items-center justify-center rounded-2xl bg-white">
                  <FileText size={23} aria-hidden />
                </span>
                <p className="mt-7 mb-2 text-sm font-extrabold tracking-[0.12em] text-ns-amber-text uppercase">
                  English
                </p>
                <h3 className="m-0 text-3xl font-bold tracking-[-0.02em]">
                  Build vocabulary, grammar, reading and writing as trainable
                  skills.
                </h3>
                <ul className="mt-6 mb-0 grid gap-3 pl-0 text-sm leading-6 text-ns-muted">
                  <li className="flex gap-3">
                    <Check
                      className="mt-1 size-4 shrink-0 text-ns-amber-text"
                      aria-hidden
                    />
                    Vocabulary and grammar in context
                  </li>
                  <li className="flex gap-3">
                    <Check
                      className="mt-1 size-4 shrink-0 text-ns-amber-text"
                      aria-hidden
                    />
                    Cloze and reading-comprehension practice
                  </li>
                  <li className="flex gap-3">
                    <Check
                      className="mt-1 size-4 shrink-0 text-ns-amber-text"
                      aria-hidden
                    />
                    A controlled writing and feedback pathway
                  </li>
                </ul>
              </article>
            </div>
          </div>
        </section>

        <section
          id="how-it-works"
          className="scroll-mt-24 px-5 py-20 lg:px-8 lg:py-28"
        >
          <div className="mx-auto w-full max-w-[1280px]">
            <SectionHeading
              eyebrow="How it works"
              title="A study session always has a next step."
              body="The template shows the full product story without promising an unverified score increase or presenting the beta as an official exam provider."
            />
            <ol className="mt-12 grid gap-4 pl-0 md:grid-cols-2 xl:grid-cols-4">
              {STEPS.map((step) => (
                <li
                  className="list-none border-t-2 border-ns-line pt-5"
                  key={step.number}
                >
                  <span className="font-mono text-sm font-bold text-ns-amber-text">
                    {step.number}
                  </span>
                  <h3 className="mt-5 mb-0 text-xl font-bold">{step.title}</h3>
                  <p className="mt-3 mb-0 text-[15px] leading-6 text-ns-muted">
                    {step.body}
                  </p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section
          id="families"
          className="scroll-mt-24 px-5 pb-20 lg:px-8 lg:pb-28"
        >
          <div className="mx-auto grid w-full max-w-[1280px] overflow-hidden rounded-[2rem] border border-ns-line bg-[linear-gradient(120deg,#f8ecd8,#ffffff_55%,#e3ecea)] shadow-ns-md lg:grid-cols-[1fr_0.72fr]">
            <div className="p-7 sm:p-12 lg:p-16">
              <p className="mb-3 text-sm font-extrabold tracking-[0.14em] text-ns-amber-text uppercase">
                For students and families
              </p>
              <h2 className="m-0 max-w-2xl text-3xl leading-tight font-bold tracking-[-0.03em] sm:text-5xl">
                A serious study tool with an honest beta boundary.
              </h2>
              <p className="mt-5 max-w-2xl text-lg leading-8 text-ns-muted">
                NextScholar organises preparation and feedback. It does not
                claim to reproduce confidential papers, guarantee a scholarship
                or replace a student&apos;s teachers.
              </p>
              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <Button
                  href={registerHref}
                  variant="primary"
                  iconRight={ArrowRight}
                >
                  Register for access
                </Button>
                <Button href="#faq" variant="secondary">
                  Read common questions
                </Button>
              </div>
            </div>
            <div className="flex min-h-72 items-end justify-center overflow-hidden bg-ns-ink/5 px-6 pt-8">
              <Hornbill
                size={310}
                mood="kind"
                pose="point"
                outfit="cap"
                label="NextScholar hornbill guiding a student"
                className="size-64 sm:size-72"
              />
            </div>
          </div>
        </section>

        <section
          id="testimonials"
          className="scroll-mt-24 border-y border-ns-line bg-white px-5 py-20 lg:px-8 lg:py-28"
        >
          <div className="mx-auto w-full max-w-[1280px]">
            <SectionHeading
              eyebrow="Testimonials"
              title="A ready home for real beta stories."
              body="These cards define the final testimonial layout. They intentionally remain placeholders until a student, parent or educator has approved an attributable quote for publication."
              centered
            />
            <div className="mt-12 grid gap-4 lg:grid-cols-3">
              {TESTIMONIAL_SLOTS.map(
                ({ icon: Icon, audience, placeholder }) => (
                  <article
                    className="flex min-h-64 flex-col rounded-3xl border border-dashed border-ns-line bg-ns-surface p-6"
                    key={audience}
                  >
                    <span className="inline-flex size-11 items-center justify-center rounded-2xl bg-ns-brand-soft text-ns-ink">
                      <Icon size={21} aria-hidden />
                    </span>
                    <p className="mt-6 mb-2 text-xs font-extrabold tracking-[0.12em] text-ns-success uppercase">
                      Evidence placeholder
                    </p>
                    <h3 className="m-0 text-xl font-bold">{audience}</h3>
                    <p className="mt-3 mb-0 leading-7 text-ns-muted">
                      {placeholder}
                    </p>
                  </article>
                ),
              )}
            </div>
            <p className="mx-auto mt-6 max-w-3xl text-center text-sm leading-6 text-ns-muted">
              No public testimonial has been approved yet. Publish only quotes
              with recorded consent, accurate attribution and enough context to
              describe the speaker&apos;s experience accurately.
            </p>
          </div>
        </section>

        <section
          id="faq"
          className="scroll-mt-24 border-t border-ns-line bg-white px-5 py-20 lg:px-8 lg:py-28"
        >
          <div className="mx-auto grid w-full max-w-[1100px] gap-12 lg:grid-cols-[0.7fr_1.3fr]">
            <SectionHeading
              eyebrow="FAQ"
              title="Clear answers before students sign in."
              body="These are the stable facts the first marketing version can state while pricing, public registration and the full Beta schedule are still being decided."
            />
            <div className="divide-y divide-ns-line border-y border-ns-line">
              {FAQ.map((item) => (
                <article className="py-6" key={item.question}>
                  <h3 className="m-0 text-lg font-bold">{item.question}</h3>
                  <p className="mt-3 mb-0 leading-7 text-ns-muted">
                    {item.answer}
                  </p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="bg-ns-amber-soft px-5 py-16 lg:px-8 lg:py-20">
          <div className="mx-auto flex w-full max-w-[1000px] flex-col items-center text-center">
            <p className="mb-3 text-sm font-extrabold tracking-[0.14em] text-ns-amber-text uppercase">
              Ready when your invitation arrives
            </p>
            <h2 className="m-0 text-3xl font-bold tracking-[-0.03em] sm:text-5xl">
              Continue from lesson to practice in one place.
            </h2>
            <p className="mt-5 max-w-2xl text-lg leading-8 text-ns-muted">
              Public account creation and pricing remain intentionally absent
              until those product decisions are approved.
            </p>
            <Button
              href={registerHref}
              variant="primary"
              iconRight={ArrowRight}
              className="mt-7 h-12 px-7 text-base"
            >
              Register for access
            </Button>
          </div>
        </section>
      </main>

      <footer className="bg-ns-dark px-5 py-10 text-ns-on-brand lg:px-8">
        <div className="mx-auto flex w-full max-w-[1280px] flex-col gap-8 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <Logo height={24} reversed />
            <p className="mt-4 mb-0 max-w-md text-sm leading-6 text-ns-on-dark-muted">
              Academic preparation for ASEAN Scholarship applicants across
              Southeast Asia.
            </p>
          </div>
          <div className="flex flex-wrap gap-5 text-sm font-semibold text-ns-on-dark-muted">
            <a className={cn("hover:text-white", focusRing)} href="#features">
              Features
            </a>
            <a className={cn("hover:text-white", focusRing)} href="#subjects">
              Subjects
            </a>
            <a
              className={cn("hover:text-white", focusRing)}
              href="#testimonials"
            >
              Testimonials
            </a>
            <a className={cn("hover:text-white", focusRing)} href="#faq">
              FAQ
            </a>
            <Link
              className={cn("hover:text-white", focusRing)}
              href={signInHref}
            >
              Student sign in
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
