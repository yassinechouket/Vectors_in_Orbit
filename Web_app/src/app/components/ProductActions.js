"use client";

import { useEffect } from "react";
import { useUser } from "@/lib/UserContext";

export default function ProductActions({ product }) {
  const { onProductView, addToCart, cart } = useUser();
  
  const isInCart = cart.some(item => item.product_id === product.product_id);

  useEffect(() => {
    // Track product view
    onProductView(product);
  }, [product.product_id]);

  const handleAddToCart = () => {
    addToCart(product);
  };

  const formatPrice = (price, currency = "INR") => {
    if (!price) return "Price unavailable";
    
    // Convert INR to TND (1 TND ≈ 27 INR)
    const priceInTND = currency === "INR" ? Math.round(price / 27) : price;
    
    return new Intl.NumberFormat('fr-TN', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(priceInTND) + " TND";
  };

  return (
    <div className="product-actions">
      <div className="product-price-large">
        {formatPrice(product.attributes.price, product.attributes.currency)}
      </div>
      
      <div className="product-availability">
        {product.attributes.availability?.in_stock ? (
          <span className="in-stock">✓ In Stock</span>
        ) : (
          <span className="out-of-stock">✗ Out of Stock</span>
        )}
      </div>

      <div className="product-action-buttons">
        <button 
          className={`btn-add-to-cart ${isInCart ? 'in-cart' : ''}`}
          onClick={handleAddToCart}
          disabled={!product.attributes.availability?.in_stock}
        >
          {isInCart ? '✓ In Cart' : '🛒 Add to Cart'}
        </button>
        
        <button className="btn-wishlist">
          ♡ Wishlist
        </button>
      </div>

      {product.links?.external_url && (
        <a
          href={product.links.external_url}
          target="_blank"
          rel="noreferrer"
          className="btn-external"
        >
          🔗 View on Store
        </a>
      )}

      <div className="product-meta-info">
        <div className="meta-item">
          <span className="meta-icon">🚚</span>
          <span>Free Delivery</span>
        </div>
        <div className="meta-item">
          <span className="meta-icon">↩️</span>
          <span>Easy Returns</span>
        </div>
        <div className="meta-item">
          <span className="meta-icon">🔒</span>
          <span>Secure Payment</span>
        </div>
      </div>
    </div>
  );
}
