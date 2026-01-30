"""
Enhanced error capture - Get full error details from API
"""
import requests
import json
import traceback

print("=" * 60)
print("TESTING BACKEND ENDPOINTS")
print("=" * 60)

# Test 1: Health check
print("\n[TEST 1] Health Check...")
try:
    r = requests.get("http://localhost:8000/health", timeout=5)
    print(f"✓ Status: {r.status_code}")
    print(f"  Response: {r.json()}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 2: Simple search
print("\n[TEST 2] Simple Search...")
payload = {
    "query": "laptop",
    "user_id": "test_user"
}

try:
    r = requests.post(
        "http://localhost:8000/search",
        json=payload,
        timeout=30
    )
    print(f"Status: {r.status_code}")
    
    try:
        response_json = r.json()
        print(f"Full Response:\n{json.dumps(response_json, indent=2)}")
    except:
        print(f"Raw Response:\n{r.text}")
        
except Exception as e:
    print(f"✗ Request Error: {e}")
    traceback.print_exc()

# Test 3: Recommend endpoint
print("\n[TEST 3] Recommend Endpoint...")
try:
    r = requests.post(
        "http://localhost:8000/recommend",
        json=payload,
        timeout=30
    )
    print(f"Status: {r.status_code}")
    
    try:
        response_json = r.json()
        print(f"Response Keys: {list(response_json.keys())}")
        if 'recommendations' in response_json:
            print(f"✓ Got {len(response_json['recommendations'])} recommendations")
        if 'detail' in response_json:
            print(f"✗ Error Detail: {response_json['detail']}")
    except:
        print(f"Raw Response:\n{r.text}")
        
except Exception as e:
    print(f"✗ Request Error: {e}")

# Test 4: Analytics
print("\n[TEST 4] Analytics...")
try:
    r = requests.get("http://localhost:8000/analytics", timeout=5)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        analytics = r.json()
        print(f"Analytics: {json.dumps(analytics, indent=2)}")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 60)
