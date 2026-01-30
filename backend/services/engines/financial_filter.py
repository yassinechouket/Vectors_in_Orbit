
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from models.schemas import (
    ProductCandidate,
    ParsedIntent,
    FinancialConstraints,
    Product,
)


@dataclass
class FilterResult:
    """Result of financial filtering"""
    candidates: List[ProductCandidate]
    filtered_count: int
    filter_reasons: Dict[str, int]


class FinancialFilter:
    """
    Applies financial and business rule filtering.
    
    Responsibilities:
    - Remove items over budget
    - Apply user constraints (boycott brands, availability)
    - Consider value-for-money
    - Reduce ~20 candidates to ~10
    """
    
    # Budget buffer for "under $X" queries (show items slightly under)
    BUDGET_BUFFER = 0.95  # Show items up to 95% of max budget by default
    
    # Maximum candidates to pass through
    MAX_CANDIDATES = 10
    
    def __init__(self):
        self.filter_stats = {}
    
    def filter(
        self,
        candidates: List[ProductCandidate],
        intent: ParsedIntent,
        constraints: Optional[FinancialConstraints] = None,
    ) -> FilterResult:
        """
        Apply financial filtering to candidates.
        
        Args:
            candidates: Products from Qdrant search
            intent: Parsed user intent
            constraints: Additional user constraints
            
        Returns:
            FilterResult with filtered candidates
        """
        filter_reasons = {
            "over_budget": 0,
            "under_min_price": 0,
            "excluded_brand": 0,
            "out_of_stock": 0,
            "boycott_brand": 0,
        }
        
        filtered = []
        
        for candidate in candidates:
            product = candidate.product
            
            # Check budget constraint
            if intent.max_price and product.price > intent.max_price:
                filter_reasons["over_budget"] += 1
                continue
            
            # Check minimum price
            if intent.min_price and product.price < intent.min_price:
                filter_reasons["under_min_price"] += 1
                continue
            
            # Check excluded brands from query
            if intent.excluded_brands:
                if product.brand and product.brand.lower() in [
                    b.lower() for b in intent.excluded_brands
                ]:
                    filter_reasons["excluded_brand"] += 1
                    continue
            
            # Check availability
            if not product.in_stock:
                filter_reasons["out_of_stock"] += 1
                continue
            
            # Check additional constraints
            if constraints:
                if constraints.boycott_brands:
                    if product.brand and product.brand.lower() in [
                        b.lower() for b in constraints.boycott_brands
                    ]:
                        filter_reasons["boycott_brand"] += 1
                        continue
                
                # Apply stricter budget from constraints
                if constraints.max_budget:
                    if product.price > constraints.max_budget:
                        filter_reasons["over_budget"] += 1
                        continue
            
            # Calculate value score for sorting
            candidate.value_score = self._calculate_value_score(
                product, intent, constraints
            )
            
            filtered.append(candidate)
        
        # Sort by combined score + value score
        filtered.sort(
            key=lambda c: c.combined_score * 0.7 + getattr(c, 'value_score', 0) * 0.3,
            reverse=True
        )
        
        # Limit to MAX_CANDIDATES
        final_candidates = filtered[:self.MAX_CANDIDATES]
        
        return FilterResult(
            candidates=final_candidates,
            filtered_count=len(candidates) - len(final_candidates),
            filter_reasons=filter_reasons,
        )
    
    def _calculate_value_score(
        self,
        product: Product,
        intent: ParsedIntent,
        constraints: Optional[FinancialConstraints],
    ) -> float:
        """
        Calculate value-for-money score.
        
        Considers:
        - Price relative to budget
        - Rating/reviews ratio
        - Feature match to preferences
        """
        score = 0.5  # Base score
        
        # Price efficiency (lower price = higher score if budget-conscious)
        if intent.max_price:
            price_ratio = product.price / intent.max_price
            if intent.priority == "price":
                # Reward lower prices more
                score += (1 - price_ratio) * 0.3
            else:
                # Slight penalty for being too cheap (quality concern)
                if price_ratio < 0.5:
                    score -= 0.1
                else:
                    score += (1 - price_ratio) * 0.15
        
        # Rating bonus
        if product.rating > 0:
            rating_bonus = (product.rating - 3) / 2 * 0.2  # -0.2 to +0.2
            score += rating_bonus
        
        # Reviews count bonus (social proof)
        if product.reviews_count > 100:
            score += 0.1
        elif product.reviews_count > 500:
            score += 0.15
        elif product.reviews_count > 1000:
            score += 0.2
        
        # Preference match bonus
        if intent.eco_friendly and product.eco_certified:
            score += 0.15
        
        # Brand preference bonus
        if intent.brand_preferences:
            if product.brand and product.brand.lower() in [
                b.lower() for b in intent.brand_preferences
            ]:
                score += 0.2
        
        return min(max(score, 0), 1)  # Clamp to [0, 1]
    
    def apply_affordability_filter(
        self,
        candidates: List[ProductCandidate],
        target_price: float,
        tolerance: float = 0.2,
    ) -> List[ProductCandidate]:
        """
        Filter candidates within a price tolerance of target.
        
        Args:
            candidates: Products to filter
            target_price: Target price point
            tolerance: Acceptable deviation (default 20%)
            
        Returns:
            Filtered candidates within price range
        """
        min_price = target_price * (1 - tolerance)
        max_price = target_price * (1 + tolerance)
        
        return [
            c for c in candidates
            if min_price <= c.product.price <= max_price
        ]
    
    def get_budget_alternatives(
        self,
        candidates: List[ProductCandidate],
        budget: float,
        count: int = 3,
    ) -> List[ProductCandidate]:
        """
        Get alternatives for users who might stretch their budget.
        
        Returns products slightly over budget with high value scores.
        """
        over_budget = [
            c for c in candidates
            if c.product.price > budget and c.product.price <= budget * 1.25
        ]
        
        # Sort by value score (assuming calculated)
        over_budget.sort(
            key=lambda c: getattr(c, 'value_score', 0),
            reverse=True
        )
        
        return over_budget[:count]
