import type { SVGProps } from "react";

/**
 * Filled game glyphs (flame, bolt, star, crown) and a few outline ones that
 * lucide-react does not draw the way the design needs. Everything else in the
 * kit uses lucide-react, which the app already depends on.
 */
export type GameIconName = "flame" | "bolt" | "star" | "crown" | "trophy" | "snow" | "target" | "lock";

const PATHS: Record<GameIconName, { d: string[]; filled: boolean }> = {
  flame: {
    d: ["M12 2.5c1.2 4 5.5 5.3 5.5 10.5a5.5 5.5 0 0 1-11 0c0-2.4 1.2-3.8 2.4-4.8 0 2.2 1 3.4 2.3 3.6-.3-3.6-.8-6 .8-9.3z"],
    filled: true,
  },
  bolt: { d: ["M13.5 2 4.5 13.5h6.5L10 22l9.5-12H13z"], filled: true },
  star: { d: ["M12 2.8l2.8 5.8 6.3.9-4.6 4.4 1.1 6.3L12 17.2l-5.6 3 1.1-6.3-4.6-4.4 6.3-.9z"], filled: true },
  crown: { d: ["M3.5 18.5h17l1-11-5.5 4.2L12 4.5 8 11.7 2.5 7.5z"], filled: true },
  trophy: {
    d: [
      "M7.5 3.5h9v5.5a4.5 4.5 0 0 1-9 0z",
      "M7.5 5.5H4.5a3 3 0 0 0 3.2 4.3M16.5 5.5h3a3 3 0 0 1-3.2 4.3M12 13.5v3.5M8 20.5h8M9.5 17h5v3.5h-5z",
    ],
    filled: false,
  },
  snow: { d: ["M12 2.5v19M3.8 7.2l16.4 9.6M3.8 16.8l16.4-9.6M9.3 4.2 12 6l2.7-1.8M9.3 19.8 12 18l2.7 1.8"], filled: false },
  target: { d: [], filled: false },
  lock: { d: ["M8 11V7a4 4 0 0 1 8 0v4"], filled: false },
};

export interface GameIconProps extends Omit<SVGProps<SVGSVGElement>, "name"> {
  name: GameIconName;
  size?: number;
}

export function GameIcon({ name, size = 20, className, ...rest }: GameIconProps) {
  const spec = PATHS[name];
  const paint = spec.filled
    ? { fill: "currentColor", stroke: "none" }
    : { fill: "none", stroke: "currentColor", strokeWidth: 2, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      aria-hidden="true"
      className={className}
      style={{ flexShrink: 0, display: "block" }}
      {...paint}
      {...rest}
    >
      {name === "target" ? (
        <>
          <circle cx={12} cy={12} r={9} />
          <circle cx={12} cy={12} r={5} />
          <circle cx={12} cy={12} r={1.2} />
        </>
      ) : null}
      {name === "lock" ? <rect x={5} y={11} width={14} height={10} rx={2} /> : null}
      {spec.d.map((d) => (
        <path key={d} d={d} />
      ))}
    </svg>
  );
}
