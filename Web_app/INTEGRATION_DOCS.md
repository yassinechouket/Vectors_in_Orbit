# 🍵 Matcha AI - Frontend Integration Documentation

## Overview

This document describes the frontend-backend integration implemented for the Matcha AI recommendation system. The webapp has been completely redesigned with a modern dark theme and full backend connectivity.

---

## 🎨 Design System

### Color Palette
| Variable | Value | Usage |
|----------|-------|-------|
| `--bg` | `#0a0a0a` | Main background |
| `--card` | `#1a1a1a` | Card backgrounds |
| `--primary` | `#6366f1` | Primary actions |
| `--accent` | `#22d3ee` | Accents, prices |
| `--success` | `#22c55e` | Stock, success states |
| `--error` | `#ef4444` | Errors, out of stock |

### Typography
- Font: Inter (system fallback)
- Headings: 700-800 weight
- Body: 400-500 weight

---

## 📁 File Structure

```
Web_app/src/
├── lib/
│   ├── api.js           # Backend API service layer
│   └── UserContext.js   # User state & feedback tracking
└── app/
    ├── globals.css      # Complete dark theme styling
    ├── layout.js        # Root layout with UserProvider
    ├── page.js          # Main product listing page
    ├── product/[id]/
    │   └── page.js      # Product detail page
    └── components/
        ├── Header.js          # Navigation with cart
        ├── SmartSearch.js     # AI-powered search
        ├── ProductCard.js     # Product card with actions
        ├── ProductActions.js  # Add to cart, wishlist
        ├── Filters.js         # Category, brand, price filters
        └── Breadcrumbs.js     # Navigation breadcrumbs
```

---

## 🔌 API Integration

### API Service (`lib/api.js`)

The API service provides all backend communication:

```javascript
import { getRecommendations, trackFeedback, healthCheck } from '@/lib/api';

// Get AI recommendations
const results = await getRecommendations('laptop under 50000');

// Track user feedback
await trackFeedback({
  event_type: 'product_click',
  product_id: 'B09Q5F1GTP',
  query: 'laptop',
  timestamp: Date.now()
});

// Check backend status
const isOnline = await healthCheck();
```

### Available API Functions

| Function | Description |
|----------|-------------|
| `getRecommendations(query)` | Get AI-powered product recommendations |
| `quickSearch(query)` | Fast search for autocomplete |
| `analyzeQuery(query)` | Analyze query intent without search |
| `trackFeedback(data)` | Track user behavior events |
| `healthCheck()` | Check if backend is online |
| `getQdrantInfo()` | Get Qdrant collection info |
| `uploadProducts(products)` | Upload products to Qdrant |

---

## 👤 User Context (`lib/UserContext.js`)

The UserContext provides state management for user interactions:

```javascript
import { useUser } from '@/lib/UserContext';

function Component() {
  const {
    cart,           // Cart items array
    cartCount,      // Number of items in cart
    cartTotal,      // Total cart value
    isOnline,       // Backend connection status
    onProductClick, // Track product clicks
    onProductView,  // Track product views
    addToCart,      // Add product to cart
    removeFromCart, // Remove from cart
    trackPurchase   // Track purchase event
  } = useUser();
}
```

### Tracked Events
- `product_click` - When user clicks a product card
- `product_view` - When user views product detail page
- `add_to_cart` - When user adds to cart
- `purchase` - When user completes purchase

---

## 🔍 SmartSearch Component

The AI-powered search shows:
- Query understanding (intent, category)
- Budget analysis
- AI recommendations with match scores
- Product explanations

```jsx
<SmartSearch />
```

---

## 🛒 Product Components

### ProductCard
Displays product with:
- Category emoji icon
- Brand and title
- Key features (top 3)
- Price in INR
- Add to cart button
- Quick actions (wishlist, quick view)

### ProductActions
On product detail page:
- Large price display
- Stock status
- Add to cart / In cart toggle
- Wishlist button
- External store link
- Delivery info

---

## 🚀 Backend Setup

### 1. Start Qdrant (Docker)
```bash
cd backend
docker-compose up -d
```

### 2. Upload Products
```bash
python upload_products.py
```

### 3. Start Backend
```bash
python main.py
```

Backend runs on: `http://localhost:8000`

### 4. Start Frontend
```bash
cd Web_app
npm run dev
```

Frontend runs on: `http://localhost:3000`

---

## 📊 API Endpoints

### POST /recommend
Get AI recommendations for a query.

**Request:**
```json
{
  "query": "laptop for programming under 50000",
  "filters": {
    "category": "laptop",
    "max_price": 50000
  },
  "top_k": 5,
  "user_context": {
    "session_id": "uuid",
    "recent_queries": ["gaming laptop"],
    "viewed_products": ["B09Q5F1GTP"]
  }
}
```

**Response:**
```json
{
  "recommendations": [...],
  "query_understanding": {
    "primary_intent": "buy",
    "category": "laptop",
    "budget_range": {"min": 0, "max": 50000}
  },
  "total_found": 15,
  "search_time_ms": 150
}
```

### POST /feedback
Track user behavior events.

### GET /health
Health check endpoint.

---

## 🎯 Features Implemented

- ✅ Modern dark theme UI
- ✅ AI-powered smart search
- ✅ Real-time backend connectivity indicator
- ✅ User behavior tracking
- ✅ Shopping cart functionality
- ✅ Product filtering (category, brand, price)
- ✅ Responsive design
- ✅ Animated product cards
- ✅ Product detail page with actions
- ✅ Session management

---

## 🔧 Technologies Used

### Frontend
- Next.js 16 (App Router)
- React 19
- CSS Variables (Custom Properties)
- LocalStorage (session/cart persistence)

### Backend
- FastAPI
- Qdrant Vector Database
- Google Gemini AI
- SentenceTransformers
- Python 3.11+

---

## 📝 Notes

1. **CORS**: Backend allows all origins for development
2. **Environment**: Backend needs `.env` with `GOOGLE_GEN_AI_API_KEY`
3. **Qdrant**: Must be running on port 6333
4. **Products**: Upload using `upload_products.py` before testing recommendations
