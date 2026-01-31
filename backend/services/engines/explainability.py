
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from models.schemas import (
    ScoredProduct,
    ParsedIntent,
    Recommendation,
    Product,
)


@dataclass
class ExplanationContext:
    """Context for generating explanations"""
    user_query: str
    intent: ParsedIntent
    total_candidates: int
    budget: Optional[float] = None


class ExplainabilityEngine:
    """
    Generates transparent, human-readable explanations.
    
    Explains:
    - Retrieval reason (why this product matched the search)
    - Ranking reason (why it scored high)
    - Evidence (concrete data points)
    - Alternatives (if product has limitations)
    """
    
    def __init__(self):
        pass
    
    def explain(
        self,
        scored_products: List[ScoredProduct],
        context: ExplanationContext,
    ) -> List[Recommendation]:
        """
        Generate explanations for scored products.
        
        Args:
            scored_products: Products with scores from re-ranking
            context: Query and intent context
            
        Returns:
            List of Recommendations with explanations
        """
        recommendations = []
        
        for i, scored in enumerate(scored_products):
            # Generate explanation components
            retrieval_reason = self._explain_retrieval(
                scored.product, context
            )
            ranking_reason = self._explain_ranking(
                scored, context, rank=i + 1
            )
            evidence = self._gather_evidence(scored.product)
            alternatives = self._suggest_alternatives(
                scored.product, context
            )
            
            # Combine into main explanation
            explanation = self._build_main_explanation(
                scored, context, retrieval_reason, ranking_reason
            )
            
            # Calculate confidence
            confidence = self._calculate_confidence(scored)
            
            recommendation = Recommendation(
                product=scored.product,
                final_score=scored.final_score,
                explanation=explanation,
                retrieval_reason=retrieval_reason,
                ranking_reason=ranking_reason,
                evidence=evidence,
                alternatives=alternatives,
                confidence=confidence,
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    def _explain_retrieval(
        self,
        product: Product,
        context: ExplanationContext,
    ) -> str:
        """Explain why this product was retrieved"""
        reasons = []
        
        # Category match
        if context.intent.category:
            if product.category.lower() == context.intent.category.lower():
                reasons.append(f"Matches your search for {context.intent.category}")
        
        # Price match
        if context.intent.max_price:
            if product.price <= context.intent.max_price:
                savings = context.intent.max_price - product.price
                reasons.append(f"Within your ${context.intent.max_price} budget (saves ${savings:.2f})")
        
        # Eco preference
        if context.intent.eco_friendly and product.eco_certified:
            reasons.append("Eco-certified as requested")
        
        # Brand preference
        if context.intent.brand_preferences:
            if product.brand in context.intent.brand_preferences:
                reasons.append(f"From preferred brand: {product.brand}")
        
        # Use case match
        if context.intent.use_case:
            if context.intent.use_case.lower() in product.description.lower():
                reasons.append(f"Suitable for {context.intent.use_case}")
        
        if not reasons:
            reasons.append("Semantically relevant to your search query")
        
        return " • ".join(reasons)
    
    def _explain_ranking(
        self,
        scored: ScoredProduct,
        context: ExplanationContext,
        rank: int,
    ) -> str:
        """Explain why this product ranks at this position"""
        factors = []
        
        # Semantic relevance
        if scored.semantic_score > 0.8:
            factors.append("Highly relevant to your query")
        elif scored.semantic_score > 0.6:
            factors.append("Good match for your search")
        
        # Value score
        if scored.value_score > 0.7:
            factors.append("Excellent value for money")
        elif scored.value_score > 0.5:
            factors.append("Good price-quality ratio")
        
        # Preference match
        if scored.preference_score > 0.7:
            factors.append("Matches most of your preferences")
        elif scored.preference_score > 0.5:
            factors.append("Aligns with some of your preferences")
        
        # Note: Behavior boost is applied but not explicitly mentioned
        # to preserve explainability and avoid exposing personalization details
            factors.append("Partially matches your preferences")
        
        # Review score
        if scored.review_score > 0.7:
            factors.append("Highly rated by other buyers")
        elif scored.review_score > 0.5:
            factors.append("Well-reviewed product")
        
        rank_text = ["Top", "Second", "Third"][min(rank - 1, 2)]
        
        if factors:
            return f"{rank_text} recommendation because: {', '.join(factors)}"
        else:
            return f"{rank_text} match based on overall relevance score"
    
    def _gather_evidence(self, product: Product) -> List[str]:
        """Gather concrete evidence for the recommendation"""
        evidence = []
        
        # Price evidence (in TND)
        evidence.append(f"Price: {product.price:,.2f} TND")
        
        # Rating evidence
        if product.rating > 0:
            stars = "★" * int(product.rating) + "☆" * (5 - int(product.rating))
            evidence.append(f"Rating: {stars} ({product.rating}/5)")
        
        # Reviews evidence
        if product.reviews_count > 0:
            evidence.append(f"Reviews: {product.reviews_count:,} customer reviews")
        
        # Eco certification
        if product.eco_certified:
            evidence.append("✓ Eco-certified product")
        
        # Availability
        if product.in_stock:
            evidence.append("✓ In stock")
        else:
            evidence.append("⚠ Currently out of stock")
        
        # Brand
        if product.brand:
            evidence.append(f"Brand: {product.brand}")
        
        # Store
        evidence.append(f"Available at: {product.store}")
        
        # Key specs (if available)
        if product.specs:
            for key, value in list(product.specs.items())[:3]:
                evidence.append(f"{key}: {value}")
        
        return evidence
    
    def _suggest_alternatives(
        self,
        product: Product,
        context: ExplanationContext,
    ) -> List[str]:
        """Suggest alternatives or considerations"""
        alternatives = []
        
        # Out of stock alternative
        if not product.in_stock:
            alternatives.append("Check other stores for availability")
            alternatives.append("Consider similar products in stock")
        
        # Budget stretch alternative
        if context.intent.max_price:
            if product.price > context.intent.max_price * 0.9:
                alternatives.append("Look for sales or discounts")
        
        # Eco alternative
        if context.intent.eco_friendly and not product.eco_certified:
            alternatives.append("Consider eco-certified alternatives")
        
        # Brand alternative
        if not product.brand or product.brand.lower() == "generic":
            alternatives.append("Check name-brand options for warranty")
        
        return alternatives
    
    def _build_main_explanation(
        self,
        scored: ScoredProduct,
        context: ExplanationContext,
        retrieval_reason: str,
        ranking_reason: str,
    ) -> str:
        """Build the main explanation text"""
        product = scored.product
        
        parts = []
        
        # Opening with confidence
        if scored.final_score > 0.8:
            parts.append(f"**Excellent match** for your search.")
        elif scored.final_score > 0.6:
            parts.append(f"**Good match** for what you're looking for.")
        else:
            parts.append(f"**Potential option** based on your criteria.")
        
        # Key selling points
        selling_points = []
        
        if context.intent.max_price and product.price < context.intent.max_price:
            savings = context.intent.max_price - product.price
            selling_points.append(f"${savings:.2f} under budget")
        
        if product.rating >= 4.5 and product.reviews_count > 100:
            selling_points.append("top-rated")
        
        if product.eco_certified:
            selling_points.append("eco-friendly")
        
        if selling_points:
            parts.append(f"Key highlights: {', '.join(selling_points)}.")
        
        # Score summary
        score_pct = int(scored.final_score * 100)
        parts.append(f"Overall match score: {score_pct}%")
        
        return " ".join(parts)
    
    def _calculate_confidence(self, scored: ScoredProduct) -> float:
        """Calculate recommendation confidence (0-1)"""
        # Based on score consistency
        scores = [
            scored.semantic_score,
            scored.value_score,
            scored.preference_score,
            scored.review_score,
        ]
        
        avg_score = sum(scores) / len(scores)
        variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
        
        # High average + low variance = high confidence
        confidence = avg_score * (1 - variance)
        
        return min(max(confidence, 0), 1)
    
    def generate_summary(
        self,
        recommendations: List[Recommendation],
        context: ExplanationContext,
    ) -> str:
        """Generate overall recommendation summary"""
        if not recommendations:
            return "No products found matching your criteria."
        
        top = recommendations[0]
        
        summary_parts = [
            f"Found {context.total_candidates} products matching your search.",
            f"Top recommendation: **{top.product.name}** at ${top.product.price:.2f}",
        ]
        
        if context.intent.max_price:
            if top.product.price < context.intent.max_price:
                savings = context.intent.max_price - top.product.price
                summary_parts.append(f"You save ${savings:.2f} compared to your budget.")
        
        return " ".join(summary_parts)
