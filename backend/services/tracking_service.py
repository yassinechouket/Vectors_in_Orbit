"""
User Tracking Service

Tracks user behavior (searches, clicks, views) and builds interest profiles
for improved personalization.
"""
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import math

from schemas.tracking import (
    SearchEvent,
    ClickEvent,
    ViewEvent,
    ConversionEvent,
    UserInterestProfile,
    TrackingStats,
    TrackingAction
)


class TrackingService:
    """Manages user behavior tracking and interest profiling"""
    
    def __init__(self):
        # In-memory storage (replace with database in production)
        self.search_events: List[SearchEvent] = []
        self.click_events: List[ClickEvent] = []
        self.view_events: List[ViewEvent] = []
        self.conversion_events: List[ConversionEvent] = []
        
        # Cached profiles
        self._interest_profiles: Dict[str, UserInterestProfile] = {}
        
        # Temporal decay parameters
        self.DECAY_HALF_LIFE_DAYS = 30
        self.DECAY_CONSTANT = math.log(2) / self.DECAY_HALF_LIFE_DAYS
    
    def track_search(self, event: SearchEvent) -> str:
        """
        Track a search event
        
        Args:
            event: SearchEvent to track
            
        Returns:
            Event ID
        """
        self.search_events.append(event)
        # Invalidate cached profile
        self._interest_profiles.pop(event.user_id, None)
        return f"search_{len(self.search_events)}"
    
    def track_click(self, event: ClickEvent) -> str:
        """
        Track a click event
        
        Args:
            event: ClickEvent to track
            
        Returns:
            Event ID
        """
        self.click_events.append(event)
        # Invalidate cached profile
        self._interest_profiles.pop(event.user_id, None)
        return f"click_{len(self.click_events)}"
    
    def track_view(self, event: ViewEvent) -> str:
        """
        Track a view event
        
        Args:
            event: ViewEvent to track
            
        Returns:
            Event ID
        """
        self.view_events.append(event)
        return f"view_{len(self.view_events)}"
    
    def track_conversion(self, event: ConversionEvent) -> str:
        """
        Track a conversion event (add to cart, purchase)
        
        Args:
            event: ConversionEvent to track
            
        Returns:
            Event ID
        """
        self.conversion_events.append(event)
        # Invalidate cached profile
        self._interest_profiles.pop(event.user_id, None)
        return f"conversion_{len(self.conversion_events)}"
    
    def extract_user_interests(self, user_id: str) -> UserInterestProfile:
        """
        Extract user interest profile from tracking data
        
        Args:
            user_id: User identifier
            
        Returns:
            UserInterestProfile with aggregated interests
        """
        # Check cache
        if user_id in self._interest_profiles:
            profile = self._interest_profiles[user_id]
            # Return if recent (within 1 hour)
            if datetime.utcnow() - profile.last_updated < timedelta(hours=1):
                return profile
        
        # Build profile from scratch
        profile = self._build_interest_profile(user_id)
        
        # Cache it
        self._interest_profiles[user_id] = profile
        
        return profile
    
    def get_tracking_stats(self, user_id: Optional[str] = None) -> TrackingStats:
        """
        Get aggregate tracking statistics
        
        Args:
            user_id: Optional user to filter by
            
        Returns:
            TrackingStats
        """
        if user_id:
            searches = [e for e in self.search_events if e.user_id == user_id]
            clicks = [e for e in self.click_events if e.user_id == user_id]
            views = [e for e in self.view_events if e.user_id == user_id]
            conversions = [e for e in self.conversion_events if e.user_id == user_id]
        else:
            searches = self.search_events
            clicks = self.click_events
            views = self.view_events
            conversions = self.conversion_events
        
        stats = TrackingStats()
        stats.total_searches = len(searches)
        stats.total_clicks = len(clicks)
        stats.total_views = len(views)
        
        # Click-through rate
        if stats.total_searches > 0:
            searches_with_clicks = len(set(e.session_id for e in clicks))
            stats.click_through_rate = searches_with_clicks / stats.total_searches
        
        # Average click position
        if stats.total_clicks > 0:
            stats.avg_click_position = sum(e.position for e in clicks) / stats.total_clicks
        
        # Average session duration
        if views:
            stats.avg_session_duration = sum(e.duration_seconds for e in views) / len(views)
        
        # Conversion rate
        if stats.total_clicks > 0:
            purchases = [e for e in conversions if e.action == TrackingAction.PURCHASE]
            stats.conversion_rate = len(purchases) / stats.total_clicks
        
        return stats
    
    def _build_interest_profile(self, user_id: str) -> UserInterestProfile:
        """Build comprehensive interest profile for user"""
        profile = UserInterestProfile(user_id=user_id)
        
        # Get user events
        user_searches = [e for e in self.search_events if e.user_id == user_id]
        user_clicks = [e for e in self.click_events if e.user_id == user_id]
        user_conversions = [e for e in self.conversion_events if e.user_id == user_id]
        
        if not user_clicks and not user_searches:
            return profile  # No data yet
        
        profile.interaction_count = len(user_clicks) + len(user_conversions)
        
        # Extract top categories
        profile.top_categories = self._extract_top_categories(user_clicks, user_conversions)
        
        # Extract top brands
        profile.top_brands = self._extract_top_brands(user_clicks, user_conversions)
        
        # Extract price range
        profile.price_range = self._extract_price_range(user_clicks, user_conversions)
        
        # Extract search patterns
        profile.search_patterns = self._extract_search_patterns(user_searches)
        
        # Extract peak activity hours
        profile.peak_activity_hours = self._extract_peak_hours(user_clicks, user_searches)
        
        # Calculate confidence
        profile.confidence = self._calculate_confidence(profile.interaction_count)
        
        profile.last_updated = datetime.utcnow()
        
        return profile
    
    def _extract_top_categories(
        self,
        clicks: List[ClickEvent],
        conversions: List[ConversionEvent]
    ) -> List[Tuple[str, float]]:
        """Extract top categories with temporal decay"""
        category_scores = defaultdict(float)
        
        now = datetime.utcnow()
        
        # Weight clicks
        for click in clicks:
            category = click.context.get('category')
            if category:
                days_old = (now - click.timestamp).days
                weight = math.exp(-days_old * self.DECAY_CONSTANT)
                category_scores[category] += weight * 1.0  # Base weight for clicks
        
        # Weight conversions higher
        for conv in conversions:
            category = conv.product_id.split('_')[0]  # Assume format: category_brand_id
            days_old = (now - conv.timestamp).days
            weight = math.exp(-days_old * self.DECAY_CONSTANT)
            
            if conv.action == TrackingAction.PURCHASE:
                category_scores[category] += weight * 5.0  # High weight for purchases
            elif conv.action == TrackingAction.ADD_TO_CART:
                category_scores[category] += weight * 2.0
            else:
                category_scores[category] += weight * 1.5
        
        # Normalize scores
        total = sum(category_scores.values())
        if total > 0:
            category_scores = {k: v/total for k, v in category_scores.items()}
        
        # Return top 5
        return sorted(category_scores.items(), key=lambda x: x[1], reverse=True)[:5]
    
    def _extract_top_brands(
        self,
        clicks: List[ClickEvent],
        conversions: List[ConversionEvent]
    ) -> List[Tuple[str, float]]:
        """Extract top brands with temporal decay"""
        brand_scores = defaultdict(float)
        
        now = datetime.utcnow()
        
        # Weight clicks
        for click in clicks:
            brand = click.context.get('brand')
            if brand:
                days_old = (now - click.timestamp).days
                weight = math.exp(-days_old * self.DECAY_CONSTANT)
                brand_scores[brand] += weight * 1.0
        
        # Weight conversions
        for conv in conversions:
            # Extract brand from product_id (format: category_brand_id)
            parts = conv.product_id.split('_')
            if len(parts) >= 2:
                brand = parts[1]
                days_old = (now - conv.timestamp).days
                weight = math.exp(-days_old * self.DECAY_CONSTANT)
                
                if conv.action == TrackingAction.PURCHASE:
                    brand_scores[brand] += weight * 5.0
                else:
                    brand_scores[brand] += weight * 2.0
        
        # Normalize
        total = sum(brand_scores.values())
        if total > 0:
            brand_scores = {k: v/total for k, v in brand_scores.items()}
        
        return sorted(brand_scores.items(), key=lambda x: x[1], reverse=True)[:5]
    
    def _extract_price_range(
        self,
        clicks: List[ClickEvent],
        conversions: List[ConversionEvent]
    ) -> Tuple[float, float]:
        """Extract typical price range from user behavior"""
        prices = []
        
        # From clicks
        for click in clicks:
            price = click.context.get('price')
            if price:
                prices.append(float(price))
        
        # From conversions
        for conv in conversions:
            if conv.price:
                prices.append(conv.price)
        
        if not prices:
            return (0, 10000)  # Default range
        
        # Use 10th and 90th percentile
        prices.sort()
        p10_idx = max(0, int(len(prices) * 0.1))
        p90_idx = min(len(prices) - 1, int(len(prices) * 0.9))
        
        return (prices[p10_idx], prices[p90_idx])
    
    def _extract_search_patterns(self, searches: List[SearchEvent]) -> List[str]:
        """Extract common search patterns"""
        query_counts = Counter(e.query.lower() for e in searches if e.query)
        
        # Return top 10 most common queries
        return [query for query, _ in query_counts.most_common(10)]
    
    def _extract_peak_hours(
        self,
        clicks: List[ClickEvent],
        searches: List[SearchEvent]
    ) -> List[int]:
        """Extract peak activity hours (0-23)"""
        hour_counts = Counter()
        
        for click in clicks:
            hour_counts[click.timestamp.hour] += 1
        
        for search in searches:
            hour_counts[search.timestamp.hour] += 1
        
        if not hour_counts:
            return []
        
        # Return top 3 hours
        return [hour for hour, _ in hour_counts.most_common(3)]
    
    def _calculate_confidence(self, interaction_count: int) -> float:
        """
        Calculate confidence score using sigmoid function
        
        More interactions = higher confidence, plateaus at ~100 interactions
        """
        # Sigmoid: confidence = 1 / (1 + e^(-(x-30)/15))
        return 1 / (1 + math.exp(-(interaction_count - 30) / 15))


# Singleton instance
tracking_service = TrackingService()
