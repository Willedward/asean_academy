import { useId } from "react";

import type { Mood, Outfit, Pose } from "../types";

const T = "#0F3D40";
const T2 = "#1B5357";
const A = "#C87A1E";
const AL = "#E3A44B";
const C = "#FBFAF7";
const D = "#0A2A2C";
const BLUSH = "#E98F6B";

function Eye({ cx, cy, r, look = 1 }: { cx: number; cy: number; r: number; look?: number }) {
  return (
    <>
      <circle cx={cx} cy={cy} r={r} fill={C} />
      <circle cx={cx + look} cy={cy + 1} r={r * 0.58} fill={D} />
      <circle cx={cx + look + 2} cy={cy - 1.8} r={r * 0.2} fill="#FFFFFF" />
    </>
  );
}

function Eyes({ mood }: { mood: Mood }) {
  switch (mood) {
    case "happy":
      return (
        <>
          <path d="M103 63 Q112 51 121 63" stroke={C} strokeWidth={5} strokeLinecap="round" fill="none" />
          <circle cx={120} cy={74} r={5} fill={BLUSH} opacity={0.55} />
        </>
      );
    case "sleepy":
      return (
        <>
          <circle cx={112} cy={60} r={9} fill={C} />
          <circle cx={113} cy={63} r={4.5} fill={D} />
          <path d="M102 60 A10 10 0 0 1 122 60 Z" fill={T} />
          <path d="M103 60 L121 60" stroke={D} strokeWidth={2} strokeLinecap="round" />
        </>
      );
    case "think":
      return (
        <>
          <circle cx={112} cy={60} r={9} fill={C} />
          <circle cx={115} cy={56} r={5} fill={D} />
          <circle cx={116.5} cy={54.5} r={1.6} fill="#FFFFFF" />
        </>
      );
    case "wow":
      return (
        <>
          <circle cx={112} cy={60} r={11} fill={C} />
          <circle cx={113} cy={61} r={6.5} fill={D} />
          <circle cx={115.5} cy={58} r={2.4} fill="#FFFFFF" />
          <circle cx={120} cy={76} r={5} fill={BLUSH} opacity={0.5} />
        </>
      );
    case "kind":
      return (
        <>
          <Eye cx={112} cy={60} r={9} look={1} />
          <path d="M103 48 Q112 44 121 49" stroke={D} strokeWidth={2.5} strokeLinecap="round" fill="none" />
        </>
      );
    default:
      return <Eye cx={112} cy={60} r={9} look={2} />;
  }
}

function Wing({ pose }: { pose: Pose }) {
  if (pose === "cheer") return <path d="M66 104 Q30 86 30 48 Q56 70 82 102 Z" fill={T2} />;
  if (pose === "point") return <path d="M70 108 Q96 118 128 112 Q104 130 72 132 Z" fill={T2} />;
  return <path d="M62 100 Q48 130 66 160 Q82 140 78 106 Z" fill={T2} />;
}

function Accessory({ outfit }: { outfit: Outfit }) {
  switch (outfit) {
    case "cap":
      return (
        <>
          <path d="M86 42 Q106 50 126 42 L126 50 Q106 58 86 50 Z" fill={T2} />
          <path d="M106 18 L142 32 L106 46 L70 32 Z" fill={D} />
          <circle cx={106} cy={32} r={3} fill={A} />
          <path d="M106 32 L136 38 L138 56" stroke={AL} strokeWidth={2.5} fill="none" strokeLinecap="round" />
          <rect x={134.5} y={54} width={7} height={10} rx={2.5} fill={AL} />
        </>
      );
    case "scarf":
      return (
        <>
          <path d="M84 84 Q106 98 128 84 L130 96 Q106 110 82 96 Z" fill={A} />
          <path d="M88 94 L78 124 L92 122 L96 98 Z" fill={A} />
          {[
            [92, 92],
            [102, 96],
            [112, 96],
            [122, 91],
            [86, 110],
          ].map(([x, y]) => (
            <circle key={`${x}-${y}`} cx={x} cy={y} r={2} fill={C} />
          ))}
        </>
      );
    case "headphones":
      return (
        <>
          <path d="M82 62 Q84 30 108 30 Q132 32 132 56" stroke={D} strokeWidth={6} fill="none" strokeLinecap="round" />
          <rect x={76} y={56} width={14} height={22} rx={6} fill={A} />
          <rect x={126} y={50} width={12} height={18} rx={5} fill={A} />
        </>
      );
    case "glasses":
      return (
        <>
          <circle cx={112} cy={60} r={12} fill="none" stroke={D} strokeWidth={3} />
          <path d="M100 58 L88 56" stroke={D} strokeWidth={3} strokeLinecap="round" />
        </>
      );
    case "crown":
      return (
        <>
          <path
            d="M88 38 L92 18 L102 30 L108 12 L116 30 L126 18 L128 38 Z"
            fill={AL}
            stroke={A}
            strokeWidth={2}
            strokeLinejoin="round"
          />
          <circle cx={108} cy={28} r={2.5} fill={C} />
        </>
      );
  }
}

export interface HornbillProps {
  size: number;
  mood?: Mood;
  pose?: Pose;
  outfit?: Outfit | null;
  /** Show the amber branch it perches on. */
  branch?: boolean;
  /** "head" crops to the head, for avatars and small icons. */
  crop?: "body" | "head";
  /** Accessible name. Leave empty when the bird is decoration. */
  label?: string;
  className?: string;
}

/** The NextScholar hornbill. Pure SVG, no assets to load. */
export function Hornbill({
  size,
  mood = "normal",
  pose = "perch",
  outfit = null,
  branch,
  crop = "body",
  label,
  className,
}: HornbillProps) {
  const titleId = useId();
  const showBranch = branch ?? crop === "body";
  const view = crop === "head" ? "72 10 120 120" : "0 0 200 200";
  return (
    <svg
      viewBox={view}
      width={size}
      height={size}
      className={className}
      style={{ display: "block", flexShrink: 0, overflow: crop === "head" ? "hidden" : "visible" }}
      role={label ? "img" : undefined}
      aria-labelledby={label ? titleId : undefined}
      aria-hidden={label ? undefined : true}
    >
      {label ? <title id={titleId}>{label}</title> : null}
      <path d="M72 150 L56 196 L78 196 L88 152 Z" fill={T2} />
      <path d="M58 188 L80 188" stroke={C} strokeWidth={5} />
      <ellipse cx={90} cy={118} rx={36} ry={44} fill={T} />
      <ellipse cx={102} cy={128} rx={20} ry={28} fill={C} />
      <Wing pose={pose} />
      {showBranch ? <path d="M28 166 L176 166" stroke={A} strokeWidth={7} strokeLinecap="round" /> : null}
      <path d="M94 158 L90 168 M106 158 L108 168" stroke={D} strokeWidth={5} strokeLinecap="round" />
      <circle cx={106} cy={64} r={27} fill={T} />
      <path d="M126 58 Q166 60 186 100 Q166 86 128 84 Z" fill={A} />
      <path d="M122 46 Q156 34 176 68 Q156 54 124 60 Z" fill={AL} />
      <path d="M130 84 Q146 88 160 94" stroke={D} strokeWidth={2} fill="none" opacity={0.3} />
      <Eyes mood={mood} />
      {outfit ? <Accessory outfit={outfit} /> : null}
    </svg>
  );
}
