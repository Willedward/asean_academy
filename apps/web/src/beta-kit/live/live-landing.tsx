import Link from "next/link";
import { BookOpen, CheckCircle2, RotateCcw, Sigma } from "lucide-react";

import { Hornbill } from "../components/hornbill";
import { Button, Card, H3, Muted, Tag } from "../components/ui";
import { BareShell, Logo } from "../shell/app-shell";

const FEATURES = [
  {
    icon: BookOpen,
    title: "Learn in course order",
    text: "Build each mathematics idea through structured notes, worked examples and active recall.",
  },
  {
    icon: CheckCircle2,
    title: "Submit final answers",
    text: "Typed numeric and algebraic answers are checked consistently against reviewed answer rules.",
  },
  {
    icon: RotateCcw,
    title: "Retry what needs work",
    text: "Use authored hints, study the worked solution when needed and revisit unresolved questions later.",
  },
  {
    icon: Sigma,
    title: "Singapore G3 Mathematics",
    text: "The private beta begins with Secondary 1 and Secondary 2 Express-equivalent mathematics.",
  },
] as const;

export function LiveLandingScreen({ signInHref }: { signInHref: string }) {
  return (
    <BareShell>
      <header className="flex h-16 items-center justify-between gap-3 border-b border-ns-line px-5 lg:h-20 lg:px-20">
        <Link href="/" aria-label="NextScholar home">
          <Logo height={26} />
        </Link>
        <Button href={signInHref} size="sm">
          Sign in
        </Button>
      </header>

      <main className="flex flex-col gap-10 px-5 pt-8 pb-12 lg:gap-16 lg:px-20 lg:pt-20 lg:pb-20">
        <section className="grid gap-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-center lg:gap-16">
          <div className="flex max-w-[620px] flex-col items-start gap-5">
            <Tag tone="amber">Private mathematics beta</Tag>
            <h1 className="m-0 text-[40px] leading-[45px] font-bold tracking-[-0.02em] lg:text-[60px] lg:leading-[64px]">
              Learn the idea. Practise it. Know what to improve next.
            </h1>
            <p className="m-0 max-w-[580px] text-[17px] leading-7 text-ns-muted lg:text-[19px] lg:leading-8">
              NextScholar is a structured learning course for students preparing
              with Singapore Secondary G3 Mathematics. Lessons, typed-answer
              practice and progress evidence stay connected in one path.
            </p>
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
              <Button href={signInHref} variant="primary">
                Sign in with your invitation
              </Button>
              <Muted>Access is limited to invited beta students.</Muted>
            </div>
          </div>

          <div className="relative flex min-h-[310px] items-center justify-center overflow-hidden rounded-3xl border border-ns-line bg-[radial-gradient(circle_at_50%_48%,var(--color-ns-amber-soft)_0%,var(--color-ns-sunken)_72%)] lg:min-h-[440px]">
            <Hornbill
              size={270}
              mood="happy"
              pose="cheer"
              outfit="scarf"
              label="NextScholar hornbill welcoming students"
              className="size-[210px] lg:size-[290px]"
            />
            <div className="absolute right-5 bottom-5 left-5 rounded-2xl border border-ns-line bg-ns-raised/95 p-4 shadow-ns-md lg:right-10 lg:bottom-8 lg:left-10">
              <div className="text-sm font-bold text-ns-ink">
                Current beta course
              </div>
              <div className="mt-1 text-sm leading-5 text-ns-muted">
                Singapore Secondary 1 G3 Mathematics, beginning with Numbers and
                their Operations.
              </div>
            </div>
          </div>
        </section>

        <section
          aria-label="How NextScholar helps"
          className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"
        >
          {FEATURES.map(({ icon: Icon, title, text }) => (
            <Card key={title} className="gap-3">
              <span className="inline-flex size-11 items-center justify-center rounded-full bg-ns-brand-soft text-ns-ink">
                <Icon size={21} aria-hidden />
              </span>
              <H3>{title}</H3>
              <Muted className="text-[15px] leading-[22px]">{text}</Muted>
            </Card>
          ))}
        </section>
      </main>
    </BareShell>
  );
}
