import katex from "katex";
import { Fragment } from "react";

export type ContentBlock =
  | { type: "text"; text: string }
  | { type: "inline_math"; latex: string }
  | { type: "display_math"; latex: string }
  | { type: "asset_ref"; asset_key: string };

function MathExpression({ latex, displayMode }: { latex: string; displayMode: boolean }) {
  const markup = katex.renderToString(latex, {
    displayMode,
    throwOnError: false,
    strict: "warn",
    trust: false,
  });
  return (
    <span
      aria-label={latex}
      className={displayMode ? "my-3 block overflow-x-auto py-1" : "inline-block"}
      dangerouslySetInnerHTML={{ __html: markup }}
    />
  );
}

export function MathContent({ blocks }: { blocks: ContentBlock[] }) {
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
          {block.type === "asset_ref" ? (
            <span className="text-amber-800">[Diagram: {block.asset_key}]</span>
          ) : null}
        </Fragment>
      ))}
    </>
  );
}
