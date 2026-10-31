"use client";

import {
  AlertTriangle,
  CheckCircle2,
  ClipboardCheck,
  LockKeyhole,
} from "lucide-react";
import { useEffect, useState } from "react";

import {
  Button,
  Callout,
  Card,
  Divider,
  Eyebrow,
  H3,
  Muted,
  Tag,
} from "@/beta-kit/components/ui";
import {
  createEnglishEssaySelfReview,
  type EnglishEssaySelfReviewCriterionRequest,
  type EnglishEssaySelfReviewResponse,
  type EnglishEssaySelfReviewWorkspaceResponse,
  type EnglishEssaySubmissionResponse,
  getEnglishEssaySelfReviewWorkspace,
} from "@/lib/api/english";

import { EnglishEssayMarking } from "./english-essay-marking";

type ReflectionDraft = {
  selectedBandLevel: number | null;
  evidenceNote: string;
  improvementAction: string;
};

function emptyReflection(): ReflectionDraft {
  return {
    selectedBandLevel: null,
    evidenceNote: "",
    improvementAction: "",
  };
}

function emptyReflections(
  workspace: EnglishEssaySelfReviewWorkspaceResponse,
): Record<string, ReflectionDraft> {
  return Object.fromEntries(
    workspace.criteria.map((criterion) => [
      criterion.criterion_key,
      emptyReflection(),
    ]),
  );
}

function completedReview(
  review: EnglishEssaySelfReviewResponse,
  completedAt: string,
) {
  return (
    <div
      className="flex flex-col gap-4"
      role="region"
      aria-label="Completed self-review"
    >
      <Callout tone="success" icon={CheckCircle2}>
        <strong>Your self-review is saved permanently.</strong>
        <span>
          Completed{" "}
          {new Intl.DateTimeFormat("en-SG", {
            dateStyle: "medium",
            timeStyle: "short",
            timeZone: "Asia/Singapore",
          }).format(new Date(completedAt))}
          . It is learner-authored and contains no AI feedback or official
          score.
        </span>
      </Callout>
      {review.criterion_reflections.map((reflection) => (
        <Card key={reflection.criterion_key} tone="sunken" shadow={false}>
          <div className="flex flex-wrap items-start justify-between gap-2">
            <H3>{reflection.criterion_title}</H3>
            <Tag>
              Descriptor {reflection.selected_band_level}:{" "}
              {reflection.selected_band_label}
            </Tag>
          </div>
          <Muted>{reflection.selected_band_descriptor}</Muted>
          <Divider />
          <div className="grid gap-3 md:grid-cols-2">
            <div>
              <p className="m-0 text-sm font-semibold text-ns-ink">
                Your evidence
              </p>
              <p className="m-0 mt-1 text-sm leading-6 text-ns-muted">
                {reflection.evidence_note}
              </p>
            </div>
            <div>
              <p className="m-0 text-sm font-semibold text-ns-ink">
                Your next action
              </p>
              <p className="m-0 mt-1 text-sm leading-6 text-ns-muted">
                {reflection.improvement_action}
              </p>
            </div>
          </div>
        </Card>
      ))}
      <Card tone="brand" shadow={false}>
        <Eyebrow>OVERALL REFLECTION</Eyebrow>
        <p className="m-0 leading-7">{review.overall_reflection}</p>
      </Card>
    </div>
  );
}

function SubmittedEssayCard({
  workspace,
}: {
  workspace: EnglishEssaySelfReviewWorkspaceResponse;
}) {
  return (
    <Card
      tone="sunken"
      shadow={false}
      className="lg:sticky lg:top-5 lg:max-h-[720px] lg:overflow-y-auto"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <H3>Submitted essay</H3>
        <Tag>Submission {workspace.submission.submission_revision}</Tag>
      </div>
      <Muted>
        This is the permanent snapshot you are reviewing, not your current
        editable draft.
      </Muted>
      <Divider />
      <p className="m-0 whitespace-pre-wrap text-[15px] leading-7 text-ns-ink">
        {workspace.submission.body}
      </p>
    </Card>
  );
}

export function EnglishEssaySelfReview({
  submission,
}: {
  submission: EnglishEssaySubmissionResponse;
}) {
  const [workspace, setWorkspace] =
    useState<EnglishEssaySelfReviewWorkspaceResponse | null>(null);
  const [reflections, setReflections] = useState<
    Record<string, ReflectionDraft>
  >({});
  const [overallReflection, setOverallReflection] = useState("");
  const [acknowledged, setAcknowledged] = useState(false);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [completed, setCompleted] =
    useState<EnglishEssaySelfReviewResponse | null>(null);

  useEffect(() => {
    let active = true;
    void getEnglishEssaySelfReviewWorkspace(submission.submission_id).then(
      (loaded) => {
        if (!active) return;
        setWorkspace(loaded);
        setCompleted(loaded.self_review ?? null);
        setReflections(emptyReflections(loaded));
        setBusy(false);
      },
      () => {
        if (!active) return;
        setError(
          "The pinned self-review rubric could not be loaded. Try again.",
        );
        setBusy(false);
      },
    );
    return () => {
      active = false;
    };
  }, [submission.submission_id]);

  if (busy) {
    return <Muted>Loading the exact rubric for this submission…</Muted>;
  }
  if (!workspace || error) {
    return (
      <Callout tone="amber" icon={AlertTriangle}>
        <strong>Self-review is temporarily unavailable.</strong>
        <span>{error}</span>
      </Callout>
    );
  }
  if (completed) {
    return (
      <div
        className="grid gap-4 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]"
        role="region"
        aria-label="Completed essay self-review"
      >
        <SubmittedEssayCard workspace={workspace} />
        <div className="flex flex-col gap-4">
          {completedReview(completed, completed.completed_at)}
          <EnglishEssayMarking submissionId={submission.submission_id} />
        </div>
      </div>
    );
  }

  const complete =
    workspace.criteria.every((criterion) => {
      const reflection = reflections[criterion.criterion_key];
      return Boolean(
        reflection?.selectedBandLevel &&
        reflection.evidenceNote.trim() &&
        reflection.improvementAction.trim(),
      );
    }) && Boolean(overallReflection.trim() && acknowledged);

  function updateReflection(
    criterionKey: string,
    patch: Partial<ReflectionDraft>,
  ) {
    setReflections((current) => ({
      ...current,
      [criterionKey]: {
        ...(current[criterionKey] ?? emptyReflection()),
        ...patch,
      },
    }));
  }

  async function submitReview() {
    if (!complete) return;
    setBusy(true);
    setError(null);
    const payload: EnglishEssaySelfReviewCriterionRequest[] =
      workspace!.criteria.map((criterion) => {
        const reflection = reflections[criterion.criterion_key];
        if (!reflection || reflection.selectedBandLevel === null) {
          throw new Error("Every rubric criterion requires a reflection.");
        }
        return {
          criterion_key: criterion.criterion_key,
          selected_band_level: reflection.selectedBandLevel,
          evidence_note: reflection.evidenceNote.trim(),
          improvement_action: reflection.improvementAction.trim(),
        };
      });
    try {
      const created = await createEnglishEssaySelfReview(
        submission.submission_id,
        payload,
        overallReflection.trim(),
      );
      setCompleted(created);
    } catch {
      setError(
        "The self-review could not be completed. Your essay submission is unchanged; try again.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className="flex flex-col gap-5"
      role="region"
      aria-label="Essay self-review form"
    >
      <div className="grid gap-4 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
        <SubmittedEssayCard workspace={workspace} />
        <div className="flex flex-col gap-4">
          {workspace.criteria.map((criterion) => {
            const reflection =
              reflections[criterion.criterion_key] ?? emptyReflection();
            return (
              <Card key={criterion.criterion_key} className="gap-4">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="flex flex-col gap-1">
                    <H3>{criterion.title}</H3>
                    <Muted>{criterion.description}</Muted>
                  </div>
                  <Tag>{criterion.weight_percent}% instructional emphasis</Tag>
                </div>
                <fieldset className="flex flex-col gap-2">
                  <legend className="mb-2 text-sm font-semibold text-ns-ink">
                    Which descriptor best matches this submitted response?
                  </legend>
                  {criterion.bands.map((band) => (
                    <label
                      key={band.level}
                      className="flex cursor-pointer items-start gap-3 rounded-xl border border-ns-line p-3 text-sm leading-6 has-[:checked]:border-ns-brand has-[:checked]:bg-ns-brand-soft"
                    >
                      <input
                        type="radio"
                        name={`band-${criterion.criterion_key}`}
                        value={band.level}
                        checked={reflection.selectedBandLevel === band.level}
                        onChange={() =>
                          updateReflection(criterion.criterion_key, {
                            selectedBandLevel: band.level,
                          })
                        }
                        className="mt-1 size-4 accent-ns-brand"
                      />
                      <span>
                        <strong>
                          {band.level}. {band.label}
                        </strong>
                        <span className="mt-0.5 block text-ns-muted">
                          {band.descriptor}
                        </span>
                      </span>
                    </label>
                  ))}
                </fieldset>
                <label className="flex flex-col gap-1.5 text-sm font-semibold text-ns-ink">
                  Evidence from this essay
                  <textarea
                    value={reflection.evidenceNote}
                    onChange={(event) =>
                      updateReflection(criterion.criterion_key, {
                        evidenceNote: event.target.value,
                      })
                    }
                    maxLength={1000}
                    placeholder="Point to a sentence, paragraph or pattern that supports your choice."
                    className="min-h-24 rounded-xl border-[1.5px] border-ns-line-strong bg-ns-raised p-3 font-normal leading-6 focus:border-ns-brand focus:outline-none focus:ring-2 focus:ring-ns-brand/20"
                  />
                </label>
                <label className="flex flex-col gap-1.5 text-sm font-semibold text-ns-ink">
                  One specific improvement action
                  <textarea
                    value={reflection.improvementAction}
                    onChange={(event) =>
                      updateReflection(criterion.criterion_key, {
                        improvementAction: event.target.value,
                      })
                    }
                    maxLength={1000}
                    placeholder="State what you will change or practise in your next version."
                    className="min-h-24 rounded-xl border-[1.5px] border-ns-line-strong bg-ns-raised p-3 font-normal leading-6 focus:border-ns-brand focus:outline-none focus:ring-2 focus:ring-ns-brand/20"
                  />
                </label>
              </Card>
            );
          })}
        </div>
      </div>
      <Card tone="amber" className="gap-4">
        <div className="flex items-start gap-3">
          <ClipboardCheck
            className="mt-0.5 shrink-0 text-ns-amber-text"
            aria-hidden
          />
          <div className="flex grow flex-col gap-3">
            <label className="flex flex-col gap-1.5 text-sm font-semibold text-ns-ink">
              Overall reflection
              <textarea
                value={overallReflection}
                onChange={(event) => setOverallReflection(event.target.value)}
                maxLength={2000}
                placeholder="What is the most important strength to keep and the first change to make next?"
                className="min-h-28 rounded-xl border-[1.5px] border-ns-amber-line bg-ns-raised p-3 font-normal leading-6 focus:border-ns-brand focus:outline-none focus:ring-2 focus:ring-ns-brand/20"
              />
            </label>
            <label className="flex cursor-pointer items-start gap-3 rounded-xl border border-ns-amber-line bg-ns-raised p-4 text-sm leading-6 text-ns-ink">
              <input
                type="checkbox"
                checked={acknowledged}
                onChange={(event) => setAcknowledged(event.target.checked)}
                className="mt-1 size-4 accent-ns-brand"
              />
              <span>{workspace.learner_disclaimer}</span>
            </label>
            {error ? (
              <Callout tone="danger" icon={AlertTriangle}>
                <strong>Self-review was not completed.</strong>
                <span>{error}</span>
              </Callout>
            ) : null}
            <Button
              variant="primary"
              onClick={() => void submitReview()}
              disabled={!complete || busy}
              icon={LockKeyhole}
            >
              {busy ? "Saving permanent self-review…" : "Complete self-review"}
            </Button>
            <Muted className="text-xs">
              Completion is permanent for this submission. You can create a new
              essay submission and review that revision separately.
            </Muted>
          </div>
        </div>
      </Card>
    </div>
  );
}
