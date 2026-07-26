import React, { useEffect, useState } from "react";

import { api } from "../api.js";
import ListingCard from "../components/ListingCard.jsx";

export default function Home() {
  const [listings, setListings] = useState([]);
  const [categories, setCategories] = useState([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [coords, setCoords] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api.categories()
    .then((data) => setCategories(data.results ?? data))
    .catch(() => setCategories([]));
  }, []);

  const fetchListings = async (useCoords) => {
    setLoading(true);
    setError("");
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (category) params.set("category", category);
    if (useCoords && coords) {
      params.set("lat", coords.lat);
      params.set("lng", coords.lng);
      params.set("radius_km", "50");
    }
    try {
      const data = await api.listings(`?${params.toString()}`);
      setListings(data.results ?? data);
    } catch (err) {
      setError("Could not load listings. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchListings(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const useMyLocation = () => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const next = { lat: position.coords.latitude, lng: position.coords.longitude };
        setCoords(next);
        fetchListings(true);
      },
      () => setError("Location permission denied.")
    );
  };

  return (
    <div>
      <section className="hero">
        <div className="container" style={{ position: "relative" }}>
          <h1>Borrow what you need. Skip what you don't.</h1>
          <p>Tools, cameras, camping gear and more — rented directly from people near you, by the hour or by the day.</p>
        </div>
      </section>

      <div className="container" style={{ padding: "36px 24px 60px" }}>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            fetchListings(Boolean(coords));
          }}
          className="card"
          style={{ display: "flex", gap: 10, flexWrap: "wrap", padding: 16, marginTop: -56, marginBottom: 32, position: "relative", zIndex: 2 }}
        >
          <input
            className="input"
            style={{ maxWidth: 280, flex: "1 1 200px" }}
            placeholder="Search items…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <select className="input" style={{ maxWidth: 220, flex: "1 1 160px" }} value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="">All categories</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
          <button type="submit" className="btn btn-primary">
            Search
          </button>
          <button type="button" className="btn btn-secondary" onClick={useMyLocation}>
            {coords ? "Near me ✓" : "Search near me"}
          </button>
        </form>

        {error && <p className="error-text">{error}</p>}
        {loading ? (
          <p style={{ color: "var(--color-ink-soft)" }}>Loading listings…</p>
        ) : listings.length === 0 ? (
          <p style={{ color: "var(--color-ink-soft)" }}>No listings match yet. Try widening your search.</p>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(230px, 1fr))", gap: 20 }}>
            {listings.map((listing) => (
              <ListingCard key={listing.id} listing={listing} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
