"use client";

import { ArrowRight, Clock, Lock, RefreshCw } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import {
  Button,
  Callout,
  Card,
  Eyebrow,
  H2,
  Muted,
  Tag,
} from "@/beta-kit/components/ui";
import {
  createEnglishMockSession,
  listEnglishMocks,
  type EnglishMockAction,
} from "@/lib/api/english";

export function EnglishMockCard() {
  const router = useRouter();
  const [mocks, setMocks] = useState<EnglishMockAction[] | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let active = true;
    void listEnglishMocks().then(
      (response) => {
        if (active) {
          setMocks(response);
          setError(null);
        }
      },
      (caught: unknown) => {
        if (active)
          setError(
            caught instanceof Error
              ? caught.message
              : "The English mocks could not be loaded.",
          );
      },
    );
    return () => {
      active = false;
    };
  }, [reload]);

  async function start(purpose: EnglishMockAction["purpose"]) {
    setBusy(purpose);
    setError(null);
    try {
      const session = await createEnglishMockSession(purpose);
      router.push(`/english/diagnostics/${session.session_id}`);
    } catch (caught: unknown) {
      setError(
        caught instanceof Error
          ? caught.message
          : "The English mock could not be started.",
      );
      setBusy(null);
    }
  }

  if (error) {
    return (
      <Callout tone="amber" icon={RefreshCw}>
        <strong>English mocks unavailable</strong>
        <span>{error}</span>
        <Button onClick={() => setReload((value) => value + 1)}>
          Try again
        </Button>
      </Callout>
    );
  }
  if (!mocks) {
    return (
      <Card className="animate-pulse">
        <Muted>Loading English mocks…</Muted>
      </Card>
    );
  }

  return (
    <Card className="gap-4">
      <div>
        <Eyebrow>FULL MOCK · SECTION 1</Eyebrow>
        <H2>Practise the whole paper</H2>
        <Muted className="mt-1">
          Each mock follows the reported 90-minute format. It is practice, not
          an official score. Section 2 is the separate timed composition.
        </Muted>
      </div>
      <ul className="m-0 flex list-none flex-col gap-3 p-0">
        {mocks.map((mock) => (
          <li
            key={mock.purpose}
            className="flex flex-col gap-3 rounded-xl border border-ns-line p-4 sm:flex-row sm:items-center sm:justify-between"
          >
            <div>
              <strong>{mock.title}</strong>
              <Muted className="mt-1">{mock.message}</Muted>
              <div className="mt-2 flex flex-wrap gap-2">
                <Tag icon={Clock}>{mock.estimated_minutes} minutes</Tag>
                {mock.expected_part_count ? (
                  <Tag>{mock.expected_part_count} scored parts</Tag>
                ) : null}
              </div>
            </div>
            {mock.status === "start" ? (
              <Button
                variant="primary"
                icon={ArrowRight}
                disabled={busy !== null}
                onClick={() => void start(mock.purpose)}
              >
                {busy === mock.purpose ? "Starting…" : "Start mock"}
              </Button>
            ) : null}
            {mock.status === "resume" && mock.session_id ? (
              <Button
                variant="primary"
                icon={ArrowRight}
                href={`/english/diagnostics/${mock.session_id}`}
              >
                Resume
              </Button>
            ) : null}
            {mock.status === "completed" && mock.result_session_id ? (
              <Button
                icon={ArrowRight}
                href={`/english/diagnostics/${mock.result_session_id}/result`}
              >
                View results
              </Button>
            ) : null}
            {mock.status === "locked" ? (
              <Tag tone="neutral" icon={Lock}>
                Locked
              </Tag>
            ) : null}
            {mock.status === "content_pending" ? (
              <Tag tone="neutral">In preparation</Tag>
            ) : null}
          </li>
        ))}
      </ul>
    </Card>
  );
}
