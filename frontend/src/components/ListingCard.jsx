import React from "react";
import { Link } from "react-router-dom";

const unitLabel = { hour: "/hr", day: "/day" };

export default function ListingCard({ listing }) {
  return (
    <Link
      to={`/listings/${listing.id}`}
      className="card card-hover"
      style={{ textDecoration: "none", color: "inherit", overflow: "hidden", display: "block" }}
    >
      <div style={{ height: 170, background: "linear-gradient(135deg, #eef2f0, #e1e9e5)", display: "flex", alignItems: "center", justifyContent: "center" }}>
        {listing.thumbnail ? (
          <img src={listing.thumbnail} alt={listing.title} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        ) : (
          <span style={{ color: "var(--color-ink-faint)", fontSize: "0.85rem" }}>No photo yet</span>
        )}
      </div>
      <div style={{ padding: "14px 16px" }}>
        {listing.category_label && <span className="pill">{listing.category_label}</span>}
        <h3 style={{ fontSize: "1.05rem", marginTop: 10, marginBottom: 4 }}>{listing.title}</h3>
        {(listing.city || listing.province) && (
          <p style={{ margin: 0, fontSize: "0.82rem", color: "var(--color-ink-faint)" }}>
            {[listing.city, listing.province].filter(Boolean).join(", ")}
          </p>
        )}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginTop: 10 }}>
          <span style={{ fontWeight: 700, color: "var(--brand-start)", fontFamily: "var(--font-display)" }}>
            ${listing.price_amount}
            <span style={{ fontWeight: 500, color: "var(--color-ink-faint)", fontFamily: "var(--font-body)", fontSize: "0.8rem" }}>
              {unitLabel[listing.price_unit] || ""}
            </span>
          </span>
          {typeof listing.distance_km === "number" && (
            <span style={{ fontSize: "0.78rem", color: "var(--color-ink-faint)" }}>{listing.distance_km.toFixed(1)} km away</span>
          )}
        </div>
      </div>
    </Link>
  );
}
