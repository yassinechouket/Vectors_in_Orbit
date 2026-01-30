import requests
import json
import sys

def test_explain():
    print("Testing /explain endpoint...")
    
    url = "http://localhost:8000/explain"
    payload = {
        "product_id": "1",  # Assuming ID 1 exists from population
        "user_history_titles": []
    }
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Success!")
            print(f"Explanation: {data.get('explanation')}")
            if not data.get('explanation'):
                print("❌ Error: Explanation field is empty")
                sys.exit(1)
        else:
            print(f"❌ Error: Status code {response.status_code}")
            print(response.text)
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_explain()
