from typing import List, Dict, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import json

from models.schemas import UserFeedback, FeedbackType

if TYPE_CHECKING:
    from models.schemas import UserBehaviorProfile


@dataclass
class CategoryPreference:
    """Category-specific preference tracking"""
    brands: Dict[str, float] = field(default_factory=dict)
    total_spent: float = 0.0
    purchase_count: int = 0
    interaction_count: int = 0


@dataclass
class UserPreferences:
    """Learned user preferences from feedback with temporal decay support"""
    user_id: str
    preferred_categories: Dict[str, float] = field(default_factory=dict)
    preferred_brands: Dict[str, float] = field(default_factory=dict)
    
    # Category-specific preferences
    category_preferences: Dict[str, CategoryPreference] = field(default_factory=dict)
    
    preferred_price_range: Optional[tuple] = None
    eco_preference: float = 0.0  # -1 to 1
    quality_preference: float = 0.0  # -1 (budget) to 1 (premium)
    interaction_count: int = 0
    last_updated: Optional[datetime] = None


@dataclass
class ProductStats:
    """Aggregated product statistics"""
    product_id: str
    views: int = 0
    clicks: int = 0
    add_to_cart: int = 0
    purchases: int = 0
    skips: int = 0
    rejects: int = 0
    
    @property
    def ctr(self) -> float:
        """Click-through rate"""
        if self.views == 0:
            return 0.0
        return self.clicks / self.views
    
    @property
    def conversion_rate(self) -> float:
        """Purchase conversion rate"""
        if self.clicks == 0:
            return 0.0
        return self.purchases / self.clicks


class FeedbackLoop:
    """
    Enhanced feedback loop with temporal decay and category isolation.
    
    Features:
    - Track user interactions with timestamps
    - Learn preferences with temporal decay (recent > old)
    - Category-specific learning (laptop prefs != monitor prefs)
    - Collaborative filtering signals
    - Analytics and insights
    """
    
    # Temporal decay: half-life in days (30 days = preference decays by 50%)
    TEMPORAL_HALF_LIFE = 30.0
    
    # Weight for different actions
    ACTION_WEIGHTS = {
        FeedbackType.VIEW: 0.1,
        FeedbackType.CLICK: 0.3,
        FeedbackType.ADD_TO_CART: 0.6,
        FeedbackType.PURCHASE: 1.0,
        FeedbackType.SKIP: -0.1,
        FeedbackType.REJECT: -0.5,
    }
    
    def __init__(self):
        # In-memory storage (replace with database in production)
        self._user_preferences: Dict[str, UserPreferences] = {}
        self._product_stats: Dict[str, ProductStats] = {}
        self._feedback_history: List[UserFeedback] = []
    
    def record_feedback(self, feedback: UserFeedback) -> bool:
        """
        Record user interaction feedback.
        
        Args:
            feedback: User feedback event
            
        Returns:
            Success status
        """
        try:
            # Store feedback
            self._feedback_history.append(feedback)
            
            # Update product stats
            self._update_product_stats(feedback)
            
            # Update user preferences
            self._update_user_preferences(feedback)
            
            return True
        except Exception as e:
            print(f"Error recording feedback: {e}")
            return False
    
    def _update_product_stats(self, feedback: UserFeedback):
        """Update product-level statistics"""
        product_id = feedback.product_id
        
        if product_id not in self._product_stats:
            self._product_stats[product_id] = ProductStats(product_id=product_id)
        
        stats = self._product_stats[product_id]
        
        if feedback.action == FeedbackType.VIEW:
            stats.views += 1
        elif feedback.action == FeedbackType.CLICK:
            stats.clicks += 1
        elif feedback.action == FeedbackType.ADD_TO_CART:
            stats.add_to_cart += 1
        elif feedback.action == FeedbackType.PURCHASE:
            stats.purchases += 1
        elif feedback.action == FeedbackType.SKIP:
            stats.skips += 1
        elif feedback.action == FeedbackType.REJECT:
            stats.rejects += 1
    
    def _update_user_preferences(self, feedback: UserFeedback):
        """Learn user preferences with temporal decay and category isolation"""
        import math
        
        user_id = feedback.user_id
        
        if user_id not in self._user_preferences:
            self._user_preferences[user_id] = UserPreferences(user_id=user_id)
        
        prefs = self._user_preferences[user_id]
        base_weight = self.ACTION_WEIGHTS.get(feedback.action, 0)
        
        # Apply temporal decay: recent interactions matter more
        try:
            timestamp = datetime.fromisoformat(feedback.timestamp)
            days_old = (datetime.utcnow() - timestamp).days
            # Exponential decay: weight = base_weight * e^(-days_old * ln(2) / half_life)
            decay_factor = math.exp(-days_old * math.log(2) / self.TEMPORAL_HALF_LIFE)
            weight = base_weight * decay_factor
        except (ValueError, TypeError):
            # Fallback if timestamp parsing fails
            weight = base_weight
        
        # Extract context from feedback
        context = feedback.context
        category = context.get("category")
        brand = context.get("brand")
        
        # Update global category preference
        if category:
            current = prefs.preferred_categories.get(category, 0)
            prefs.preferred_categories[category] = current + weight
            
            # Update category-specific preferences (isolation)
            if category not in prefs.category_preferences:
                prefs.category_preferences[category] = CategoryPreference()
            
            cat_prefs = prefs.category_preferences[category]
            cat_prefs.interaction_count += 1
            
            # Track brand within this category
            if brand:
                current_brand = cat_prefs.brands.get(brand, 0)
                cat_prefs.brands[brand] = current_brand + weight
            
            # Track price within category
            price = context.get("price", 0)
            if price > 0 and feedback.action == FeedbackType.PURCHASE:
                cat_prefs.total_spent += price
                cat_prefs.purchase_count += 1
        
        # Update global brand preference (backward compatibility)
        if brand:
            current = prefs.preferred_brands.get(brand, 0)
            prefs.preferred_brands[brand] = current + weight
        
        # Update eco preference
        if context.get("eco_certified"):
            prefs.eco_preference += weight * 0.1
            prefs.eco_preference = max(-1, min(1, prefs.eco_preference))
        
        # Update quality/price preference
        price = context.get("price", 0)
        if price > 0:
            # Positive weight on expensive items = quality preference
            budget = context.get("user_budget", price)
            price_ratio = price / budget if budget > 0 else 0.5
            
            if weight > 0:
                if price_ratio > 0.8:
                    prefs.quality_preference += 0.1
                elif price_ratio < 0.5:
                    prefs.quality_preference -= 0.1
            
            prefs.quality_preference = max(-1, min(1, prefs.quality_preference))
        
        prefs.interaction_count += 1
        prefs.last_updated = datetime.utcnow()
    
    def get_user_preferences(self, user_id: str) -> Optional[UserPreferences]:
        """Get learned preferences for a user"""
        return self._user_preferences.get(user_id)
    
    def get_behavior_profile(self, user_id: str) -> Optional['UserBehaviorProfile']:
        """
        Compute enhanced behavior profile with category isolation.
        This is used ONLY for soft re-ranking adjustments, not search.
        
        Args:
            user_id: User identifier
            
        Returns:
            UserBehaviorProfile with category-specific tendencies or None if insufficient data
        """
        from models.schemas import UserBehaviorProfile, CategoryProfile
        
        prefs = self.get_user_preferences(user_id)
        if not prefs or prefs.interaction_count < 5:
            return None  # Need minimum interactions
        
        # Build category-specific profiles
        category_profiles = {}
        for cat_name, cat_prefs in prefs.category_preferences.items():
            if cat_prefs.interaction_count < 2:
                continue  # Skip categories with too few interactions
            
            # Get top 3 preferred brands in this category
            preferred = sorted(
                cat_prefs.brands.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            preferred_brands = [b for b, score in preferred if score > 0]
            
            # Get avoided brands in this category
            avoided = sorted(
                cat_prefs.brands.items(),
                key=lambda x: x[1]
            )[:3]
            avoided_brands = [b for b, score in avoided if score < -0.2]
            
            # Calculate average price and range in category
            avg_price = cat_prefs.total_spent / cat_prefs.purchase_count if cat_prefs.purchase_count > 0 else 0.0
            
            category_profiles[cat_name] = CategoryProfile(
                category_name=cat_name,
                preferred_brands=preferred_brands,
                avoided_brands=avoided_brands,
                avg_price=avg_price,
                interaction_count=cat_prefs.interaction_count
            )
        
        # Extract global top 3 preferred brands (backward compatibility)
        preferred_brands = sorted(
            prefs.preferred_brands.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        preferred_brands = [brand for brand, _ in preferred_brands if _ > 0]
        
        # Extract global avoided brands
        avoided_brands = sorted(
            prefs.preferred_brands.items(),
            key=lambda x: x[1]
        )[:3]
        avoided_brands = [brand for brand, score in avoided_brands if score < -0.2]
        
        # Extract top 5 categories
        top_categories = dict(sorted(
            prefs.preferred_categories.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5])
        
        # Normalize price sensitivity to 0-1 range
        price_sensitivity = (prefs.quality_preference + 1) / 2
        
        return UserBehaviorProfile(
            user_id=user_id,
            price_sensitivity=price_sensitivity,
            category_profiles=category_profiles,
            preferred_brands=preferred_brands,
            avoided_brands=avoided_brands,
            eco_interest=prefs.eco_preference,
            category_affinity=top_categories,
            interaction_count=prefs.interaction_count,
            last_updated=prefs.last_updated.isoformat() if prefs.last_updated else None
        )
    
    def get_product_stats(self, product_id: str) -> Optional[ProductStats]:
        """Get statistics for a specific product"""
        return self._product_stats.get(product_id)
    
    def get_analytics(self) -> Dict[str, Any]:
        """Get system-wide analytics"""
        total_feedback = len(self._feedback_history)
        total_users = len(self._user_preferences)
        total_products = len(self._product_stats)
        
        # Calculate overall metrics
        if total_products > 0:
            avg_ctr = sum(
                s.ctr for s in self._product_stats.values()
            ) / total_products
            avg_conversion = sum(
                s.conversion_rate for s in self._product_stats.values()
            ) / total_products
        else:
            avg_ctr = 0
            avg_conversion = 0
        
        # Get top products
        top_products = sorted(
            self._product_stats.values(),
            key=lambda x: x.purchases,
            reverse=True,
        )[:10]
        
        # Action breakdown
        action_counts = defaultdict(int)
        for fb in self._feedback_history:
            action_counts[fb.action.value] += 1
        
        return {
            "total_feedback_events": total_feedback,
            "unique_users": total_users,
            "tracked_products": total_products,
            "average_ctr": round(avg_ctr, 4),
            "average_conversion_rate": round(avg_conversion, 4),
            "action_breakdown": dict(action_counts),
            "top_products": [
                {
                    "product_id": p.product_id,
                    "purchases": p.purchases,
                    "ctr": round(p.ctr, 4),
                }
                for p in top_products
            ],
        }
    
    def get_product_stats(self, product_id: str) -> Optional[ProductStats]:
        """Get statistics for a specific product"""
        return self._product_stats.get(product_id)
    
    def export_feedback(self) -> List[Dict[str, Any]]:
        """Export feedback history for analysis"""
        return [
            {
                "user_id": fb.user_id,
                "product_id": fb.product_id,
                "action": fb.action.value,
                "timestamp": fb.timestamp,
                "context": fb.context,
            }
            for fb in self._feedback_history
        ]
    
    def decay_old_preferences(self, days: int = 30):
        """
        Apply decay to old preferences.
        Should be run periodically.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        for prefs in self._user_preferences.values():
            if prefs.last_updated and prefs.last_updated < cutoff:
                # Decay category preferences
                for cat in prefs.preferred_categories:
                    prefs.preferred_categories[cat] *= self.DECAY_FACTOR
                
                # Decay brand preferences
                for brand in prefs.preferred_brands:
                    prefs.preferred_brands[brand] *= self.DECAY_FACTOR
                
                # Decay eco preference toward neutral
                prefs.eco_preference *= self.DECAY_FACTOR
                prefs.quality_preference *= self.DECAY_FACTOR
