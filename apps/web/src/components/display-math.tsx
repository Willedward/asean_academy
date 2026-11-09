"use client";

import { useEffect, useRef, useState } from "react";

import { focusRing } from "@/beta-kit/components/ui";
import { cn } from "@/lib/utils";

/** Display equation; only a line wider than its column becomes a keyboard scroll stop. */
export function DisplayMath({ markup }: { markup: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const [overflows, setOverflows] = useState(false);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;
    const measure = () =>
      setOverflows(element.scrollWidth > element.clientWidth + 1);
    measure();
    if (typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    return () => observer.disconnect();
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
