"use client";

import { ArrowRight, FilePenLine } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button, Card, Eyebrow, H2, Muted, Tag } from "@/beta-kit/components/ui";
import {
  createEnglishEssayDraft,
  type EnglishEssayPromptResponse,
} from "@/lib/api/english";

export function EnglishEssayDraftCard({
  prompt,
}: {
  prompt: EnglishEssayPromptResponse;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function openDraft() {
    setBusy(true);
    setError(null);
    try {
      const draft = await createEnglishEssayDraft(
        prompt.stable_key,
        prompt.revision,
      );
      router.push(`/english/essays/${draft.draft_id}`);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Your essay draft could not be opened.",
      );
      setBusy(false);
    }
  }

  return (
    <Card className="gap-4 border-ns-brand bg-ns-brand-soft/40">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="max-w-2xl">
          <Eyebrow>EXTENDED WRITING · DRAFT ONLY</Eyebrow>
          <H2>{prompt.title}</H2>
          <Muted className="mt-1">{prompt.prompt_text}</Muted>
          <div className="mt-3 flex flex-wrap gap-2">
            <Tag icon={FilePenLine}>{prompt.time_limit_minutes} minutes</Tag>
            {prompt.word_count_guidance ? (
              <Tag>About {prompt.word_count_guidance} words</Tag>
            ) : null}
            <Tag tone="amber">No marking yet</Tag>
          </div>
        </div>
        <Button
          variant="primary"
          icon={ArrowRight}
          disabled={busy}
          onClick={() => void openDraft()}
        >
          {busy ? "Opening…" : "Write or resume"}
        </Button>
      </div>
      <p className="m-0 text-sm font-semibold text-ns-muted">
        Your working copy autosaves. Submission and AI feedback remain disabled
        until later quality gates are complete.
      </p>
      {error ? (
        <p role="alert" className="m-0 text-sm font-semibold text-red-700">
          {error}
        </p>
      ) : null}
    </Card>
  );
}
