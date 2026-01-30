from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uvicorn

# Import orchestrator and models
from services.engines import (
    RecommendationOrchestrator,
    PipelineConfig,
)
from services.qdrant import QdrantManager
from services.qdrant import QdrantManager
from models.schemas import FeedbackType
from schemas.product_detection import ProductPageRequest

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


class ExplainRequest(BaseModel):
    """Request for product explanation"""
    product_id: str = Field(..., description="ID of the product to explain")
    user_history_titles: Optional[List[str]] = Field(default_factory=list, description="User's browsing history names")


@app.post("/explain")
async def explain_product(request: ExplainRequest):
    """
    Generate an explanation for a specific product.
    """
    try:
        # 1. Retrieve product from Qdrant
        # Handle both string and int IDs
        try:
            point_id = int(request.product_id)
        except ValueError:
            point_id = request.product_id
            
        points = orchestrator.qdrant_manager.client.retrieve(
            collection_name="products",
            ids=[point_id]
        )
        
        if not points:
            raise HTTPException(status_code=404, detail="Product not found")
        
        product_data = points[0].payload
        
        # 2. Generate explanation
        # Simple template-based explanation since we don't have the original query context
        parts = []
        
        name = product_data.get('name', 'This product')
        brand = product_data.get('brand', 'Generic')
        category = product_data.get('category', 'item')
        price = product_data.get('price', 0)
        rating = product_data.get('rating', 0)
        features = product_data.get('specs', {})
        
        # Opening
        if rating >= 4.5:
            parts.append(f"This top-rated {brand} {category} is an excellent choice.")
        else:
            parts.append(f"This {brand} {category} is a solid option.")
            
        # Price context
        parts.append(f"At ${price}, it offers competitive value.")
        
        # Features
        if features:
            key_specs = list(features.values())[:2]
            parts.append(f"It features {', '.join(str(s) for s in key_specs)}.")
            
        # Closing
        if product_data.get('eco_certified'):
            parts.append("Plus, it's eco-certified!")
            
        explanation = " ".join(parts)
        
        return {"explanation": explanation}
        
    except Exception as e:
        print(f"Explain error: {e}")
        return {"explanation": "Could not analyze product at this time."}


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
        
        # Build session context if session data provided
        session_context = build_session_context(request)
        
        # Execute full pipeline with all enhancements
        # Note: session_context is built but not currently used by orchestrator
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

@app.post("/search")
async def search_products(request: RecommendationRequest):
    """
    Search/recommend products (alias for /recommend for extension compatibility)
    
    This endpoint provides the same functionality as /recommend
    """
    return await get_recommendations(request)

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


# =============================================================================
# PRODUCT PAGE DETECTION ENDPOINTS
# =============================================================================

@app.post("/detect-product-page")
async def detect_product_page_endpoint(request: ProductPageRequest):
    """
    Detect if HTML is a product page and extract structured information
    """
    try:
        from services.product_page_detector import product_detector
        from schemas.product_detection import ProductPageRequest, ProductPageResponse
        
        # Detect if it's a product page
        detection = product_detector.detect_product_page(request.html, request.url)
        
        # Extract product info if detected
        product_info = None
        enhanced_query = None
        
        if detection.is_product_page:
            product_info = product_detector.extract_product_info(request.html, request.url)
            
            if product_info:
                # Generate enhanced query
                enhanced_query = product_detector.enhance_prompt_with_context(
                    "", 
                    product_info
                )
                
                # =========================================================
                # AUTO-INDEXING: Add product to Qdrant immediately
                # =========================================================
                try:
                    from services.qdrant.client import QdrantManager
                    from urllib.parse import urlparse
                    import uuid
                    
                    # 1. Prepare text for embedding
                    text = f"{product_info.name} {product_info.description or ''} {product_info.category or ''}"
                    
                    # 2. Generate embedding (reuse loaded model from orchestrator)
                    # Note: orchestrator is global in main.py
                    embedding = orchestrator.query_engine.embedding_model.encode(text).tolist()
                    
                    # 3. Prepare product payload
                    # Use UUID5 for deterministic ID based on URL or Name
                    id_source = product_info.url or product_info.name or str(datetime.now())
                    product_id = str(uuid.uuid5(uuid.NAMESPACE_URL, id_source))
                    
                    product_dict = {
                        "id": product_id,
                        "name": product_info.name,
                        "price": product_info.price or 0.0,
                        "category": product_info.category or "Uncategorized",
                        "description": product_info.description or "",
                        "store": urlparse(request.url).netloc, # Extract store domain
                        "brand": product_info.brand,
                        "rating": product_info.rating or 0.0,
                        "reviews_count": product_info.review_count or 0,
                        "eco_certified": False, # Default
                        "in_stock": product_info.availability == "InStock" if product_info.availability else True,
                        "image_url": product_info.images[0] if product_info.images else None,
                        "specs": product_info.specifications or {}
                    }
                    
                    # 4. Upsert to Qdrant
                    qdrant = QdrantManager()
                    qdrant.upsert_products(
                        products=[product_dict],
                        dense_vectors=[embedding]
                    )
                    print(f"✅ Auto-indexed product: {product_info.name} (ID: {product_id})")
                    
                except Exception as index_err:
                    print(f"⚠️ Auto-indexing failed: {index_err}")
                    # Log to file to be sure we see it
                    with open("debug_auto_index.log", "a") as f:
                        f.write(f"Failed to auto-index: {index_err}\n")
                    # Don't fail the request, just log error
        
        response = ProductPageResponse(
            detection=detection,
            product_info=product_info,
            enhanced_query=enhanced_query
        )
        
        return response.dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# TRACKING ENDPOINTS
# =============================================================================

@app.post("/tracking/search")
async def log_search_event(event: "SearchEvent"):
    """Log a search event for analytics"""
    try:
        from services.tracking_service import tracking_service
        from schemas.tracking import SearchEvent
        
        event_id = tracking_service.track_search(event)
        return {"status": "logged", "event_id": event_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tracking/click")
async def log_click_event(event: "ClickEvent"):
    """Log a click event for analytics"""
    try:
        from services.tracking_service import tracking_service
        from schemas.tracking import ClickEvent
        
        event_id = tracking_service.track_click(event)
        return {"status": "logged", "event_id": event_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tracking/view")
async def log_view_event(event: "ViewEvent"):
    """Log a product view event"""
    try:
        from services.tracking_service import tracking_service
        from schemas.tracking import ViewEvent
        
        event_id = tracking_service.track_view(event)
        return {"status": "logged", "event_id": event_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tracking/conversion")
async def log_conversion_event(event: "ConversionEvent"):
    """Log a conversion event (add to cart, purchase)"""
    try:
        from services.tracking_service import tracking_service
        from schemas.tracking import ConversionEvent
        
        event_id = tracking_service.track_conversion(event)
        return {"status": "logged", "event_id": event_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tracking/interests/{user_id}")
async def get_user_interests(user_id: str):
    """Get user interest profile from tracking data"""
    try:
        from services.tracking_service import tracking_service
        
        profile = tracking_service.extract_user_interests(user_id)
        return profile.dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tracking/stats")
async def get_tracking_stats(user_id: Optional[str] = Query(None)):
    """Get aggregate tracking statistics"""
    try:
        from services.tracking_service import tracking_service
        
        stats = tracking_service.get_tracking_stats(user_id)
        return stats.dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# WISHLIST ENDPOINTS
# =============================================================================

@app.post("/wishlist/add")
async def add_to_wishlist_endpoint(item: "WishlistItem"):
    """Add product to user's wishlist"""
    try:
        from services.wishlist_service import wishlist_service
        from schemas.wishlist import WishlistItem
        
        item_id = wishlist_service.add_to_wishlist(item)
        return {"status": "added", "wishlist_item_id": item_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/wishlist/remove/{product_id}")
async def remove_from_wishlist_endpoint(
    product_id: str,
    user_id: str = Query(..., description="User ID")
):
    """Remove product from wishlist"""
    try:
        from services.wishlist_service import wishlist_service
        
        success = wishlist_service.remove_from_wishlist(user_id, product_id)
        
        if success:
            return {"status": "removed"}
        else:
            raise HTTPException(status_code=404, detail="Item not found in wishlist")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/wishlist/{user_id}")
async def get_wishlist_endpoint(
    user_id: str,
    collection: Optional[str] = Query(None, description="Filter by collection")
):
    """Get user's wishlist"""
    try:
        from services.wishlist_service import wishlist_service
        
        items = wishlist_service.get_wishlist(user_id, collection)
        
        return {
            "user_id": user_id,
            "items": [item.dict() for item in items],
            "total_items": len(items)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/wishlist/summary/{user_id}")
async def get_wishlist_summary_endpoint(user_id: str):
    """Get wishlist summary statistics"""
    try:
        from services.wishlist_service import wishlist_service
        
        summary = wishlist_service.get_wishlist_summary(user_id)
        return summary.dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/wishlist/collections/{user_id}")
async def get_wishlist_collections(user_id: str):
    """Get list of wishlist collections for user"""
    try:
        from services.wishlist_service import wishlist_service
        
        collections = wishlist_service.get_collections(user_id)
        return {"collections": collections}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# PREFERENCES ENDPOINTS
# =============================================================================

@app.get("/preferences/{user_id}")
async def get_preferences_endpoint(user_id: str):
    """Get all user preferences"""
    try:
        from services.preferences_service import preferences_service
        
        prefs = preferences_service.get_preferences(user_id)
        return prefs.dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/preferences/financial/{user_id}")
async def update_financial_info_endpoint(user_id: str, info: "FinancialInfo"):
    """Update user's financial information"""
    try:
        from services.preferences_service import preferences_service
        from schemas.preferences import FinancialInfo
        
        preferences_service.update_financial_info(user_id, info)
        
        return {
            "status": "updated",
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/preferences/boycott/{user_id}")
async def add_brand_boycott_endpoint(user_id: str, boycott: "BrandBoycott"):
    """Add brand boycott"""
    try:
        from services.preferences_service import preferences_service
        from schemas.preferences import BrandBoycott
        
        boycott_id = preferences_service.add_boycott(user_id, boycott)
        
        return {
            "status": "added",
            "boycott_id": boycott_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/preferences/boycott/{user_id}/{brand}")
async def remove_brand_boycott_endpoint(user_id: str, brand: str):
    """Remove brand boycott"""
    try:
        from services.preferences_service import preferences_service
        
        success = preferences_service.remove_boycott(user_id, brand)
        
        if success:
            return {"status": "removed"}
        else:
            raise HTTPException(status_code=404, detail="Boycott not found")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/preferences/ethical/{user_id}")
async def update_ethical_preferences_endpoint(user_id: str, prefs: "EthicalPreferences"):
    """Update ethical preferences"""
    try:
        from services.preferences_service import preferences_service
        from schemas.preferences import EthicalPreferences
        
        preferences_service.update_ethical_preferences(user_id, prefs)
        
        return {"status": "updated"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/preferences/priority/{user_id}")
async def set_priority_endpoint(user_id: str, priority: "Priority"):
    """Set recommendation priority"""
    try:
        from services.preferences_service import preferences_service
        from schemas.preferences import Priority
        
        # If priority is a dict with 'priority' key, extract it
        if isinstance(priority, dict):
            priority_value = Priority(priority['priority'])
        else:
            priority_value = priority
        
        preferences_service.set_priority(user_id, priority_value)
        
        return {"status": "updated"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/preferences/budget-status/{user_id}")
async def check_budget_status_endpoint(
    user_id: str,
    category: str = Query(..., description="Product category"),
    amount: float = Query(..., description="Purchase amount")
):
    """Check if purchase fits within budget"""
    try:
        from services.preferences_service import preferences_service
        
        status = preferences_service.check_budget_status(user_id, category, amount)
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# IMAGE SEARCH ENDPOINTS
# =============================================================================

from fastapi import UploadFile, File


@app.post("/recommend/by-image")
async def search_by_image_endpoint(
    image: UploadFile = File(..., description="Product image file"),
    text_query: Optional[str] = Query(None, description="Optional text query for hybrid search"),
    max_results: int = Query(10, ge=1, le=50),
    min_similarity: float = Query(0.5, ge=0, le=1)
):
    """
    Search for products using an uploaded image
    
    Supports:
    - Pure visual search (image only)
    - Hybrid search (image + text)
    
    Example:
        curl -X POST http://localhost:8000/recommend/by-image \
          -F "image=@laptop.jpg" \
          -F "text_query=gaming laptop"
    """
    try:
        from services.image_search_service import image_search_service
        from PIL import Image
        import io
        
        # Read uploaded image
        image_bytes = await image.read()
        pil_image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if needed
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")
        
        # For demo purposes, we'll use a mock product database
        # In production, this would come from Qdrant
        product_embeddings = {}
        product_metadata = {}
        
        # TODO: Replace with actual Qdrant search
        # For now, return a placeholder response
        from schemas.image_search import ImageSearchResponse, VisualMatch
        
        response = ImageSearchResponse(
            matches=[
                VisualMatch(
                    product_id="demo_product_1",
                    product_name="Similar Product (Demo)",
                    similarity_score=0.85,
                    price=799.99,
                    category="Electronics",
                    brand="Demo Brand",
                    metadata={"note": "This is a demo response. Integrate with Qdrant for real results."}
                )
            ],
            total_matches=1,
            query_embedding_dims=512,
            search_time_ms=45.0,
            model_used="clip-vit-base-patch32"
        )
        
        return response.dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/recommend/by-image-url")
async def search_by_image_url_endpoint(
    image_url: str = Query(..., description="URL of product image"),
    text_query: Optional[str] = Query(None, description="Optional text query"),
    max_results: int = Query(10, ge=1, le=50),
    min_similarity: float = Query(0.5, ge=0, le=1)
):
    """
    Search for products using an image URL
    
    Example:
        GET /recommend/by-image-url?image_url=https://example.com/laptop.jpg&text_query=gaming
    """
    try:
        from services.image_search_service import image_search_service
        
        # Load image from URL
        pil_image = image_search_service.load_image_from_url(image_url)
        
        # Generate embedding
        embedding_result = image_search_service.encode_image(pil_image)
        
        # TODO: Search in Qdrant using embedding
        # For now, return demo response
        from schemas.image_search import ImageSearchResponse, VisualMatch
        
        response = ImageSearchResponse(
            matches=[
                VisualMatch(
                    product_id="demo_url_product",
                    product_name="Product from URL Search (Demo)",
                    similarity_score=0.88,
                    price=899.99,
                    category="Electronics",
                    brand="Demo Brand"
                )
            ],
            total_matches=1,
            query_embedding_dims=embedding_result.dimensions,
            search_time_ms=embedding_result.processing_time_ms + 10,
            model_used=embedding_result.model
        )
        
        return response.dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


@app.post("/image/encode")
async def encode_image_endpoint(
    image: UploadFile = File(..., description="Image to encode")
):
    """
    Generate CLIP embedding for an uploaded image
    
    Useful for:
    - Pre-computing embeddings
    - Testing image encoding
    - Debugging
    """
    try:
        from services.image_search_service import image_search_service
        from PIL import Image
        import io
        
        # Read and process image
        image_bytes = await image.read()
        pil_image = Image.open(io.BytesIO(image_bytes))
        
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")
        
        # Generate embedding
        embedding_result = image_search_service.encode_image(pil_image)
        
        return {
            "dimensions": embedding_result.dimensions,
            "model": embedding_result.model,
            "processing_time_ms": embedding_result.processing_time_ms,
            "embedding_preview": embedding_result.embedding[:10]  # First 10 values
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
