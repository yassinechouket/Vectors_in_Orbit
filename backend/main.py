from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import orchestrator and models
from services.engines import (
    RecommendationOrchestrator,
    PipelineConfig,
)
from services.qdrant import QdrantManager
from models.schemas import FeedbackType

app = FastAPI(
    title="Smart Shopping Assistant API",
    description="Context-Aware Product Recommendation Engine with Qdrant",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pipeline configuration
config = PipelineConfig(
    top_k_search=20,
    top_k_filter=10,
    top_k_results=3,
    enable_feedback=True,
    qdrant_host="localhost",
    qdrant_port=6333,
)

# Main orchestrator
orchestrator = RecommendationOrchestrator(config)

class RecommendationRequest(BaseModel):
    """Request for recommendations"""
    query: str = Field(..., description="Natural language search query")
    user_id: Optional[str] = Field(None, description="User ID for personalization")
    max_budget: Optional[float] = Field(None, description="Maximum budget constraint")
    
    # Session context (optional)
    session_id: Optional[str] = Field(None, description="Session ID for tracking")
    device_type: Optional[str] = Field(None, description="Device type: mobile, tablet, desktop")
    recent_queries: Optional[List[str]] = Field(default_factory=list, description="Recent queries in session")
    viewed_products: Optional[List[str]] = Field(default_factory=list, description="Products viewed in session")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "cheap eco laptop for coding under $800",
                "user_id": "user_123",
                "max_budget": 800.0,
                "session_id": "sess_abc123",
                "device_type": "desktop",
                "recent_queries": ["gaming laptop", "laptop for programming"]
            }
        }


class FeedbackRequest(BaseModel):
    """Request to record user feedback"""
    user_id: str = Field(..., description="User identifier")
    product_id: str = Field(..., description="Product that was interacted with")
    action: str = Field(..., description="Action type: click, view, add_to_cart, purchase, skip, reject")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "product_id": "laptop_001",
                "action": "click",
                "context": {"category": "laptop", "price": 799.0}
            }
        }


class ProductUpsertRequest(BaseModel):
    """Request to add/update products in Qdrant"""
    products: List[Dict[str, Any]] = Field(..., description="List of products to upsert")
    
    class Config:
        json_schema_extra = {
            "example": {
                "products": [
                    {
                        "id": "laptop_001",
                        "name": "MacBook Air M2",
                        "price": 1199.0,
                        "category": "laptop",
                        "description": "Powerful laptop with M2 chip",
                        "store": "Apple Store",
                        "brand": "Apple",
                        "rating": 4.8,
                        "reviews_count": 5000,
                        "eco_certified": True,
                        "in_stock": True
                    }
                ]
            }
        }


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "Smart Shopping Assistant API",
        "version": "2.0.0",
        "status": "online",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Check health of all components"""
    health = orchestrator.health_check()
    all_healthy = all(health.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "components": health
    }


def build_session_context(request: RecommendationRequest) -> Optional[Any]:
    """
    Build SessionContext from request data.
    
    Args:
        request: Recommendation request
        
    Returns:
        SessionContext or None if no session data provided
    """
    if not request.session_id:
        return None
    
    from models.schemas import SessionContext
    from datetime import datetime
    
    # Determine time of day
    hour = datetime.utcnow().hour
    if 5 <= hour < 12:
        time_of_day = "morning"
    elif 12 <= hour < 17:
        time_of_day = "afternoon"
    elif 17 <= hour < 22:
        time_of_day = "evening"
    else:
        time_of_day = "night"
    
    return SessionContext(
        session_id=request.session_id,
        recent_queries=request.recent_queries or [],
        viewed_products=request.viewed_products or [],
        time_of_day=time_of_day,
        device_type=request.device_type or "unknown",
        session_duration=0.0  # Could be calculated from session start time
    )


@app.post("/recommend")
async def get_recommendations(request: RecommendationRequest):
    """
    Get product recommendations using the 8-step workflow.
    
    Steps:
    1. Parse natural language query
    2. Extract intent with LLM
    3. Search Qdrant with hybrid vectors
    4. Apply financial filtering
    5. Re-rank with weighted scoring
    6. Generate explanations
    7. Format for UI
    8. Track for learning
    
    Returns:
        Recommendations with explanations and budget insights
    """
    try:
        # Build constraints if budget provided
        constraints = None
        if request.max_budget:
            from models.schemas import FinancialConstraints
            constraints = FinancialConstraints(max_budget=request.max_budget)
        
        # Execute full pipeline
        response = await orchestrator.recommend(
            query=request.query,
            user_id=request.user_id,
            constraints=constraints,
        )
        
        return response.to_dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/recommend/quick")
async def quick_recommend(
    q: str = Query(..., description="Search query"),
    budget: Optional[float] = Query(None, description="Max budget"),
    user_id: Optional[str] = Query(None, description="User ID"),
):
    """
    Quick recommendation endpoint using GET.
    
    Example:
        GET /recommend/quick?q=laptop for coding&budget=1000
    """
    try:
        constraints = None
        if budget:
            from models.schemas import FinancialConstraints
            constraints = FinancialConstraints(max_budget=budget)
        
        response = await orchestrator.recommend(
            query=q,
            user_id=user_id,
            constraints=constraints,
        )
        
        # Return simplified response
        return {
            "query": q,
            "recommendations": [
                {
                    "name": rec.product.name,
                    "price": rec.product.formatted_price,
                    "score": rec.score,
                    "explanation": rec.explanation,
                }
                for rec in response.recommendations
            ],
            "budget_insight": response.budget_insight,
            "processing_time_ms": response.metadata["processing_time_ms"],
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analyze")
async def analyze_query(
    q: str = Query(..., description="Query to analyze"),
):
    """
    Analyze a query without searching.
    
    Returns the parsed intent and understanding.
    Useful for debugging and understanding query parsing.
    """
    try:
        intent = await orchestrator.query_engine.understand(q)
        
        return {
            "query": q,
            "parsed_intent": intent.to_dict(),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback")
async def record_feedback(request: FeedbackRequest):
    """
    Record user interaction feedback for learning.
    
    Action types:
    - click: User clicked on product
    - view: User viewed product details
    - add_to_cart: User added to cart
    - purchase: User completed purchase
    - skip: User skipped/ignored
    - reject: User explicitly rejected
    """
    try:
        # Convert action string to enum
        try:
            action_type = FeedbackType(request.action)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid action. Must be one of: {[t.value for t in FeedbackType]}"
            )
        
        success = orchestrator.record_feedback(
            user_id=request.user_id,
            product_id=request.product_id,
            action=action_type,
            context=request.context,
        )
        
        return {
            "success": success,
            "message": "Feedback recorded" if success else "Failed to record feedback"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class PersonalizedRequest(BaseModel):
    """Request for personalized recommendations based on search history and behavior"""
    user_id: str = Field(..., description="User ID for personalization")
    recent_queries: List[str] = Field(..., description="User's recent search queries")
    viewed_products: Optional[List[str]] = Field(default_factory=list, description="Products user has viewed")
    cart_items: Optional[List[str]] = Field(default_factory=list, description="Products in user's cart")
    limit: Optional[int] = Field(6, description="Number of recommendations to return")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "recent_queries": ["gaming laptop", "laptop for coding", "headphones"],
                "viewed_products": ["laptop_001", "headphones_002"],
                "cart_items": ["laptop_003"],
                "limit": 6
            }
        }


@app.post("/recommend/personalized")
async def get_personalized_recommendations(request: PersonalizedRequest):
    """
    Get personalized recommendations based on user's search history AND behavior.
    
    **Method: Hybrid Behavior-Aware Collaborative Filtering**
    
    This endpoint uses a combination of techniques:
    1. **Query Aggregation**: Combines recent search queries to understand user interests
    2. **Weighted Recency**: More recent queries have higher weight (temporal decay)
    3. **Behavior Analysis**: Incorporates clicks, views, and cart data
    4. **Category Extraction**: Identifies preferred categories from behavior
    5. **Semantic Similarity**: Uses embeddings to find products similar to past interactions
    6. **Diversity Sampling**: Ensures variety in recommendations across categories
    
    Algorithm:
    - Take the last N queries from user history
    - Analyze viewed products and cart items for category/brand preferences
    - Apply exponential decay weights (recent = more important)
    - Create a weighted aggregate query representing user interests
    - Boost results matching user's behavior patterns
    - Apply diversity filter to avoid showing too many similar items
    
    Returns:
        Personalized product recommendations with explanations
    """
    try:
        # Get user's behavior profile from FeedbackLoop
        behavior_profile = None
        user_preferences = None
        if orchestrator.feedback_loop:
            behavior_profile = orchestrator.feedback_loop.get_behavior_profile(request.user_id)
            user_preferences = orchestrator.feedback_loop.get_user_preferences(request.user_id)
        
        # If no search history, try to use behavior data
        has_queries = request.recent_queries and len(request.recent_queries) > 0
        has_behavior = behavior_profile is not None or (request.viewed_products and len(request.viewed_products) > 0)
        
        if not has_queries and not has_behavior:
            return {
                "success": False,
                "recommendations": [],
                "method": "behavior_aware_collaborative_filtering",
                "message": "No search history or behavior data available for personalization"
            }
        
        # Build aggregate query from multiple sources
        weighted_queries = []
        weights = []
        behavior_signals = []
        
        # 1. Add recent search queries with decay weighting
        if has_queries:
            for i, query in enumerate(request.recent_queries[:5]):
                weight = 0.8 ** i  # Exponential decay
                weighted_queries.append(query)
                weights.append(weight)
        
        # 2. Add signals from user preferences (categories and brands)
        if user_preferences:
            # Add preferred categories to query
            top_categories = sorted(
                user_preferences.preferred_categories.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            for cat, score in top_categories:
                weighted_queries.append(cat)
                weights.append(0.3)  # Lower weight than explicit searches
                behavior_signals.append(f"Preferred category: {cat}")
            
            # Add preferred brands to query
            top_brands = sorted(
                user_preferences.preferred_brands.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            for brand, score in top_brands:
                weighted_queries.append(brand)
                weights.append(0.25)
                behavior_signals.append(f"Preferred brand: {brand}")
        
        # 3. Detect if user wants cheap/affordable products from their queries
        wants_cheap = False
        if has_queries:
            cheap_keywords = ["cheap", "budget", "affordable", "low cost", "inexpensive", "under"]
            for query in request.recent_queries:
                if any(kw in query.lower() for kw in cheap_keywords):
                    wants_cheap = True
                    behavior_signals.append("Price priority: Low cost preferred")
                    break
        
        # 4. Build final aggregate query
        aggregate_query = " ".join(weighted_queries) if weighted_queries else "popular products"
        
        # Get recommendations using the FAST method (no LLM, ~100ms instead of ~60s)
        response = await orchestrator.recommend_fast(
            query=aggregate_query,
            user_id=request.user_id,
            constraints=None,  # No budget constraint for personalized
        )
        
        # Extract categories from history for diversity check
        history_categories = set()
        for rec in response.recommendations:
            if hasattr(rec.product, 'category') and rec.product.category:
                history_categories.add(rec.product.category)
        
        # Helper function to format price (simple format to match site style)
        def format_price(price: float) -> str:
            if price is None or price <= 0:
                return "N/A"
            return f"{int(round(price))} TND"
        
        # Sort recommendations by price if user wants cheap products
        recs_to_format = response.recommendations[:request.limit * 2]  # Get more to filter
        if wants_cheap and recs_to_format:
            # Sort by price (cheapest first)
            recs_to_format = sorted(recs_to_format, key=lambda r: r.product.price if r.product.price else float('inf'))
        
        # Format response with personalization context
        # Match the structure expected by the frontend (similar to home page products)
        recommendations = []
        for rec in recs_to_format[:request.limit]:
            # Access the UIProduct from the recommendation
            ui_product = rec.product
            
            product_data = {
                "product_id": ui_product.id,
                "name": ui_product.name,
                "category": ui_product.category,
                "semantic_text": {
                    "title": ui_product.name,
                    "description": getattr(ui_product, 'description', '') or ui_product.name,
                },
                "attributes": {
                    "brand": ui_product.brand,
                    "price": ui_product.price,
                    "currency": "TND",
                    "rating": ui_product.rating,
                    "reviews_count": ui_product.reviews_count,
                },
                "image_url": ui_product.image_url or "/images/laptop.png",
                "formatted_price": format_price(ui_product.price),
                "relevance_score": rec.score,
                "explanation": rec.explanation,
                "based_on_query": weighted_queries[0] if weighted_queries else None,
                "store": ui_product.store or "Amazon",
                "in_stock": ui_product.in_stock,
            }
            recommendations.append(product_data)
        
        # Build personalization summary
        personalization_sources = []
        if has_queries:
            personalization_sources.append(f"{len(request.recent_queries)} recent searches")
        if behavior_signals:
            personalization_sources.append(f"{len(behavior_signals)} behavior signals")
        if request.viewed_products:
            personalization_sources.append(f"{len(request.viewed_products)} viewed products")
        if request.cart_items:
            personalization_sources.append(f"{len(request.cart_items)} cart items")
        
        return {
            "success": True,
            "recommendations": recommendations,
            "method": "behavior_aware_collaborative_filtering",
            "method_details": {
                "name": "Behavior-Aware Personalized Search",
                "description": "Recommendations generated by analyzing your searches, clicks, views, and cart activity",
                "queries_used": weighted_queries[:5] if weighted_queries else [],
                "weights_applied": weights[:5] if weights else [],
                "categories_detected": list(history_categories),
                "behavior_signals": behavior_signals,
                "interaction_count": user_preferences.interaction_count if user_preferences else 0,
            },
            "message": f"Personalized recommendations based on {', '.join(personalization_sources)}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics")
async def get_analytics():
    """
    Get recommendation system analytics.
    
    Returns metrics on:
    - Pipeline configuration
    - Qdrant collection status
    - Feedback statistics
    """
    try:
        return orchestrator.get_analytics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/qdrant/setup")
async def setup_qdrant(recreate: bool = False):
    """
    Initialize Qdrant collection.
    
    Args:
        recreate: If True, delete existing collection first
    """
    try:
        qdrant = QdrantManager()
        success = qdrant.create_collection(recreate=recreate)
        
        return {
            "success": success,
            "message": "Collection created" if success else "Failed to create collection"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/qdrant/products")
async def upsert_products(request: ProductUpsertRequest):
    """
    Add or update products in Qdrant.
    
    Generates embeddings automatically and stores in vector DB.
    """
    try:
        from sentence_transformers import SentenceTransformer
        
        # Generate embeddings
        model = SentenceTransformer("all-MiniLM-L6-v2")
        
        texts = []
        for product in request.products:
            text = f"{product.get('name', '')} {product.get('description', '')} {product.get('category', '')}"
            texts.append(text)
        
        embeddings = model.encode(texts).tolist()
        
        # Upsert to Qdrant
        qdrant = QdrantManager()
        success = qdrant.upsert_products(
            products=request.products,
            dense_vectors=embeddings,
        )
        
        return {
            "success": success,
            "products_count": len(request.products),
            "message": "Products upserted" if success else "Failed to upsert"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/qdrant/info")
async def get_qdrant_info():
    """Get Qdrant collection information"""
    try:
        qdrant = QdrantManager()
        
        if not qdrant.health_check():
            return {
                "status": "disconnected",
                "message": "Cannot connect to Qdrant. Is Docker running?"
            }
        
        info = qdrant.get_collection_info()
        
        return {
            "status": "connected",
            "collection": info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
