// API Service Layer - Connects frontend to backend
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Session management
export function getSessionId() {
  if (typeof window === 'undefined') return null;
  let sessionId = sessionStorage.getItem('session_id');
  if (!sessionId) {
    sessionId = `sess_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
    sessionStorage.setItem('session_id', sessionId);
  }
  return sessionId;
}

export function getUserId() {
  if (typeof window === 'undefined') return null;
  let userId = localStorage.getItem('user_id');
  if (!userId) {
    userId = `user_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
    localStorage.setItem('user_id', userId);
  }
  return userId;
}

export function getDeviceType() {
  if (typeof window === 'undefined') return 'unknown';
  const width = window.innerWidth;
  if (width < 768) return 'mobile';
  if (width < 1024) return 'tablet';
  return 'desktop';
}

export function getRecentQueries() {
  if (typeof window === 'undefined') return [];
  try {
    return JSON.parse(localStorage.getItem('recent_queries') || '[]');
  } catch {
    return [];
  }
}

export function addToRecentQueries(query) {
  if (typeof window === 'undefined') return;
  const recent = getRecentQueries();
  const filtered = recent.filter(q => q !== query);
  filtered.unshift(query);
  localStorage.setItem('recent_queries', JSON.stringify(filtered.slice(0, 10)));
}

export function getViewedProducts() {
  if (typeof window === 'undefined') return [];
  try {
    return JSON.parse(localStorage.getItem('viewed_products') || '[]');
  } catch {
    return [];
  }
}

export function addToViewedProducts(productId) {
  if (typeof window === 'undefined') return;
  const viewed = getViewedProducts();
  const filtered = viewed.filter(id => id !== productId);
  filtered.unshift(productId);
  localStorage.setItem('viewed_products', JSON.stringify(filtered.slice(0, 20)));
}

// API Calls
export async function getRecommendations(query, maxBudget = null) {
  try {
    const response = await fetch(`${API_BASE}/recommend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        user_id: getUserId(),
        max_budget: maxBudget,
        session_id: getSessionId(),
        device_type: getDeviceType(),
        recent_queries: getRecentQueries(),
        viewed_products: getViewedProducts(),
      }),
    });
    
    if (!response.ok) throw new Error('API request failed');
    
    addToRecentQueries(query);
    return await response.json();
  } catch (error) {
    console.error('Recommendation API error:', error);
    return null;
  }
}

export async function quickSearch(query, budget = null) {
  try {
    const params = new URLSearchParams({ q: query });
    if (budget) params.append('budget', budget.toString());
    if (getUserId()) params.append('user_id', getUserId());
    
    const response = await fetch(`${API_BASE}/recommend/quick?${params}`);
    if (!response.ok) throw new Error('API request failed');
    
    addToRecentQueries(query);
    return await response.json();
  } catch (error) {
    console.error('Quick search error:', error);
    return null;
  }
}

export async function analyzeQuery(query) {
  try {
    const response = await fetch(`${API_BASE}/analyze?q=${encodeURIComponent(query)}`);
    if (!response.ok) throw new Error('API request failed');
    return await response.json();
  } catch (error) {
    console.error('Analyze query error:', error);
    return null;
  }
}

export async function trackFeedback(productId, action, context = {}) {
  try {
    const userId = getUserId();
    if (!userId) return false;
    
    const response = await fetch(`${API_BASE}/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        product_id: productId,
        action, // 'click', 'view', 'add_to_cart', 'purchase', 'skip', 'reject'
        context: {
          ...context,
          session_id: getSessionId(),
          timestamp: Date.now(),
        },
      }),
    });
    
    return response.ok;
  } catch (error) {
    console.error('Feedback tracking error:', error);
    return false;
  }
}

export async function healthCheck() {
  try {
    const response = await fetch(`${API_BASE}/health`);
    return await response.json();
  } catch {
    return { status: 'offline', components: {} };
  }
}

export async function getQdrantInfo() {
  try {
    const response = await fetch(`${API_BASE}/qdrant/info`);
    return await response.json();
  } catch {
    return { status: 'disconnected' };
  }
}

export async function setupQdrant(recreate = false) {
  try {
    const response = await fetch(`${API_BASE}/qdrant/setup?recreate=${recreate}`, {
      method: 'POST',
    });
    return await response.json();
  } catch (error) {
    console.error('Qdrant setup error:', error);
    return { success: false };
  }
}

export async function uploadProducts(products) {
  try {
    const response = await fetch(`${API_BASE}/qdrant/products`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ products }),
    });
    return await response.json();
  } catch (error) {
    console.error('Upload products error:', error);
    return { success: false };
  }
}

/**
 * Get personalized recommendations based on user's search history.
 * 
 * Method: History-Based Collaborative Filtering with Weighted Recency
 * - Analyzes recent search queries with temporal decay weighting
 * - More recent searches have higher influence
 * - Uses semantic similarity to find matching products
 * 
 * @param {number} limit - Maximum number of recommendations to return
 * @returns {Promise<Object>} Personalized recommendations with method details
 */
export async function getPersonalizedRecommendations(limit = 6) {
  try {
    const userId = getUserId();
    const recentQueries = getRecentQueries();
    const viewedProducts = getViewedProducts();
    
    // Get cart items from localStorage
    let cartItems = [];
    try {
      const cart = JSON.parse(localStorage.getItem('cart') || '[]');
      cartItems = cart.map(item => item.product_id);
    } catch {
      cartItems = [];
    }
    
    // Call API even if no queries - backend now uses behavior data too
    const response = await fetch(`${API_BASE}/recommend/personalized`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        recent_queries: recentQueries || [],
        viewed_products: viewedProducts || [],
        cart_items: cartItems,
        limit,
      }),
    });
    
    if (!response.ok) throw new Error('API request failed');
    return await response.json();
  } catch (error) {
    console.error('Personalized recommendations error:', error);
    return { success: false, recommendations: [], message: error.message };
  }
}
