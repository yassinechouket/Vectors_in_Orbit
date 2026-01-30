"""
Pydantic models for user tracking system
"""
from typing import Optional, Dict, List, Any, Tuple
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class TrackingAction(str, Enum):
    """Types of user actions to track"""
    SEARCH = "search"
    CLICK = "click"
    VIEW = "view"
    ADD_TO_CART = "add_to_cart"
    PURCHASE = "purchase"
    WISHLIST_ADD = "wishlist_add"


class SearchEvent(BaseModel):
    """Search event tracking"""
    user_id: str = Field(..., description="User identifier")
    query: str = Field(..., description="Search query text")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    results_count: int = Field(..., ge=0, description="Number of results returned")
    clicked_positions: List[int] = Field(default_factory=list, description="Positions clicked in results")
    device_type: str = Field(default="unknown", description="Device type: desktop, mobile, tablet")
    session_id: str = Field(..., description="Session identifier")
    filters_applied: Dict[str, Any] = Field(default_factory=dict, description="Filters used in search")


class ClickEvent(BaseModel):
    """Click event tracking"""
    user_id: str = Field(..., description="User identifier")
    product_id: str = Field(..., description="Product clicked")
    position: int = Field(..., ge=0, description="Position in results (0-indexed)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = Field(..., description="Source: search_results, recommendations, wishlist")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    session_id: Optional[str] = Field(None, description="Session identifier")


class ViewEvent(BaseModel):
    """Product view event tracking"""
    user_id: str = Field(..., description="User identifier")
    product_id: str = Field(..., description="Product viewed")
    duration_seconds: int = Field(..., ge=0, description="Time spent viewing")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    scroll_depth: Optional[float] = Field(None, ge=0, le=1, description="How far user scrolled (0-1)")
    interactions: List[str] = Field(default_factory=list, description="Elements interacted with")


class ConversionEvent(BaseModel):
    """Conversion event (add to cart, purchase)"""
    user_id: str = Field(..., description="User identifier")
    product_id: str = Field(..., description="Product ID")
    action: TrackingAction = Field(..., description="Type of conversion")
    price: Optional[float] = Field(None, ge=0, description="Transaction price")
    quantity: int = Field(1, ge=1, description="Quantity")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class UserInterestProfile(BaseModel):
    """Aggregated user interest profile from tracking data"""
    user_id: str = Field(..., description="User identifier")
    top_categories: List[Tuple[str, float]] = Field(
        default_factory=list,
        description="Top categories with affinity scores"
    )
    top_brands: List[Tuple[str, float]] = Field(
        default_factory=list,
        description="Top brands with affinity scores"
    )
    price_range: Tuple[float, float] = Field(
        default=(0, 10000),
        description="Typical price range (min, max)"
    )
    search_patterns: List[str] = Field(
        default_factory=list,
        description="Common search queries"
    )
    peak_activity_hours: List[int] = Field(
        default_factory=list,
        description="Hours of day when user is most active (0-23)"
    )
    interaction_count: int = Field(default=0, ge=0, description="Total interactions")
    confidence: float = Field(default=0.0, ge=0, le=1, description="Profile confidence (0-1)")
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "top_categories": [["Laptops", 0.45], ["Gaming", 0.32]],
                "top_brands": [["Dell", 0.38], ["Lenovo", 0.25]],
                "price_range": [500, 1200],
                "search_patterns": ["gaming laptop", "budget laptop"],
                "peak_activity_hours": [18, 19, 20],
                "interaction_count": 156,
                "confidence": 0.87
            }
        }


class TrackingStats(BaseModel):
    """Aggregated tracking statistics"""
    total_searches: int = Field(default=0)
    total_clicks: int = Field(default=0)
    total_views: int = Field(default=0)
    avg_click_position: float = Field(default=0.0)
    click_through_rate: float = Field(default=0.0, ge=0, le=1)
    avg_session_duration: float = Field(default=0.0, ge=0)
    conversion_rate: float = Field(default=0.0, ge=0, le=1)
