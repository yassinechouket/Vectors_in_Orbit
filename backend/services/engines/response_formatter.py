
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from models.schemas import (
    Recommendation,
    RecommendationResponse,
    BudgetInsight,
    ParsedIntent,
)


@dataclass
class UIProduct:
    """Product formatted for UI display"""
    id: str
    name: str
    price: float
    formatted_price: str
    category: str
    brand: Optional[str]
    rating: float
    rating_stars: str
    reviews_count: int
    reviews_formatted: str
    image_url: Optional[str]
    store: str
    eco_badge: bool
    in_stock: bool


@dataclass
class UIRecommendation:
    """Single recommendation formatted for UI"""
    product: UIProduct
    rank: int
    score: float
    score_label: str
    explanation: str
    retrieval_reason: str
    ranking_reason: str
    evidence: List[str]
    alternatives: List[str]
    confidence: float
    confidence_label: str
    actions: Dict[str, str]


@dataclass
class UIBudgetInsight:
    """Budget analysis for UI"""
    has_budget: bool
    budget: Optional[float]
    recommended_price: float
    savings: float
    savings_percentage: float
    value_rating: str
    comparison_text: str
    budget_status: str  # "under", "at", "over"


@dataclass
class UIResponse:
    """Complete response formatted for UI"""
    success: bool
    recommendations: List[UIRecommendation]
    budget_insight: Optional[UIBudgetInsight]
    query_understanding: Dict[str, Any]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ResponseFormatter:
    """
    Formats recommendation responses for UI consumption.
    
    Provides:
    - Human-friendly formatting
    - Action button URLs
    - Budget impact visualization
    - Accessibility-friendly labels
    """
    
    DEFAULT_IMAGE_URL = "https://images.unsplash.com/photo-1550009158-9ebf69173e03?w=800&auto=format&fit=crop"

    def __init__(self, base_url: str = ""):
        """
        Initialize formatter.
        
        Args:
            base_url: Base URL for action buttons
        """
        self.base_url = base_url
    
    def format(
        self,
        recommendations: List[Recommendation],
        intent: ParsedIntent,
        total_candidates: int,
        processing_time_ms: float,
    ) -> UIResponse:
        """
        Format recommendations for UI.
        
        Args:
            recommendations: Recommendations with explanations
            intent: Parsed user intent
            total_candidates: Total products searched
            processing_time_ms: Processing time
            
        Returns:
            UIResponse ready for frontend
        """
        # Format each recommendation
        ui_recommendations = []
        for i, rec in enumerate(recommendations):
            ui_rec = self._format_recommendation(rec, rank=i + 1)
            ui_recommendations.append(ui_rec)
        
        # Format budget insight
        budget_insight = None
        if intent.max_price and recommendations:
            budget_insight = self._format_budget_insight(
                recommendations, intent.max_price
            )
        
        # Format query understanding
        query_understanding = self._format_query_understanding(intent)
        
        # Build metadata
        metadata = {
            "total_candidates": total_candidates,
            "results_count": len(recommendations),
            "processing_time_ms": round(processing_time_ms, 2),
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        return UIResponse(
            success=True,
            recommendations=ui_recommendations,
            budget_insight=budget_insight,
            query_understanding=query_understanding,
            metadata=metadata,
        )
    
    def _format_recommendation(
        self,
        rec: Recommendation,
        rank: int,
    ) -> UIRecommendation:
        """Format single recommendation"""
        product = rec.product
        
        # Format product
        ui_product = UIProduct(
            id=product.id,
            name=product.name,
            price=product.price,
            formatted_price=f"${product.price:,.2f}",
            category=product.category.title(),
            brand=product.brand,
            rating=product.rating,
            rating_stars=self._format_stars(product.rating),
            reviews_count=product.reviews_count,
            reviews_formatted=self._format_reviews_count(product.reviews_count),
            image_url=product.image_url or self.DEFAULT_IMAGE_URL,
            store=product.store,
            eco_badge=product.eco_certified,
            in_stock=product.in_stock,
        )
        
        # Determine score label
        score_label = self._get_score_label(rec.final_score)
        confidence_label = self._get_confidence_label(rec.confidence)
        
        # Build action URLs
        actions = self._build_actions(product.id, product.store)
        
        return UIRecommendation(
            product=ui_product,
            rank=rank,
            score=round(rec.final_score, 2),
            score_label=score_label,
            explanation=rec.explanation,
            retrieval_reason=rec.retrieval_reason,
            ranking_reason=rec.ranking_reason,
            evidence=rec.evidence,
            alternatives=rec.alternatives,
            confidence=round(rec.confidence, 2),
            confidence_label=confidence_label,
            actions=actions,
        )
    
    def _format_budget_insight(
        self,
        recommendations: List[Recommendation],
        budget: float,
    ) -> UIBudgetInsight:
        """Format budget analysis"""
        if not recommendations:
            return UIBudgetInsight(
                has_budget=True,
                budget=budget,
                recommended_price=0,
                savings=0,
                savings_percentage=0,
                value_rating="N/A",
                comparison_text="No products found",
                budget_status="under",
            )
        
        top = recommendations[0]
        recommended_price = top.product.price
        savings = budget - recommended_price
        savings_pct = (savings / budget) * 100 if budget > 0 else 0
        
        # Determine budget status
        if savings > 0:
            budget_status = "under"
        elif savings == 0:
            budget_status = "at"
        else:
            budget_status = "over"
        
        # Determine value rating
        if savings_pct > 20:
            value_rating = "Excellent Value"
        elif savings_pct > 10:
            value_rating = "Good Value"
        elif savings_pct > 0:
            value_rating = "Fair Value"
        elif savings_pct > -10:
            value_rating = "At Budget"
        else:
            value_rating = "Over Budget"
        
        # Build comparison text
        if savings > 0:
            comparison_text = f"Save ${savings:.2f} ({savings_pct:.0f}% under budget)"
        elif savings == 0:
            comparison_text = "Exactly at your budget"
        else:
            comparison_text = f"${abs(savings):.2f} over budget"
        
        return UIBudgetInsight(
            has_budget=True,
            budget=budget,
            recommended_price=recommended_price,
            savings=savings,
            savings_percentage=round(savings_pct, 1),
            value_rating=value_rating,
            comparison_text=comparison_text,
            budget_status=budget_status,
        )
    
    def _format_query_understanding(self, intent: ParsedIntent) -> Dict[str, Any]:
        """Format parsed intent for display"""
        return {
            "category": intent.category or "All categories",
            "budget": f"${intent.max_price:,.2f}" if intent.max_price else "No limit",
            "eco_friendly": intent.eco_friendly,
            "priority": intent.priority.title(),
            "use_case": intent.use_case or "General",
            "preferences": intent.preferences,
            "brand_preferences": intent.brand_preferences,
            "excluded_brands": intent.excluded_brands,
        }
    
    def _format_stars(self, rating: float) -> str:
        """Format rating as star string"""
        full_stars = int(rating)
        half_star = 1 if rating - full_stars >= 0.5 else 0
        empty_stars = 5 - full_stars - half_star
        
        return "★" * full_stars + "⯪" * half_star + "☆" * empty_stars
    
    def _format_reviews_count(self, count: int) -> str:
        """Format review count for display"""
        if count >= 1000000:
            return f"{count / 1000000:.1f}M reviews"
        elif count >= 1000:
            return f"{count / 1000:.1f}K reviews"
        elif count == 1:
            return "1 review"
        else:
            return f"{count} reviews"
    
    def _get_score_label(self, score: float) -> str:
        """Get human-readable score label"""
        if score >= 0.9:
            return "Perfect Match"
        elif score >= 0.8:
            return "Excellent Match"
        elif score >= 0.7:
            return "Great Match"
        elif score >= 0.6:
            return "Good Match"
        elif score >= 0.5:
            return "Fair Match"
        else:
            return "Possible Match"
    
    def _get_confidence_label(self, confidence: float) -> str:
        """Get confidence level label"""
        if confidence >= 0.8:
            return "High Confidence"
        elif confidence >= 0.6:
            return "Medium Confidence"
        else:
            return "Low Confidence"
    
    def _build_actions(self, product_id: str, store: str) -> Dict[str, str]:
        """Build action button URLs"""
        return {
            "view": f"{self.base_url}/product/{product_id}",
            "compare": f"{self.base_url}/compare?ids={product_id}",
            "buy": f"{self.base_url}/redirect/{store}/{product_id}",
            "save": f"{self.base_url}/wishlist/add/{product_id}",
        }
    
    def format_error(
        self,
        error: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Format error response"""
        return {
            "success": False,
            "error": error,
            "details": details,
            "timestamp": datetime.utcnow().isoformat(),
        }
