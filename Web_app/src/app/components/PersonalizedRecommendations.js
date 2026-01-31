"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { getPersonalizedRecommendations, getRecentQueries } from "@/lib/api";
import { useUser } from "@/lib/UserContext";

/**
 * PersonalizedRecommendations Component
 * 
 * Displays product recommendations based on user's search history.
 * Similar to YouTube's recommendation system when no search is active.
 * 
 * **Method Used: History-Based Collaborative Filtering with Weighted Recency**
 * 
 * How it works:
 * 1. Aggregates user's recent search queries
 * 2. Applies exponential decay weighting (recent searches = higher weight)
 * 3. Creates a semantic representation of user interests
 * 4. Searches the product database using this aggregated representation
 * 5. Returns diverse recommendations matching user's preferences
 * 
 * The weighting formula: weight = 0.8^(index)
 * - Query 1 (most recent): weight = 1.0
 * - Query 2: weight = 0.8
 * - Query 3: weight = 0.64
 * - etc.
 */
export default function PersonalizedRecommendations() {
  const [recommendations, setRecommendations] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [methodInfo, setMethodInfo] = useState(null);
  const [hasHistory, setHasHistory] = useState(false);
  const router = useRouter();
  const { onProductClick, addToCart } = useUser();

  useEffect(() => {
    loadPersonalizedRecommendations();
  }, []);

  const loadPersonalizedRecommendations = async () => {
    setIsLoading(true);
    
    // Check if user has any activity (search history, viewed products, or cart)
    const recentQueries = getRecentQueries();
    const hasSearchHistory = recentQueries && recentQueries.length > 0;
    
    // Check for viewed products
    let hasViewedProducts = false;
    try {
      const viewed = JSON.parse(localStorage.getItem('viewed_products') || '[]');
      hasViewedProducts = viewed.length > 0;
    } catch {}
    
    // Check for cart items
    let hasCartItems = false;
    try {
      const cart = JSON.parse(localStorage.getItem('cart') || '[]');
      hasCartItems = cart.length > 0;
    } catch {}
    
    // Need at least some activity for personalization
    if (!hasSearchHistory && !hasViewedProducts && !hasCartItems) {
      setHasHistory(false);
      setIsLoading(false);
      return;
    }
    
    setHasHistory(true);
    
    try {
      const response = await getPersonalizedRecommendations(8);
      
      if (response.success && response.recommendations?.length > 0) {
        setRecommendations(response.recommendations);
        setMethodInfo(response.method_details);
      }
    } catch (error) {
      console.error("Failed to load personalized recommendations:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleProductClick = (product) => {
    // Format product for tracking (match ProductCard structure)
    const formattedProduct = {
      product_id: product.product_id,
      category: product.category,
      attributes: product.attributes,
      semantic_text: product.semantic_text,
    };
    onProductClick(formattedProduct);
    router.push(`/product/${product.product_id}`);
  };

  const handleAddToCart = (e, product) => {
    e.preventDefault();
    e.stopPropagation();
    // Format product for cart
    const cartProduct = {
      product_id: product.product_id,
      category: product.category,
      attributes: product.attributes,
      semantic_text: product.semantic_text,
    };
    addToCart(cartProduct);
  };

  const formatPrice = (price, currency = "TND") => {
    if (!price || price <= 0) return "N/A";
    
    let displayPrice = price;
    // Convert if legacy INR data
    if (currency === "INR") {
      displayPrice = price / 27;
    }
    
    // Simple format matching the site style
    return Math.round(displayPrice) + " TND";
  };

  const getCategoryImage = (category) => {
    const map = {
      laptop: "laptop.png",
      phone: "smartphone.png",
      smartphone: "smartphone.png",
      headphones: "headphones.png",
      tablet: "laptop.png",
      camera: "camera.png",
      watch: "smartwatch.png",
      smartwatch: "smartwatch.png",
      speaker: "speaker.png",
      drone: "drone.png",
      keyboard: "laptop.png",
      mouse: "laptop.png",
      monitor: "pc.png",
      pc: "pc.png",
      computer: "pc.png",
    };
    return `/images/${map[category?.toLowerCase()] || "laptop.png"}`;
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
      smartwatch: "⌚",
      speaker: "🔊",
      keyboard: "⌨️",
      mouse: "🖱️",
      monitor: "🖥️",
      drone: "🚁",
      default: "📦"
    };
    return emojis[category?.toLowerCase()] || emojis.default;
  };

  // Don't show section if no history or no recommendations
  if (!hasHistory || (!isLoading && recommendations.length === 0)) {
    return null;
  }

  return (
    <div className="personalized-section">
      {/* Header */}
      <div className="personalized-header">
        <div className="personalized-title-group">
          <span className="personalized-icon">✨</span>
          <h2 className="personalized-title">Recommended For You</h2>
          <span className="personalized-badge">AI-Powered</span>
        </div>
        
        {methodInfo && (
          <div className="method-info-tooltip">
            <button className="method-info-btn" title="How this works">
              ℹ️
            </button>
            <div className="method-info-dropdown">
              <h4>🧠 {methodInfo.name}</h4>
              <p>{methodInfo.description}</p>
              {methodInfo.queries_used && (
                <div className="method-queries">
                  <span>Based on: </span>
                  {methodInfo.queries_used.slice(0, 3).map((q, i) => (
                    <span key={i} className="query-tag">{q}</span>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Loading State */}
      {isLoading ? (
        <div className="personalized-loading">
          <div className="loading-spinner"></div>
          <span>Finding recommendations based on your history...</span>
        </div>
      ) : (
        /* Recommendations Grid */
        <div className="personalized-grid">
          {recommendations.map((product, index) => (
            <div 
              key={product.product_id || index}
              className="personalized-card"
              onClick={() => handleProductClick(product)}
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              {/* Product Image */}
              <div className="personalized-card-image">
                <img 
                  src={product.image_url || getCategoryImage(product.category)} 
                  alt={product.semantic_text?.title || product.name}
                  onError={(e) => {
                    e.target.src = getCategoryImage(product.category);
                  }}
                />

                {/* Quick Actions */}
                <div className="personalized-card-actions">
                  <button 
                    className="quick-action-btn wishlist-btn"
                    onClick={(e) => { e.stopPropagation(); }}
                    title="Add to Wishlist"
                  >
                    ♡
                  </button>
                  <button 
                    className="quick-action-btn cart-btn"
                    onClick={(e) => handleAddToCart(e, product)}
                    title="Add to Cart"
                  >
                    🛒
                  </button>
                </div>
              </div>

              {/* Product Info */}
              <div className="personalized-card-content">
                <div className="personalized-card-category">
                  {getCategoryEmoji(product.category)} {product.category}
                </div>
                <h3 className="personalized-card-name">
                  {product.semantic_text?.title || product.name}
                </h3>
                
                {product.attributes?.brand && (
                  <div className="personalized-card-brand">{product.attributes.brand}</div>
                )}
                
                <div className="personalized-card-footer">
                  <span className="personalized-card-price">
                    {product.formatted_price || formatPrice(product.attributes?.price, product.attributes?.currency)}
                  </span>
                  {product.attributes?.rating > 0 && (
                    <span className="personalized-card-rating">
                      ⭐ {product.attributes.rating.toFixed(1)}
                    </span>
                  )}
                </div>

                {/* Based on query hint */}
                {product.based_on_query && (
                  <div className="personalized-card-source">
                    Based on "{product.based_on_query}"
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* View More / Refresh */}
      <div className="personalized-actions">
        <button 
          className="refresh-btn"
          onClick={loadPersonalizedRecommendations}
          disabled={isLoading}
        >
          🔄 Refresh Recommendations
        </button>
      </div>
    </div>
  );
}
