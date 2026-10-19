import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ReconnectPage } from "./error";

describe("ReconnectPage", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
  });

  it("reloads the document when the automatic retry expires", () => {
    const reloadPage = vi.fn();

    render(
      <ReconnectPage
        error={Object.assign(new Error("unavailable"), { digest: "wake-1" })}
        reloadPage={reloadPage}
      />,
    );

    act(() => vi.advanceTimersByTime(10_000));

    expect(reloadPage).toHaveBeenCalledOnce();
  });

  it("reloads the document when Try now is selected", () => {
    const reloadPage = vi.fn();

    render(
      <ReconnectPage
        error={Object.assign(new Error("unavailable"), { digest: "wake-2" })}
        reloadPage={reloadPage}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Try now" }));

    expect(reloadPage).toHaveBeenCalledOnce();
  });
});
