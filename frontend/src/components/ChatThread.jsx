import React, { useEffect, useRef, useState } from "react";

import { api } from "../api.js";
import { useAuth } from "../context/AuthContext.jsx";

const POLL_INTERVAL_MS = 4000;

export default function ChatThread({ listingId, otherUserId }) {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const data = await api.conversation(listingId, otherUserId);
        if (!cancelled) setMessages(data.results ?? data);
      } catch {
        // Silently retry on next poll; a transient network error shouldn't break the thread.
      }
    };

    load();
    const interval = setInterval(load, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [listingId, otherUserId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  const send = async (e) => {
    e.preventDefault();
    if (!draft.trim()) return;
    const body = draft;
    setDraft("");
    const message = await api.sendMessage(listingId, otherUserId, body);
    setMessages((prev) => [...prev, message]);
  };

  return (
    <div className="card" style={{ padding: 16, display: "flex", flexDirection: "column", height: 360 }}>
      <div style={{ flex: 1, overflowY: "auto", marginBottom: 10 }}>
        {messages.length === 0 && <p style={{ color: "var(--color-ink-soft)", fontSize: "0.9rem" }}>Say hello to start arranging pickup.</p>}
        {messages.map((m) => {
          const mine = m.sender === user.id;
          return (
            <div key={m.id} style={{ display: "flex", justifyContent: mine ? "flex-end" : "flex-start", marginBottom: 8 }}>
              <div
                style={{
                  maxWidth: "75%",
                  padding: "8px 12px",
                  borderRadius: 12,
                  background: mine ? "var(--gradient-brand)" : "var(--color-bg)",
                  color: mine ? "#fff" : "var(--color-ink)",
                  fontSize: "0.9rem",
                }}
              >
                {m.body}
              </div>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>
      <form onSubmit={send} style={{ display: "flex", gap: 8 }}>
        <input className="input" placeholder="Message the owner…" value={draft} onChange={(e) => setDraft(e.target.value)} />
        <button className="btn btn-primary">Send</button>
      </form>
    </div>
  );
}
