import { MathContent } from "@/components/math-content";

export type TutorBlock = {
  type: "text" | "display_math" | "bullets";
  content: string;
};

function bulletItems(content: string) {
  return content
    .split("\n")
    .map((item) => item.replace(/^\s*(?:[-*•]|\d+[.)])\s*/, "").trim())
    .filter(Boolean);
}

export function TutorContent({ blocks }: { blocks: TutorBlock[] }) {
  return (
    <div className="space-y-2">
      {blocks.map((block, index) => {
        if (block.type === "display_math") {
          return (
            <MathContent
              key={index}
              blocks={[{ type: "display_math", latex: block.content }]}
            />
          );
        }
        if (block.type === "bullets") {
          return (
            <ul key={index} className="list-disc space-y-1 pl-5">
              {bulletItems(block.content).map((item, itemIndex) => (
                <li key={itemIndex}>{item}</li>
              ))}
            </ul>
          );
        }
        return (
          <p key={index} className="whitespace-pre-wrap">
            {block.content}
          </p>
        );
      })}
    </div>
  );
}
