"""
Diagnostic Script - Test Recommendation System
==============================================
Tests if the recommendation API is working with the populated database
"""

import requests
import json
import sys

def test_health():
    """Test backend health endpoint"""
    print("\n[1/4] Testing Backend Health...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Backend is healthy: {data}")
            return True
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        return False


def test_qdrant_status():
    """Check Qdrant collection status"""
    print("\n[2/4] Checking Qdrant Database...")
    try:
        sys.path.insert(0, '.')
        from services.qdrant.client import QdrantManager
        
        qm = QdrantManager()
        if not qm.health_check():
            print("❌ Qdrant is not accessible")
            return False
        
        info = qm.get_collection_info()
        if info:
            print(f"✓ Qdrant connected")
            print(f"  Collection: {qm.COLLECTION_NAME}")
            print(f"  Products: {info['points_count']}")
            print(f"  Status: {info['status']}")
            
            if info['points_count'] == 0:
                print("\n⚠️  WARNING: Database is empty!")
                print("Run: python populate_database.py --recreate")
                return False
            return True
        else:
            print("❌ Cannot get collection info")
            return False
            
    except Exception as e:
        print(f"❌ Error checking Qdrant: {e}")
        return False


def test_recommend_endpoint():
    """Test the recommendation endpoint"""
    print("\n[3/4] Testing Recommendation Endpoint...")
    
    test_queries = [
        {
            "query": "laptop for coding",
            "user_id": "test_user_1"
        },
        {
            "query": "gaming headphones under $200",
            "user_id": "test_user_2",
            "max_budget": 200
        }
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n  Test {i}: '{query['query']}'")
        try:
            response = requests.post(
                "http://localhost:8000/recommend",
                json=query,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                recs = data.get('recommendations', [])
                print(f"  ✓ Got {len(recs)} recommendations")
                
                if len(recs) > 0:
                    # Show first recommendation
                    rec = recs[0]
                    product = rec['product']
                    print(f"    Top result: {product['name']} (${product['price']})")
                else:
                    print(f"  ⚠️  No recommendations returned (empty list)")
                    return False
                    
            elif response.status_code == 500:
                print(f"  ❌ Server error: {response.text[:200]}")
                return False
            else:
                print(f"  ❌ HTTP {response.status_code}")
                print(f"  Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    
    return True


def test_frontend_query():
    """Test a typical frontend query with session context"""
    print("\n[4/4] Testing Frontend-Style Query...")
    
    payload = {
        "query": "cheap laptop",
        "user_id": "frontend_user",
        "max_budget": 1000,
        "session_context": {
            "device_type": "desktop",
            "time_of_day": "evening"
        }
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/recommend",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            recs = data.get('recommendations', [])
            print(f"✓ Frontend query successful: {len(recs)} recommendations")
            
            if len(recs) > 0:
                print("\nTop 3 recommendations:")
                for i, rec in enumerate(recs[:3], 1):
                    p = rec['product']
                    print(f"  {i}. {p['name']} - ${p['price']} ({p['category']})")
                return True
            else:
                print("⚠️  No recommendations returned")
                return False
        else:
            print(f"❌ HTTP {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print("RECOMMENDATION SYSTEM DIAGNOSTIC")
    print("=" * 60)
    
    results = {
        "Backend Health": test_health(),
        "Qdrant Database": test_qdrant_status(),
        "Recommendation API": test_recommend_endpoint(),
        "Frontend Query": test_frontend_query()
    }
    
    print("\n" + "=" * 60)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 All tests passed! Your recommendation system is working!")
        print("\nIf you're still seeing 'No recommendations' in the UI:")
        print("  1. Check browser console for errors (F12)")
        print("  2. Verify the frontend is connecting to http://localhost:8000")
        print("  3. Check CORS settings in the backend")
        print("  4. Refresh the extension/webapp")
    else:
        print("\n⚠️  Some tests failed. See details above.")
        print("\nCommon fixes:")
        print("  - Backend not running: cd backend && python main.py")
        print("  - Empty database: python populate_database.py --recreate")
        print("  - Qdrant not running: docker run -p 6333:6333 qdrant/qdrant")
    
    return all_passed


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
