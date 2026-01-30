"""
Test Recommendation API
========================
Quick test script to verify the vector database is working
"""

import requests
import json

# Test query
payload = {
    "query": "cheap laptop for coding under $800",
    "user_id": "test_user_123",
    "max_budget": 800
}

print("=" * 60)
print("Testing Recommendation API")
print("=" * 60)
print(f"\nQuery: {payload['query']}")
print(f"Budget: ${payload['max_budget']}")

try:
    response = requests.post(
        "http://localhost:8000/recommend",
        json=payload,
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"\n✓ Success! Got {len(data.get('recommendations', []))} recommendations")
        
        # Display recommendations
        for i, rec in enumerate(data.get('recommendations', [])[:3], 1):
            product = rec['product']
            print(f"\n{i}. {product['name']}")
            print(f"   Price: ${product['price']}")
            print(f"   Category: {product['category']}")
            print(f"   Brand: {product.get('brand', 'N/A')}")
            print(f"   Rating: {product.get('rating', 0):.1f}/5.0")
            print(f"   Score: {rec['score']:.3f}")
            print(f"   Image: {product.get('image_url', 'N/A')}")
            print(f"   Why: {rec.get('explanation', 'No explanation')[:100]}...")
        
        # Check query understanding
        if 'query_understanding' in data:
            qu = data['query_understanding']
            print(f"\n\nQuery Understanding:")
            print(f"  Category: {qu.get('category', 'N/A')}")
            print(f"  Max Price: ${qu.get('max_price', 'N/A')}")
            print(f"  Preferences: {', '.join(qu.get('preferences', []))}")
        
        print(f"\n\n{'='*60}")
        print("DATABASE IS WORKING! ✓")
        print(f"{'='*60}\n")
        
    else:
        print(f"\n❌ Error: HTTP {response.status_code}")
        print(response.text)
        
except requests.exceptions.ConnectionError:
    print("\n❌ Error: Cannot connect to backend")
    print("Make sure the backend is running on http://localhost:8000")
except Exception as e:
    print(f"\n❌ Error: {e}")
