import React from "react";
import { Link } from "react-router-dom";

function formatWhen(iso) {
  return new Date(iso).toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
}

export default function MessageThreadList({ threads, viewerIsOwnerSide }) {
  if (threads.length === 0) {
    return <p style={{ color: "var(--color-ink-soft)" }}>No conversations yet.</p>;
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {threads.map((t) => {
        const to = viewerIsOwnerSide
          ? `/listings/${t.listing_id}?with=${t.other_user_id}`
          : `/listings/${t.listing_id}`;
        return (
          <Link
            key={`${t.listing_id}-${t.other_user_id}`}
            to={to}
            className="card card-hover"
            style={{ padding: 14, textDecoration: "none", color: "inherit", display: "flex", justifyContent: "space-between", gap: 12 }}
          >
            <div style={{ minWidth: 0 }}>
              <strong style={{ fontSize: "0.92rem" }}>{t.listing_title}</strong>
              <span style={{ color: "var(--color-ink-faint)", fontSize: "0.82rem" }}> · {t.other_username}</span>
              <p style={{ margin: "4px 0 0", color: "var(--color-ink-soft)", fontSize: "0.85rem", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                {t.last_message}
              </p>
            </div>
            <div style={{ textAlign: "right", flexShrink: 0 }}>
              <div style={{ color: "var(--color-ink-faint)", fontSize: "0.75rem" }}>{formatWhen(t.last_message_at)}</div>
              {t.unread_count > 0 && (
                <span
                  style={{
                    display: "inline-block", marginTop: 4, background: "var(--color-accent)", color: "#fff",
                    borderRadius: 999, fontSize: "0.72rem", fontWeight: 700, padding: "1px 8px",
                  }}
                >
                  {t.unread_count}
                </span>
              )}
            </div>
          </Link>
        );
      })}
    </div>
  );
}
