"use client";

import { Bell, X } from "lucide-react";
import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";

import { STATUS_LABELS, type RequestStatus } from "@/lib/types";

import { useUser } from "./session";

export interface RequestEvent {
  kind: "created" | "status_changed" | "assignments_changed";
  actor_id: number;
  request_id: number;
  client_id: number;
  status: RequestStatus;
  task_name: string;
}

type Listener = (event: RequestEvent) => void;

interface LiveContextValue {
  connected: boolean;
  subscribe: (listener: Listener) => () => void;
}

const LiveContext = createContext<LiveContextValue | null>(null);

interface Toast {
  id: number;
  text: string;
}

/**
 * One EventSource per tab (`/api/events`, proxied to the API's SSE endpoint). Pages
 * subscribe to refetch what they show; changes made by someone else also pop a toast.
 * EventSource reconnects by itself using the server's `retry:` hint.
 */
export function LiveProvider({ children }: { children: React.ReactNode }) {
  const user = useUser();
  const listeners = useRef(new Set<Listener>());
  const [connected, setConnected] = useState(false);
  const [toasts, setToasts] = useState<Toast[]>([]);

  const dismiss = useCallback((id: number) => setToasts((t) => t.filter((x) => x.id !== id)), []);

  useEffect(() => {
    const source = new EventSource("/api/events");
    source.onopen = () => setConnected(true);
    source.onerror = () => setConnected(false);
    source.onmessage = (msg) => {
      const event = JSON.parse(msg.data) as RequestEvent;
      listeners.current.forEach((l) => l(event));

      const text =
        event.kind === "created"
          ? `New request #${event.request_id} · ${event.task_name}`
          : event.kind === "status_changed"
            ? `Request #${event.request_id} is now ${STATUS_LABELS[event.status]}`
            : null;
      if (text && event.actor_id !== user.id) {
        const id = Date.now() + Math.random();
        setToasts((t) => [...t.slice(-3), { id, text }]);
        setTimeout(() => dismiss(id), 5000);
      }
    };
    return () => source.close();
  }, [user.id, dismiss]);

  const subscribe = useCallback((listener: Listener) => {
    listeners.current.add(listener);
    return () => {
      listeners.current.delete(listener);
    };
  }, []);

  return (
    <LiveContext.Provider value={{ connected, subscribe }}>
      {children}
      <div
        aria-live="polite"
        className="pointer-events-none fixed right-6 bottom-6 z-50 flex w-80 flex-col gap-2"
      >
        {toasts.map((t) => (
          <div
            key={t.id}
            className="pointer-events-auto flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-4 text-sm shadow-lg shadow-slate-900/10"
          >
            <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-brand-50 text-brand-600">
              <Bell className="h-4 w-4" />
            </span>
            <p className="flex-1 pt-1.5 font-medium text-slate-800">{t.text}</p>
            <button
              aria-label="Dismiss"
              onClick={() => dismiss(t.id)}
              className="rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
      </div>
    </LiveContext.Provider>
  );
}

/** Call `onEvent` for every live event (optionally only those of one request). */
export function useLiveEvents(onEvent: Listener, requestId?: number) {
  const ctx = useContext(LiveContext);
  const handler = useRef(onEvent);
  useEffect(() => {
    handler.current = onEvent;
  });
  useEffect(() => {
    if (!ctx) return;
    return ctx.subscribe((e) => {
      if (requestId === undefined || e.request_id === requestId) handler.current(e);
    });
  }, [ctx, requestId]);
}

export function LiveIndicator() {
  const connected = useContext(LiveContext)?.connected ?? false;
  return (
    <span
      className="inline-flex items-center gap-2 rounded-full bg-white px-3 py-1 text-xs font-medium text-slate-600 ring-1 ring-slate-200"
      title={connected ? "Receiving live updates" : "Reconnecting…"}
    >
      <span className="relative flex h-2 w-2">
        {connected && (
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
        )}
        <span
          className={`relative inline-flex h-2 w-2 rounded-full ${connected ? "bg-emerald-500" : "bg-slate-300"}`}
        />
      </span>
      {connected ? "Live" : "Offline"}
    </span>
  );
}
