import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type {
  ContentItem,
  ContentPreview,
  ContentQueue,
} from "@/lib/api/admin-dashboard";

import { ContentReviewPanel } from "./content-review-panel";

const item: ContentItem = {
  content_kind: "question",
  stable_key: "n2-l1-001",
  revision: 1,
  source_content_sha256: "a".repeat(64),
  review_fingerprint: "b".repeat(64),
  title: "Simplifying a ratio",
  source_status: "draft",
  difficulty: 1,
  outcome_code: "2.1",
  position: null,
  batch_id: "g3-sec1-n2-b001",
  unit_key: "g3-sec1-n2",
  review_state: "approved",
  mathematics_review: null,
  editorial_review: null,
  lifecycle_request: null,
  blockers: [],
  can_request_publication: true,
  can_request_retirement: false,
};

const queue: ContentQueue = {
  items: [item],
  batch_ids: ["g3-sec1-n2-b001"],
  unit_keys: ["g3-sec1-n2"],
  total: 1,
  limit: 25,
  offset: 0,
};
const preview: ContentPreview = {
  content_kind: "question",
  stable_key: item.stable_key,
  revision: item.revision,
  review_fingerprint: item.review_fingerprint,
  batch_id: "g3-sec1-n2-b001",
  review_content: {
    stable_key: item.stable_key,
    title: item.title,
    stem: [{ type: "asset_ref", asset_key: "n2-l1-001-diagram" }],
    assets: [
      {
        asset_key: "n2-l1-001-diagram",
        alt_text: "A ratio diagram for reviewer inspection.",
      },
    ],
    difficulty: 1,
    primary_outcome: "2.1",
    total_marks: 2,
    calculator_allowed: false,
    parts: [
      {
        position: 1,
        label: null,
        marks: 2,
        prompt: [{ type: "text", text: "Simplify the ratio 12:18." }],
        response: {
          type: "algebraic_expression",
          canonical_expression: "2:3",
        },
        hints: [
          {
            stage: 1,
            content: [
              { type: "text", text: "Find the greatest common factor." },
            ],
          },
        ],
        solution: [
          {
            position: 1,
            content: [{ type: "display_math", latex: "12:18=2:3" }],
            mark_type: "A",
            mark_value: 2,
          },
        ],
      },
    ],
  },
};

const groundingItem: ContentItem = {
  ...item,
  content_kind: "tutor_grounding",
  stable_key: "g3-sec1-n2-tutor-grounding-v1",
  title: "Ratio and proportion tutor calibration grounding",
  outcome_code: "N2",
  batch_id: null,
  unit_key: null,
  review_state: "unreviewed",
  blockers: [
    "Mathematics approval is required.",
    "Editorial approval is required.",
  ],
  can_request_publication: false,
};

const groundingPreview: ContentPreview = {
  content_kind: "tutor_grounding",
  stable_key: groundingItem.stable_key,
  revision: 1,
  review_fingerprint: groundingItem.review_fingerprint,
  batch_id: null,
  review_content: {
    grounding_id: groundingItem.stable_key,
    revision: 1,
    status: "draft_for_review",
    title: groundingItem.title,
    topic_code: "N2",
    scope: "Secondary 1 outcomes 2.1, 2.2 and 2.3 only",
    source_references: [
      {
        path: "backend_resources/syllabi/g3_math/v1/catalogue.json",
        role: "official_syllabus_transcription",
      },
    ],
    sections_by_outcome: {
      "2.1": [
        {
          section_key: "ratio-meaning-and-order",
          section_type: "explanation",
          title: "Meaning and order of a ratio",
          content: {
            blocks: [
              {
                type: "text",
                text: "A ratio compares quantities in a stated order.",
              },
              { type: "display_math", content: "3:5" },
            ],
          },
        },
      ],
    },
  },
};

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("ContentReviewPanel", () => {
  it("lets a content administrator open the protected preview and submit only editorial review", async () => {
    const fetcher = vi.fn(async (url: string, init: RequestInit) => {
      void init;
      if (url.includes("/review-preview"))
        return new Response(JSON.stringify(preview));
      if (url.includes("/reviews"))
        return new Response(JSON.stringify({}), { status: 201 });
      return new Response(JSON.stringify(queue));
    });
    vi.stubGlobal("fetch", fetcher);

    render(<ContentReviewPanel academic={false} />);
    await screen.findByText("Simplifying a ratio");

    const reviewArea = screen.getByLabelText("Review area for n2-l1-001");
    expect(reviewArea).toHaveValue("editorial");
    expect(screen.getByRole("option", { name: "Mathematics" })).toBeDisabled();

    fireEvent.click(
      screen.getByRole("button", { name: "Open reviewer preview" }),
    );
    expect(await screen.findByText("Canonical answer")).toBeInTheDocument();
    expect(screen.getByText("Authored hints")).toBeInTheDocument();
    expect(screen.getByText("Worked solution")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Review notes for n2-l1-001"), {
      target: { value: "Language and marks have been checked." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Record review" }));

    await waitFor(() => {
      const call = fetcher.mock.calls.find(([url]) =>
        String(url).includes("/reviews"),
      );
      expect(call).toBeDefined();
      expect(JSON.parse(String(call?.[1]?.body))).toMatchObject({
        dimension: "editorial",
        decision: "approved",
      });
    });
  });

  it("routes diagram feedback into a changes-requested review note", async () => {
    const fetcher = vi.fn(async (url: string) => {
      if (url.includes("/review-preview"))
        return new Response(JSON.stringify(preview));
      return new Response(JSON.stringify(queue));
    });
    vi.stubGlobal("fetch", fetcher);

    render(<ContentReviewPanel academic />);
    await screen.findByText("Simplifying a ratio");
    fireEvent.click(
      screen.getByRole("button", { name: "Open reviewer preview" }),
    );

    fireEvent.click(
      await screen.findByRole("button", { name: "Comment on diagram" }),
    );

    expect(screen.getByLabelText("Decision for n2-l1-001")).toHaveValue(
      "changes_requested",
    );
    expect(screen.getByLabelText("Review notes for n2-l1-001")).toHaveValue(
      "Diagram n2-l1-001-diagram: ",
    );
    expect(screen.getByLabelText("Review notes for n2-l1-001")).toHaveFocus();
  });

  it("filters the queue by authoring batch and shows batch approval progress", async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify(queue)));
    vi.stubGlobal("fetch", fetcher);

    render(<ContentReviewPanel academic />);
    await screen.findByText("Simplifying a ratio");

    fireEvent.change(screen.getByLabelText("Authoring batch"), {
      target: { value: "g3-sec1-n2-b001" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Apply filters" }));

    await waitFor(() => {
      expect(fetcher).toHaveBeenCalledWith(
        expect.stringContaining("batch_id=g3-sec1-n2-b001"),
        expect.anything(),
      );
      expect(fetcher).toHaveBeenCalledWith(
        expect.stringContaining("limit=250"),
        expect.anything(),
      );
    });
    expect(screen.getByTestId("scope-progress")).toHaveTextContent(
      "0 fully approved",
    );
    expect(
      screen.getByRole("link", { name: "Open correction export" }),
    ).toHaveAttribute(
      "href",
      expect.stringContaining("batch_id=g3-sec1-n2-b001"),
    );
  });

  it("reviews a unit as one packet while excluding an item that needs correction", async () => {
    const lesson: ContentItem = {
      ...item,
      content_kind: "lesson",
      stable_key: "g3-sec1-n2-l1",
      source_content_sha256: "c".repeat(64),
      review_fingerprint: "d".repeat(64),
      title: "Ratios and equivalent ratios",
      batch_id: null,
      position: 1,
      review_state: "unreviewed",
    };
    const unitQueue: ContentQueue = {
      ...queue,
      items: [lesson, item],
      total: 2,
      limit: 250,
    };
    const fetcher = vi.fn(async (url: string, init?: RequestInit) => {
      if (url.includes("bulk-review-preview")) {
        return new Response(
          JSON.stringify({
            scope: "unit",
            scope_key: "g3-sec1-n2",
            items: [preview],
          }),
        );
      }
      if (url.includes("bulk-reviews")) {
        return new Response(
          JSON.stringify({
            scope: "unit",
            scope_key: "g3-sec1-n2",
            recorded_count: 1,
            records: [],
          }),
          { status: 201 },
        );
      }
      if (url.includes("unit_key=g3-sec1-n2")) {
        return new Response(JSON.stringify(unitQueue));
      }
      void init;
      return new Response(JSON.stringify(queue));
    });
    vi.stubGlobal("fetch", fetcher);

    render(<ContentReviewPanel academic />);
    await screen.findByText("Simplifying a ratio");

    fireEvent.change(screen.getByLabelText("Curriculum unit"), {
      target: { value: "g3-sec1-n2" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Apply filters" }));

    await screen.findByText("Review g3-sec1-n2 as one consolidated packet");
    fireEvent.click(screen.getByLabelText("Include g3-sec1-n2-l1"));
    expect(screen.getByText(/1 excluded for correction/)).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", {
        name: "Open consolidated reviewer preview",
      }),
    );
    expect(
      await screen.findByText("Consolidated reviewer preview · 1 items"),
    ).toBeInTheDocument();

    const previewCall = fetcher.mock.calls.find(([url]) =>
      String(url).includes("bulk-review-preview"),
    );
    expect(JSON.parse(String(previewCall?.[1]?.body))).toMatchObject({
      scope: "unit",
      scope_key: "g3-sec1-n2",
      targets: [
        {
          content_kind: "question",
          stable_key: "n2-l1-001",
          source_revision: 1,
        },
      ],
    });

    fireEvent.change(screen.getByLabelText("Bulk review notes"), {
      target: { value: "All selected answers and explanations were checked." },
    });
    fireEvent.click(screen.getByLabelText("Confirm bulk review"));
    fireEvent.click(screen.getByRole("button", { name: "Record 1 reviews" }));

    await waitFor(() => {
      const reviewCall = fetcher.mock.calls.find(([url]) =>
        String(url).includes("bulk-reviews"),
      );
      expect(reviewCall).toBeDefined();
      expect(JSON.parse(String(reviewCall?.[1]?.body))).toMatchObject({
        scope: "unit",
        scope_key: "g3-sec1-n2",
        dimension: "mathematics",
        decision: "approved",
        confirmed: true,
        targets: [{ stable_key: "n2-l1-001" }],
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
    fireEvent.click(
      await screen.findByRole("button", { name: "Review publication request" }),
    );

    const confirm = screen.getByRole("button", {
      name: "Confirm publish request",
    });
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

  it("renders protected tutor grounding without a student publication action", async () => {
    const groundingQueue: ContentQueue = {
      ...queue,
      items: [groundingItem],
      batch_ids: [],
      unit_keys: [],
    };
    const fetcher = vi.fn(async (url: string) => {
      if (url.includes("/review-preview")) {
        return new Response(JSON.stringify(groundingPreview));
      }
      return new Response(JSON.stringify(groundingQueue));
    });
    vi.stubGlobal("fetch", fetcher);

    render(<ContentReviewPanel academic />);
    await screen.findByText(groundingItem.title);
    expect(
      screen.getByText(
        /Both approvals unlock the live model-evaluation milestone/,
      ),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Review publication request" }),
    ).not.toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", { name: "Open reviewer preview" }),
    );

    expect(await screen.findByText("Outcome 2.1")).toBeInTheDocument();
    expect(
      screen.getByText("Meaning and order of a ratio"),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("3:5")).toBeInTheDocument();
    expect(screen.getByText("Source references")).toBeInTheDocument();
  });
});
