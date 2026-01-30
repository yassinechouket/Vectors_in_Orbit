"use client";

import { useEffect, useState } from "react";
import ProductCard from "./components/ProductCard";
import SmartSearch from "./components/SmartSearch";
import Filters from "./components/Filters";
import PersonalizedRecommendations from "./components/PersonalizedRecommendations";
import { healthCheck } from "@/lib/api";
import { useUser } from "@/lib/UserContext";

export default function Home() {
  const { cartCount } = useUser();
  const [products, setProducts] = useState([]);
  const [query, setQuery] = useState("");
  const [brand, setBrand] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [category, setCategory] = useState("");
  const [isBackendOnline, setIsBackendOnline] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    // Load products
    fetch("/data/reference_catalog_clean.json")
      .then(r => r.json())
      .then(setProducts);

    // Check backend health
    healthCheck().then(result => {
      setIsBackendOnline(result?.status === 'healthy' || result?.status === 'degraded');
    });
  }, []);

  const brands = [...new Set(products.map(p => p.attributes?.brand).filter(Boolean))].sort();
  const categories = [...new Set(products.map(p => p.category).filter(Boolean))].sort();

  const filtered = products.filter(p => {
    const text = (p.semantic_text.title + " " + p.semantic_text.description).toLowerCase();

    return (
      text.includes(query.toLowerCase()) &&
      (!category || p.category === category) &&
      (!brand || p.attributes.brand === brand) &&
      (!maxPrice || (p.attributes.price && p.attributes.price <= Number(maxPrice)))
    );
  });

  const handleReset = () => {
    setQuery("");
    setBrand("");
    setMaxPrice("");
    setCategory("");
  };

  const handleSearchResults = (results) => {
    // If SmartSearch returns results, we can use them
    // For now, we'll just use the local filtering
  };

  return (
    <div className="layout-modern">
      {/* Top Navigation Bar */}
      <nav className="top-nav">
        <div className="top-nav-container">
          <div className="nav-logo">
            <span className="logo-icon">🛍️</span>
            <span className="logo-text">Matcha</span>
          </div>

          {/* Search Bar */}
          <div className="top-search-wrapper">
            <SmartSearch />
          </div>

          {/* Sidebar Toggle & Cart */}
          <div className="nav-actions">
            <button 
              className="sidebar-toggle"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              title="Toggle Filters"
            >
              ☰
            </button>
            <div className="cart-icon">
              🛒
              <span className="cart-badge">{cartCount || 0}</span>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Container */}
      <div className="main-container">
        {/* Sidebar */}
        <aside className={`sidebar-modern ${sidebarOpen ? 'open' : 'closed'}`}>
          <div className="sidebar-sticky">
            <div className="sidebar-header-modern">
              <h2>Filters</h2>
              <button 
                className="close-sidebar-btn"
                onClick={() => setSidebarOpen(false)}
              >
                ✕
              </button>
            </div>

            <Filters
              categories={categories}
              selectedCategory={category}
              setCategory={setCategory}
              brands={brands}
              selectedBrand={brand}
              setBrand={setBrand}
              maxPrice={maxPrice}
              setMaxPrice={setMaxPrice}
              onReset={handleReset}
            />

            {/* Sidebar Stats */}
            <div className="sidebar-stats-modern">
              <div className="stat-box">
                <div className="stat-icon">📦</div>
                <div className="stat-info">
                  <div className="stat-value">{products.length}</div>
                  <div className="stat-label">Products</div>
                </div>
              </div>
              <div className="stat-box">
                <div className="stat-icon">🏷️</div>
                <div className="stat-info">
                  <div className="stat-value">{brands.length}</div>
                  <div className="stat-label">Brands</div>
                </div>
              </div>
              <div className="stat-box">
                <div className="stat-icon">📂</div>
                <div className="stat-info">
                  <div className="stat-value">{categories.length}</div>
                  <div className="stat-label">Categories</div>
                </div>
              </div>
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <section className="main-content-modern">
          {/* Enhanced Content Header */}
          <div className="content-header-modern">
            <div className="header-left">
              <div className="title-wrapper">
                <div className="title-icon-wrapper">
                  <span className="title-icon">🛒</span>
                  <div className="title-icon-pulse"></div>
                </div>
                <div className="title-content">
                  <h1 className="page-title">Discover Products</h1>
                  <div className="title-underline"></div>
                </div>
              </div>
              <div className="results-info">
                <span className="results-count-badge">
                  <span className="count-number">{filtered.length}</span>
                  <span className="count-text">{filtered.length === 1 ? 'product' : 'products'} available</span>
                </span>
                {(category || brand || maxPrice) && (
                  <span className="filters-active-badge">
                    <span className="filter-dot"></span>
                    Filters active
                  </span>
                )}
              </div>
            </div>
            
            {/* Enhanced Quick Filter */}
            <div className="quick-filter-wrapper">
              <div className="quick-filter-container">
                <span className="search-icon-emoji">🔍</span>
                <input 
                  type="text"
                  className="quick-filter-input"
                  placeholder="Search products..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
                {query && (
                  <button 
                    className="clear-filter-btn"
                    onClick={() => setQuery('')}
                    title="Clear search"
                  >
                    ✕
                  </button>
                )}
                {!query && (
                  <span className="filter-shortcut">⌘K</span>
                )}
              </div>
            </div>
          </div>

          {/* Category Chips with Icons */}
          <div className="category-chips">
            <button 
              className={`category-chip ${category === '' ? 'active' : ''}`}
              onClick={() => setCategory('')}
            >
              <span className="chip-icon">✨</span> All
            </button>
            {categories.slice(0, 8).map(cat => {
              const icons = {
                laptop: '💻', phone: '📱', smartphone: '📱', headphones: '🎧',
                camera: '📷', smartwatch: '⌚', watch: '⌚', speaker: '🔊',
                drone: '🚁', pc: '🖥️', tablet: '📱', keyboard: '⌨️'
              };
              return (
                <button 
                  key={cat}
                  className={`category-chip ${category === cat ? 'active' : ''}`}
                  onClick={() => setCategory(cat)}
                >
                  <span className="chip-icon">{icons[cat.toLowerCase()] || '📦'}</span>
                  {cat.charAt(0).toUpperCase() + cat.slice(1)}
                </button>
              );
            })}
          </div>

          {/* Personalized Recommendations - Based on Search History */}
          {/* Only shows when user has search history, like YouTube's homepage */}
          <PersonalizedRecommendations />

          {/* Products Grid */}
          {filtered.length === 0 ? (
            <div className="empty-state-modern">
              <div className="empty-icon">🔍</div>
              <h3>No products found</h3>
              <p>Try adjusting your filters or search terms</p>
              <button className="btn-reset" onClick={handleReset}>
                Clear All Filters
              </button>
            </div>
          ) : (
            <div className="products-grid-modern">
              {filtered.map((p, index) => (
                <ProductCard key={p.product_id} product={p} index={index} />
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
