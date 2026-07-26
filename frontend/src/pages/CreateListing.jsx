import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../api.js";
import { useAuth } from "../context/AuthContext.jsx";

const EMPTY_FORM = {
  title: "", description: "", price_amount: "", price_unit: "day", category_id: "", custom_category: "",
  city: "", province: "", address: "", latitude: "", longitude: "", location_link: "",
};

export default function CreateListing() {
  const { user, switchRole } = useAuth();
  const navigate = useNavigate();
  const [categories, setCategories] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [imageFiles, setImageFiles] = useState([]);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api.categories()
    .then((data) => setCategories(data.results ?? data))
    .catch(() => setCategories([]));
  }, []);

  if (!user) {
    return (
      <div className="container" style={{ padding: 60 }}>
        <p>You need to log in to list an item.</p>
      </div>
    );
  }

  if (user.active_role !== "seller") {
    return (
      <div className="container" style={{ padding: 60, maxWidth: 460 }}>
        <div className="card" style={{ padding: 24 }}>
          <h3>Switch to selling mode first</h3>
          <p style={{ color: "var(--color-ink-soft)" }}>Your account is currently in buying mode. Switch to selling mode to list an item — you can switch back anytime.</p>
          <button className="btn btn-primary" onClick={() => switchRole("seller")}>
            Switch to selling
          </button>
        </div>
      </div>
    );
  }

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const selectedCategory = categories.find((c) => String(c.id) === String(form.category_id));
  const isOtherCategory = selectedCategory?.is_other;

  const useMyLocation = () => {
    navigator.geolocation.getCurrentPosition((position) => {
      const { latitude, longitude } = position.coords;
      setForm({
        ...form,
        latitude,
        longitude,
        location_link: `https://www.google.com/maps?q=${latitude},${longitude}`,
      });
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const payload = {
        ...form,
        price_amount: Number(form.price_amount),
        latitude: form.latitude === "" ? null : Number(form.latitude),
        longitude: form.longitude === "" ? null : Number(form.longitude),
      };
      const listing = await api.createListing(payload);
      if (imageFiles.length > 0) {
        await api.uploadListingImages(listing.id, imageFiles);
      }
      navigate(`/listings/${listing.id}`);
    } catch (err) {
      setError("Could not create listing. Check that every required field is filled in.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="container" style={{ maxWidth: 560, padding: "40px 24px 60px" }}>
      <h2>List an item</h2>
      <form onSubmit={handleSubmit} className="card" style={{ padding: 26 }}>
        <div className="field">
          <label htmlFor="title">Title</label>
          <input id="title" className="input" value={form.title} onChange={update("title")} required />
        </div>
        <div className="field">
          <label htmlFor="description">Description</label>
          <textarea id="description" className="input" rows={4} value={form.description} onChange={update("description")} required />
        </div>

        <div className="field">
          <label htmlFor="category">Category</label>
          <select id="category" className="input" value={form.category_id} onChange={update("category_id")} required>
            <option value="">Select a category</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>
        {isOtherCategory && (
          <div className="field">
            <label htmlFor="custom_category">Your category name</label>
            <input id="custom_category" className="input" placeholder="e.g. Costumes" value={form.custom_category} onChange={update("custom_category")} required />
          </div>
        )}

        <div className="field" style={{ display: "flex", gap: 10 }}>
          <div style={{ flex: 2 }}>
            <label htmlFor="price">Price</label>
            <input id="price" type="number" min="0" step="0.01" className="input" value={form.price_amount} onChange={update("price_amount")} required />
          </div>
          <div style={{ flex: 1 }}>
            <label htmlFor="unit">Per</label>
            <select id="unit" className="input" value={form.price_unit} onChange={update("price_unit")}>
              <option value="hour">Hour</option>
              <option value="day">Day</option>
            </select>
          </div>
        </div>

        <h4 style={{ marginTop: 24 }}>Location</h4>
        <div className="field" style={{ display: "flex", gap: 10 }}>
          <div style={{ flex: 1 }}>
            <label htmlFor="city">City</label>
            <input id="city" className="input" value={form.city} onChange={update("city")} required />
          </div>
          <div style={{ flex: 1 }}>
            <label htmlFor="province">Province / State</label>
            <input id="province" className="input" value={form.province} onChange={update("province")} required />
          </div>
        </div>
        <div className="field">
          <label htmlFor="address">Address (optional)</label>
          <input id="address" className="input" placeholder="Street, area, landmark…" value={form.address} onChange={update("address")} />
        </div>

        <button type="button" className="btn btn-secondary" style={{ marginBottom: 14 }} onClick={useMyLocation}>
          Use my current location
        </button>

        <div className="field" style={{ display: "flex", gap: 10 }}>
          <div style={{ flex: 1 }}>
            <label htmlFor="lat">Latitude (optional)</label>
            <input id="lat" className="input" value={form.latitude} onChange={update("latitude")} placeholder="Auto-filled or manual" />
          </div>
          <div style={{ flex: 1 }}>
            <label htmlFor="lng">Longitude (optional)</label>
            <input id="lng" className="input" value={form.longitude} onChange={update("longitude")} placeholder="Auto-filled or manual" />
          </div>
        </div>
        <div className="field">
          <label htmlFor="location_link">Google Maps link (optional)</label>
          <input id="location_link" type="url" className="input" placeholder="https://maps.google.com/…" value={form.location_link} onChange={update("location_link")} />
          <p className="hint-text">Auto-filled when you use your current location — or paste your own link.</p>
        </div>

        <div className="field">
          <label htmlFor="images">Photos</label>
          <input id="images" type="file" accept="image/*" multiple onChange={(e) => setImageFiles(Array.from(e.target.files))} />
          {imageFiles.length > 0 && <p className="hint-text">{imageFiles.length} photo(s) selected</p>}
        </div>

        {error && <p className="error-text">{error}</p>}
        <button className="btn btn-primary" style={{ width: "100%" }} disabled={submitting}>
          {submitting ? "Publishing…" : "Publish listing"}
        </button>
      </form>
    </div>
  );
}
