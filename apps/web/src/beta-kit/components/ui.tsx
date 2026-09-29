import Link from "next/link";
import type { ComponentType, ReactNode } from "react";
import { AlertCircle, Lightbulb } from "lucide-react";

import { cn } from "@/lib/utils";

import type { Href, Tone } from "../types";

type IconType = ComponentType<{ size?: number; className?: string; "aria-hidden"?: boolean }>;

export const focusRing =
  "focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-ns-success";

/* ------------------------------------------------------------------ */
/* Button                                                              */
/* ------------------------------------------------------------------ */

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger" | "gold";

const VARIANT: Record<ButtonVariant, string> = {
  primary: "bg-ns-ink text-ns-on-brand border-ns-ink hover:bg-ns-dark",
  secondary: "bg-ns-raised text-ns-ink border-ns-line-strong hover:bg-ns-sunken",
  ghost: "bg-transparent text-ns-ink border-transparent hover:bg-ns-sunken",
  danger: "bg-ns-raised text-ns-danger border-ns-danger hover:bg-ns-danger-soft",
  gold: "bg-ns-gold text-ns-ink border-ns-gold font-black animate-ns-glow",
};

export interface ButtonProps {
  children: ReactNode;
  variant?: ButtonVariant;
  size?: "md" | "sm";
  full?: boolean;
  href?: Href;
  icon?: IconType;
  iconRight?: IconType;
  disabled?: boolean;
  type?: "button" | "submit";
  /** id of a <form> elsewhere on the page, for submit buttons in a footer. */
  form?: string;
  onClick?: () => void;
  ariaLabel?: string;
  className?: string;
}

export function Button({
  children,
  variant = "secondary",
  size = "md",
  full,
  href,
  icon: Icon,
  iconRight: IconRight,
  disabled,
  type = "button",
  form,
  onClick,
  ariaLabel,
  className,
}: ButtonProps) {
  const classes = cn(
    "inline-flex items-center justify-center gap-2 rounded-full border-[1.5px] font-semibold whitespace-nowrap no-underline transition-colors",
    size === "md" ? "h-11 px-6 text-[15px]" : "h-9 px-4 text-sm",
    full && "flex w-full",
    VARIANT[variant],
    disabled && "pointer-events-none opacity-45",
    focusRing,
    className,
  );
  const inner = (
    <>
      {Icon ? <Icon size={18} aria-hidden /> : null}
      {children}
      {IconRight ? <IconRight size={18} aria-hidden /> : null}
    </>
  );
  if (href && !disabled) {
    return (
      <Link href={href} className={classes} aria-label={ariaLabel}>
        {inner}
      </Link>
    );
  }
  return (
    <button type={type} form={form} className={classes} disabled={disabled} onClick={onClick} aria-label={ariaLabel}>
      {inner}
    </button>
  );
}

export function IconButton({
  icon: Icon,
  label,
  href,
  onClick,
  className,
}: {
  icon: IconType;
  label: string;
  href?: Href;
  onClick?: () => void;
  className?: string;
}) {
  const classes = cn(
    "inline-flex size-11 shrink-0 items-center justify-center rounded-full text-ns-ink hover:bg-ns-sunken",
    focusRing,
    className,
  );
  if (href) {
    return (
      <Link href={href} aria-label={label} className={classes}>
        <Icon size={22} aria-hidden />
      </Link>
    );
  }
  return (
    <button type="button" aria-label={label} onClick={onClick} className={classes}>
      <Icon size={22} aria-hidden />
    </button>
  );
}

/* ------------------------------------------------------------------ */
/* Surfaces and text                                                   */
/* ------------------------------------------------------------------ */

export function Card({
  children,
  className,
  tone = "raised",
  shadow = true,
}: {
  children: ReactNode;
  className?: string;
  tone?: "raised" | "sunken" | "amber" | "success" | "brand";
  shadow?: boolean;
}) {
  const toneClass = {
    raised: "bg-ns-raised border-ns-line",
    sunken: "bg-ns-sunken border-ns-line",
    amber: "bg-ns-amber-soft border-ns-amber-line",
    success: "bg-ns-success-soft border-ns-success-soft",
    brand: "bg-ns-ink border-ns-ink text-ns-on-brand",
  }[tone];
  return (
    <div
      className={cn(
        "flex min-w-0 flex-col gap-3 rounded-2xl border p-5",
        toneClass,
        shadow && tone === "raised" && "shadow-ns-sm",
        className,
      )}
    >
      {children}
    </div>
  );
}

const TAG_TONE: Record<Tone, string> = {
  neutral: "bg-ns-sunken text-ns-muted shadow-[inset_0_0_0_1px_var(--color-ns-line)]",
  brand: "bg-ns-brand-soft text-ns-ink",
  amber: "bg-ns-amber-soft text-ns-amber-text",
  success: "bg-ns-success-soft text-ns-success",
  danger: "bg-ns-danger-soft text-ns-danger",
};

export function Tag({ children, tone = "neutral", icon: Icon }: { children: ReactNode; tone?: Tone; icon?: IconType }) {
  return (
    <span
      className={cn(
        "inline-flex h-6 shrink-0 items-center gap-1 rounded-full px-2.5 text-xs font-semibold tracking-[0.02em] whitespace-nowrap",
        TAG_TONE[tone],
      )}
    >
      {Icon ? <Icon size={14} aria-hidden /> : null}
      {children}
    </span>
  );
}

export function Eyebrow({ children, muted }: { children: ReactNode; muted?: boolean }) {
  return (
    <div className={cn("text-xs font-semibold tracking-[0.02em]", muted ? "text-ns-muted" : "text-ns-amber-text")}>
      {children}
    </div>
  );
}

export function H1({ children, className }: { children: ReactNode; className?: string }) {
  return <h1 className={cn("m-0 text-[26px] leading-8 font-bold tracking-[-0.01em] lg:text-[32px] lg:leading-10", className)}>{children}</h1>;
}

export function H2({ children, className }: { children: ReactNode; className?: string }) {
  return <h2 className={cn("m-0 text-xl leading-7 font-semibold", className)}>{children}</h2>;
}

export function H3({ children, className }: { children: ReactNode; className?: string }) {
  return <h3 className={cn("m-0 text-[17px] leading-6 font-semibold", className)}>{children}</h3>;
}

export function Muted({ children, className }: { children: ReactNode; className?: string }) {
  return <p className={cn("m-0 text-sm leading-5 text-ns-muted", className)}>{children}</p>;
}

export function Divider() {
  return <div className="h-px bg-ns-line" />;
}

export function Stat({ value, label, sub }: { value: ReactNode; label: string; sub?: string }) {
  return (
    <div className="flex min-w-0 flex-col gap-0.5">
      <div className="text-[26px] leading-8 font-bold tabular-nums">{value}</div>
      <div className="text-[13px] leading-[18px] text-ns-muted">{label}</div>
      {sub ? <div className="text-xs text-ns-muted">{sub}</div> : null}
    </div>
  );
}

export function Avatar({ initials, size = 36 }: { initials: string; size?: number }) {
  return (
    <span
      aria-hidden="true"
      className="inline-flex shrink-0 items-center justify-center rounded-full bg-ns-brand-soft font-bold text-ns-ink"
      style={{ width: size, height: size, fontSize: Math.round(size * 0.36) }}
    >
      {initials}
    </span>
  );
}

export function IconCircle({
  icon: Icon,
  tone = "brand",
  size = 36,
}: {
  icon: IconType;
  tone?: Tone;
  size?: number;
}) {
  return (
    <span
      className={cn("inline-flex shrink-0 items-center justify-center rounded-full", TAG_TONE[tone])}
      style={{ width: size, height: size }}
    >
      <Icon size={Math.round(size / 2)} aria-hidden />
    </span>
  );
}

/* ------------------------------------------------------------------ */
/* Progress                                                            */
/* ------------------------------------------------------------------ */

export function Bar({ pct, height = 8, fill = "amber" }: { pct: number; height?: number; fill?: "amber" | "success" }) {
  return (
    <div className="overflow-hidden rounded-full bg-ns-brand-soft" style={{ height }}>
      <div
        className={cn("h-full rounded-full", fill === "success" ? "bg-ns-success" : "bg-ns-amber")}
        style={{ width: `${Math.max(0, Math.min(100, pct))}%` }}
      />
    </div>
  );
}

export function ProgressBar({
  label,
  value,
  pct,
  fill = "amber",
}: {
  label: string;
  value: string;
  pct: number;
  fill?: "amber" | "success";
}) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex justify-between gap-3 text-sm leading-5">
        <span className="font-semibold">{label}</span>
        <span className="text-ns-muted tabular-nums">{value}</span>
      </div>
      <div role="progressbar" aria-label={label} aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
        <Bar pct={pct} height={10} fill={fill} />
      </div>
    </div>
  );
}

/** Segmented progress for question steps. */
export function Steps({ done, current, total }: { done: number; current: number; total: number }) {
  return (
    <div aria-hidden="true" className="flex gap-1.5">
      {Array.from({ length: total }, (_, i) => (
        <span
          key={i}
          className={cn(
            "h-1.5 flex-1 rounded-full",
            i < done ? "bg-ns-success" : i === current ? "bg-ns-amber" : "bg-ns-line",
          )}
        />
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Callouts and fields                                                 */
/* ------------------------------------------------------------------ */

export function Callout({
  children,
  tone = "amber",
  icon: Icon = Lightbulb,
}: {
  children: ReactNode;
  tone?: Tone;
  icon?: IconType;
}) {
  const bg = {
    amber: "bg-ns-amber-soft text-ns-amber-text",
    brand: "bg-ns-brand-soft text-ns-ink",
    success: "bg-ns-success-soft text-ns-success",
    danger: "bg-ns-danger-soft text-ns-danger",
    neutral: "bg-ns-sunken text-ns-muted",
  }[tone];
  return (
    <div role="status" className={cn("flex items-start gap-3 rounded-xl p-4", bg)}>
      <span className="flex pt-0.5">
        <Icon size={20} aria-hidden />
      </span>
      <div className="flex min-w-0 grow flex-col gap-1 text-sm leading-5 text-ns-ink">{children}</div>
    </div>
  );
}

export function Field({
  id,
  name,
  label,
  value,
  placeholder,
  hint,
  error,
  readOnly,
  math,
  mono,
  onChange,
}: {
  id: string;
  /** Form field name, so the input posts with a <form> or server action. */
  name?: string;
  label: ReactNode;
  value?: string;
  placeholder?: string;
  hint?: ReactNode;
  error?: string;
  readOnly?: boolean;
  math?: boolean;
  mono?: boolean;
  onChange?: (value: string) => void;
}) {
  const described = error || hint ? `${id}-msg` : undefined;
  return (
    <div className="flex min-w-0 flex-col gap-2">
      <label htmlFor={id} className="text-[15px] leading-5 font-semibold">
        {label}
      </label>
      <input
        id={id}
        name={name}
        type="text"
        defaultValue={onChange ? undefined : value}
        value={onChange ? (value ?? "") : undefined}
        onChange={onChange ? (event) => onChange(event.target.value) : undefined}
        placeholder={placeholder}
        readOnly={readOnly}
        aria-invalid={error ? true : undefined}
        aria-describedby={described}
        className={cn(
          "h-12 w-full min-w-0 rounded-lg border-[1.5px] px-4 text-base text-ns-ink",
          error ? "border-ns-danger" : "border-ns-line-strong",
          readOnly ? "bg-ns-sunken" : "bg-ns-raised",
          math && "font-ns-math text-lg",
          mono && "font-mono tracking-wide",
          focusRing,
        )}
      />
      {error ? (
        <div id={described} className="flex items-start gap-1.5 text-sm leading-5 font-semibold text-ns-danger">
          <AlertCircle size={18} className="shrink-0" aria-hidden />
          <span>{error}</span>
        </div>
      ) : hint ? (
        <div id={described} className="text-sm leading-5 text-ns-muted">
          {hint}
        </div>
      ) : null}
    </div>
  );
}

/** Inline maths, e.g. <M>360<i>k</i></M>. Real content should go through the
 *  app's existing MathContent (KaTeX) component. */
export function M({ children }: { children: ReactNode }) {
  return <span className="font-ns-math text-[1.12em] text-ns-ink">{children}</span>;
}

export function Sup({ base, exp }: { base: ReactNode; exp: ReactNode }) {
  return (
    <>
      {base}
      <sup className="text-[0.7em]">{exp}</sup>
    </>
  );
}

/** Bottom sheet dialog used on phones (centred card on desktop). */
export function Sheet({
  titleId,
  children,
}: {
  titleId: string;
  children: ReactNode;
}) {
  return (
    <div className="fixed inset-0 z-40 flex items-end justify-center bg-ns-dark/45 lg:items-center">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="flex w-full max-w-[520px] flex-col gap-4 rounded-t-3xl bg-ns-raised px-5 pt-3 pb-7 shadow-ns-lg lg:rounded-3xl lg:pt-6"
      >
        <span className="h-1 w-10 self-center rounded-full bg-ns-line lg:hidden" />
        {children}
      </div>
    </div>
  );
}
