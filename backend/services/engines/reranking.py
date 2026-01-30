
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from models.schemas import (
    ProductCandidate,
    ScoredProduct,
    ParsedIntent,
    Product,
)


@dataclass
class RankingWeights:
    semantic: float = 0.45
    value: float = 0.25
    preference: float = 0.20
    review: float = 0.10
    
    def validate(self) -> bool:
        """Ensure weights sum to 1.0"""
        total = self.semantic + self.value + self.preference + self.review
        return abs(total - 1.0) < 0.01


class ReRankingEngine:
    """
    Re-ranks candidates using behavior-driven weighted scoring.
    
    Formula:
    final_score = semantic_score × 0.45 
                + value_score × 0.25 
                + preference_alignment × 0.20 
                + review_score × 0.10
    
    preference_alignment uses UserBehaviorProfile from FeedbackLoop.    
    Outputs top 3 products.
    """
    
    DEFAULT_WEIGHTS = RankingWeights()
    TOP_K = 3
    
    def __init__(self, weights: Optional[RankingWeights] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS
        
        if not self.weights.validate():
            raise ValueError("Ranking weights must sum to 1.0")
    
    def rerank(
        self,
        candidates: List[ProductCandidate],
        intent: ParsedIntent,
        top_k: Optional[int] = None,
        user_id: Optional[str] = None,
        feedback_loop: Optional[Any] = None,
    ) -> List[ScoredProduct]:
        """
        Production-quality re-ranking using behavior-driven scoring.
        
        NO artificial boosts - only real user behavior from FeedbackLoop.
        
        Args:
            candidates: Filtered product candidates
            intent: Parsed user intent for preference matching
            top_k: Number of top results (default: 3)
            user_id: Optional user ID for personalization via UserBehaviorProfile
            feedback_loop: Optional FeedbackLoop for behavior-driven scoring
            
        Returns:
            Top-K scored products with detailed scores
        """
        top_k = top_k or self.TOP_K
        scored_products = []
        behavior_profile = None
        if user_id and feedback_loop:
            behavior_profile = feedback_loop.get_behavior_profile(user_id)
        
        # Adjust weights based on priority
        weights = self.weights
        if intent.priority == "price":
            # When user wants "cheap", value (price) is most important
            semantic_weight = 0.20
            value_weight = 0.60  # Price dominates
            preference_weight = 0.10
            review_weight = 0.10
        elif intent.priority == "quality":
            # Quality priority - reviews and ratings matter more
            semantic_weight = 0.30
            value_weight = 0.15
            preference_weight = 0.20
            review_weight = 0.35
        else:
            # Balanced
            semantic_weight = weights.semantic
            value_weight = weights.value
            preference_weight = weights.preference
            review_weight = weights.review
        
        for candidate in candidates:
            semantic_score = self._normalize_semantic_score(candidate.combined_score)
            value_score = self._calculate_value_score(candidate.product, intent)
            review_score = self._calculate_review_score(candidate.product)
            
           
            preference_alignment_score = self._calculate_preference_alignment(
                candidate.product,
                intent,
                behavior_profile
            )
            
            # Use dynamic weights based on priority
            final_score = (
                semantic_score * semantic_weight +
                value_score * value_weight +
                preference_alignment_score * preference_weight +
                review_score * review_weight
            )
            
            
            final_score = max(0.0, min(1.0, final_score))
            
            scored = ScoredProduct(
                product=candidate.product,
                semantic_score=semantic_score,
                value_score=value_score,
                preference_score=preference_alignment_score,
                review_score=review_score,
                final_score=final_score,
            )
            scored_products.append(scored)
        
        
        scored_products.sort(key=lambda x: x.final_score, reverse=True)
        
        return scored_products[:top_k]
    
    def _normalize_semantic_score(self, score: float) -> float:
        """
        Normalize semantic similarity score to [0, 1].
        Qdrant cosine similarity is already in [-1, 1].
        """
        
        if score < 0:
            return (score + 1) / 2
        return min(score, 1.0)
    
    def _calculate_value_score(
        self,
        product: Product,
        intent: ParsedIntent,
    ) -> float:
        """
        Calculate value-for-money score.
        
        Considers:
        - Price efficiency relative to budget
        - Price-to-rating ratio
        - Deal quality indicators
        """
        score = 0.5  
        
        # When user wants "cheap", heavily prioritize lower prices
        if intent.priority == "price":
            # Find max price in dataset for normalization (use 10000 as reasonable max)
            max_reasonable_price = intent.max_price if intent.max_price else 10000
            
            # Lower price = higher score (inverse relationship)
            price_score = 1 - (product.price / max_reasonable_price)
            price_score = max(0, min(1, price_score))  # Clamp to [0, 1]
            
            # Price is the dominant factor when user says "cheap"
            return price_score * 0.9 + 0.1  # Range: [0.1, 1.0]
        
        if intent.max_price:
            price_ratio = product.price / intent.max_price
            
            if 0.5 <= price_ratio <= 0.8:
                # Sweet spot - good value
                score += 0.2
            else:
                score += (1 - price_ratio) * 0.2
        
        # Rating-to-price ratio
        if product.rating > 0 and product.price > 0:
            value_ratio = product.rating / (product.price / 100)
            score += min(value_ratio * 0.1, 0.3)
        
        return min(max(score, 0), 1)
    
    def _calculate_preference_alignment(
        self,
        product: Product,
        intent: ParsedIntent,
        behavior_profile: Optional[Any] = None,
    ) -> float:
        """
        Calculate preference alignment score using UserBehaviorProfile.
        
        This is the ONLY personalization layer - no artificial boosts.
        Uses real user behavior data from FeedbackLoop.
        
        Scoring components:
        - Category affinity (from past interactions)
        - Brand preference/avoidance (learned from feedback)
        - Price sensitivity alignment (behavioral)
        - Eco preference match (behavioral)
        - Intent-based preference matching
        
        Args:
            product: Product to score
            intent: User's current intent
            behavior_profile: UserBehaviorProfile from FeedbackLoop (if available)
            
        Returns:
            Preference alignment score in [0, 1]
        """
        score = 0.3  # Base score
        
        # INTENT-BASED SCORING (works for all users)
        matches = 0
        total_prefs = 0
        
        # Brand preference from intent - HIGH PRIORITY
        if intent.brand_preferences:
            total_prefs += 1
            if product.brand and product.brand.lower() in [
                b.lower() for b in intent.brand_preferences
            ]:
                matches += 1
                score += 0.35  # Strong boost for matching brand (e.g., MacBook -> Apple)
            else:
                score -= 0.15  # Penalty for non-matching brand when user specified preference
        
        # Eco preference from intent
        if intent.eco_friendly:
            total_prefs += 1
            if product.eco_certified:
                matches += 1
                score += 0.15
        
        # Category match from intent
        if intent.category:
            total_prefs += 1
            if product.category.lower() == intent.category.lower():
                matches += 1
                score += 0.10
        
        # Use case matching from intent
        if intent.use_case and product.description:
            total_prefs += 1
            if intent.use_case.lower() in product.description.lower():
                matches += 1
                score += 0.10
        
        # Feature preferences from intent
        if intent.preferences:
            for pref in intent.preferences:
                total_prefs += 1
                pref_lower = pref.lower()
                specs_str = str(product.specs).lower()
                desc_lower = product.description.lower()
                
                if pref_lower in specs_str or pref_lower in desc_lower:
                    matches += 1
                    score += 0.05
        
        # BEHAVIOR-BASED SCORING (only if profile exists)

        
        if behavior_profile is None:
            # Cold start: return intent-based score only
            return min(max(score, 0), 1)
        
        # Get confidence level (smooth scaling based on interaction count)
        confidence = behavior_profile.get_confidence()
        
        if confidence < 0.1:
            # Insufficient data - use intent-based score only
            return min(max(score, 0), 1)
        
        # Category affinity (learned from past interactions)
        if product.category in behavior_profile.category_affinity:
            affinity = behavior_profile.category_affinity[product.category]
            max_affinity = max(behavior_profile.category_affinity.values()) if behavior_profile.category_affinity else 1.0
            normalized_affinity = (affinity / max_affinity) * 0.15
            score += normalized_affinity * confidence
        
        # Brand preference (learned from feedback)
        if product.brand:
            brand_lower = product.brand.lower()
            
            # Check preferred brands
            if brand_lower in [b.lower() for b in behavior_profile.preferred_brands]:
                score += 0.15 * confidence
            
            # Check avoided brands (learned from skips/rejects)
            elif brand_lower in [b.lower() for b in behavior_profile.avoided_brands]:
                score -= 0.15 * confidence
        
        # Category-specific brand preferences (more accurate)
        if product.category in behavior_profile.category_profiles:
            cat_profile = behavior_profile.category_profiles[product.category]
            cat_confidence = behavior_profile.get_category_confidence(product.category)
            
            if product.brand:
                brand_lower = product.brand.lower()
                
                if brand_lower in [b.lower() for b in cat_profile.preferred_brands]:
                    score += 0.12 * cat_confidence
                elif brand_lower in [b.lower() for b in cat_profile.avoided_brands]:
                    score -= 0.12 * cat_confidence
            
            # Price alignment within category (learned average price)
            if cat_profile.avg_price > 0 and product.price > 0:
                price_diff_ratio = abs(product.price - cat_profile.avg_price) / cat_profile.avg_price
                
                # Reward products near user's typical price in this category
                if price_diff_ratio < 0.3:  # Within 30% of typical price
                    score += 0.10 * cat_confidence
                elif price_diff_ratio > 1.0:  # More than 2x typical price
                    score -= 0.05 * cat_confidence
        
        # Price sensitivity alignment (behavioral)
        if product.price > 0 and intent.max_price:
            price_ratio = product.price / intent.max_price
            
            # High price_sensitivity (0.7-1.0) = prefers premium/quality
            # Low price_sensitivity (0.0-0.3) = prefers budget
            if behavior_profile.price_sensitivity > 0.7:
                # Premium seeker - reward higher-priced quality items
                if price_ratio > 0.7:
                    score += 0.08 * confidence
                elif price_ratio < 0.3:
                    score -= 0.05 * confidence  # Penalize suspiciously cheap
            elif behavior_profile.price_sensitivity < 0.3:
                # Budget seeker - reward lower prices
                if price_ratio < 0.5:
                    score += 0.08 * confidence
                elif price_ratio > 0.9:
                    score -= 0.05 * confidence
        
        # Eco preference alignment (behavioral)
        if abs(behavior_profile.eco_interest) > 0.3:  # Strong eco preference
            if product.eco_certified and behavior_profile.eco_interest > 0:
                score += 0.10 * confidence
            elif not product.eco_certified and behavior_profile.eco_interest > 0.5:
                score -= 0.05 * confidence  # Penalize non-eco for eco seekers
        
        return min(max(score, 0), 1)
    
    def _calculate_review_score(self, product: Product) -> float:
        """
        Calculate review quality score.
        
        Combines rating and review count for social proof.
        """
        score = 0.3  # Base score
        
        # Rating contribution (0-5 scale)
        if product.rating > 0:
            # Normalize rating to [0, 0.5]
            rating_contribution = (product.rating / 5) * 0.5
            score += rating_contribution
        
        # Review count contribution (social proof)
        if product.reviews_count > 0:
            # Logarithmic scale for review count
            import math
            log_reviews = math.log10(product.reviews_count + 1)
            # Normalize: 1 review = 0, 1000 reviews = ~0.3
            count_contribution = min(log_reviews / 10, 0.3)
            score += count_contribution
        
        # Penalize low ratings
        if product.rating < 3.0 and product.reviews_count > 10:
            score -= 0.2
        
        return min(max(score, 0), 1)
    
    def explain_ranking(self, scored: ScoredProduct) -> Dict[str, Any]:
        """
        Generate explanation of ranking scores.
        
        Args:
            scored: Scored product to explain
            
        Returns:
            Dictionary with score breakdown
        """
        return {
            "final_score": round(scored.final_score, 3),
            "breakdown": {
                "semantic_similarity": {
                    "score": round(scored.semantic_score, 3),
                    "weight": self.weights.semantic,
                    "contribution": round(scored.semantic_score * self.weights.semantic, 3),
                },
                "value_for_money": {
                    "score": round(scored.value_score, 3),
                    "weight": self.weights.value,
                    "contribution": round(scored.value_score * self.weights.value, 3),
                },
                "preference_match": {
                    "score": round(scored.preference_score, 3),
                    "weight": self.weights.preference,
                    "contribution": round(scored.preference_score * self.weights.preference, 3),
                },
                "review_quality": {
                    "score": round(scored.review_score, 3),
                    "weight": self.weights.review,
                    "contribution": round(scored.review_score * self.weights.review, 3),
                },
            },
            "formula": "semantic×0.45 + value×0.25 + preference_alignment×0.20 + review×0.10",
        }
    
    def adjust_weights_for_priority(self, priority: str) -> RankingWeights:
        """
        Adjust ranking weights based on user priority.
        
        Maintains new ratios while shifting emphasis.
        
        Args:
            priority: User priority (price, quality, eco, balanced)
            
        Returns:
            Adjusted RankingWeights
        """
        if priority == "price":
            # Price-focused: increase value weight
            return RankingWeights(
                semantic=0.35,
                value=0.40,
                preference=0.15,
                review=0.10,
            )
        elif priority == "quality":
            # Quality-focused: increase review weight
            return RankingWeights(
                semantic=0.40,
                value=0.20,
                preference=0.20,
                review=0.20,
            )
        elif priority == "eco":
            # Eco-focused: increase preference weight (captures eco from behavior)
            return RankingWeights(
                semantic=0.35,
                value=0.20,
                preference=0.35,
                review=0.10,
            )
        else:
            # Balanced (default weights)
            return self.DEFAULT_WEIGHTS
