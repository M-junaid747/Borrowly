import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { api } from "../api.js";
import CategorySidebar from "../components/CategorySidebar.jsx";
import ListingCard from "../components/ListingCard.jsx";

const EMPTY_FILTERS = { category: "", minPrice: "", maxPrice: "", priceUnit: "", ordering: "" };

export default function Home() {
  const [searchParams] = useSearchParams();
  const [listings, setListings] = useState([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [categories, setCategories] = useState([]);
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [coords, setCoords] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api.categories().then(setCategories).catch(() => setCategories([]));
  }, []);

  // Support deep links like /?category=tools-equipment from the footer,
  // which use the category's slug since that's stable/readable in a URL -
  // the API itself filters by category id, so resolve slug -> id here.
  useEffect(() => {
    const slug = searchParams.get("category");
    if (slug && categories.length > 0) {
      const match = categories.find((c) => c.slug === slug);
      if (match) setFilters((f) => ({ ...f, category: String(match.id) }));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [categories]);

  const fetchListings = async (pageNum, useCoords) => {
    setLoading(true);
    setError("");
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (filters.category) params.set("category", filters.category);
    if (filters.minPrice) params.set("min_price", filters.minPrice);
    if (filters.maxPrice) params.set("max_price", filters.maxPrice);
    if (filters.priceUnit) params.set("price_unit", filters.priceUnit);
    if (filters.ordering) params.set("ordering", filters.ordering);
    if (useCoords && coords) {
      params.set("lat", coords.lat);
      params.set("lng", coords.lng);
      params.set("radius_km", "50");
    }
    params.set("page", pageNum);

    try {
      const data = await api.listings(`?${params.toString()}`);
      setListings(data.results ?? data);
      setCount(data.count ?? (data.results ?? data).length);
      setPage(pageNum);
    } catch (err) {
      setError("Could not load listings. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchListings(1, Boolean(coords));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters]);

  const useMyLocation = () => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const next = { lat: position.coords.latitude, lng: position.coords.longitude };
        setCoords(next);
        fetchListings(1, true);
      },
      () => setError("Location permission denied.")
    );
  };

  const pageSize = 20;
  const totalPages = Math.max(Math.ceil(count / pageSize), 1);

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
            fetchListings(1, Boolean(coords));
          }}
          className="card"
          style={{ display: "flex", gap: 10, flexWrap: "wrap", padding: 16, marginTop: -56, marginBottom: 28, position: "relative", zIndex: 2 }}
        >
          <input
            className="input"
            style={{ maxWidth: 320, flex: "1 1 220px" }}
            placeholder="Search items…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <button type="submit" className="btn btn-primary">
            Search
          </button>
          <button type="button" className="btn btn-secondary" onClick={useMyLocation}>
            {coords ? "Near me ✓" : "Search near me"}
          </button>
        </form>

        <div style={{ display: "grid", gridTemplateColumns: "220px 1fr", gap: 28, alignItems: "start" }}>
          <CategorySidebar categories={categories} filters={filters} onChange={setFilters} />

          <div>
            {error && <p className="error-text">{error}</p>}
            {loading ? (
              <p style={{ color: "var(--color-ink-soft)" }}>Loading listings…</p>
            ) : listings.length === 0 ? (
              <p style={{ color: "var(--color-ink-soft)" }}>No listings match yet. Try widening your search.</p>
            ) : (
              <>
                <p style={{ color: "var(--color-ink-faint)", fontSize: "0.85rem", marginBottom: 14 }}>{count} item{count !== 1 ? "s" : ""} found</p>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(230px, 1fr))", gap: 20, marginBottom: 28 }}>
                  {listings.map((listing) => (
                    <ListingCard key={listing.id} listing={listing} />
                  ))}
                </div>
                {totalPages > 1 && (
                  <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: 14 }}>
                    <button className="btn btn-secondary btn-sm" disabled={page <= 1} onClick={() => fetchListings(page - 1, Boolean(coords))}>
                      ← Previous
                    </button>
                    <span style={{ color: "var(--color-ink-soft)", fontSize: "0.85rem" }}>Page {page} of {totalPages}</span>
                    <button className="btn btn-secondary btn-sm" disabled={page >= totalPages} onClick={() => fetchListings(page + 1, Boolean(coords))}>
                      Next →
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}