import React from "react";

export default function CategorySidebar({ categories, filters, onChange }) {
  const update = (field) => (e) => onChange({ ...filters, [field]: e.target.value });

  return (
    <aside className="card" style={{ padding: 20, height: "fit-content", position: "sticky", top: 84 }}>
      <h4 style={{ marginBottom: 12 }}>Categories</h4>
      <div style={{ display: "flex", flexDirection: "column", gap: 4, marginBottom: 24 }}>
        <button
          type="button"
          onClick={() => onChange({ ...filters, category: "" })}
          style={sidebarButtonStyle(filters.category === "")}
        >
          All categories
        </button>
        {categories.map((c) => (
          <button
            key={c.id}
            type="button"
            onClick={() => onChange({ ...filters, category: String(c.id) })}
            style={sidebarButtonStyle(filters.category === String(c.id))}
          >
            {c.name}
          </button>
        ))}
      </div>

      <h4 style={{ marginBottom: 12 }}>Price</h4>
      <div className="field" style={{ display: "flex", gap: 8 }}>
        <input
          type="number" min="0" className="input" placeholder="Min"
          value={filters.minPrice} onChange={update("minPrice")}
        />
        <input
          type="number" min="0" className="input" placeholder="Max"
          value={filters.maxPrice} onChange={update("maxPrice")}
        />
      </div>
      <div className="field">
        <label htmlFor="price-unit">Billed per</label>
        <select id="price-unit" className="input" value={filters.priceUnit} onChange={update("priceUnit")}>
          <option value="">Any</option>
          <option value="hour">Hour</option>
          <option value="day">Day</option>
        </select>
      </div>

      <h4 style={{ marginBottom: 12, marginTop: 20 }}>Sort by</h4>
      <select className="input" value={filters.ordering} onChange={update("ordering")}>
        <option value="">Newest first</option>
        <option value="price_amount">Price: low to high</option>
        <option value="-price_amount">Price: high to low</option>
      </select>
    </aside>
  );
}

function sidebarButtonStyle(active) {
  return {
    textAlign: "left",
    border: "none",
    background: active ? "rgba(15,110,92,0.08)" : "transparent",
    color: active ? "var(--brand-start)" : "var(--color-ink-soft)",
    fontWeight: active ? 700 : 500,
    padding: "8px 10px",
    borderRadius: 8,
    cursor: "pointer",
    fontSize: "0.88rem",
  };
}