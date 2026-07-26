import React, { useState } from "react";

import { api } from "../api.js";

export default function DummyCheckoutModal({ booking, onClose, onPaid }) {
  const [form, setForm] = useState({ name_on_card: "", card_number: "", expiry: "", cvv: "" });
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  const errorText = (field) => {
    const value = errors[field];
    if (!value) return null;
    return Array.isArray(value) ? value[0] : value;
  };

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setErrors({});
    try {
      const updated = await api.dummyPay(booking.id, form);
      onPaid(updated);
    } catch (err) {
      setErrors(err.data || { general: "Payment failed. Check your card details." });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      style={{
        position: "fixed", inset: 0, background: "rgba(16,36,28,0.45)",
        display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100, padding: 20,
      }}
      onClick={onClose}
    >
      <div className="card" style={{ padding: 26, maxWidth: 400, width: "100%" }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start", marginBottom: 4 }}>
          <h3 style={{ margin: 0 }}>Checkout</h3>
          <button onClick={onClose} className="btn btn-secondary btn-sm" type="button">✕</button>
        </div>
        <p className="pill pill-accent" style={{ marginBottom: 4 }}>Demo payment — no real charge</p>
        <p style={{ color: "var(--color-ink-soft)", fontSize: "0.9rem", marginBottom: 16 }}>
          {booking.listing_title} · <strong>${booking.total_price}</strong>
        </p>

        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="name_on_card">Name on card</label>
            <input id="name_on_card" className="input" value={form.name_on_card} onChange={update("name_on_card")} required />
            {errorText("name_on_card") && <p className="error-text">{errorText("name_on_card")}</p>}
          </div>
          <div className="field">
            <label htmlFor="card_number">Card number</label>
            <input
              id="card_number" className="input" placeholder="4242 4242 4242 4242" maxLength={19}
              value={form.card_number} onChange={update("card_number")} required
            />
            {errorText("card_number") && <p className="error-text">{errorText("card_number")}</p>}
          </div>
          <div className="field" style={{ display: "flex", gap: 10 }}>
            <div style={{ flex: 1 }}>
              <label htmlFor="expiry">Expiry (MM/YY)</label>
              <input id="expiry" className="input" placeholder="12/29" value={form.expiry} onChange={update("expiry")} required />
              {errorText("expiry") && <p className="error-text">{errorText("expiry")}</p>}
            </div>
            <div style={{ flex: 1 }}>
              <label htmlFor="cvv">CVV</label>
              <input id="cvv" className="input" placeholder="123" maxLength={4} value={form.cvv} onChange={update("cvv")} required />
              {errorText("cvv") && <p className="error-text">{errorText("cvv")}</p>}
            </div>
          </div>
          {errorText("general") && <p className="error-text">{errorText("general")}</p>}
          <button className="btn btn-accent" style={{ width: "100%", marginTop: 8 }} disabled={submitting}>
            {submitting ? "Processing…" : `Pay $${booking.total_price}`}
          </button>
        </form>
      </div>
    </div>
  );
}
