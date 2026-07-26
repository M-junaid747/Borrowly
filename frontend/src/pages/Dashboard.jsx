import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api.js";
import DummyCheckoutModal from "../components/DummyCheckoutModal.jsx";
import MessageThreadList from "../components/MessageThreadList.jsx";
import RoleSwitch from "../components/RoleSwitch.jsx";
import { useAuth } from "../context/AuthContext.jsx";

function formatWhen(iso) {
  return new Date(iso).toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
}

function BookingRow({ booking, isSellerSide, onAct, onPay }) {
  return (
    <div className="card" style={{ padding: 16, display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 10 }}>
      <div>
        <strong>{booking.listing_title}</strong>
        {isSellerSide && <span style={{ color: "var(--color-ink-faint)", fontSize: "0.85rem" }}> · requested by {booking.renter_username}</span>}
        <p style={{ margin: "4px 0", color: "var(--color-ink-soft)", fontSize: "0.9rem" }}>
          {formatWhen(booking.start_datetime)} → {formatWhen(booking.end_datetime)} · ${booking.total_price} ·{" "}
          <span className="pill">{booking.status}</span>
        </p>
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        {isSellerSide && booking.status === "requested" && (
          <>
            <button className="btn btn-primary btn-sm" onClick={() => onAct(booking.id, "confirmed")}>Confirm</button>
            <button className="btn btn-danger btn-sm" onClick={() => onAct(booking.id, "cancelled")}>Decline</button>
          </>
        )}
        {!isSellerSide && booking.status === "confirmed" && (
          <button className="btn btn-accent btn-sm" onClick={() => onPay(booking)}>Pay now</button>
        )}
      </div>
    </div>
  );
}

function BuyerDashboard() {
  const [bookings, setBookings] = useState([]);
  const [threads, setThreads] = useState([]);
  const [payingBooking, setPayingBooking] = useState(null);
  const [error, setError] = useState("");

  const load = () => {
    api.bookings().then((data) => setBookings((data.results ?? data).filter((b) => b.viewer_role === "buyer"))).catch(() => setError("Could not load bookings."));
    api.inbox().then((data) => setThreads(data.filter((t) => t.role === "buyer"))).catch(() => {});
  };
  useEffect(load, []);

  return (
    <div>
      <h3>My bookings</h3>
      {error && <p className="error-text">{error}</p>}
      {bookings.length === 0 && <p style={{ color: "var(--color-ink-soft)" }}>No bookings yet — go find something to rent.</p>}
      <div style={{ display: "flex", flexDirection: "column", gap: 12, marginBottom: 32 }}>
        {bookings.map((b) => (
          <BookingRow key={b.id} booking={b} isSellerSide={false} onAct={() => {}} onPay={setPayingBooking} />
        ))}
      </div>

      <h3>My messages</h3>
      <MessageThreadList threads={threads} viewerIsOwnerSide={false} />

      {payingBooking && (
        <DummyCheckoutModal
          booking={payingBooking}
          onClose={() => setPayingBooking(null)}
          onPaid={() => {
            setPayingBooking(null);
            load();
          }}
        />
      )}
    </div>
  );
}

function SellerDashboard() {
  const [listings, setListings] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [threads, setThreads] = useState([]);
  const [error, setError] = useState("");

  const load = () => {
    api.myListings().then((data) => setListings(data.results ?? data)).catch(() => setError("Could not load your listings."));
    api.bookings().then((data) => setBookings((data.results ?? data).filter((b) => b.viewer_role === "seller"))).catch(() => setError("Could not load bookings."));
    api.inbox().then((data) => setThreads(data.filter((t) => t.role === "seller"))).catch(() => {});
  };
  useEffect(load, []);

  const act = async (id, status) => {
    try {
      await api.updateBookingStatus(id, status);
      load();
    } catch {
      setError("Could not update that booking.");
    }
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h3>My listings</h3>
        <Link to="/listings/new" className="btn btn-primary btn-sm" style={{ textDecoration: "none" }}>+ New listing</Link>
      </div>
      {error && <p className="error-text">{error}</p>}
      {listings.length === 0 ? (
        <p style={{ color: "var(--color-ink-soft)" }}>You haven't listed anything yet.</p>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 16, marginBottom: 32 }}>
          {listings.map((l) => (
            <Link key={l.id} to={`/listings/${l.id}`} className="card card-hover" style={{ padding: 14, textDecoration: "none", color: "inherit" }}>
              <strong style={{ fontSize: "0.95rem" }}>{l.title}</strong>
              <p style={{ margin: "4px 0 0", color: "var(--brand-start)", fontWeight: 700 }}>${l.price_amount}/{l.price_unit}</p>
            </Link>
          ))}
        </div>
      )}

      <h3>Incoming booking requests</h3>
      {bookings.length === 0 ? (
        <p style={{ color: "var(--color-ink-soft)" }}>No requests yet.</p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12, marginBottom: 32 }}>
          {bookings.map((b) => (
            <BookingRow key={b.id} booking={b} isSellerSide onAct={act} onPay={() => {}} />
          ))}
        </div>
      )}

      <h3>Messages from renters</h3>
      <MessageThreadList threads={threads} viewerIsOwnerSide />
    </div>
  );
}

export default function Dashboard() {
  const { user, switchRole } = useAuth();

  if (!user) {
    return <div className="container" style={{ padding: 60 }}><p>Log in to see your dashboard.</p></div>;
  }

  return (
    <div className="container" style={{ padding: "40px 24px 60px", maxWidth: 760 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24, flexWrap: "wrap", gap: 12 }}>
        <h2 style={{ margin: 0 }}>Dashboard</h2>
        <RoleSwitch activeRole={user.active_role} onSwitch={switchRole} />
      </div>
      {user.active_role === "seller" ? <SellerDashboard /> : <BuyerDashboard />}
    </div>
  );
}
