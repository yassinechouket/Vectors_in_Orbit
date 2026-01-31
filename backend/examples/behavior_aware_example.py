"""
Example: Using Behavior-Aware Recommendations
==============================================

This demonstrates how the behavior-aware re-ranking system works in practice.
"""

import asyncio
from services.engines import RecommendationOrchestrator, PipelineConfig
from services.engines.feedback_loop import FeedbackLoop
from models.schemas import FeedbackType, UserFeedback
from datetime import datetime


async def main():
    # =========================================================================
    # SETUP: Initialize orchestrator with feedback enabled
    # =========================================================================
    
    config = PipelineConfig(
        top_k_search=20,
        top_k_filter=10,
        top_k_results=3,
        enable_feedback=True,  # ⭐ Enable behavior tracking
        qdrant_host="localhost",
        qdrant_port=6333,
    )
    
    orchestrator = RecommendationOrchestrator(config)
    feedback_loop = orchestrator.feedback_loop
    
    
    # =========================================================================
    # SCENARIO 1: NEW USER (Cold Start - No Behavior)
    # =========================================================================
    
    print("=" * 70)
    print("SCENARIO 1: New User (No Behavior History)")
    print("=" * 70)
    
    response = await orchestrator.recommend(
        query="laptop for coding under $800",
        user_id="user_new_001",
    )
    
    print(f"\nQuery: {response.query_understanding.category}")
    print(f"Budget: ${response.query_understanding.max_price}")
    print(f"\nBehavior Profile: None (new user)")
    print(f"Behavior Boost Applied: No")
    print(f"\nTop 3 Results:")
    for i, rec in enumerate(response.recommendations, 1):
        print(f"  {i}. {rec.product.name}")
        print(f"     Price: ${rec.product.price}")
        print(f"     Score: {rec.final_score:.3f}")
        print(f"     Ranking: {rec.ranking_reason}")
    
    
    # =========================================================================
    # SCENARIO 2: BUILD USER BEHAVIOR PROFILE
    # =========================================================================
    
    print("\n" + "=" * 70)
    print("SCENARIO 2: Building Behavior Profile (Simulated Interactions)")
    print("=" * 70)
    
    user_id = "user_regular_002"
    
    # Simulate user interactions over time
    interactions = [
        # User prefers Dell laptops
        UserFeedback(
            user_id=user_id,
            product_id="laptop_dell_001",
            action=FeedbackType.CLICK,
            timestamp=datetime.utcnow().isoformat(),
            context={"brand": "Dell", "category": "laptop", "price": 750, "eco_certified": True}
        ),
        UserFeedback(
            user_id=user_id,
            product_id="laptop_dell_002",
            action=FeedbackType.PURCHASE,
            timestamp=datetime.utcnow().isoformat(),
            context={"brand": "Dell", "category": "laptop", "price": 800, "eco_certified": True}
        ),
        # User views eco-certified products
        UserFeedback(
            user_id=user_id,
            product_id="laptop_lenovo_001",
            action=FeedbackType.VIEW,
            timestamp=datetime.utcnow().isoformat(),
            context={"brand": "Lenovo", "category": "laptop", "price": 850, "eco_certified": True}
        ),
        # User skips Acer
        UserFeedback(
            user_id=user_id,
            product_id="laptop_acer_001",
            action=FeedbackType.SKIP,
            timestamp=datetime.utcnow().isoformat(),
            context={"brand": "Acer", "category": "laptop", "price": 600, "eco_certified": False}
        ),
        # More Dell interactions (building preference)
        UserFeedback(
            user_id=user_id,
            product_id="laptop_dell_003",
            action=FeedbackType.ADD_TO_CART,
            timestamp=datetime.utcnow().isoformat(),
            context={"brand": "Dell", "category": "laptop", "price": 900, "eco_certified": True}
        ),
        # Add more interactions to reach threshold (need 10+ for confidence)
        *[
            UserFeedback(
                user_id=user_id,
                product_id=f"laptop_dell_{i:03d}",
                action=FeedbackType.VIEW if i % 2 == 0 else FeedbackType.CLICK,
                timestamp=datetime.utcnow().isoformat(),
                context={"brand": "Dell", "category": "laptop", "price": 750 + i*10, "eco_certified": True}
            )
            for i in range(4, 15)
        ],
    ]
    
    # Record all interactions
    for feedback in interactions:
        feedback_loop.record_feedback(feedback)
    
    # Get behavior profile
    behavior_profile = feedback_loop.get_behavior_profile(user_id)
    
    print(f"\nUser: {user_id}")
    print(f"Total Interactions: {behavior_profile.interaction_count}")
    print(f"Confidence Level: {behavior_profile.get_confidence():.1%}")
    print(f"\nBehavior Profile:")
    print(f"  Preferred Brands: {behavior_profile.preferred_brands}")
    print(f"  Avoided Brands: {behavior_profile.avoided_brands}")
    print(f"  Eco Interest: {behavior_profile.eco_interest:.2f} (scale: -1 to 1)")
    print(f"  Price Sensitivity: {behavior_profile.price_sensitivity:.2f} (0=budget, 1=premium)")
    print(f"  Top Categories: {list(behavior_profile.category_affinity.keys())}")
    
    
    # =========================================================================
    # SCENARIO 3: RECOMMENDATIONS WITH BEHAVIOR BOOST
    # =========================================================================
    
    print("\n" + "=" * 70)
    print("SCENARIO 3: Recommendations with Behavior Boost")
    print("=" * 70)
    
    response_with_behavior = await orchestrator.recommend(
        query="laptop for coding under $900",
        user_id=user_id,  # User with behavior history
    )
    
    print(f"\nQuery: laptop for coding")
    print(f"User: {user_id} (has behavior history)")
    print(f"Behavior Boost: ENABLED")
    print(f"\nTop 3 Results:")
    for i, rec in enumerate(response_with_behavior.recommendations, 1):
        product = rec.product
        
        # Calculate what the boost might be (simplified)
        brand_match = product.brand in behavior_profile.preferred_brands if product.brand else False
        eco_match = product.eco_certified and behavior_profile.eco_interest > 0.5
        
        potential_boost = 0
        if brand_match:
            potential_boost += 2  # +2%
        if eco_match:
            potential_boost += 1  # +1%
        
        print(f"  {i}. {product.name}")
        print(f"     Brand: {product.brand}")
        print(f"     Price: ${product.price}")
        print(f"     Eco: {'Yes' if product.eco_certified else 'No'}")
        print(f"     Score: {rec.final_score:.3f}")
        print(f"     Brand Match: {'✓' if brand_match else '✗'}")
        print(f"     Eco Match: {'✓' if eco_match else '✗'}")
        print(f"     Est. Behavior Boost: ~+{potential_boost}%")
        print(f"     Reason: {rec.ranking_reason}")
    
    
    # =========================================================================
    # SCENARIO 4: BEHAVIOR IMPACT COMPARISON
    # =========================================================================
    
    print("\n" + "=" * 70)
    print("SCENARIO 4: Impact of Behavior (Same Query, Different Users)")
    print("=" * 70)
    
    # New user (no behavior)
    response_no_behavior = await orchestrator.recommend(
        query="laptop for coding under $900",
        user_id="user_new_003",  # New user
    )
    
    # User with behavior
    response_with_behavior = await orchestrator.recommend(
        query="laptop for coding under $900",
        user_id=user_id,  # User with Dell preference
    )
    
    print("\nSame Query, Different Users:")
    print("-" * 70)
    print("\nUser A (New User - No Behavior):")
    for i, rec in enumerate(response_no_behavior.recommendations[:3], 1):
        print(f"  {i}. {rec.product.name} (${rec.product.price}) - Score: {rec.final_score:.3f}")
    
    print(f"\nUser B (Regular User - Prefers Dell, Eco-Friendly):")
    for i, rec in enumerate(response_with_behavior.recommendations[:3], 1):
        brand_indicator = "⭐" if rec.product.brand == "Dell" else ""
        print(f"  {i}. {rec.product.name} (${rec.product.price}) - Score: {rec.final_score:.3f} {brand_indicator}")
    
    print("\nKey Insights:")
    print("  • Behavior boost is subtle (max ±5%)")
    print("  • Dell laptops get small boost for User B")
    print("  • Results are still diverse (not just Dell)")
    print("  • Search quality remains primary ranking factor")
    
    
    # =========================================================================
    # SCENARIO 5: ANALYTICS
    # =========================================================================
    
    print("\n" + "=" * 70)
    print("SCENARIO 5: System Analytics")
    print("=" * 70)
    
    analytics = feedback_loop.get_analytics()
    
    print(f"\nSystem-Wide Metrics:")
    print(f"  Total Users: {analytics['total_users']}")
    print(f"  Total Products Tracked: {analytics['total_products']}")
    print(f"  Total Feedback Events: {analytics['total_feedback']}")
    print(f"  Average CTR: {analytics.get('avg_ctr', 0):.2%}")
    print(f"  Average Conversion: {analytics.get('avg_conversion', 0):.2%}")
    
    print(f"\nTop Products by Purchases:")
    for i, product in enumerate(analytics.get('top_products', [])[:5], 1):
        print(f"  {i}. Product {product.product_id}")
        print(f"     Purchases: {product.purchases}, CTR: {product.ctr:.2%}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("BEHAVIOR-AWARE RECOMMENDATION SYSTEM - EXAMPLES")
    print("=" * 70)
    print("\nThis demonstrates how behavior influences recommendations as a")
    print("soft modifier (max ±5% score adjustment) while keeping semantic")
    print("search and constraints as the primary ranking factors.")
    print("\n" + "=" * 70 + "\n")
    
    asyncio.run(main())
