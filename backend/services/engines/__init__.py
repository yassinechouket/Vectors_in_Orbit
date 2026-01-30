# Engines Package
# Clean modular architecture for the recommendation pipeline

from .orchestrator import (
    RecommendationOrchestrator,
    PipelineConfig,
    get_recommendations,
)
from .query_understanding import QueryUnderstandingEngine
from .financial_filter import FinancialFilter, FilterResult
from .reranking import ReRankingEngine, RankingWeights
from .explainability import ExplainabilityEngine, ExplanationContext
from .response_formatter import ResponseFormatter, UIResponse
from .feedback_loop import FeedbackLoop

__all__ = [
    # Main Orchestrator
    "RecommendationOrchestrator",
    "PipelineConfig",
    "get_recommendations",
    
    # Step 2: Query Understanding
    "QueryUnderstandingEngine",
    
    # Step 4: Financial Filtering
    "FinancialFilter",
    "FilterResult",
    
    # Step 5: Re-Ranking
    "ReRankingEngine",
    "RankingWeights",
    
    # Step 6: Explainability
    "ExplainabilityEngine",
    "ExplanationContext",
    
    # Step 7: Response Formatting
    "ResponseFormatter",
    "UIResponse",
    
    # Step 8: Feedback Loop
    "FeedbackLoop",
]