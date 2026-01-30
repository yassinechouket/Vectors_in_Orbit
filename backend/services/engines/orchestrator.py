import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from models.schemas import (
    UserQuery,
    ParsedIntent,
    ProductCandidate,
    ScoredProduct,
    Recommendation,
    RecommendationResponse,
    FinancialConstraints,
    UserFeedback,
    FeedbackType,
    Product,
)

from services.qdrant.client import QdrantManager
from services.qdrant.hybrid_search import HybridSearchEngine
from services.engines.query_understanding import QueryUnderstandingEngine
from services.engines.financial_filter import FinancialFilter
from services.engines.reranking import ReRankingEngine
from services.engines.explainability import ExplainabilityEngine, ExplanationContext
from services.engines.response_formatter import ResponseFormatter, UIResponse
from services.engines.feedback_loop import FeedbackLoop


@dataclass
class PipelineConfig:
    """Configuration for the recommendation pipeline"""
    top_k_search: int = 20      # Step 3: Qdrant search results
    top_k_filter: int = 10      # Step 4: After financial filtering
    top_k_results: int = 3      # Step 5: Final recommendations
    enable_feedback: bool = True
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333


class RecommendationOrchestrator:
    def __init__(self, config: Optional[PipelineConfig] = None):
        """
        Initialize the orchestrator with all engines.
        
        Args:
            config: Pipeline configuration
        """
        self.config = config or PipelineConfig()
        
        # Initialize components
        self._init_components()
    
    def _init_components(self):
        """Initialize all pipeline components"""
        # Step 2: Query Understanding
        self.query_engine = QueryUnderstandingEngine()
        
        # Step 3: Qdrant Search
        self.qdrant_manager = QdrantManager(
            host=self.config.qdrant_host,
            port=self.config.qdrant_port,
        )
        self.search_engine = HybridSearchEngine(self.qdrant_manager.client)
        
        # Step 4: Financial Filter
        self.financial_filter = FinancialFilter()
        
        # Step 5: Re-Ranking
        self.reranking_engine = ReRankingEngine()
        
        # Step 6: Explainability
        self.explainability_engine = ExplainabilityEngine()
        
        # Step 7: Response Formatter
        self.response_formatter = ResponseFormatter()
        
        # Step 8: Feedback Loop
        if self.config.enable_feedback:
            self.feedback_loop = FeedbackLoop()
        else:
            self.feedback_loop = None
    
    async def recommend(
        self,
        query: str,
        user_id: Optional[str] = None,
        constraints: Optional[FinancialConstraints] = None,
    ) -> UIResponse:
        """
        Execute the full recommendation pipeline with behavior-driven personalization.
        
        Args:
            query: Natural language user query
            user_id: Optional user ID for personalization via UserBehaviorProfile
            constraints: Optional additional financial constraints
            
        Returns:
            UIResponse with recommendations
        """
        start_time = time.time()
        
        # ═══════════════════════════════════════════════════════
        # STEP 1: USER QUERY
        # ═══════════════════════════════════════════════════════
        user_query = UserQuery(text=query, user_id=user_id)
        
        # ═══════════════════════════════════════════════════════
        # STEP 2: QUERY UNDERSTANDING
        # ═══════════════════════════════════════════════════════
        intent = await self.query_engine.understand(query)
        embedding = self.query_engine.generate_embedding(query, intent)
        search_filters = self.query_engine.build_search_filters(intent)
        
        # ═══════════════════════════════════════════════════════
        # STEP 3: QDRANT HYBRID SEARCH
        # ═══════════════════════════════════════════════════════
        candidates = self.search_engine.search(
            embedding=embedding,
            filters=search_filters,
            top_k=self.config.top_k_search,
        )
        
        total_candidates = len(candidates)
        
        # ═══════════════════════════════════════════════════════
        # STEP 4: FINANCIAL CONTEXT FILTERING
        # ═══════════════════════════════════════════════════════
        filter_result = self.financial_filter.filter(
            candidates=candidates,
            intent=intent,
            constraints=constraints,
        )
        filtered_candidates = filter_result.candidates
        
        # ═══════════════════════════════════════════════════════
        # STEP 5: BEHAVIOR-DRIVEN RE-RANKING
        # ═══════════════════════════════════════════════════════
        # Adjust weights based on priority
        adjusted_weights = self.reranking_engine.adjust_weights_for_priority(
            intent.priority
        )
        self.reranking_engine.weights = adjusted_weights
        
        # Re-rank using behavior-driven scoring (NO artificial boosts)
        # Uses UserBehaviorProfile from FeedbackLoop for personalization
        scored_products = self.reranking_engine.rerank(
            candidates=filtered_candidates,
            intent=intent,
            top_k=self.config.top_k_results,
            user_id=user_id,
            feedback_loop=self.feedback_loop,
        )
        
        # ═══════════════════════════════════════════════════════
        # STEP 6: EXPLAINABILITY
        # ═══════════════════════════════════════════════════════
        explanation_context = ExplanationContext(
            user_query=query,
            intent=intent,
            total_candidates=total_candidates,
            budget=intent.max_price,
        )
        
        recommendations = self.explainability_engine.explain(
            scored_products=scored_products,
            context=explanation_context,
        )
        
        # ═══════════════════════════════════════════════════════
        # STEP 7: RESPONSE FORMATTING
        # ═══════════════════════════════════════════════════════
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        response = self.response_formatter.format(
            recommendations=recommendations,
            intent=intent,
            total_candidates=total_candidates,
            processing_time_ms=processing_time,
        )
        
        return response
    
    def record_feedback(
        self,
        user_id: str,
        product_id: str,
        action: FeedbackType,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Record user feedback for learning.
        
        Args:
            user_id: User identifier
            product_id: Product that was interacted with
            action: Type of interaction
            context: Additional context
            
        Returns:
            Success status
        """
        if not self.feedback_loop:
            return False
        
        from datetime import datetime
        
        feedback = UserFeedback(
            user_id=user_id,
            product_id=product_id,
            action=action,
            timestamp=datetime.utcnow().isoformat(),
            context=context or {},
        )
        
        return self.feedback_loop.record_feedback(feedback)
    
    def get_analytics(self) -> Dict[str, Any]:
        """Get recommendation system analytics"""
        analytics = {
            "pipeline_config": {
                "top_k_search": self.config.top_k_search,
                "top_k_filter": self.config.top_k_filter,
                "top_k_results": self.config.top_k_results,
            },
            "qdrant_status": self.qdrant_manager.health_check(),
        }
        
        if self.feedback_loop:
            analytics["feedback"] = self.feedback_loop.get_analytics()
        
        collection_info = self.qdrant_manager.get_collection_info()
        if collection_info:
            analytics["collection"] = collection_info
        
        return analytics
    
    def health_check(self) -> Dict[str, bool]:
        """Check health of all components"""
        return {
            "qdrant": self.qdrant_manager.health_check(),
            "query_engine": self.query_engine is not None,
            "search_engine": self.search_engine is not None,
            "financial_filter": self.financial_filter is not None,
            "reranking_engine": self.reranking_engine is not None,
            "explainability_engine": self.explainability_engine is not None,
            "response_formatter": self.response_formatter is not None,
            "feedback_loop": self.feedback_loop is not None,
        }


# Convenience function for simple usage
async def get_recommendations(
    query: str,
    user_id: Optional[str] = None,
) -> UIResponse:
    """
    Simple interface to get recommendations.
    
    Usage:
        response = await get_recommendations("cheap eco laptop for coding")
    """
    orchestrator = RecommendationOrchestrator()
    return await orchestrator.recommend(query, user_id)
