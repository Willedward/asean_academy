import katex from "katex";
import { Fragment } from "react";

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
}: {
  latex: string;
  displayMode: boolean;
}) {
  const markup = katex.renderToString(latex, {
    displayMode,
    throwOnError: false,
    strict: "warn",
    trust: false,
  });
  return (
    <span
      aria-label={latex}
      className={
        displayMode ? "my-3 block overflow-x-auto py-1" : "inline-block"
      }
      dangerouslySetInnerHTML={{ __html: markup }}
    />
  );
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
          {block.type === "text" ? block.text : null}
          {block.type === "inline_math" ? (
            <MathExpression displayMode={false} latex={block.latex} />
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
