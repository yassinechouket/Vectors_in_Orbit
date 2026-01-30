#!/usr/bin/env python3
"""
API Integration Example for Intelligent Recommendation Engine

This shows how to integrate the recommendation engine into FastAPI endpoints
for your e-commerce application.
"""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime

from services.engines import IntelligentRecommendationEngine
from services.engines.response_formatter import RecommendationResponse
from helpers.logger import get_logger

logger = get_logger(__name__)

# Pydantic models for API
class ProductSpecs(BaseModel):
    """Product specifications"""
    cpu: Optional[str] = None
    ram: Optional[str] = None
    storage: Optional[str] = None
    screen: Optional[str] = None
    battery: Optional[str] = None

class Product(BaseModel):
    """Product model for API"""
    name: str
    price: float
    category: str
    brand: str
    rating: Optional[float] = 0.0
    reviews: Optional[int] = 0
    specs: Optional[ProductSpecs] = None
    is_available: bool = True
    is_eco_friendly: bool = False
    semantic_similarity: Optional[float] = None
    description: Optional[str] = ""

class RecommendationRequest(BaseModel):
    """Request model for intelligent recommendations"""
    user_query: str = Field(..., description="Natural language query from user")
    vector_candidates: Optional[List[Product]] = Field(None, description="Pre-retrieved candidates from vector DB")
    max_results: Optional[int] = Field(3, description="Maximum recommendations to return")
    user_context: Optional[Dict[str, Any]] = Field(None, description="Additional user context")

class LegacyRecommendationRequest(BaseModel):
    """Legacy request model for backward compatibility"""
    viewed_product: Product
    candidate_products: List[Product] 
    user_preferences: Dict[str, Any]

class SimpleRecommendationResponse(BaseModel):
    """Simplified response for quick integration"""
    recommendations: List[Dict[str, Any]]
    processing_time: float
    total_candidates: int
    budget_insight: Optional[str] = None

# Initialize FastAPI app
app = FastAPI(
    title="Intelligent Recommendation Engine API",
    description="Context-aware e-commerce recommendations with explainable AI",
    version="1.0.0"
)

# Global recommendation engine instance
recommendation_engine = IntelligentRecommendationEngine()

@app.post("/api/recommendations/intelligent", response_model=Dict[str, Any])
async def get_intelligent_recommendations(request: RecommendationRequest):
    """
    Get intelligent recommendations using the 6-step workflow.
    
    This endpoint provides the full power of the intelligent recommendation engine:
    - Query understanding and intent extraction
    - Context-aware filtering and ranking 
    - Explainable AI with detailed reasoning
    - Budget optimization insights
    """
    try:
        logger.info(f"Intelligent recommendation request: '{request.user_query[:100]}...'")
        
        # Convert Pydantic models to dicts for processing
        vector_candidates = None
        if request.vector_candidates:
            vector_candidates = [product.dict() for product in request.vector_candidates]
        
        # Get recommendations using the intelligent engine
        response = await recommendation_engine.get_intelligent_recommendations(
            user_query=request.user_query,
            vector_candidates=vector_candidates,
            max_results=request.max_results
        )
        
        # Convert dataclass response to dict for JSON serialization
        response_dict = {
            "top_recommendations": [
                {
                    "product_name": rec.product_name,
                    "price": rec.price,
                    "key_specs": rec.key_specs,
                    "final_score": rec.final_score,
                    "explanation": rec.explanation,
                    "confidence": rec.confidence,
                    "value_proposition": rec.value_proposition
                }
                for rec in response.top_recommendations
            ],
            "alternatives": response.alternatives,
            "budget_insight": response.budget_insight,
            "query_understanding": {
                "category": response.query_understanding.category,
                "max_price": response.query_understanding.max_price,
                "min_price": response.query_understanding.min_price,
                "eco_friendly": response.query_understanding.eco_friendly,
                "use_case": response.query_understanding.use_case,
                "priority": response.query_understanding.priority,
                "brand_preferences": response.query_understanding.brand_preferences,
                "excluded_brands": response.query_understanding.excluded_brands,
                "semantic_query": response.query_understanding.semantic_query,
                "constraints": response.query_understanding.constraints
            },
            "total_candidates": response.total_candidates,
            "processing_time": response.processing_time,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Intelligent recommendations completed in {response.processing_time:.3f}s")
        return response_dict
        
    except Exception as e:
        logger.error(f"Error in intelligent recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Recommendation processing failed: {str(e)}")

@app.post("/api/recommendations/simple", response_model=SimpleRecommendationResponse)
async def get_simple_recommendations(request: RecommendationRequest):
    """
    Get simplified recommendations for quick integration.
    
    This endpoint provides a streamlined response format that's easier to integrate
    into existing UIs while still leveraging the intelligent engine's capabilities.
    """
    try:
        # Get full intelligent recommendations
        vector_candidates = None
        if request.vector_candidates:
            vector_candidates = [product.dict() for product in request.vector_candidates]
        
        response = await recommendation_engine.get_intelligent_recommendations(
            user_query=request.user_query,
            vector_candidates=vector_candidates,
            max_results=request.max_results
        )
        
        # Simplify the response
        simple_recommendations = []
        for rec in response.top_recommendations:
            simple_recommendations.append({
                "name": rec.product_name,
                "price": rec.price,
                "score": round(rec.final_score, 1),
                "reason": rec.explanation,
                "specs": rec.key_specs
            })
        
        # Generate simple budget insight
        budget_insight = None
        if response.budget_insight and 'recommended_price' in response.budget_insight:
            savings = response.budget_insight.get('money_saved', 0)
            if savings > 0:
                budget_insight = f"Save ${savings:.2f} with our top recommendation"
            else:
                budget_insight = response.budget_insight.get('value_comparison', 'Good value recommendation')
        
        return SimpleRecommendationResponse(
            recommendations=simple_recommendations,
            processing_time=response.processing_time,
            total_candidates=response.total_candidates,
            budget_insight=budget_insight
        )
        
    except Exception as e:
        logger.error(f"Error in simple recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Recommendation processing failed: {str(e)}")

@app.post("/api/recommendations/legacy", response_model=Dict[str, Any])
async def get_legacy_recommendations(request: LegacyRecommendationRequest):
    """
    Legacy endpoint for backward compatibility.
    
    This maintains compatibility with existing code while leveraging 
    the new intelligent engine under the hood.
    """
    try:
        from services.recommendation_service import RecommendationService
        
        legacy_service = RecommendationService()
        
        recommendations = await legacy_service.get_recommendations(
            viewed_product=request.viewed_product.dict(),
            candidate_products=[p.dict() for p in request.candidate_products],
            user_preferences=request.user_preferences
        )
        
        return {
            "recommendations": recommendations,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "legacy_compatible"
        }
        
    except Exception as e:
        logger.error(f"Error in legacy recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Legacy recommendation processing failed: {str(e)}")

@app.get("/api/recommendations/analyze-query")
async def analyze_query(
    query: str = Query(..., description="User query to analyze"),
    detailed: bool = Query(False, description="Return detailed analysis")
):
    """
    Analyze a user query to understand intent and extract structured information.
    
    Useful for debugging and understanding how the engine interprets queries.
    """
    try:
        query_analysis = recommendation_engine.analyze_user_query(query)
        
        analysis_result = {
            "original_query": query,
            "category": query_analysis.category,
            "max_price": query_analysis.max_price,
            "min_price": query_analysis.min_price,
            "eco_friendly": query_analysis.eco_friendly,
            "use_case": query_analysis.use_case,
            "priority": query_analysis.priority,
            "brand_preferences": query_analysis.brand_preferences,
            "excluded_brands": query_analysis.excluded_brands,
            "semantic_query": query_analysis.semantic_query,
            "constraints": query_analysis.constraints
        }
        
        if detailed:
            analysis_result["analysis_confidence"] = "High" if query_analysis.category else "Medium"
            analysis_result["detected_budget"] = query_analysis.max_price is not None
            analysis_result["detected_preferences"] = len(query_analysis.brand_preferences or []) > 0
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"Error analyzing query: {e}")
        raise HTTPException(status_code=500, detail=f"Query analysis failed: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Intelligent Recommendation Engine",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/recommendations/demo")
async def demo_recommendations():
    """
    Demo endpoint that shows the recommendation engine with sample data.
    
    Useful for testing and demonstrating capabilities without external data.
    """
    # Sample products for demo
    sample_products = [
        Product(
            name="MacBook Air M2",
            price=1199.0,
            category="laptop",
            brand="Apple",
            rating=4.6,
            reviews=2847,
            specs=ProductSpecs(
                cpu="Apple M2",
                ram="8GB",
                storage="256GB SSD",
                screen="13.6-inch Retina",
                battery="18 hours"
            ),
            is_eco_friendly=True,
            semantic_similarity=0.92,
            description="Supercharged by M2 chip for incredible performance"
        ),
        Product(
            name="Dell XPS 13 Plus", 
            price=999.0,
            category="laptop",
            brand="Dell",
            rating=4.3,
            reviews=1243,
            specs=ProductSpecs(
                cpu="Intel i7-1260P",
                ram="16GB", 
                storage="512GB SSD",
                screen="13.4-inch OLED",
                battery="12 hours"
            ),
            is_eco_friendly=False,
            semantic_similarity=0.89,
            description="Premium ultrabook with stunning OLED display"
        )
    ]
    
    # Demo queries to test
    demo_queries = [
        "Best laptop for coding under $1200",
        "Eco-friendly laptop for business use",
        "Affordable student laptop under $800"
    ]
    
    results = {}
    
    for query in demo_queries:
        try:
            response = await recommendation_engine.get_intelligent_recommendations(
                user_query=query,
                vector_candidates=[p.dict() for p in sample_products],
                max_results=2
            )
            
            results[query] = {
                "recommendations": [
                    {
                        "name": rec.product_name,
                        "price": rec.price,
                        "score": round(rec.final_score, 1),
                        "explanation": rec.explanation
                    }
                    for rec in response.top_recommendations
                ],
                "processing_time": response.processing_time
            }
        except Exception as e:
            results[query] = {"error": str(e)}
    
    return {
        "demo_results": results,
        "sample_products_count": len(sample_products),
        "timestamp": datetime.utcnow().isoformat()
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.error(f"HTTP {exc.status_code}: {exc.detail}")
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Intelligent Recommendation Engine API")
    print("📚 Available endpoints:")
    print("   POST /api/recommendations/intelligent - Full intelligent recommendations")
    print("   POST /api/recommendations/simple - Simplified recommendations")
    print("   POST /api/recommendations/legacy - Legacy compatible endpoint")
    print("   GET  /api/recommendations/analyze-query - Query analysis")
    print("   GET  /api/recommendations/demo - Demo with sample data")
    print("   GET  /api/health - Health check")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")