import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { api } from "../api.js";
import { useAuth } from "../context/AuthContext.jsx";

export default function EditListing() {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [categories, setCategories] = useState([]);
  const [form, setForm] = useState(null);
  const [images, setImages] = useState([]);
  const [newImageFiles, setNewImageFiles] = useState([]);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    api.categories().then(setCategories).catch(() => setCategories([]));
    api.listing(id).then((listing) => {
      setForm({
        title: listing.title,
        description: listing.description,
        price_amount: listing.price_amount,
        price_unit: listing.price_unit,
        category_id: listing.category?.id ?? "",
        custom_category: listing.custom_category ?? "",
        city: listing.city ?? "",
        province: listing.province ?? "",
        address: listing.address ?? "",
        latitude: listing.latitude ?? "",
        longitude: listing.longitude ?? "",
        location_link: listing.location_link ?? "",
        owner_id: listing.owner.id,
      });
      setImages(listing.images ?? []);
    }).catch(() => setError("Could not load this listing."));
  }, [id]);

  if (error && !form) return <div className="container" style={{ padding: 60 }}><p className="error-text">{error}</p></div>;
  if (!form) return <div className="container" style={{ padding: 60 }}><p>Loading…</p></div>;

  if (!user || user.id !== form.owner_id) {
    return <div className="container" style={{ padding: 60 }}><p>You can only edit your own listings.</p></div>;
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

  const removeExistingImage = async (imageId) => {
    try {
      await api.deleteListingImage(id, imageId);
      setImages((prev) => prev.filter((img) => img.id !== imageId));
    } catch {
      setError("Could not remove that photo.");
    }
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
      delete payload.owner_id;
      await api.updateListing(id, payload);
      if (newImageFiles.length > 0) {
        await api.uploadListingImages(id, newImageFiles);
      }
      navigate(`/listings/${id}`);
    } catch (err) {
      setError("Could not save changes. Check that every required field is filled in.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteListing = async () => {
    if (!window.confirm("Delete this listing permanently? This can't be undone.")) return;
    setDeleting(true);
    try {
      await api.deleteListing(id);
      navigate("/dashboard");
    } catch {
      setError("Could not delete this listing.");
      setDeleting(false);
    }
  };

  return (
    <div className="container" style={{ maxWidth: 560, padding: "40px 24px 60px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2>Edit listing</h2>
        <button type="button" className="btn btn-danger btn-sm" onClick={handleDeleteListing} disabled={deleting}>
          {deleting ? "Deleting…" : "Delete listing"}
        </button>
      </div>

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
            <input id="custom_category" className="input" value={form.custom_category} onChange={update("custom_category")} required />
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
          <input id="address" className="input" value={form.address} onChange={update("address")} />
        </div>

        <button type="button" className="btn btn-secondary" style={{ marginBottom: 14 }} onClick={useMyLocation}>
          Use my current location
        </button>

        <div className="field" style={{ display: "flex", gap: 10 }}>
          <div style={{ flex: 1 }}>
            <label htmlFor="lat">Latitude (optional)</label>
            <input id="lat" className="input" value={form.latitude} onChange={update("latitude")} />
          </div>
          <div style={{ flex: 1 }}>
            <label htmlFor="lng">Longitude (optional)</label>
            <input id="lng" className="input" value={form.longitude} onChange={update("longitude")} />
          </div>
        </div>
        <div className="field">
          <label htmlFor="location_link">Google Maps link (optional)</label>
          <input id="location_link" type="url" className="input" value={form.location_link} onChange={update("location_link")} />
        </div>

        {images.length > 0 && (
          <div className="field">
            <label>Current photos</label>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {images.map((img) => (
                <div key={img.id} style={{ position: "relative" }}>
                  <img src={img.image} alt="" style={{ width: 72, height: 72, objectFit: "cover", borderRadius: 8 }} />
                  <button
                    type="button"
                    onClick={() => removeExistingImage(img.id)}
                    title="Remove photo"
                    style={{
                      position: "absolute", top: -6, right: -6, width: 22, height: 22, borderRadius: "50%",
                      border: "none", background: "var(--color-danger)", color: "#fff", cursor: "pointer", fontSize: "0.75rem",
                    }}
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
        <div className="field">
          <label htmlFor="images">Add more photos</label>
          <input id="images" type="file" accept="image/*" multiple onChange={(e) => setNewImageFiles(Array.from(e.target.files))} />
          {newImageFiles.length > 0 && <p className="hint-text">{newImageFiles.length} new photo(s) selected</p>}
        </div>

        {error && <p className="error-text">{error}</p>}
        <button className="btn btn-primary" style={{ width: "100%" }} disabled={submitting}>
          {submitting ? "Saving…" : "Save changes"}
        </button>
      </form>
    </div>
  );
}