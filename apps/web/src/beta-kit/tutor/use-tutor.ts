"use client";

/**
 * Client state for one tutor conversation, pinned to one practice question.
 * Follows docs/plan/AI_TUTOR_FRONTEND_BACKEND_HANDOFF.md:
 * - the server owns the conversation; the browser only remembers the session id
 *   (sessionStorage) so a refresh can restore it with GET;
 * - one send at a time, and a failed send is only retried when the learner taps
 *   "Try again" (no idempotency key on the endpoint);
 * - mode, answer lock and quota always come from the server;
 * - mount a fresh hook per question (TutorDock keys it), and the old session is
 *   closed when the learner leaves the question.
 */
import { useCallback, useEffect, useMemo, useReducer, useRef } from "react";

import {
  closeTutorSession,
  createTutorSession,
  getTutorSession,
  sendTutorMessage,
  type TutorAnswerLockState,
  type TutorQuotaResponse,
  type TutorReplyResponse,
  type TutorSessionResponse,
} from "@/lib/api/tutor";

import { errorAction, quotaNotice, toChatMessage } from "./format";
import type { TutorChatMessage, TutorNotice } from "./types";

export interface TutorIdentity {
  /** API: PracticeSessionResponse.session_id */
  practiceSessionId: string;
  /** API: PublicQuestionResponse.stable_key */
  questionKey: string;
  /** API: PublicQuestionResponse.revision */
  questionRevision: number;
}

export interface TutorState {
  availability: "unknown" | "disabled" | "available";
  session: "absent" | "creating" | "active" | "closed";
  send: "idle" | "sending" | "failed";
  sessionId: string | null;
  messages: TutorChatMessage[];
  lock: TutorAnswerLockState | null;
  quota: TutorQuotaResponse | null;
  suggestions: string[];
  nextStep: string | null;
  notice: TutorNotice | null;
  /** The learner's text from the last failed send, for an explicit retry. */
  failedText: string | null;
  /** The server said the learner's plan does not include the tutor. */
  planRequired: boolean;
}

export const initialTutorState: TutorState = {
  availability: "unknown",
  session: "absent",
  send: "idle",
  sessionId: null,
  messages: [],
  lock: null,
  quota: null,
  suggestions: [],
  nextStep: null,
  notice: null,
  failedText: null,
  planRequired: false,
};

type Action =
  | { type: "creating" }
  | { type: "loaded"; session: TutorSessionResponse }
  | { type: "forget"; notice: TutorNotice | null }
  | { type: "send_start"; message: TutorChatMessage }
  | { type: "send_ok"; localId: string; reply: TutorReplyResponse }
  | { type: "send_failed"; localId: string; text: string; notice: TutorNotice | null }
  | { type: "drop_message"; id: string }
  | { type: "notice"; notice: TutorNotice | null }
  | { type: "disable" }
  | { type: "plan_required" };

export function tutorReducer(state: TutorState, action: Action): TutorState {
  switch (action.type) {
    case "creating":
      return { ...state, session: "creating" };
    case "loaded": {
      const closed = action.session.status === "closed";
      return {
        ...state,
        availability: "available",
        session: closed ? "closed" : "active",
        sessionId: action.session.session_id,
        // Keep any learner message that is still sending; the server copy arrives with the reply.
        messages: [
          ...action.session.messages.map(toChatMessage),
          ...state.messages.filter((message) => message.delivery === "sending"),
        ],
        lock: action.session.answer_lock_state,
        notice: closed ? { kind: "closed" } : state.notice,
      };
    }
    case "forget":
      return { ...state, session: "absent", sessionId: null, notice: action.notice };
    case "send_start":
      return {
        ...state,
        send: "sending",
        failedText: null,
        notice: state.notice?.kind === "quota_low" ? state.notice : null,
        nextStep: null,
        messages: [...state.messages, action.message],
      };
    case "send_ok": {
      const { reply } = action;
      return {
        ...state,
        availability: "available",
        send: "idle",
        messages: [
          ...state.messages.map((message) =>
            message.id === action.localId ? { ...message, delivery: "sent" as const } : message,
          ),
          toChatMessage(reply.message),
        ],
        suggestions: reply.suggested_replies.slice(0, 4),
        nextStep: reply.recommended_next_action ?? null,
        lock: reply.answer_lock_state,
        quota: reply.quota,
        notice: quotaNotice(reply.quota),
      };
    }
    case "send_failed":
      return {
        ...state,
        send: "failed",
        failedText: action.text,
        notice: action.notice,
        messages: state.messages.map((message) =>
          message.id === action.localId ? { ...message, delivery: "failed" as const } : message,
        ),
      };
    case "drop_message":
      return { ...state, messages: state.messages.filter((message) => message.id !== action.id) };
    case "notice":
      return { ...state, session: state.session === "creating" ? "absent" : state.session, notice: action.notice };
    case "disable":
      return { ...state, availability: "disabled", session: state.session === "creating" ? "absent" : state.session, send: "idle" };
    case "plan_required":
      return { ...state, planRequired: true, session: state.session === "creating" ? "absent" : state.session, send: "idle" };
  }
}

function storageKey(identity: TutorIdentity) {
  return `ns-tutor:${identity.practiceSessionId}:${identity.questionKey}:${identity.questionRevision}`;
}

function readStored(key: string): string | null {
  try {
    return window.sessionStorage.getItem(key);
  } catch {
    return null;
  }
}

function writeStored(key: string, value: string | null) {
  try {
    if (value) window.sessionStorage.setItem(key, value);
    else window.sessionStorage.removeItem(key);
  } catch {
    /* private mode or blocked storage: the chat just will not survive a refresh */
  }
}

let localCounter = 0;
function localId() {
  localCounter += 1;
  return `local-${Date.now()}-${localCounter}`;
}

export interface UseTutorOptions extends TutorIdentity {
  accessToken?: string;
  /** 401: send the learner to the existing sign-in flow. */
  onSignIn?: () => void;
}

export function useTutor({ practiceSessionId, questionKey, questionRevision, accessToken, onSignIn }: UseTutorOptions) {
  const [state, dispatch] = useReducer(tutorReducer, initialTutorState);
  const key = useMemo(
    () => storageKey({ practiceSessionId, questionKey, questionRevision }),
    [practiceSessionId, questionKey, questionRevision],
  );
  const sessionIdRef = useRef<string | null>(null);
  const creatingRef = useRef<Promise<string | null> | null>(null);
  const sendingRef = useRef(false);
  const signInRef = useRef(onSignIn);
  useEffect(() => {
    signInRef.current = onSignIn;
  }, [onSignIn]);

  /** Applies a failed request. Returns the notice to show, if any. */
  const handleError = useCallback(
    (error: unknown): TutorNotice | null => {
      const action = errorAction(error);
      switch (action.type) {
        case "sign_in":
          signInRef.current?.();
          return null;
        case "disable":
          dispatch({ type: "disable" });
          return null;
        case "plan_required":
          dispatch({ type: "plan_required" });
          return null;
        case "forget_session":
          sessionIdRef.current = null;
          writeStored(key, null);
          dispatch({ type: "forget", notice: action.notice });
          return action.notice;
        case "notice":
          return action.notice;
      }
    },
    [key],
  );

  /** Restores the stored session or creates one. Safe to call repeatedly. */
  const ensureSession = useCallback((): Promise<string | null> => {
    if (sessionIdRef.current) return Promise.resolve(sessionIdRef.current);
    if (creatingRef.current) return creatingRef.current;
    dispatch({ type: "creating" });
    const work = (async () => {
      const stored = readStored(key);
      if (stored) {
        try {
          const restored = await getTutorSession(stored, accessToken);
          if (restored.status === "active" && restored.question_key === questionKey && restored.question_revision === questionRevision) {
            sessionIdRef.current = restored.session_id;
            dispatch({ type: "loaded", session: restored });
            return restored.session_id;
          }
        } catch {
          /* stale or foreign id: start a new session below */
        }
        writeStored(key, null);
      }
      try {
        const created = await createTutorSession(
          { practice_session_id: practiceSessionId, question_key: questionKey, question_revision: questionRevision },
          accessToken,
        );
        sessionIdRef.current = created.session_id;
        writeStored(key, created.session_id);
        dispatch({ type: "loaded", session: created });
        return created.session_id;
      } catch (error) {
        const notice = handleError(error);
        if (notice) dispatch({ type: "notice", notice });
        return null;
      }
    })();
    creatingRef.current = work;
    void work.finally(() => {
      creatingRef.current = null;
    });
    return work;
  }, [accessToken, handleError, key, practiceSessionId, questionKey, questionRevision]);

  /** Sends what the learner typed or tapped. Ignored while another send is in flight. */
  const send = useCallback(
    async (raw: string) => {
      const text = raw.trim();
      if (!text || sendingRef.current) return false;
      sendingRef.current = true;
      const id = localId();
      dispatch({
        type: "send_start",
        message: { id, role: "student", blocks: [{ type: "text", content: text }], delivery: "sending" },
      });
      try {
        const sessionId = await ensureSession();
        if (!sessionId) {
          dispatch({ type: "send_failed", localId: id, text, notice: null });
          return false;
        }
        const reply = await sendTutorMessage(sessionId, text, accessToken);
        dispatch({ type: "send_ok", localId: id, reply });
        return true;
      } catch (error) {
        const notice = handleError(error);
        dispatch({ type: "send_failed", localId: id, text, notice });
        return false;
      } finally {
        sendingRef.current = false;
      }
    },
    [accessToken, ensureSession, handleError],
  );

  /** "Try again" after a failed send: removes the failed bubble and sends the same text once. */
  const retry = useCallback(async () => {
    const failed = [...state.messages].reverse().find((message) => message.delivery === "failed");
    const text = state.failedText;
    if (!text) return false;
    if (failed) dispatch({ type: "drop_message", id: failed.id });
    return send(text);
  }, [send, state.failedText, state.messages]);

  /** The learner ends the chat on purpose. */
  const endSession = useCallback(async () => {
    const id = sessionIdRef.current;
    sessionIdRef.current = null;
    writeStored(key, null);
    dispatch({ type: "forget", notice: null });
    if (id) await closeTutorSession(id, accessToken).catch(() => undefined);
  }, [accessToken, key]);

  // Leaving the question (unmount or a new question key) closes the server session.
  // A page refresh does not run this, so the stored id restores the chat.
  useEffect(() => {
    return () => {
      const id = sessionIdRef.current;
      if (!id) return;
      sessionIdRef.current = null;
      writeStored(key, null);
      void closeTutorSession(id, accessToken).catch(() => undefined);
    };
  }, [accessToken, key]);

  return { state, ensureSession, send, retry, endSession };
}
