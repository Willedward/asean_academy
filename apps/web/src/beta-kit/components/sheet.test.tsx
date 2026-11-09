import { fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";

import { Sheet } from "./sheet";

function Host({ onClose }: { onClose: () => void }) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button onClick={() => setOpen(true)}>Open</button>
      {open ? (
        <Sheet
          titleId="sheet-title"
          onClose={() => {
            onClose();
            setOpen(false);
          }}
        >
          <h2 id="sheet-title">Report</h2>
          <button>First</button>
          <button>Last</button>
        </Sheet>
      ) : null}
    </>
  );
}

function open() {
  const opener = screen.getByRole("button", { name: "Open" });
  opener.focus();
  fireEvent.click(opener);
  return opener;
}

describe("Sheet focus", () => {
  it("moves focus in, keeps Tab inside and returns focus on Escape", () => {
    const onClose = vi.fn();
    // jsdom has no layout, so report every element as rendered.
    vi.spyOn(HTMLElement.prototype, "getClientRects").mockReturnValue([
      {},
    ] as unknown as DOMRectList);
    render(<Host onClose={onClose} />);
    const opener = open();

    const first = screen.getByRole("button", { name: "First" });
    const last = screen.getByRole("button", { name: "Last" });
    expect(first).toHaveFocus();

    last.focus();
    fireEvent.keyDown(last, { key: "Tab" });
    expect(first).toHaveFocus();
    fireEvent.keyDown(first, { key: "Tab", shiftKey: true });
    expect(last).toHaveFocus();

    fireEvent.keyDown(document.body, { key: "Escape" });
    expect(onClose).toHaveBeenCalledOnce();
    expect(opener).toHaveFocus();
    vi.restoreAllMocks();
  });
});
