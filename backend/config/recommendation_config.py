"""
Configuration file for Intelligent Recommendation Engine

This file contains all configurable parameters for the recommendation system.
Modify these settings to tune the engine's behavior for your specific use case.
"""

import os
from typing import Dict, Any

# =============================================================================
# CORE ENGINE CONFIGURATION
# =============================================================================

# Scoring weights for adaptive re-ranking (must sum to 1.0)
SCORING_WEIGHTS = {
    'semantic_score': 0.4,    # Relevance to user query
    'value_score': 0.3,       # Price-to-value ratio
    'preference_match': 0.2,  # User preference alignment
    'review_score': 0.1       # Social proof/reviews
}

# OpenAI Configuration
OPENAI_CONFIG = {
    'model': os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    'temperature': 0.1,       # Lower = more consistent
    'max_tokens': 1500,       # Enough for complex analysis
    'timeout': 30             # Request timeout in seconds
}

# =============================================================================
# QUERY UNDERSTANDING SETTINGS
# =============================================================================

# Category detection keywords
CATEGORY_KEYWORDS = {
    'laptop': ['laptop', 'notebook', 'computer', 'macbook', 'thinkpad', 'ultrabook'],
    'smartphone': ['phone', 'mobile', 'smartphone', 'iphone', 'android', 'galaxy'],
    'tablet': ['tablet', 'ipad', 'surface', 'kindle'],
    'headphones': ['headphones', 'earbuds', 'audio', 'airpods', 'beats'],
    'camera': ['camera', 'photography', 'dslr', 'mirrorless', 'canon', 'nikon'],
    'monitor': ['monitor', 'display', 'screen', '4k', 'gaming monitor'],
    'keyboard': ['keyboard', 'mechanical', 'gaming keyboard', 'wireless keyboard'],
    'mouse': ['mouse', 'gaming mouse', 'wireless mouse', 'trackball'],
    'speaker': ['speaker', 'bluetooth speaker', 'soundbar', 'home audio']
}

# Use case detection patterns
USE_CASE_KEYWORDS = {
    'gaming': ['gaming', 'games', 'rtx', 'gpu', 'graphics', 'fps', 'esports'],
    'coding': ['coding', 'programming', 'development', 'developer', 'software', 'ide'],
    'business': ['business', 'office', 'work', 'professional', 'enterprise', 'productivity'],
    'creative': ['creative', 'design', 'photo editing', 'video editing', 'adobe', 'art'],
    'student': ['student', 'school', 'college', 'university', 'education', 'homework'],
    'casual': ['casual', 'home', 'everyday', 'basic', 'simple', 'general use']
}

# Eco-friendly detection keywords
ECO_KEYWORDS = [
    'eco', 'eco-friendly', 'green', 'sustainable', 'environment', 'recycled',
    'energy efficient', 'carbon neutral', 'renewable', 'organic'
]

# =============================================================================
# RETRIEVAL AND FILTERING SETTINGS
# =============================================================================

# Maximum candidates to process at each stage
CANDIDATE_LIMITS = {
    'retrieval': 20,          # From vector search
    'after_filtering': 10,    # After constraint application
    'final_recommendations': 3 # Final output
}

# Price analysis settings
PRICE_ANALYSIS = {
    'budget_utilization_excellent': 0.7,  # < 70% = excellent value
    'budget_utilization_good': 0.85,      # < 85% = good value
    'budget_utilization_max': 1.0,        # <= 100% = acceptable
    
    # Price categories for scoring (when no budget given)
    'budget_friendly_max': 100,
    'mid_range_max': 500,
    'higher_end_max': 1000
}

# =============================================================================
# SCORING ALGORITHM CONFIGURATION
# =============================================================================

# Semantic similarity thresholds
SEMANTIC_THRESHOLDS = {
    'excellent': 0.85,        # Highly relevant
    'good': 0.7,              # Good match
    'acceptable': 0.5,        # Acceptable match
    'poor': 0.3               # Poor match
}

# Value score calculation parameters
VALUE_SCORE_CONFIG = {
    'great_value_threshold': 0.7,     # Price ratio for great value
    'good_value_threshold': 0.85,     # Price ratio for good value
    'acceptable_threshold': 1.0,      # Price ratio for acceptable
    
    # Scores for different value categories
    'great_value_score': 90,
    'good_value_score': 75,
    'acceptable_score': 60,
    'overpriced_score': 20
}

# Review score configuration
REVIEW_SCORE_CONFIG = {
    'high_review_count': 100,         # Many reviews
    'medium_review_count': 50,        # Moderate reviews
    'low_review_count': 10,           # Few reviews
    
    'high_confidence_boost': 10,      # Boost for many reviews
    'medium_confidence_boost': 5,     # Boost for moderate reviews
    'low_confidence_boost': 2         # Boost for few reviews
}

# Preference matching bonuses
PREFERENCE_BONUSES = {
    'preferred_brand': 25,            # Brand in preferences
    'eco_friendly_match': 20,         # Eco requirement met
    'use_case_match': 15,            # Use case keywords found
    'base_score': 50                 # Starting preference score
}

# =============================================================================
# EXPLAINABILITY SETTINGS
# =============================================================================

# Explanation templates
EXPLANATION_TEMPLATES = {
    'high_semantic': "closely matches your search requirements",
    'medium_semantic': "good match for your needs",
    'high_value': "excellent value for money",
    'medium_value': "reasonably priced",
    'high_preference': "matches your preferences well",
    'high_reviews': "highly rated by customers",
    'medium_reviews': "well-reviewed",
    'fallback': "suitable option for your requirements"
}

# Alternative ranking reasons
ALTERNATIVE_REASONS = {
    'price_unfavorable': "Less favorable pricing compared to top recommendations",
    'preference_mismatch': "Doesn't match your preferences as closely",
    'relevance_lower': "Less relevant to your specific search",
    'overall_lower': "Good option but scored lower overall"
}

# =============================================================================
# ERROR HANDLING AND FALLBACKS
# =============================================================================

# Retry configuration
RETRY_CONFIG = {
    'max_retries': 3,
    'retry_delay': 1.0,               # Seconds between retries
    'backoff_multiplier': 2.0         # Exponential backoff
}

# Fallback behavior
FALLBACK_CONFIG = {
    'use_rule_based_scoring': True,   # Use rule-based if AI fails
    'minimum_candidates': 1,          # Minimum to return recommendations
    'default_confidence': 0.5,        # Default confidence score
    'enable_mock_data': False         # Use mock data if no candidates (dev only)
}

# =============================================================================
# PERFORMANCE SETTINGS
# =============================================================================

# Processing limits
PERFORMANCE_LIMITS = {
    'max_query_length': 500,          # Characters
    'max_candidates_process': 50,     # Products to score
    'processing_timeout': 30,         # Seconds
    'cache_ttl': 300                  # Cache results for 5 minutes
}

# Logging configuration
LOGGING_CONFIG = {
    'log_query_analysis': True,
    'log_candidate_filtering': True,
    'log_scoring_details': False,     # Verbose scoring logs
    'log_processing_time': True,
    'log_errors_only': False          # Only log errors in production
}

# =============================================================================
# VECTOR SEARCH INTEGRATION (Qdrant)
# =============================================================================

# Qdrant configuration (for future integration)
QDRANT_CONFIG = {
    'collection_name': 'products',
    'dense_vector_name': 'dense_embedding',
    'sparse_vector_name': 'sparse_embedding',
    'search_limit': 20,
    'score_threshold': 0.5,
    
    # Hybrid search weights
    'dense_weight': 0.7,              # Semantic similarity
    'sparse_weight': 0.3              # Keyword matching
}

# =============================================================================
# FEATURE FLAGS
# =============================================================================

# Enable/disable features
FEATURE_FLAGS = {
    'enable_ai_query_analysis': True,
    'enable_detailed_explanations': True,
    'enable_budget_optimization': True,
    'enable_preference_learning': False,  # Future feature
    'enable_a_b_testing': False,         # Future feature
    'enable_real_time_scoring': True,
    'enable_diversity_filter': True
}

# =============================================================================
# VALIDATION RULES
# =============================================================================

# Input validation
VALIDATION_RULES = {
    'min_query_length': 3,
    'max_query_length': 500,
    'min_price': 0.01,
    'max_price': 100000.0,
    'max_candidates': 100,
    'required_product_fields': ['name', 'price', 'category'],
    'optional_product_fields': ['brand', 'rating', 'reviews', 'specs', 'description']
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_config_value(key: str, default: Any = None) -> Any:
    """Get configuration value with fallback to environment variable"""
    config_key = key.upper().replace('.', '_')
    return os.getenv(config_key, default)

def validate_scoring_weights(weights: Dict[str, float]) -> bool:
    """Validate that scoring weights sum to 1.0"""
    total = sum(weights.values())
    return abs(total - 1.0) < 0.001  # Allow small floating point errors

def get_active_features() -> Dict[str, bool]:
    """Get currently active feature flags"""
    return {k: v for k, v in FEATURE_FLAGS.items() if v}

# Validate configuration on import
if not validate_scoring_weights(SCORING_WEIGHTS):
    raise ValueError(f"Scoring weights must sum to 1.0, got {sum(SCORING_WEIGHTS.values())}")

# Export commonly used configurations
__all__ = [
    'SCORING_WEIGHTS',
    'OPENAI_CONFIG', 
    'CATEGORY_KEYWORDS',
    'USE_CASE_KEYWORDS',
    'CANDIDATE_LIMITS',
    'FEATURE_FLAGS',
    'get_config_value',
    'validate_scoring_weights',
    'get_active_features'
]