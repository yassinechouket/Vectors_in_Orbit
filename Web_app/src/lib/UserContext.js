// Context provider for managing user session and feedback tracking
"use client";

import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { 
  trackFeedback, 
  getSessionId, 
  getUserId, 
  getRecentQueries,
  getViewedProducts,
  addToViewedProducts
} from './api';

const UserContext = createContext(null);

export function UserProvider({ children }) {
  const [sessionId, setSessionId] = useState(null);
  const [userId, setUserId] = useState(null);
  const [recentQueries, setRecentQueries] = useState([]);
  const [viewedProducts, setViewedProducts] = useState([]);
  const [cart, setCart] = useState([]);
  const [isOnline, setIsOnline] = useState(true);

  useEffect(() => {
    // Initialize session on client-side
    setSessionId(getSessionId());
    setUserId(getUserId());
    setRecentQueries(getRecentQueries());
    setViewedProducts(getViewedProducts());
    
    // Load cart from localStorage
    try {
      const savedCart = JSON.parse(localStorage.getItem('cart') || '[]');
      setCart(savedCart);
    } catch {
      setCart([]);
    }

    // Check online status
    setIsOnline(navigator.onLine);
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Track product click
  const onProductClick = useCallback((product) => {
    trackFeedback(product.product_id || product.id, 'click', {
      category: product.category,
      price: product.attributes?.price || product.price,
      brand: product.attributes?.brand || product.brand,
    });
  }, []);

  // Track product view (when viewing details)
  const onProductView = useCallback((product) => {
    const productId = product.product_id || product.id;
    addToViewedProducts(productId);
    setViewedProducts(getViewedProducts());
    
    trackFeedback(productId, 'view', {
      category: product.category,
      price: product.attributes?.price || product.price,
      brand: product.attributes?.brand || product.brand,
    });
  }, []);

  // Add to cart
  const addToCart = useCallback((product) => {
    const productId = product.product_id || product.id;
    
    setCart(prev => {
      const existing = prev.find(item => item.product_id === productId);
      let newCart;
      if (existing) {
        newCart = prev.map(item => 
          item.product_id === productId 
            ? { ...item, quantity: item.quantity + 1 }
            : item
        );
      } else {
        newCart = [...prev, { ...product, product_id: productId, quantity: 1 }];
      }
      localStorage.setItem('cart', JSON.stringify(newCart));
      return newCart;
    });

    trackFeedback(productId, 'add_to_cart', {
      category: product.category,
      price: product.attributes?.price || product.price,
      brand: product.attributes?.brand || product.brand,
    });
  }, []);

  // Remove from cart
  const removeFromCart = useCallback((productId) => {
    setCart(prev => {
      const newCart = prev.filter(item => item.product_id !== productId);
      localStorage.setItem('cart', JSON.stringify(newCart));
      return newCart;
    });
  }, []);

  // Update cart quantity
  const updateCartQuantity = useCallback((productId, quantity) => {
    if (quantity <= 0) {
      removeFromCart(productId);
      return;
    }
    
    setCart(prev => {
      const newCart = prev.map(item =>
        item.product_id === productId ? { ...item, quantity } : item
      );
      localStorage.setItem('cart', JSON.stringify(newCart));
      return newCart;
    });
  }, [removeFromCart]);

  // Track purchase
  const trackPurchase = useCallback((products) => {
    products.forEach(product => {
      trackFeedback(product.product_id || product.id, 'purchase', {
        category: product.category,
        price: product.attributes?.price || product.price,
        quantity: product.quantity,
      });
    });
  }, []);

  const value = {
    sessionId,
    userId,
    recentQueries,
    viewedProducts,
    cart,
    cartCount: cart.reduce((sum, item) => sum + item.quantity, 0),
    cartTotal: cart.reduce((sum, item) => {
      const price = item.attributes?.price || item.price || 0;
      return sum + (price * item.quantity);
    }, 0),
    isOnline,
    onProductClick,
    onProductView,
    addToCart,
    removeFromCart,
    updateCartQuantity,
    trackPurchase,
  };

  return (
    <UserContext.Provider value={value}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
}
