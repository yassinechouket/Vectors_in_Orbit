"use client";

import Link from "next/link";
import { useUser } from "@/lib/UserContext";

export default function ProductCard({ product, index = 0 }) {
  const { onProductClick, addToCart } = useUser();
  const { semantic_text, attributes, product_id, category } = product;

  const getCategoryImage = (cat) => {
    const map = {
      laptop: "laptop.png",
      phone: "smartphone.png",
      smartphone: "smartphone.png",
      headphones: "headphones.png",
      tablet: "laptop.png",
      camera: "camera.png",
      watch: "smartwatch.png",
      speaker: "speaker.png",
      drone: "drone.png",
      "vr headset": "headphones.png",
      "gaming console": "pc.png",
      console: "pc.png",
      "virtual reality": "headphones.png",
      tv: "pc.png",
      television: "pc.png",
      computer: "pc.png",
      pc: "pc.png",
      "coffee maker": "coffe.png",
      coffee: "coffe.png"
    };
    return map[cat?.toLowerCase()] || "laptop.png";
  };

  const formatPrice = (price, currency = "TND") => {
    if (!price) return "N/A";

    // Price is already in TND from backend
    let displayPrice = price;
    
    // Only convert if legacy INR data
    if (currency === "INR") {
      displayPrice = price / 27;
    }

    // Simple format: round to whole number
    return Math.round(displayPrice) + " TND";
  };

  const handleAddToCart = (e) => {
    e.preventDefault();
    e.stopPropagation();
    addToCart(product);
    // Send feedback to backend
    sendFeedback('add_to_cart');
  };

  const handleProductClick = () => {
    onProductClick(product);
  };

  const handleWishlist = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    // Toggle wishlist state (visual feedback)
    const btn = e.currentTarget;
    const isLiked = btn.textContent === '♥';
    btn.textContent = isLiked ? '♡' : '♥';
    btn.classList.toggle('liked');
    
    // Send feedback to backend
    await sendFeedback(isLiked ? 'skip' : 'click');
  };

  const handleQuickView = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    // Send view feedback
    await sendFeedback('view');
    
    // Navigate to product page
    window.location.href = `/product/${product_id}`;
  };

  const sendFeedback = async (action) => {
    try {
      const userId = localStorage.getItem('user_id') || 'guest_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('user_id', userId);

      await fetch('http://localhost:8000/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          product_id: product_id,
          action: action,
          context: {
            category: category,
            price: attributes.price,
            brand: attributes.brand
          }
        }),
      });
    } catch (error) {
      console.log('Feedback tracking failed:', error);
    }
  };

  return (
    <div className="product-card">
      <div className="product-card-image">
        <Link href={`/product/${product_id}`} onClick={handleProductClick} className="w-full h-full flex items-center justify-center">
          <img
            src={`/images/${getCategoryImage(category)}`}
            alt={semantic_text.title}
            className="product-img"
            onError={(e) => {
              e.target.style.display = 'none';
            }}
          />
        </Link>

        <div className="product-badges">
          {attributes.availability?.in_stock && (
            <span className="product-badge stock">In Stock</span>
          )}
          {attributes.rating > 4.5 && (
            <span className="product-badge top-rated">Top Rated</span>
          )}
        </div>

        <div className="product-quick-actions">
          <button 
            className="quick-action-btn" 
            title="Add to Wishlist"
            onClick={handleWishlist}
          >
            ♡
          </button>
          <button 
            className="quick-action-btn" 
            title="Quick View"
            onClick={handleQuickView}
          >
            👁
          </button>
        </div>
      </div>

      <div className="product-card-content">
        <div className="product-card-brand">{attributes.brand}</div>

        <Link href={`/product/${product_id}`} onClick={handleProductClick} className="no-underline text-inherit">
          <h3 className="product-card-title" title={semantic_text.title}>
            {semantic_text.title}
          </h3>
        </Link>

        <div className="product-rating">
          <span className="stars">
            {'★'.repeat(Math.floor(attributes.rating || 0))}
            {'☆'.repeat(5 - Math.floor(attributes.rating || 0))}
          </span>
          <span>({attributes.reviews_count || 0})</span>
        </div>

        <div className="product-card-footer">
          <div className="product-price">
            {formatPrice(attributes.price, attributes.currency)}
            <span>TND</span>
          </div>
        </div>

        <button className="add-to-cart-btn" onClick={handleAddToCart}>
          🛒 Add to Cart
        </button>
      </div>
    </div>
  );
}
