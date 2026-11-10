"use client";

import { useEffect, useRef, useState } from "react";

import { focusRing } from "@/beta-kit/components/ui";
import { cn } from "@/lib/utils";

/**
 * Smallest scale used to fit a display equation into its column. At phone width a
 * scrolling equation looked complete when it was cut off mid-line ("4 × 3 = 1" for
 * "4 × 3 = 12 cm²"), so a line that is only somewhat too wide is shrunk to fit.
 * Wider lines keep the keyboard scroll stop.
 */
export const MIN_DISPLAY_MATH_SCALE = 0.7;

/** Display equation; a line wider than its column is shrunk, or scrolls when far too wide. */
export function DisplayMath({ markup }: { markup: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const [overflows, setOverflows] = useState(false);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;
    const measure = () => {
      element.style.fontSize = "";
      const natural = element.scrollWidth;
      const available = element.clientWidth;
      if (natural <= available + 1) {
        setOverflows(false);
        return;
      }
      // KaTeX sizes almost everything in em, so the line width roughly follows the
      // font size; a few fixed-width parts need a second or third pass.
      let scale = 1;
      let width = natural;
      for (let pass = 0; pass < 3 && width > available + 1; pass++) {
        scale = Math.floor(scale * (available / width) * 100) / 100;
        if (scale < MIN_DISPLAY_MATH_SCALE) break;
        element.style.fontSize = `${scale}em`;
        width = element.scrollWidth;
      }
      if (scale < MIN_DISPLAY_MATH_SCALE) element.style.fontSize = "";
      setOverflows(element.scrollWidth > element.clientWidth + 1);
    };
    measure();
    // KaTeX's web fonts can arrive after the first measurement and widen the line
    // without resizing its box, which the observer below would not notice.
    let active = true;
    void document.fonts?.ready.then(() => {
      if (active) measure();
    });
    if (typeof ResizeObserver === "undefined") {
      return () => {
        active = false;
      };
    }
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    return () => {
      active = false;
      observer.disconnect();
    };
  }, [markup]);

  return (
    <span
      ref={ref}
      {...(overflows
        ? {
            role: "group",
            tabIndex: 0,
            "aria-label": "Equation, scrolls sideways",
          }
        : {})}
      className={cn("my-3 block overflow-x-auto py-1", focusRing)}
      dangerouslySetInnerHTML={{ __html: markup }}
    />
  );
}
