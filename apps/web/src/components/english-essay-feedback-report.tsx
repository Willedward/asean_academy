"use client";

import {
  AlertTriangle,
  CheckCircle2,
  FileClock,
  FlaskConical,
  Quote,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { useEffect, useState } from "react";

import {
  Button,
  Callout,
  Card,
  Divider,
  Eyebrow,
  H2,
  H3,
  Muted,
  Tag,
} from "@/beta-kit/components/ui";
import {
  createEnglishEssayFeedbackUsefulness,
  getEnglishEssayFeedbackReport,
  getEnglishEssayHistory,
  type EnglishEssayFeedbackReportResponse,
  type EnglishEssayHistoryResponse,
  type EnglishEssayUsefulnessRating,
} from "@/lib/api/english";

const RATING_OPTIONS: Array<{
  value: EnglishEssayUsefulnessRating;
  label: string;
}> = [
  { value: "helpful", label: "Helpful" },
  { value: "partly_helpful", label: "Partly helpful" },
  { value: "not_helpful", label: "Not helpful" },
];

function displayDate(value: string): string {
  return new Intl.DateTimeFormat("en-SG", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Singapore",
  }).format(new Date(value));
}

function ratingLabel(rating: EnglishEssayUsefulnessRating): string {
  return (
    RATING_OPTIONS.find((option) => option.value === rating)?.label ?? rating
  );
}

export function EnglishEssayFeedbackReport({
  draftId,
  currentSubmissionId,
}: {
  draftId: string;
  currentSubmissionId: string;
}) {
  const [history, setHistory] = useState<EnglishEssayHistoryResponse | null>(
    null,
  );
  const [selectedSubmissionId, setSelectedSubmissionId] =
    useState(currentSubmissionId);
  const [report, setReport] =
    useState<EnglishEssayFeedbackReportResponse | null>(null);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [loadingReport, setLoadingReport] = useState(true);
  const [historyRefresh, setHistoryRefresh] = useState(0);
  const [reportRefresh, setReportRefresh] = useState(0);
  const [rating, setRating] = useState<EnglishEssayUsefulnessRating | null>(
    null,
  );
  const [note, setNote] = useState("");
  const [ratingBusy, setRatingBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void getEnglishEssayHistory(draftId).then(
      (loaded) => {
        if (!active) return;
        setHistory(loaded);
        setError(null);
        setLoadingHistory(false);
      },
      () => {
        if (!active) return;
        setError("Essay version history could not be loaded. Try again.");
        setLoadingHistory(false);
      },
    );
    return () => {
      active = false;
    };
  }, [draftId, historyRefresh]);

  useEffect(() => {
    let active = true;
    void getEnglishEssayFeedbackReport(selectedSubmissionId).then(
      (loaded) => {
        if (!active) return;
        setReport(loaded);
        setError(null);
        setLoadingReport(false);
      },
      () => {
        if (!active) return;
        setError(
          "The feedback report for this submission could not be loaded.",
        );
        setLoadingReport(false);
      },
    );
    return () => {
      active = false;
    };
  }, [reportRefresh, selectedSubmissionId]);

  async function submitUsefulness() {
    const feedback = report?.feedback;
    if (!feedback || !rating || report.usefulness_response) return;
    setRatingBusy(true);
    setError(null);
    try {
      const created = await createEnglishEssayFeedbackUsefulness(
        report.submission.submission_id,
        feedback.feedback_id,
        feedback.feedback_source,
        rating,
        note.trim() || null,
      );
      setReport({ ...report, usefulness_response: created });
      setHistory((current) =>
        current
          ? {
              ...current,
              submissions: current.submissions.map((item) =>
                item.submission_id === created.submission_id
                  ? { ...item, usefulness_rating: created.rating }
                  : item,
              ),
            }
          : current,
      );
    } catch {
      setError("Your usefulness response could not be saved. Try again.");
    } finally {
      setRatingBusy(false);
    }
  }

  const feedback = report?.feedback;

  return (
    <section
      aria-label="Essay version history and feedback"
      className="flex flex-col gap-4"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex flex-col gap-1">
          <Eyebrow>VERSION HISTORY &amp; FEEDBACK</Eyebrow>
          <H2>Review feedback against the exact submitted essay</H2>
          <Muted>
            Each report stays pinned to one permanent submission, even after you
            continue editing or submit another revision.
          </Muted>
        </div>
        <Button
          size="sm"
          icon={RefreshCw}
          onClick={() => {
            setLoadingHistory(true);
            setLoadingReport(true);
            setHistoryRefresh((value) => value + 1);
            setReportRefresh((value) => value + 1);
          }}
        >
          Refresh reports
        </Button>
      </div>

      {error ? (
        <Callout tone="amber" icon={AlertTriangle}>
          <strong>Some feedback information is unavailable.</strong>
          <span>{error}</span>
        </Callout>
      ) : null}

      <div className="grid items-start gap-4 lg:grid-cols-[280px_minmax(0,1fr)]">
        <Card className="gap-3">
          <div className="flex items-center gap-2">
            <FileClock size={19} className="text-ns-brand" aria-hidden />
            <H3>Submitted versions</H3>
          </div>
          {loadingHistory ? <Muted>Loading submission history…</Muted> : null}
          <div className="flex flex-col gap-2">
            {history?.submissions.map((item) => {
              const selected = item.submission_id === selectedSubmissionId;
              return (
                <button
                  key={item.submission_id}
                  type="button"
                  aria-pressed={selected}
                  onClick={() => {
                    if (!selected) {
                      setLoadingReport(true);
                      setReport(null);
                      setRating(null);
                      setNote("");
                      setSelectedSubmissionId(item.submission_id);
                    }
                  }}
                  className={`rounded-xl border p-3 text-left transition-colors ${
                    selected
                      ? "border-ns-brand bg-ns-brand-soft"
                      : "border-ns-line bg-ns-raised hover:bg-ns-sunken"
                  }`}
                >
                  <span className="block text-sm font-semibold text-ns-ink">
                    Submission {item.submission_revision}
                  </span>
                  <span className="mt-1 block text-xs leading-5 text-ns-muted">
                    {item.word_count} words · {displayDate(item.submitted_at)}
                  </span>
                  <span className="mt-2 flex flex-wrap gap-1.5">
                    <Tag tone={item.feedback_id ? "success" : "neutral"}>
                      {item.feedback_id ? "Feedback ready" : "No feedback yet"}
                    </Tag>
                    {item.usefulness_rating ? (
                      <Tag>{ratingLabel(item.usefulness_rating)}</Tag>
                    ) : null}
                  </span>
                </button>
              );
            })}
          </div>
        </Card>

        <div className="flex min-w-0 flex-col gap-4">
          {loadingReport ? (
            <Card>
              <Muted>Loading the pinned report…</Muted>
            </Card>
          ) : null}
          {report ? (
            <>
              <Callout tone="brand" icon={FileClock}>
                <strong>
                  Immutable submission {report.submission.submission_revision}
                </strong>
                <span>{report.exact_submission_notice}</span>
              </Callout>
              <div className="grid items-start gap-4 xl:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)]">
                <Card
                  tone="sunken"
                  shadow={false}
                  className="xl:sticky xl:top-5 xl:max-h-[760px] xl:overflow-y-auto"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <H3>Exact submitted essay</H3>
                    <Tag>{report.submission.word_count} words</Tag>
                  </div>
                  <Muted>
                    Submitted {displayDate(report.submission.submitted_at)}.
                    Later draft edits are not shown here.
                  </Muted>
                  <Divider />
                  <p className="m-0 whitespace-pre-wrap text-[15px] leading-7 text-ns-ink">
                    {report.submission.body}
                  </p>
                </Card>

                {!feedback ? (
                  <Card className="gap-4">
                    <Callout tone="neutral" icon={FileClock}>
                      <strong>
                        No feedback report exists for this submission yet.
                      </strong>
                      <span>
                        Complete self-review and request feedback, then refresh
                        this report. The essay snapshot remains safely stored.
                      </span>
                    </Callout>
                  </Card>
                ) : (
                  <div
                    className="flex flex-col gap-4"
                    aria-label="Pinned essay feedback report"
                  >
                    <Card className="gap-4">
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <Eyebrow>
                            {feedback.feedback_source === "development_fixture"
                              ? "DEVELOPMENT FIXTURE"
                              : "VALIDATED AI FEEDBACK"}
                          </Eyebrow>
                          <H3>Structured revision report</H3>
                        </div>
                        {feedback.preparation_estimate ? (
                          <Tag tone="brand" icon={Sparkles}>
                            AI preparation estimate:{" "}
                            {feedback.preparation_estimate}
                          </Tag>
                        ) : null}
                      </div>
                      {feedback.feedback_source === "development_fixture" ? (
                        <Callout tone="amber" icon={FlaskConical}>
                          <strong>
                            This is deterministic test feedback, not live AI
                            marking.
                          </strong>
                          <span>
                            It validates the report workflow without a paid API
                            call.
                          </span>
                        </Callout>
                      ) : null}
                      <p className="m-0 leading-7 text-ns-ink">
                        {feedback.overall_summary}
                      </p>
                      <div className="grid gap-3 sm:grid-cols-2">
                        <Card tone="success" shadow={false}>
                          <p className="m-0 text-sm font-semibold text-ns-ink">
                            Keep doing
                          </p>
                          <ul className="m-0 space-y-2 pl-5 text-sm leading-6 text-ns-muted">
                            {feedback.strengths.map((strength) => (
                              <li key={strength}>{strength}</li>
                            ))}
                          </ul>
                        </Card>
                        <Card tone="amber" shadow={false}>
                          <p className="m-0 text-sm font-semibold text-ns-ink">
                            Prioritise next
                          </p>
                          <ul className="m-0 space-y-2 pl-5 text-sm leading-6 text-ns-muted">
                            {feedback.priorities.map((priority) => (
                              <li key={priority}>{priority}</li>
                            ))}
                          </ul>
                        </Card>
                      </div>
                    </Card>

                    {feedback.criterion_feedback.map((criterion) => (
                      <Card key={criterion.criterion_key} className="gap-4">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <H3>{criterion.criterion_title}</H3>
                          {criterion.preparation_level ? (
                            <Tag>
                              Preparation level {criterion.preparation_level}/5
                            </Tag>
                          ) : null}
                        </div>
                        {(criterion.evidence_spans ?? []).length ? (
                          <div className="flex flex-col gap-2">
                            <p className="m-0 text-sm font-semibold text-ns-ink">
                              Evidence from this essay
                            </p>
                            {(criterion.evidence_spans ?? []).map((span) => (
                              <blockquote
                                key={`${span.start}-${span.end}-${span.quote}`}
                                className="m-0 flex gap-2 rounded-xl border-l-4 border-ns-amber bg-ns-sunken p-3 text-sm italic leading-6 text-ns-ink"
                              >
                                <Quote
                                  size={17}
                                  className="mt-0.5 shrink-0 text-ns-amber-text"
                                  aria-hidden
                                />
                                <span>{span.quote}</span>
                              </blockquote>
                            ))}
                          </div>
                        ) : criterion.observed_evidence ? (
                          <div>
                            <p className="m-0 text-sm font-semibold text-ns-ink">
                              Evidence noticed
                            </p>
                            <Muted>{criterion.observed_evidence}</Muted>
                          </div>
                        ) : null}
                        <div className="grid gap-3 sm:grid-cols-2">
                          <div>
                            <p className="m-0 text-sm font-semibold text-ns-ink">
                              What works
                            </p>
                            <Muted>{criterion.what_works}</Muted>
                          </div>
                          <div>
                            <p className="m-0 text-sm font-semibold text-ns-ink">
                              Next revision step
                            </p>
                            <Muted>{criterion.next_step}</Muted>
                          </div>
                        </div>
                      </Card>
                    ))}

                    {feedback.revision_task || feedback.transfer_goal ? (
                      <Card tone="brand" shadow={false}>
                        {feedback.revision_task ? (
                          <div>
                            <Eyebrow>REVISION TASK</Eyebrow>
                            <p className="m-0 mt-1 leading-7">
                              {feedback.revision_task}
                            </p>
                          </div>
                        ) : null}
                        {feedback.transfer_goal ? (
                          <div>
                            <Eyebrow>TRANSFER GOAL</Eyebrow>
                            <p className="m-0 mt-1 leading-7">
                              {feedback.transfer_goal}
                            </p>
                          </div>
                        ) : null}
                      </Card>
                    ) : null}

                    <Callout tone="amber" icon={AlertTriangle}>
                      <strong>
                        Preparation guidance, not an official result.
                      </strong>
                      <span>{feedback.learner_disclaimer}</span>
                    </Callout>

                    {report.usefulness_response ? (
                      <Callout tone="success" icon={CheckCircle2}>
                        <strong>Your response is saved permanently.</strong>
                        <span>
                          You rated this report “
                          {ratingLabel(report.usefulness_response.rating)}”. The
                          response cannot be edited, which preserves the
                          evaluation record.
                        </span>
                      </Callout>
                    ) : (
                      <Card className="gap-4">
                        <div>
                          <H3>Was this report useful?</H3>
                          <Muted>
                            Your answer is recorded once and cannot be changed.
                          </Muted>
                        </div>
                        <fieldset className="flex flex-wrap gap-2">
                          <legend className="sr-only">
                            Feedback usefulness
                          </legend>
                          {RATING_OPTIONS.map((option) => (
                            <label
                              key={option.value}
                              className="cursor-pointer rounded-full border border-ns-line-strong px-4 py-2 text-sm font-semibold text-ns-ink has-[:checked]:border-ns-brand has-[:checked]:bg-ns-brand-soft"
                            >
                              <input
                                type="radio"
                                name={`feedback-rating-${feedback.feedback_id}`}
                                value={option.value}
                                checked={rating === option.value}
                                onChange={() => setRating(option.value)}
                                className="sr-only"
                              />
                              {option.label}
                            </label>
                          ))}
                        </fieldset>
                        <label className="flex flex-col gap-2 text-sm font-semibold text-ns-ink">
                          Optional note
                          <textarea
                            value={note}
                            onChange={(event) => setNote(event.target.value)}
                            maxLength={1000}
                            rows={3}
                            className="rounded-xl border border-ns-line-strong bg-ns-raised p-3 font-normal leading-6 focus:border-ns-brand focus:outline-none focus:ring-2 focus:ring-ns-brand/20"
                          />
                        </label>
                        <Button
                          variant="primary"
                          disabled={!rating || ratingBusy}
                          onClick={() => void submitUsefulness()}
                        >
                          {ratingBusy
                            ? "Saving response…"
                            : "Save usefulness response"}
                        </Button>
                      </Card>
                    )}
                  </div>
                )}
              </div>
            </>
          ) : null}
        </div>
      </div>
    </section>
  );
}
