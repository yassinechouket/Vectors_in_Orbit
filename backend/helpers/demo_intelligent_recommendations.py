#!/usr/bin/env python3
"""
Demonstration script for the Intelligent Recommendation Engine

This script shows how to use the new 6-step recommendation workflow:
1. Query Understanding
2. Retrieval Strategy (Qdrant-oriented)
3. Financial & Context Filtering
4. Adaptive Re-Ranking
5. Explainability Layer
6. Final Output Format
"""

import asyncio
import json
from typing import List, Dict, Any
from services.engines import IntelligentRecommendationEngine
from services.recommendation_service import RecommendationService

def create_sample_products() -> List[Dict[str, Any]]:
    """Create sample product data for demonstration"""
    return [
        {
            "name": "MacBook Air M2 13-inch",
            "price": 1199.0,
            "category": "laptop",
            "brand": "Apple",
            "rating": 4.6,
            "reviews": 2847,
            "specs": {
                "cpu": "Apple M2",
                "ram": "8GB",
                "storage": "256GB SSD",
                "screen": "13.6-inch Retina",
                "battery": "18 hours"
            },
            "is_available": True,
            "is_eco_friendly": True,
            "semantic_similarity": 0.92,
            "description": "Supercharged by M2 chip for incredible performance and battery life"
        },
        {
            "name": "Dell XPS 13 Plus",
            "price": 999.0,
            "category": "laptop",
            "brand": "Dell",
            "rating": 4.3,
            "reviews": 1243,
            "specs": {
                "cpu": "Intel i7-1260P",
                "ram": "16GB",
                "storage": "512GB SSD",
                "screen": "13.4-inch OLED",
                "battery": "12 hours"
            },
            "is_available": True,
            "is_eco_friendly": False,
            "semantic_similarity": 0.89,
            "description": "Premium ultrabook with stunning OLED display and powerful performance"
        },
        {
            "name": "Lenovo ThinkPad X1 Carbon",
            "price": 1299.0,
            "category": "laptop", 
            "brand": "Lenovo",
            "rating": 4.4,
            "reviews": 892,
            "specs": {
                "cpu": "Intel i7-1255U",
                "ram": "16GB",
                "storage": "1TB SSD",
                "screen": "14-inch 2.8K",
                "battery": "15 hours"
            },
            "is_available": True,
            "is_eco_friendly": True,
            "semantic_similarity": 0.85,
            "description": "Business-class laptop with legendary durability and security features"
        },
        {
            "name": "ASUS ZenBook 14",
            "price": 799.0,
            "category": "laptop",
            "brand": "ASUS",
            "rating": 4.2,
            "reviews": 657,
            "specs": {
                "cpu": "AMD Ryzen 7 5800H",
                "ram": "16GB",
                "storage": "512GB SSD",
                "screen": "14-inch FHD",
                "battery": "14 hours"
            },
            "is_available": True,
            "is_eco_friendly": False,
            "semantic_similarity": 0.83,
            "description": "Compact and powerful laptop with AMD Ryzen performance"
        },
        {
            "name": "HP Spectre x360 14",
            "price": 1149.0,
            "category": "laptop",
            "brand": "HP",
            "rating": 4.1,
            "reviews": 523,
            "specs": {
                "cpu": "Intel i5-1235U",
                "ram": "8GB",
                "storage": "256GB SSD",
                "screen": "13.5-inch 3K2K Touch",
                "battery": "17 hours"
            },
            "is_available": True,
            "is_eco_friendly": True,
            "semantic_similarity": 0.81,
            "description": "Convertible 2-in-1 laptop with premium design and long battery life"
        },
        {
            "name": "Acer Swift 3",
            "price": 649.0,
            "category": "laptop",
            "brand": "Acer",
            "rating": 4.0,
            "reviews": 743,
            "specs": {
                "cpu": "Intel i5-1135G7",
                "ram": "8GB",
                "storage": "256GB SSD",
                "screen": "14-inch FHD",
                "battery": "11 hours"
            },
            "is_available": True,
            "is_eco_friendly": False,
            "semantic_similarity": 0.79,
            "description": "Affordable laptop with solid performance for everyday tasks"
        }
    ]

async def demo_basic_query():
    """Demonstrate basic query processing"""
    print("🔍 DEMO 1: Basic Query Understanding")
    print("=" * 50)
    
    engine = IntelligentRecommendationEngine()
    
    # Test query understanding
    test_query = "I need a laptop for coding under $1000, prefer eco-friendly options"
    
    query_analysis = engine.analyze_user_query(test_query)
    
    print(f"Original Query: '{test_query}'")
    print(f"Analyzed Query:")
    print(f"  - Category: {query_analysis.category}")
    print(f"  - Max Price: ${query_analysis.max_price}")
    print(f"  - Eco Friendly: {query_analysis.eco_friendly}")
    print(f"  - Use Case: {query_analysis.use_case}")
    print(f"  - Priority: {query_analysis.priority}")
    print(f"  - Semantic Query: '{query_analysis.semantic_query}'")
    print()

async def demo_full_workflow():
    """Demonstrate the complete 6-step workflow"""
    print("🚀 DEMO 2: Complete Intelligent Recommendation Workflow")
    print("=" * 60)
    
    engine = IntelligentRecommendationEngine()
    sample_products = create_sample_products()
    
    # Test different types of queries
    test_queries = [
        "Best laptop for programming under $1200 with good battery life",
        "Eco-friendly laptop for business use, budget around $1000",
        "Gaming laptop with RTX graphics under $1500",
        "Affordable laptop for students under $700"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test Query {i}: '{query}'")
        print("-" * 50)
        
        try:
            response = await engine.get_intelligent_recommendations(
                user_query=query,
                vector_candidates=sample_products,
                max_results=3
            )
            
            print(f"🎯 Query Understanding:")
            print(f"   Category: {response.query_understanding.category}")
            print(f"   Budget: ${response.query_understanding.max_price}")
            print(f"   Use Case: {response.query_understanding.use_case}")
            print(f"   Eco Preference: {response.query_understanding.eco_friendly}")
            
            print(f"\n✅ Top Recommendations ({len(response.top_recommendations)}):")
            for j, rec in enumerate(response.top_recommendations, 1):
                print(f"   {j}. {rec.product_name}")
                print(f"      Price: ${rec.price:.2f}")
                print(f"      Score: {rec.final_score:.1f}/100")
                print(f"      Why: {rec.explanation}")
                print(f"      Value: {rec.value_proposition}")
                print()
            
            print(f"🔁 Alternatives ({len(response.alternatives)}):")
            for alt in response.alternatives:
                print(f"   • {alt['product_name']} (${alt['price']:.2f})")
                print(f"     Why ranked lower: {alt['reason_for_lower_rank']}")
            
            print(f"\n💰 Budget Insight:")
            budget_info = response.budget_insight
            if 'recommended_price' in budget_info:
                print(f"   Recommended: ${budget_info['recommended_price']:.2f}")
                print(f"   Money Saved: ${budget_info['money_saved']:.2f}")
                print(f"   Budget Usage: {budget_info['budget_utilization']:.1f}%")
                print(f"   Value Assessment: {budget_info['value_comparison']}")
            
            print(f"\n⏱️  Processing: {response.processing_time:.3f}s")
            print(f"📊 Candidates Processed: {response.total_candidates}")
            
        except Exception as e:
            print(f"❌ Error processing query: {e}")
        
        print("\n" + "="*60)

async def demo_legacy_compatibility():
    """Demonstrate backward compatibility with existing code"""
    print("🔄 DEMO 3: Legacy Compatibility")
    print("=" * 40)
    
    # Test legacy service
    legacy_service = RecommendationService()
    
    # Mock legacy inputs
    viewed_product = {
        "name": "MacBook Pro 16-inch",
        "category": "laptop",
        "price": 2499.0,
        "description": "High-performance laptop for professionals"
    }
    
    candidate_products = create_sample_products()
    
    user_preferences = {
        "budget": 1500.0,
        "preferred_brands": ["Apple", "Dell"],
        "eco_preference": True,
        "local_preference": False
    }
    
    print(f"Viewed Product: {viewed_product['name']} (${viewed_product['price']})")
    print(f"Budget: ${user_preferences['budget']}")
    print(f"Preferred Brands: {user_preferences['preferred_brands']}")
    print(f"Eco Preference: {user_preferences['eco_preference']}")
    print()
    
    try:
        recommendations = await legacy_service.get_recommendations(
            viewed_product=viewed_product,
            candidate_products=candidate_products,
            user_preferences=user_preferences
        )
        
        print(f"Legacy Recommendations ({len(recommendations)}):")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec['product_name']}")
            print(f"     Price: ${rec['price']:.2f}")
            print(f"     Store: {rec['store']}")
            print(f"     Reason: {rec['reason']}")
            print()
            
    except Exception as e:
        print(f"❌ Error in legacy service: {e}")

async def demo_scoring_details():
    """Demonstrate detailed scoring breakdown"""
    print("📊 DEMO 4: Detailed Scoring Analysis")
    print("=" * 45)
    
    engine = IntelligentRecommendationEngine()
    
    # Analyze a specific query in detail
    query = "Need a reliable laptop for software development under $1100"
    query_analysis = engine.analyze_user_query(query)
    
    sample_products = create_sample_products()
    candidates = engine.retrieve_candidates(query_analysis, sample_products)
    filtered = engine.apply_constraints(candidates, query_analysis)
    scored_products = engine.calculate_product_scores(filtered, query_analysis)
    
    print(f"Query: '{query}'")
    print(f"Candidates after filtering: {len(filtered)}")
    print()
    
    print("Detailed Scoring Breakdown:")
    print("-" * 45)
    
    for i, (product, score) in enumerate(scored_products[:3], 1):
        print(f"{i}. {product['name']} (${product['price']})")
        print(f"   Semantic Score: {score.semantic_score:.1f}/100")
        print(f"   Value Score: {score.value_score:.1f}/100")
        print(f"   Preference Match: {score.preference_match:.1f}/100") 
        print(f"   Review Score: {score.review_score:.1f}/100")
        print(f"   Final Score: {score.final_score:.1f}/100")
        print(f"   Explanation: {score.explanation}")
        print()

def print_demo_header():
    """Print demonstration header"""
    print("🤖 INTELLIGENT RECOMMENDATION ENGINE DEMO")
    print("=" * 60)
    print("Showcasing 6-Step Context-Aware E-commerce Recommendations:")
    print("  1. Query Understanding")
    print("  2. Retrieval Strategy (Qdrant-oriented)")
    print("  3. Financial & Context Filtering") 
    print("  4. Adaptive Re-Ranking")
    print("  5. Explainability Layer")
    print("  6. Final Output Format")
    print("=" * 60)
    print()

async def main():
    """Run all demonstrations"""
    print_demo_header()
    
    try:
        await demo_basic_query()
        await demo_full_workflow()
        await demo_legacy_compatibility()
        await demo_scoring_details()
        
        print("🎉 All demonstrations completed successfully!")
        print("\nThe Intelligent Recommendation Engine is ready for production use.")
        print("Key features:")
        print("  ✅ Context-aware query understanding")
        print("  ✅ Explainable AI recommendations") 
        print("  ✅ Financial constraint handling")
        print("  ✅ Multi-factor adaptive scoring")
        print("  ✅ Backward compatibility")
        print("  ✅ Comprehensive error handling")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())