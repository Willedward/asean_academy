"use client";

import { useRef, type ReactNode } from "react";

import { useDialogFocus } from "./use-focus";

/** Bottom sheet dialog used on phones (centred card on desktop). */
export function Sheet({
  titleId,
  onClose,
  children,
}: {
  titleId: string;
  onClose?: () => void;
  children: ReactNode;
}) {
  const dialogRef = useRef<HTMLDivElement>(null);
  useDialogFocus(dialogRef, { modal: true, onEscape: onClose, focusFirst: true });
  return (
    <div className="fixed inset-0 z-40 flex items-end justify-center bg-ns-dark/45 lg:items-center">
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        className="flex w-full max-w-[520px] flex-col gap-4 rounded-t-3xl bg-ns-raised px-5 pt-3 pb-7 shadow-ns-lg lg:rounded-3xl lg:pt-6"
      >
        <span className="h-1 w-10 self-center rounded-full bg-ns-line lg:hidden" />
        {children}
      </div>
    </div>
  );
}
