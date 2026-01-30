"use client";

export default function Filters({
  categories,
  selectedCategory,
  setCategory,
  brands,
  selectedBrand,
  setBrand,
  maxPrice,
  setMaxPrice,
  onReset
}) {
  const getCategoryEmoji = (cat) => {
    const emojis = {
      laptop: "💻",
      phone: "📱",
      smartphone: "📱",
      headphones: "🎧",
      tablet: "📱",
      camera: "📷",
      watch: "⌚",
      speaker: "🔊"
    };
    return emojis[cat?.toLowerCase()] || "📦";
  };

  const hasFilters = selectedCategory || selectedBrand || maxPrice;

  const formatPrice = (price) => {
    return new Intl.NumberFormat('fr-TN', {
      style: 'currency',
      currency: 'TND',
      maximumFractionDigits: 0
    }).format(price);
  };

  // Max price in TND (approx 200,000 INR / 27 ~= 7500 TND)
  const MAX_PRICE_TND = 8000;

  return (
    <div className="filters-container">
      <div className="filter-header">
        <h3>🔍 Filters</h3>
        {hasFilters && (
          <button className="filter-reset" onClick={onReset}>
            Clear All
          </button>
        )}
      </div>

      <div className="filter-group">
        <label className="filter-label">Category</label>
        <div className="filter-select-wrapper">
          <select
            className="filter-select"
            value={selectedCategory}
            onChange={(e) => setCategory(e.target.value)}
          >
            <option value="">All Categories</option>
            {categories.map((c) => (
              <option key={c} value={c}>
                {getCategoryEmoji(c)} {c.charAt(0).toUpperCase() + c.slice(1)}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="filter-group">
        <label className="filter-label">Brand</label>
        <div className="filter-select-wrapper">
          <select
            className="filter-select"
            value={selectedBrand}
            onChange={(e) => setBrand(e.target.value)}
          >
            <option value="">All Brands</option>
            {brands.map((b) => (
              <option key={b} value={b}>{b}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="filter-group">
        <label className="filter-label">
          Max Price {maxPrice && `(${formatPrice(maxPrice)})`}
        </label>
        <input
          type="range"
          className="filter-range"
          min="0"
          max={MAX_PRICE_TND}
          step="100"
          value={maxPrice || MAX_PRICE_TND}
          onChange={(e) => setMaxPrice(e.target.value === String(MAX_PRICE_TND) ? "" : e.target.value)}
        />
        <div className="range-labels">
          <span>0 TND</span>
          <span>{formatPrice(MAX_PRICE_TND)}</span>
        </div>
      </div>

      {hasFilters && (
        <div className="active-filters">
          <span className="active-filters-label">Active:</span>
          {selectedCategory && (
            <span className="filter-tag">
              {getCategoryEmoji(selectedCategory)} {selectedCategory}
              <button onClick={() => setCategory("")}>×</button>
            </span>
          )}
          {selectedBrand && (
            <span className="filter-tag">
              {selectedBrand}
              <button onClick={() => setBrand("")}>×</button>
            </span>
          )}
          {maxPrice && (
            <span className="filter-tag">
              ≤ {formatPrice(maxPrice)}
              <button onClick={() => setMaxPrice("")}>×</button>
            </span>
          )}
        </div>
      )}
    </div>
  );
}
