import { MathContent } from "@/components/math-content";

export type TutorBlock = {
  type: "text" | "inline_math" | "display_math" | "bullets";
  content: string;
};

function groupTutorBlocks(blocks: TutorBlock[]) {
  const groups: TutorBlock[][] = [];
  for (const block of blocks) {
    const inline = block.type === "text" || block.type === "inline_math";
    const previous = groups.at(-1);
    if (
      inline &&
      previous?.every(
        (item) => item.type === "text" || item.type === "inline_math",
      )
    ) {
      previous.push(block);
    } else {
      groups.push([block]);
    }
  }
  return groups;
}

function bulletItems(content: string) {
  return content
    .split("\n")
    .map((item) => item.replace(/^\s*(?:[-*•]|\d+[.)])\s*/, "").trim())
    .filter(Boolean);
}

export function TutorContent({ blocks }: { blocks: TutorBlock[] }) {
  return (
    <div className="space-y-2">
      {groupTutorBlocks(blocks).map((group, index) => {
        const block = group[0]!;
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
            {group.map((item, itemIndex) =>
              item.type === "inline_math" ? (
                <MathContent
                  key={itemIndex}
                  blocks={[{ type: "inline_math", latex: item.content }]}
                />
              ) : (
                <span key={itemIndex}>{item.content}</span>
              ),
            )}
          </p>
        );
      })}
    </div>
  );
}
