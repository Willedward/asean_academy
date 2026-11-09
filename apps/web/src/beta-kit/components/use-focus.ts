"use client";

import { useEffect, useRef } from "react";

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

const openModals: HTMLElement[] = [];

/** Focus `target` when `value` changes to a new truthy value. */
export function useFocusOnChange(
  value: unknown,
  target: () => HTMLElement | null,
  { skipFirst = false }: { skipFirst?: boolean } = {},
) {
  const previous = useRef<unknown>(undefined);
  const targetRef = useRef(target);
  useEffect(() => {
    targetRef.current = target;
  });
  useEffect(() => {
    const before = previous.current;
    previous.current = value;
    if (!value || value === before || (skipFirst && !before)) return;
    targetRef.current()?.focus();
  }, [value, skipFirst]);
}

/**
 * Returns focus to the opener when a dialog closes. While `modal` is true, Tab stays
 * inside the dialog and Escape closes it wherever focus is.
 */
export function useDialogFocus(
  dialogRef: { current: HTMLElement | null },
  {
    modal,
    onEscape,
    focusFirst = false,
  }: { modal: boolean; onEscape?: () => void; focusFirst?: boolean },
) {
  const escapeRef = useRef(onEscape);
  useEffect(() => {
    escapeRef.current = onEscape;
  });

  useEffect(() => {
    const opener = document.activeElement as HTMLElement | null;
    return () => {
      if (opener?.isConnected) opener.focus({ preventScroll: true });
    };
  }, []);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog || !focusFirst) return;
    (focusableIn(dialog)[0] ?? dialog).focus();
  }, [dialogRef, focusFirst]);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!modal || !dialog) return;
    openModals.push(dialog);
    const onKeyDown = (event: KeyboardEvent) => {
      if (openModals.at(-1) !== dialog) return;
      if (event.key === "Escape") {
        escapeRef.current?.();
        return;
      }
      if (event.key !== "Tab") return;
      const items = focusableIn(dialog);
      const first = items[0];
      const last = items.at(-1);
      const active = document.activeElement;
      if (!first || !last) {
        event.preventDefault();
        dialog.focus();
      } else if (!dialog.contains(active)) {
        event.preventDefault();
        first.focus();
      } else if (event.shiftKey && (active === first || active === dialog)) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && active === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      openModals.splice(openModals.indexOf(dialog), 1);
    };
  }, [dialogRef, modal]);
}

function focusableIn(dialog: HTMLElement) {
  return [...dialog.querySelectorAll<HTMLElement>(FOCUSABLE)].filter(
    (element) => element.getClientRects().length > 0,
  );
}
