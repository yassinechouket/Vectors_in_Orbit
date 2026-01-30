"""
Test Auto-Indexing and Smart Search
===================================
1. send /detect-product-page request with unique product
2. check if it receives "enhanced_query"
3. search for the product to verify it was indexed
"""
import requests
import json
import time

API_URL = "http://localhost:8000"

# 1. Simulate Product Page Detection
print("\n[1/3] Simulating visit to new product page...")

product_name = "SuperGamer-X 9000 Ultra"
unique_id = f"test_{int(time.time())}"
html_content = f"""
<html>
    <head>
        <title>{product_name} - Best Gaming Gear</title>
        <meta name="description" content="The ultimate gaming laptop with RTX 5090 and 64GB RAM.">
    </head>
    <body>
        <div itemscope itemtype="http://schema.org/Product">
            <div class="product-title" itemprop="name">{product_name}</div>
            <div class="product-price" itemprop="offers" itemscope itemtype="http://schema.org/Offer">
                <span itemprop="price">{2999.99}</span>
                <span itemprop="priceCurrency">USD</span>
                <span itemprop="availability">InStock</span>
            </div>
            <div class="product-description" itemprop="description">
                Experience 8K gaming with the {product_name}. 
                Features mechanical keyboard, RGB lighting, and liquid cooling.
            </div>
            <span itemprop="brand">TechGiant</span>
            <span itemprop="category">Gaming Laptops</span>
            <div class="specs">
                <li itemprop="spec">RTX 5090</li>
                <li itemprop="spec">64GB RAM</li>
            </div>
        </div>
    </body>
</html>
"""

payload = {
    "url": f"https://techgiant.com/products/{unique_id}",
    "html": html_content
}

try:
    response = requests.post(f"{API_URL}/detect-product-page", json=payload)
    if response.status_code == 200:
        data = response.json()
        print("✓ Detection successful")
        print(f"  Enhanced Query: {data.get('enhanced_query')}")
        
        info = data.get('product_info', {})
        print(f"  Detected: {info.get('name')} (${info.get('price')})")
        
    else:
        print(f"❌ Detection failed: {response.text}")
        exit(1)

except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# 2. Verify Indexing (wait random time for simple consistency)
print("\n[2/3] Waiting for indexing...")
time.sleep(2)

# 3. Search for the product
print("\n[3/3] Searching for the new product...")
search_payload = {
    "query": f"gaming laptop {product_name}",
    "limit": 5
}

try:
    response = requests.post(f"{API_URL}/recommend", json=search_payload)
    if response.status_code == 200:
        results = response.json().get("recommendations", [])
        found = False
        for rec in results:
            prod = rec['product']
            print(f"- Found: {prod['name']} (Score: {rec['score']:.2f})")
            if prod['name'] == product_name:
                found = True
        
        if found:
            print(f"\n✅ SUCCESS! Product '{product_name}' was auto-indexed and found!")
        else:
            print(f"\n❌ FAILURE: Product not found in search results.")
    else:
        print(f"❌ Search failed: {response.text}")

except Exception as e:
    print(f"❌ Error: {e}")
