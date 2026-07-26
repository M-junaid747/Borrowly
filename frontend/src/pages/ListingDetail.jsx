import React, { useEffect, useMemo, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";

import { api } from "../api.js";
import ChatThread from "../components/ChatThread.jsx";
import { useAuth } from "../context/AuthContext.jsx";

const unitLabel = { hour: "hour", day: "day" };

function mapsLinkFor(listing) {
  if (listing.location_link) return listing.location_link;
  if (listing.latitude != null && listing.longitude != null) {
    return `https://www.google.com/maps?q=${listing.latitude},${listing.longitude}`;
  }
  return null;
}

export default function ListingDetail() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const { user, switchRole } = useAuth();
  const [listing, setListing] = useState(null);
  const [activeImage, setActiveImage] = useState(0);
  const [startDatetime, setStartDatetime] = useState("");
  const [endDatetime, setEndDatetime] = useState("");
  const [bookingMessage, setBookingMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api.listing(id).then(setListing).catch(() => setError("Listing not found."));
  }, [id]);

  const estimatedPrice = useMemo(() => {
    if (!listing || !startDatetime || !endDatetime) return null;
    const start = new Date(startDatetime);
    const end = new Date(endDatetime);
    const diffMs = end - start;
    if (diffMs <= 0) return null;
    const unitMs = listing.price_unit === "hour" ? 3600_000 : 86_400_000;
    const units = Math.max(Math.ceil(diffMs / unitMs), 1);
    return { units, total: (units * Number(listing.price_amount)).toFixed(2) };
  }, [listing, startDatetime, endDatetime]);

  if (error) return <div className="container" style={{ padding: 60 }}><p className="error-text">{error}</p></div>;
  if (!listing) return <div className="container" style={{ padding: 60 }}><p>Loading…</p></div>;

  const isOwnListing = user && listing.owner.id === user.id;
  const inBuyingMode = user && user.active_role === "buyer";
  // Owners reach a specific conversation via a link from their dashboard
  // inbox (?with=<renterId>); everyone else chats with the owner directly.
  const chatCounterpartId = isOwnListing ? Number(searchParams.get("with")) || null : listing.owner.id;
  const canChat = user && (isOwnListing ? Boolean(chatCounterpartId) : inBuyingMode);

  const maps = mapsLinkFor(listing);
  const locationLine = [listing.city, listing.province].filter(Boolean).join(", ");

  const submitBooking = async (e) => {
    e.preventDefault();
    setBookingMessage("");
    setError("");
    try {
      await api.createBooking({ listing_id: listing.id, start_datetime: startDatetime, end_datetime: endDatetime });
      setBookingMessage("Booking requested! The owner will confirm it, then you can pay from your dashboard.");
    } catch (err) {
      setError("Could not create booking. Check your dates/times.");
    }
  };

  return (
    <div className="container" style={{ padding: "40px 24px 60px", display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 32 }}>
      <div>
        <div style={{ height: 340, borderRadius: 16, overflow: "hidden", background: "linear-gradient(135deg,#eef2f0,#e1e9e5)", marginBottom: 10 }}>
          {listing.images?.length > 0 ? (
            <img src={listing.images[activeImage].image} alt={listing.title} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          ) : (
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "var(--color-ink-faint)" }}>
              No photo yet
            </div>
          )}
        </div>
        {listing.images?.length > 1 && (
          <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
            {listing.images.map((img, idx) => (
              <button
                key={img.id}
                onClick={() => setActiveImage(idx)}
                style={{
                  width: 64, height: 64, borderRadius: 10, overflow: "hidden", padding: 0, cursor: "pointer",
                  border: idx === activeImage ? "2px solid var(--brand-mid)" : "1.5px solid var(--color-border)",
                }}
              >
                <img src={img.image} alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
              </button>
            ))}
          </div>
        )}

        {listing.category_label && <span className="pill" style={{ marginTop: 4 }}>{listing.category_label}</span>}
        <h1 style={{ marginTop: 10 }}>{listing.title}</h1>
        <p style={{ color: "var(--color-ink-soft)", lineHeight: 1.6 }}>{listing.description}</p>
        <p style={{ fontWeight: 700, fontSize: "1.25rem", color: "var(--brand-start)", fontFamily: "var(--font-display)" }}>
          ${listing.price_amount} <span style={{ fontSize: "0.9rem", fontWeight: 500, color: "var(--color-ink-faint)", fontFamily: "var(--font-body)" }}>/ {unitLabel[listing.price_unit]}</span>
        </p>
        <p style={{ color: "var(--color-ink-soft)", fontSize: "0.9rem" }}>
          Owner: {listing.owner.username} · ⭐ {listing.owner.average_rating || "No ratings yet"}
        </p>

        <div className="card" style={{ padding: 16, marginTop: 16 }}>
          <h4 style={{ marginBottom: 6 }}>Location</h4>
          <p style={{ margin: 0, color: "var(--color-ink-soft)" }}>{locationLine || "Not specified"}</p>
          {listing.address && <p style={{ margin: "4px 0 0", color: "var(--color-ink-faint)", fontSize: "0.9rem" }}>{listing.address}</p>}
          {maps && (
            <a href={maps} target="_blank" rel="noreferrer" className="btn btn-secondary btn-sm" style={{ marginTop: 10, textDecoration: "none" }}>
              Open in Google Maps
            </a>
          )}
        </div>

        {canChat && (
          <>
            <h3 style={{ marginTop: 28 }}>{isOwnListing ? "Conversation" : "Chat with the owner"}</h3>
            <ChatThread listingId={listing.id} otherUserId={chatCounterpartId} />
          </>
        )}
      </div>

      <div>
        {isOwnListing ? (
          <div className="card" style={{ padding: 20 }}>
            <p>This is your listing. Reply to renters from your Dashboard inbox, or manage it there.</p>
          </div>
        ) : !user ? (
          <div className="card" style={{ padding: 20 }}>
            <h3>Request to rent</h3>
            <p style={{ color: "var(--color-ink-soft)" }}>Log in to request a booking.</p>
          </div>
        ) : !inBuyingMode ? (
          <div className="card" style={{ padding: 20 }}>
            <h3>Browsing in selling mode</h3>
            <p style={{ color: "var(--color-ink-soft)" }}>
              You're viewing this in selling mode, which is preview-only. Switch to buying mode to request a booking or message the owner.
            </p>
            <button className="btn btn-primary" onClick={() => switchRole("buyer")}>Switch to buying</button>
          </div>
        ) : (
          <div className="card" style={{ padding: 20 }}>
            <h3>Request to rent</h3>
            <form onSubmit={submitBooking}>
              <div className="field">
                <label htmlFor="start">Start</label>
                <input id="start" type="datetime-local" className="input" value={startDatetime} onChange={(e) => setStartDatetime(e.target.value)} required />
              </div>
              <div className="field">
                <label htmlFor="end">End</label>
                <input id="end" type="datetime-local" className="input" value={endDatetime} onChange={(e) => setEndDatetime(e.target.value)} required />
              </div>
              {estimatedPrice && (
                <p className="pill pill-accent" style={{ marginBottom: 14 }}>
                  {estimatedPrice.units} {unitLabel[listing.price_unit]}{estimatedPrice.units > 1 ? "s" : ""} · Est. ${estimatedPrice.total}
                </p>
              )}
              {error && <p className="error-text">{error}</p>}
              {bookingMessage && <p style={{ color: "var(--brand-start)", fontSize: "0.9rem" }}>{bookingMessage}</p>}
              <button className="btn btn-primary" style={{ width: "100%" }}>Request booking</button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}
