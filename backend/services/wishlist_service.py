"""
Wishlist Service

Manages user wishlists with price tracking and recommendations
"""
from typing import List, Optional, Dict
from collections import Counter
from datetime import datetime

from schemas.wishlist import (
    WishlistItem,
    PriceDropAlert,
    WishlistSummary
)


class WishlistService:
    """Manages user wishlists and provides wishlist-based features"""
    
    def __init__(self):
        # In-memory storage (replace with database in production)
        self.wishlist_items: Dict[str, List[WishlistItem]] = {}  # user_id -> items
        self.price_history: Dict[str, List[float]] = {}  # product_id -> price history
    
    def add_to_wishlist(self, item: WishlistItem) -> str:
        """
        Add item to user's wishlist
        
        Args:
            item: WishlistItem to add
            
        Returns:
            Item ID
        """
        if item.user_id not in self.wishlist_items:
            self.wishlist_items[item.user_id] = []
        
        # Check if already in wishlist
        existing = next(
            (i for i in self.wishlist_items[item.user_id] 
             if i.product_id == item.product_id and i.collection == item.collection),
            None
        )
        
        if existing:
            # Update existing item
            existing.notes = item.notes or existing.notes
            existing.priority = item.priority
            return f"wishlist_updated_{item.product_id}"
        
        self.wishlist_items[item.user_id].append(item)
        
        # Track initial price
        if item.current_price:
            if item.product_id not in self.price_history:
                self.price_history[item.product_id] = []
            self.price_history[item.product_id].append(item.current_price)
        
        return f"wishlist_{len(self.wishlist_items[item.user_id])}"
    
    def remove_from_wishlist(self, user_id: str, product_id: str) -> bool:
        """
        Remove item from wishlist
        
        Args:
            user_id: User identifier
            product_id: Product to remove
            
        Returns:
            True if removed, False if not found
        """
        if user_id not in self.wishlist_items:
            return False
        
        original_len = len(self.wishlist_items[user_id])
        self.wishlist_items[user_id] = [
            item for item in self.wishlist_items[user_id]
            if item.product_id != product_id
        ]
        
        return len(self.wishlist_items[user_id]) < original_len
    
    def get_wishlist(
        self, 
        user_id: str, 
        collection: Optional[str] = None
    ) -> List[WishlistItem]:
        """
        Get user's wishlist
        
        Args:
            user_id: User identifier
            collection: Optional collection filter
            
        Returns:
            List of WishlistItems
        """
        if user_id not in self.wishlist_items:
            return []
        
        items = self.wishlist_items[user_id]
        
        if collection:
            items = [item for item in items if item.collection == collection]
        
        return items
    
    def get_collections(self, user_id: str) -> List[str]:
        """Get list of collection names for user"""
        if user_id not in self.wishlist_items:
            return []
        
        return list(set(item.collection for item in self.wishlist_items[user_id]))
    
    def get_wishlist_summary(self, user_id: str) -> WishlistSummary:
        """
        Get summary statistics for user's wishlist
        
        Args:
            user_id: User identifier
            
        Returns:
            WishlistSummary
        """
        items = self.get_wishlist(user_id)
        summary = WishlistSummary()
        
        if not items:
            return summary
        
        summary.total_items = len(items)
        
        # Calculate  values
        prices = [item.current_price for item in items if item.current_price]
        if prices:
            summary.total_value = sum(prices)
            summary.avg_price = summary.total_value / len(prices)
            summary.price_range = (min(prices), max(prices))
        
        # Extract categories (from product_id format: category_brand_id)
        categories = [item.product_id.split('_')[0] for item in items]
        category_counts = Counter(categories)
        summary.common_categories = [cat for cat, _ in category_counts.most_common(5)]
        
        # Extract brands
        brands = []
        for item in items:
            parts = item.product_id.split('_')
            if len(parts) >= 2:
                brands.append(parts[1])
        brand_counts = Counter(brands)
        summary.preferred_brands = [brand for brand, _ in brand_counts.most_common(5)]
        
        return summary
    
    def check_price_drops(
        self, 
        user_id: str,
        current_prices: Dict[str, float],
        threshold_percent: float = 5.0
    ) -> List[PriceDropAlert]:
        """
        Check for price drops on wishlist items
        
        Args:
            user_id: User identifier
            current_prices: Dict of product_id -> current_price
            threshold_percent: Minimum drop percentage to alert
            
        Returns:
            List of PriceDropAlerts
        """
        items = self.get_wishlist(user_id)
        alerts = []
        
        for item in items:
            if item.product_id not in current_prices:
                continue
            
            current_price = current_prices[item.product_id]
            original_price = item.original_price or item.current_price
            
            if not original_price:
                continue
            
            drop_percent = ((original_price - current_price) / original_price) * 100
            
            if drop_percent >= threshold_percent:
                # Extract product name from product_id or use placeholder
                product_name = item.product_id.replace('_', ' ').title()
                
                alert = PriceDropAlert(
                    product_id=item.product_id,
                    product_name=product_name,
                    original_price=original_price,
                    current_price=current_price,
                    drop_percentage=drop_percent
                )
                alerts.append(alert)
                
                # Update item's current price
                item.current_price = current_price
        
        return alerts
    
    def get_wishlist_based_query(self, user_id: str) -> str:
        """
        Generate a search query based on wishlist items
        
        Args:
            user_id: User identifier
            
        Returns:
            Search query string
        """
        summary = self.get_wishlist_summary(user_id)
        
        if not summary.total_items:
            return ""
        
        parts = []
        
        if summary.common_categories:
            parts.append(f"Products in {', '.join(summary.common_categories[:2])}")
        
        if summary.preferred_brands:
            parts.append(f"similar to {', '.join(summary.preferred_brands[:2])}")
        
        if summary.avg_price > 0:
            parts.append(f"around ${summary.avg_price:.0f}")
        
        return " ".join(parts) if parts else "recommended products"


# Singleton instance
wishlist_service = WishlistService()
