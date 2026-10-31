"use client";

import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  FlaskConical,
  RefreshCw,
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
  createEnglishEssayMarkingJob,
  getEnglishEssayMarkingWorkspace,
  type EnglishEssayMarkingWorkspaceResponse,
} from "@/lib/api/english";

const PENDING = new Set(["queued", "processing", "retryable_failed"]);

export function EnglishEssayMarking({
  submissionId,
}: {
  submissionId: string;
}) {
  const [workspace, setWorkspace] =
    useState<EnglishEssayMarkingWorkspaceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [requesting, setRequesting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const next = await getEnglishEssayMarkingWorkspace(submissionId);
        if (!active) return;
        setWorkspace(next);
        setError(null);
      } catch {
        if (active) {
          setError("Fixture feedback status could not be loaded. Try again.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, [submissionId]);

  const markingStatus = workspace?.job?.status;
  useEffect(() => {
    if (!markingStatus || !PENDING.has(markingStatus)) return;
    let active = true;
    let timeout: ReturnType<typeof setTimeout>;
    async function poll() {
      try {
        const next = await getEnglishEssayMarkingWorkspace(submissionId);
        if (!active) return;
        setWorkspace(next);
        setError(null);
        if (next.job && PENDING.has(next.job.status)) {
          timeout = setTimeout(() => void poll(), 1200);
        }
      } catch {
        if (!active) return;
        setError("Fixture feedback status could not be refreshed.");
        timeout = setTimeout(() => void poll(), 3000);
      }
    }
    timeout = setTimeout(() => void poll(), 1200);
    return () => {
      active = false;
      clearTimeout(timeout);
    };
  }, [markingStatus, submissionId]);

  async function requestFeedback() {
    setRequesting(true);
    setError(null);
    try {
      const created = await createEnglishEssayMarkingJob(submissionId);
      setWorkspace(created);
      const restored = await getEnglishEssayMarkingWorkspace(submissionId);
      setWorkspace(restored);
    } catch {
      setError(
        "Fixture feedback could not be queued. Your submission and self-review are unchanged.",
      );
    } finally {
      setRequesting(false);
    }
  }

  if (loading && !workspace) {
    return <Muted>Checking fixture feedback status…</Muted>;
  }

  const job = workspace?.job;
  const feedback = workspace?.feedback;

  if (feedback) {
    return (
      <div role="region" aria-label="Fixture essay feedback">
        <Card className="gap-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <Eyebrow>DEVELOPMENT FIXTURE</Eyebrow>
              <H3>Structured revision feedback</H3>
            </div>
            <Tag tone="success" icon={CheckCircle2}>
              Fixture complete
            </Tag>
          </div>
          <Callout tone="amber" icon={FlaskConical}>
            <strong>This is not live AI marking.</strong>
            <span>{feedback.learner_disclaimer}</span>
          </Callout>
          <p className="m-0 leading-7 text-ns-ink">
            {feedback.overall_summary}
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            <Card tone="success" shadow={false}>
              <p className="m-0 text-sm font-semibold text-ns-ink">Keep</p>
              <ul className="m-0 mt-2 space-y-2 pl-5 text-sm leading-6 text-ns-muted">
                {feedback.strengths.map((strength) => (
                  <li key={strength}>{strength}</li>
                ))}
              </ul>
            </Card>
            <Card tone="amber" shadow={false}>
              <p className="m-0 text-sm font-semibold text-ns-ink">
                Prioritise
              </p>
              <ul className="m-0 mt-2 space-y-2 pl-5 text-sm leading-6 text-ns-muted">
                {feedback.priorities.map((priority) => (
                  <li key={priority}>{priority}</li>
                ))}
              </ul>
            </Card>
          </div>
          <Divider />
          {feedback.criterion_feedback.map((criterion) => (
            <Card key={criterion.criterion_key} tone="sunken" shadow={false}>
              <H3>{criterion.criterion_title}</H3>
              <div className="mt-3 grid gap-3">
                <div>
                  <p className="m-0 text-sm font-semibold text-ns-ink">
                    Evidence noticed
                  </p>
                  <Muted>{criterion.observed_evidence}</Muted>
                </div>
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
        </Card>
      </div>
    );
  }

  if (job && PENDING.has(job.status)) {
    return (
      <Callout tone="amber" icon={Clock3}>
        <strong>Fixture feedback is being prepared.</strong>
        <span>
          Attempt {job.attempt_count} of {job.max_attempts}. This page checks
          the durable job automatically; no external provider is being used.
        </span>
        {error ? <span>{error} Retrying automatically.</span> : null}
      </Callout>
    );
  }

  if (job?.status === "permanent_failed") {
    return (
      <Callout tone="danger" icon={AlertTriangle}>
        <strong>
          The fixture worker stopped after {job.max_attempts} attempts.
        </strong>
        <span>
          Your essay and self-review are safe. An administrator can inspect the
          stored failure before retry support is enabled.
        </span>
      </Callout>
    );
  }

  return (
    <Card tone="brand" className="gap-4">
      <div className="flex items-start gap-3">
        <FlaskConical className="mt-0.5 shrink-0 text-ns-brand" aria-hidden />
        <div>
          <H3>Test structured marking feedback</H3>
          <Muted>
            This deterministic fixture exercises the full queue and feedback UI.
            It makes no paid API call and does not give an official score.
          </Muted>
        </div>
      </div>
      {error ? (
        <Callout tone="danger" icon={AlertTriangle}>
          <strong>Fixture feedback is unavailable.</strong>
          <span>{error}</span>
        </Callout>
      ) : null}
      <Button
        variant="primary"
        icon={requesting ? RefreshCw : FlaskConical}
        disabled={requesting}
        onClick={() => void requestFeedback()}
      >
        {requesting ? "Queuing fixture feedback…" : "Generate fixture feedback"}
      </Button>
    </Card>
  );
}
