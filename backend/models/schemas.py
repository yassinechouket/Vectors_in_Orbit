"""
Data Models for the Recommendation Engine
==========================================
Clean, typed schemas for all workflow steps.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


# ============================================================
# ENUMS
# ============================================================

class FeedbackType(str, Enum):
    """Types of user feedback actions"""
    CLICK = "click"
    VIEW = "view"
    ADD_TO_CART = "add_to_cart"
    PURCHASE = "purchase"
    SKIP = "skip"
    REJECT = "reject"


class Priority(str, Enum):
    """User priority preferences"""
    PRICE = "price"
    QUALITY = "quality"
    ECO = "eco"
    PERFORMANCE = "performance"
    BRAND = "brand"


# ============================================================
# STEP 1: USER QUERY
# ============================================================

class UserQuery(BaseModel):
    """Raw user query input"""
    text: str = Field(..., description="Natural language query")
    user_id: Optional[str] = Field(None, description="User identifier for personalization")
    session_id: Optional[str] = Field(None, description="Session tracking")


# ============================================================
# STEP 2: QUERY UNDERSTANDING
# ============================================================

@dataclass
class ParsedIntent:
    """Structured intent extracted from user query"""
    category: Optional[str] = None
    max_price: Optional[float] = None
    min_price: Optional[float] = None
    eco_friendly: bool = False
    preferences: List[str] = field(default_factory=list)
    use_case: Optional[str] = None
    priority: str = "balanced"
    brand_preferences: List[str] = field(default_factory=list)
    excluded_brands: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "max_price": self.max_price,
            "min_price": self.min_price,
            "eco_friendly": self.eco_friendly,
            "preferences": self.preferences,
            "use_case": self.use_case,
            "priority": self.priority,
            "brand_preferences": self.brand_preferences,
            "excluded_brands": self.excluded_brands,
            "keywords": self.keywords,
        }


@dataclass
class QueryEmbedding:
    """Generated embeddings for search"""
    dense_vector: List[float]
    sparse_vector: Optional[Dict[str, float]] = None
    text_for_embedding: str = ""


# ============================================================
# STEP 3: QDRANT SEARCH
# ============================================================

@dataclass
class SearchFilters:
    """Filters for Qdrant payload filtering"""
    max_price: Optional[float] = None
    min_price: Optional[float] = None
    category: Optional[str] = None
    eco_certified: Optional[bool] = None
    in_stock: bool = True
    excluded_brands: List[str] = field(default_factory=list)
    
    def to_qdrant_filter(self) -> Dict[str, Any]:
        """Convert to Qdrant filter format"""
        must = []
        must_not = []
        
        if self.max_price is not None:
            must.append({
                "key": "price",
                "range": {"lte": self.max_price}
            })
        
        if self.min_price is not None:
            must.append({
                "key": "price", 
                "range": {"gte": self.min_price}
            })
        
        if self.category:
            must.append({
                "key": "category",
                "match": {"value": self.category.lower()}
            })
        
        if self.eco_certified:
            must.append({
                "key": "eco_certified",
                "match": {"value": True}
            })
        
        if self.in_stock:
            must.append({
                "key": "in_stock",
                "match": {"value": True}
            })
        
        for brand in self.excluded_brands:
            must_not.append({
                "key": "brand",
                "match": {"value": brand.lower()}
            })
        
        filter_dict = {}
        if must:
            filter_dict["must"] = must
        if must_not:
            filter_dict["must_not"] = must_not
            
        return filter_dict


# ============================================================
# STEP 4: PRODUCT MODELS
# ============================================================

@dataclass
class Product:
    """Base product model"""
    id: str
    name: str
    price: float
    category: str
    description: str
    store: str
    brand: Optional[str] = None
    rating: float = 0.0
    reviews_count: int = 0
    eco_certified: bool = False
    in_stock: bool = True
    specs: Dict[str, Any] = field(default_factory=dict)
    image_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "category": self.category,
            "description": self.description,
            "store": self.store,
            "brand": self.brand,
            "rating": self.rating,
            "reviews_count": self.reviews_count,
            "eco_certified": self.eco_certified,
            "in_stock": self.in_stock,
            "specs": self.specs,
            "image_url": self.image_url,
        }


@dataclass
class ProductCandidate:
    """Product with search scores"""
    product: Product
    semantic_score: float = 0.0
    sparse_score: float = 0.0
    combined_score: float = 0.0


@dataclass 
class ScoredProduct:
    """Product with final ranking scores"""
    product: Product
    semantic_score: float = 0.0
    value_score: float = 0.0
    preference_score: float = 0.0
    review_score: float = 0.0
    final_score: float = 0.0


# ============================================================
# STEP 5: FINANCIAL FILTERING
# ============================================================

@dataclass
class FinancialConstraints:
    """User financial constraints"""
    max_budget: Optional[float] = None
    preferred_price_range: Optional[tuple] = None
    value_priority: float = 0.5  # 0 = cheap, 1 = quality
    boycott_brands: List[str] = field(default_factory=list)


# ============================================================
# STEP 6 & 7: RECOMMENDATION OUTPUT
# ============================================================

@dataclass
class Recommendation:
    """Single recommendation with explanation"""
    product: Product
    final_score: float
    explanation: str
    retrieval_reason: str
    ranking_reason: str
    evidence: List[str]
    alternatives: List[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class BudgetInsight:
    """Budget analysis for recommendations"""
    total_budget: Optional[float]
    recommended_price: float
    savings: float
    value_rating: str
    comparison: str


@dataclass
class RecommendationResponse:
    """Complete recommendation response"""
    recommendations: List[Recommendation]
    budget_insight: Optional[BudgetInsight]
    query_understanding: ParsedIntent
    total_candidates: int
    processing_time_ms: float
    

# ============================================================
# STEP 8: FEEDBACK
# ============================================================

@dataclass
class CategoryProfile:
    """
    Category-specific user preferences to prevent cross-category pollution.
    Example: User's laptop brand preference shouldn't affect monitor choices.
    """
    category_name: str
    preferred_brands: List[str] = field(default_factory=list)
    avoided_brands: List[str] = field(default_factory=list)
    avg_price: float = 0.0
    price_range: tuple = field(default_factory=lambda: (0.0, 0.0))
    interaction_count: int = 0


@dataclass
class SessionContext:
    """
    Current browsing session context for contextual recommendations.
    Captures short-term intent and behavior patterns.
    """
    session_id: str
    
    # Recent queries in this session
    recent_queries: List[str] = field(default_factory=list)
    
    # Products viewed in this session
    viewed_products: List[str] = field(default_factory=list)
    
    # Time context
    time_of_day: str = "unknown"  # morning, afternoon, evening, night
    
    # Device context
    device_type: str = "unknown"  # mobile, tablet, desktop
    
    # Referrer/source
    referrer: Optional[str] = None
    
    # Session duration (minutes)
    session_duration: float = 0.0


@dataclass
class UserBehaviorProfile:
    """
    Enhanced user behavior profile with category isolation and temporal decay.
    Used ONLY for soft re-ranking adjustments, not for search/retrieval.
    
    Privacy-friendly: Only stores aggregated tendencies, not raw events.
    """
    user_id: str
    
    # Global price sensitivity (0.0 = budget-focused, 1.0 = premium)
    price_sensitivity: float = 0.5
    
    # Category-specific preferences (isolates laptop vs monitor preferences)
    category_profiles: Dict[str, CategoryProfile] = field(default_factory=dict)
    
    # Legacy: Global preferred brands (kept for backward compatibility)
    preferred_brands: List[str] = field(default_factory=list)
    
    # Top 3 avoided brands (from skips/rejects)
    avoided_brands: List[str] = field(default_factory=list)
    
    # Eco-friendliness interest (-1.0 = no interest, 1.0 = strong preference)
    eco_interest: float = 0.0
    
    # Category affinity scores (top 5 categories)
    category_affinity: Dict[str, float] = field(default_factory=dict)
    
    # Interaction count (used to determine confidence)
    interaction_count: int = 0
    
    # Last update timestamp
    last_updated: Optional[str] = None
    
    def get_confidence(self) -> float:
        """
        Calculate confidence level based on interactions using smooth sigmoid curve.
        
        Benefits over hard thresholds:
        - Smooth transition (no sudden jumps)
        - 50% confidence at ~30 interactions
        - Asymptotically approaches 1.0
        
        Returns:
            Confidence score in [0, 1]
        """
        import math
        # Sigmoid curve: smooth growth with interactions
        # Formula: 1 / (1 + e^(-(x - midpoint) / steepness))
        # Midpoint = 30 interactions for 50% confidence
        # Steepness = 15 (controls how quickly confidence grows)
        return 1 / (1 + math.exp(-(self.interaction_count - 30) / 15))
    
    def get_category_confidence(self, category: str) -> float:
        """
        Get confidence for a specific category.
        
        Args:
            category: Product category name
            
        Returns:
            Category-specific confidence in [0, 1]
        """
        import math
        if category not in self.category_profiles:
            return 0.0
        
        count = self.category_profiles[category].interaction_count
        # Same sigmoid, but per-category
        return 1 / (1 + math.exp(-(count - 15) / 8))


@dataclass
class UserFeedback:
    """User interaction feedback"""
    user_id: str
    product_id: str
    action: FeedbackType
    timestamp: str
    session_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
