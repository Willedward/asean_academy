import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { ContentItem, ContentPreview, ContentQueue } from "@/lib/api/admin-dashboard";

import { ContentReviewPanel } from "./content-review-panel";

const item: ContentItem = {
  content_kind: "question",
  stable_key: "n1-l1-01",
  revision: 1,
  source_content_sha256: "a".repeat(64),
  review_fingerprint: "b".repeat(64),
  title: "Prime factorisation",
  source_status: "draft",
  difficulty: 1,
  outcome_code: "1.1",
  position: null,
  review_state: "approved",
  mathematics_review: null,
  editorial_review: null,
  lifecycle_request: null,
  blockers: [],
  can_request_publication: true,
  can_request_retirement: false,
};

const queue: ContentQueue = { items: [item], total: 1, limit: 25, offset: 0 };
const preview: ContentPreview = {
  content_kind: "question",
  stable_key: item.stable_key,
  revision: item.revision,
  review_fingerprint: item.review_fingerprint,
  public_content: {
    title: item.title,
    stem: [],
    difficulty: 1,
    primary_outcome: "1.1",
    total_marks: 2,
    parts: [
      {
        position: 1,
        label: null,
        marks: 2,
        prompt: [],
        input_placeholder: "Enter your answer",
      },
    ],
  },
};

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("ContentReviewPanel", () => {
  it("lets a content administrator preview safely and submit only editorial review", async () => {
    const fetcher = vi.fn(async (url: string, init: RequestInit) => {
      void init;
      if (url.includes("/preview")) return new Response(JSON.stringify(preview));
      if (url.includes("/reviews")) return new Response(JSON.stringify({}), { status: 201 });
      return new Response(JSON.stringify(queue));
    });
    vi.stubGlobal("fetch", fetcher);

    render(<ContentReviewPanel academic={false} />);
    await screen.findByText("Prime factorisation");

    const reviewArea = screen.getByLabelText("Review area for n1-l1-01");
    expect(reviewArea).toHaveValue("editorial");
    expect(screen.getByRole("option", { name: "Mathematics" })).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "Preview as student" }));
    expect(await screen.findByLabelText("Student answer for part 1")).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Review notes for n1-l1-01"), {
      target: { value: "Language and marks have been checked." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Record review" }));

    await waitFor(() => {
      const call = fetcher.mock.calls.find(([url]) => String(url).includes("/reviews"));
      expect(call).toBeDefined();
      expect(JSON.parse(String(call?.[1]?.body))).toMatchObject({
        dimension: "editorial",
        decision: "approved",
      });
    });
  });

  it("requires an explicit reason before an academic publication request", async () => {
    const fetcher = vi.fn(async (url: string, init?: RequestInit) => {
      void init;
      if (url.includes("/lifecycle-requests")) {
        return new Response(JSON.stringify({}), { status: 201 });
      }
      return new Response(JSON.stringify(queue));
    });
    vi.stubGlobal("fetch", fetcher);

    render(<ContentReviewPanel academic />);
    fireEvent.click(await screen.findByRole("button", { name: "Review publication request" }));

    const confirm = screen.getByRole("button", { name: "Confirm publish request" });
    expect(confirm).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Reason for publish request"), {
      target: { value: "Both independent reviews are complete." },
    });
    fireEvent.click(confirm);

    await waitFor(() => {
      const call = fetcher.mock.calls.find(([url]) =>
        String(url).includes("/lifecycle-requests"),
      );
      expect(call).toBeDefined();
      expect(JSON.parse(String(call?.[1]?.body))).toMatchObject({
        action: "publish",
        reason: "Both independent reviews are complete.",
      });
    });
  });
});
