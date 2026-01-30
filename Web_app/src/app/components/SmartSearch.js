"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { getRecommendations, addToRecentQueries } from "@/lib/api";
import { useUser } from "@/lib/UserContext";

export default function SmartSearch({ onResults }) {
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [results, setResults] = useState(null);
  const [budget, setBudget] = useState("");
  const dropdownRef = useRef(null);
  const inputRef = useRef(null);
  const router = useRouter();
  const { onProductClick } = useUser();

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSearch = async (e) => {
    e?.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    setShowDropdown(true);

    try {
      const maxBudget = budget ? parseFloat(budget) : null;
      const response = await getRecommendations(query, maxBudget);

      if (response) {
        setResults(response);
        addToRecentQueries(query);

        // Pass results to parent if callback provided
        if (onResults) {
          onResults(response);
        }
      }
    } catch (error) {
      console.error("Search error:", error);
    } finally {
      setIsSearching(false);
    }
  };

  const handleProductClick = (product) => {
    onProductClick(product);
    setShowDropdown(false);
    router.push(`/product/${product.product_id || product.id}`);
  };

  const getCategoryEmoji = (category) => {
    const emojis = {
      laptop: "💻",
      phone: "📱",
      smartphone: "📱",
      headphones: "🎧",
      tablet: "📱",
      camera: "📷",
      watch: "⌚",
      speaker: "🔊",
      default: "📦"
    };
    return emojis[category?.toLowerCase()] || emojis.default;
  };

  const formatPrice = (price, currency = "TND") => {
    if (!price) return "N/A";

    // Price is already in TND from backend
    let displayPrice = price;
    
    // Only convert if legacy INR data
    if (currency === "INR") {
      displayPrice = price / 27;
    }

    return new Intl.NumberFormat('fr-TN', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(displayPrice) + " TND";
  };

  return (
    <div className="search-container" ref={dropdownRef}>
      <form onSubmit={handleSearch}>
        <div className="search-input-wrapper">
          <span className="search-icon">🔍</span>
          <input
            ref={inputRef}
            type="text"
            className="search-input"
            placeholder="Ask AI: 'gaming laptop under 3000 TND' or 'best phone for photos'..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => results && setShowDropdown(true)}
          />
          <button
            type="submit"
            className="search-btn"
            disabled={isSearching || !query.trim()}
          >
            {isSearching ? (
              <span className="loading-spinner" style={{ width: 16, height: 16 }} />
            ) : (
              "✨ Search"
            )}
          </button>
        </div>
      </form>

      {/* AI-Powered Search Dropdown */}
      {showDropdown && results && (
        <div className="search-dropdown">
          {/* AI Understanding */}
          {results.query_understanding && (
            <div className="search-dropdown-section">
              <div className="search-dropdown-title">
                <span className="icon">🧠</span>
                AI Understanding
              </div>
              <div className="ai-insight">
                <div className="ai-insight-label">Detected Intent</div>
                <div className="ai-insight-text">
                  {results.query_understanding.category && (
                    <span>Category: <strong>{results.query_understanding.category}</strong> • </span>
                  )}
                  {results.query_understanding.max_price && (
                    <span>Budget: <strong>≤{formatPrice(results.query_understanding.max_price)}</strong> • </span>
                  )}
                  {results.query_understanding.use_case && (
                    <span>Use: <strong>{results.query_understanding.use_case}</strong> • </span>
                  )}
                  {results.query_understanding.priority && (
                    <span>Priority: <strong>{results.query_understanding.priority}</strong></span>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Budget Insight */}
          {results.budget_insight && (
            <div className="search-dropdown-section">
              <div className="search-dropdown-title">
                <span className="icon">💰</span>
                Budget Analysis
              </div>
              <div className="ai-insight">
                <div className="ai-insight-text">
                  {results.budget_insight.comparison ||
                    `Best value at ${formatPrice(results.budget_insight.recommended_price)}`}
                </div>
              </div>
            </div>
          )}

          {/* Recommendations */}
          {results.recommendations && results.recommendations.length > 0 && (
            <div className="search-dropdown-section">
              <div className="search-dropdown-title">
                <span className="icon">⭐</span>
                AI Recommendations ({results.recommendations.length})
              </div>

              {results.recommendations.map((rec, index) => {
                const product = rec.product || rec;
                return (
                  <div
                    key={product.id || index}
                    className="recommendation-item"
                    onClick={() => handleProductClick(product)}
                  >
                    <div className="recommendation-image">
                      {getCategoryEmoji(product.category)}
                    </div>
                    <div className="recommendation-content">
                      <div className="recommendation-name">
                        {product.name || product.semantic_text?.title}
                      </div>
                      <div className="recommendation-meta">
                        <span className="recommendation-price">
                          {formatPrice(product.price || product.attributes?.price)}
                        </span>
                        {rec.score && (
                          <span className="recommendation-score">
                            Match: <span className="highlight">{Math.round(rec.score * 100)}%</span>
                          </span>
                        )}
                      </div>
                      {rec.explanation && (
                        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                          {rec.explanation.slice(0, 80)}...
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* No Results */}
          {results.recommendations && results.recommendations.length === 0 && (
            <div className="search-dropdown-section">
              <div className="empty-state" style={{ padding: 40 }}>
                <div className="empty-state-icon">🔍</div>
                <h3>No matches found</h3>
                <p>Try adjusting your search or budget constraints</p>
              </div>
            </div>
          )}

          {/* Processing Time */}
          {results.metadata?.processing_time_ms && (
            <div className="search-dropdown-section" style={{ padding: '8px 16px', textAlign: 'center' }}>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                AI processed in {results.metadata.processing_time_ms}ms
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
