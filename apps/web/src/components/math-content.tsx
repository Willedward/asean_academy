import katex from "katex";
import { Fragment } from "react";

import { DisplayMath } from "@/components/display-math";

export type ContentBlock =
  | { type: "text"; text: string }
  | { type: "inline_math"; latex: string }
  | { type: "display_math"; latex: string }
  | { type: "asset_ref"; asset_key: string };

export type ContentAsset = {
  asset_key: string;
  alt_text: string;
  width?: number | null;
  height?: number | null;
};

function MathExpression({
  latex,
  displayMode,
  lead = "",
  trail = "",
}: {
  latex: string;
  displayMode: boolean;
  lead?: string;
  trail?: string;
}) {
  const markup = katex.renderToString(latex, {
    displayMode,
    throwOnError: false,
    strict: "warn",
    trust: false,
  });
  if (displayMode) return <DisplayMath markup={markup} />;
  const expression = (
    <span
      className="inline-block"
      dangerouslySetInnerHTML={{ __html: markup }}
    />
  );
  if (!lead && !trail) return expression;
  return (
    <span className="whitespace-nowrap">
      {lead}
      {expression}
      {trail}
    </span>
  );
}

// Inline maths is an atomic inline-block, so the browser may break the line between
// it and touching punctuation, leaving "." or ")" alone at the start of a line. The
// punctuation that touches an expression is moved into one unbreakable span with it.
const CLOSING = /^[.,;:!?%)\]}’”'"]+/;
const OPENING = /[(\[{‘“$]+$/;

function touchingLead(previous: ContentBlock | undefined) {
  return previous?.type === "text"
    ? (previous.text.match(OPENING)?.[0] ?? "")
    : "";
}

function touchingTrail(next: ContentBlock | undefined) {
  return next?.type === "text" ? (next.text.match(CLOSING)?.[0] ?? "") : "";
}

function textBlock(blocks: ContentBlock[], index: number, text: string) {
  const previous = blocks[index - 1];
  const next = blocks[index + 1];
  let start = 0;
  let end = text.length;
  if (previous?.type === "inline_math")
    start = touchingTrail(blocks[index]).length;
  if (next?.type === "inline_math") end -= touchingLead(blocks[index]).length;
  return textWithSeparator(previous, start < end ? text.slice(start, end) : "");
}

/**
 * Authors split sentences into separate text blocks ("…totals 360°." then "Use…").
 * Rendered inline, the blocks would run together ("360°.Use"), so a text block that
 * directly follows another text block gets a space unless either side already has one.
 */
function textWithSeparator(previous: ContentBlock | undefined, text: string) {
  if (previous?.type !== "text" || !previous.text || !text) return text;
  if (/\s$/.test(previous.text) || /^\s/.test(text)) return text;
  return ` ${text}`;
}

export function MathContent({
  assets = [],
  assetScope,
  blocks,
}: {
  assets?: ContentAsset[];
  assetScope?: { kind: "lesson" | "question"; stableKey: string };
  blocks: ContentBlock[];
}) {
  const assetByKey = new Map(assets.map((asset) => [asset.asset_key, asset]));
  return (
    <>
      {blocks.map((block, index) => (
        <Fragment key={index}>
          {block.type === "text" ? textBlock(blocks, index, block.text) : null}
          {block.type === "inline_math" ? (
            <MathExpression
              displayMode={false}
              latex={block.latex}
              lead={touchingLead(blocks[index - 1])}
              trail={touchingTrail(blocks[index + 1])}
            />
          ) : null}
          {block.type === "display_math" ? (
            <MathExpression displayMode latex={block.latex} />
          ) : null}
          {block.type === "asset_ref"
            ? (() => {
                const asset = assetByKey.get(block.asset_key);
                if (!asset || !assetScope) {
                  return (
                    <span className="text-amber-800">
                      [Diagram unavailable]
                    </span>
                  );
                }
                const source = `/api/v1/content-assets/${assetScope.kind}/${encodeURIComponent(assetScope.stableKey)}/${encodeURIComponent(asset.asset_key)}`;
                return (
                  <span className="my-4 block overflow-hidden rounded-2xl border border-slate-200 bg-white p-3">
                    {/* Authenticated dynamic SVGs are intentionally served through the app proxy. */}
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      alt={asset.alt_text}
                      className="mx-auto h-auto max-h-[32rem] w-auto max-w-full"
                      height={asset.height ?? undefined}
                      loading="lazy"
                      src={source}
                      width={asset.width ?? undefined}
                    />
                  </span>
                );
              })()
            : null}
        </Fragment>
      ))}
    </>
  );
}
