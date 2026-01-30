"""
Pydantic models for wishlist/bookmark system
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class WishlistItem(BaseModel):
    """Item in user's wishlist"""
    user_id: str = Field(..., description="User identifier")
    product_id: str = Field(..., description="Product identifier")
    collection: str = Field(default="default", description="Wishlist collection name")
    added_at: datetime = Field(default_factory=datetime.utcnow)
    original_price: Optional[float] = Field(None, ge=0, description="Price when added")
    current_price: Optional[float] = Field(None, ge=0, description="Current price")
    notes: Optional[str] = Field(None, description="User notes")
    priority: int = Field(default=0, ge=0, le=5, description="Priority level (0-5)")


class PriceDropAlert(BaseModel):
    """Alert for price drop on wishlist item"""
    product_id: str = Field(..., description="Product identifier")
    product_name: str = Field(..., description="Product name")
    original_price: float = Field(..., ge=0)
    current_price: float = Field(..., ge=0)
    drop_percentage: float = Field(..., ge=0, le=100)
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    user_notified: bool = Field(default=False)


class WishlistSummary(BaseModel):
    """Summary statistics for a wishlist"""
    total_items: int = Field(default=0)
    total_value: float = Field(default=0.0)
    avg_price: float = Field(default=0.0)
    common_categories: List[str] = Field(default_factory=list)
    preferred_brands: List[str] = Field(default_factory=list)
    price_range: tuple[float, float] = Field(default=(0, 0))
