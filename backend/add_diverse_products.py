"""
Add diverse products to the catalog
"""

import json
from pathlib import Path

CATALOG_PATH = Path(__file__).parent.parent / "Web_app" / "public" / "data" / "reference_catalog_clean.json"

# New diverse products to add
NEW_PRODUCTS = [
    # Headphones
    {
        "product_id": "HEADPHONE001",
        "category": "headphones",
        "semantic_text": {
            "title": "Sony WH-1000XM5 Wireless Noise Cancelling Headphones",
            "description": "Industry-leading noise cancellation with Auto NC Optimizer, exceptional sound quality with new integrated processor V1",
            "features": ["Active Noise Cancellation", "30hr Battery", "Multipoint Connection", "Speak-to-Chat"],
            "intended_use": ["music listening", "travel", "work from home", "commuting"],
            "tags": ["premium headphones", "wireless", "noise cancelling"]
        },
        "attributes": {
            "brand": "Sony",
            "price": 29990,
            "currency": "INR",
            "payment_options": ["cash", "credit_card"],
            "availability": {"in_stock": True}
        },
        "links": {"external_url": "https://amazon.in/dp/HEADPHONE001"}
    },
    {
        "product_id": "HEADPHONE002",
        "category": "headphones",
        "semantic_text": {
            "title": "JBL Tune 760NC Wireless Over-Ear Headphones",
            "description": "JBL Pure Bass Sound with Active Noise Cancelling, 35 hours of battery life",
            "features": ["Active Noise Cancellation", "35hr Battery", "JBL Pure Bass", "Foldable Design"],
            "intended_use": ["music", "gaming", "calls", "travel"],
            "tags": ["budget headphones", "wireless", "bass"]
        },
        "attributes": {
            "brand": "JBL",
            "price": 5999,
            "currency": "INR",
            "payment_options": ["cash", "credit_card"],
            "availability": {"in_stock": True}
        },
        "links": {"external_url": "https://amazon.in/dp/HEADPHONE002"}
    },
    {
        "product_id": "HEADPHONE003",
        "category": "headphones",
        "semantic_text": {
            "title": "boAt Rockerz 550 Bluetooth Wireless Headphones",
            "description": "Over Ear Headphones with 50mm drivers, immersive audio, and 20H playback",
            "features": ["50mm Drivers", "20hr Battery", "Physical Noise Isolation", "Dual Modes"],
            "intended_use": ["music", "gaming", "calls"],
            "tags": ["budget headphones", "wireless", "indian brand"]
        },
        "attributes": {
            "brand": "boAt",
            "price": 1499,
            "currency": "INR",
            "payment_options": ["cash", "credit_card"],
            "availability": {"in_stock": True}
        },
        "links": {"external_url": "https://amazon.in/dp/HEADPHONE003"}
    },
    
    # Smartwatches
    {
        "product_id": "WATCH001",
        "category": "smartwatch",
        "semantic_text": {
            "title": "Apple Watch Series 9 GPS 45mm",
            "description": "Advanced health features with Blood Oxygen & ECG, Always-On Retina display, S9 SiP chip",
            "features": ["Blood Oxygen", "ECG", "Always-On Display", "Crash Detection"],
            "intended_use": ["fitness tracking", "health monitoring", "notifications", "daily wear"],
            "tags": ["premium smartwatch", "apple", "health tracking"]
        },
        "attributes": {
            "brand": "Apple",
            "price": 44900,
            "currency": "INR",
            "payment_options": ["cash", "credit_card"],
            "availability": {"in_stock": True}
        },
        "links": {"external_url": "https://amazon.in/dp/WATCH001"}
    },
    {
        "product_id": "WATCH002",
        "category": "smartwatch",
        "semantic_text": {
            "title": "Samsung Galaxy Watch 6 Classic 47mm",
            "description": "Premium smartwatch with rotating bezel, advanced sleep coaching, and body composition analysis",
            "features": ["Rotating Bezel", "Sleep Coaching", "Body Composition", "Sapphire Crystal"],
            "intended_use": ["fitness", "health", "style", "notifications"],
            "tags": ["premium smartwatch", "samsung", "classic design"]
        },
        "attributes": {
            "brand": "Samsung",
            "price": 35999,
            "currency": "INR",
            "payment_options": ["cash", "credit_card"],
            "availability": {"in_stock": True}
        },
        "links": {"external_url": "https://amazon.in/dp/WATCH002"}
    },
    {
        "product_id": "WATCH003",
        "category": "smartwatch",
        "semantic_text": {
            "title": "Noise ColorFit Pro 4 Smart Watch",
            "description": "1.72\" TruView Display, Bluetooth Calling, 100+ Sports Modes, 7-day battery",
            "features": ["Bluetooth Calling", "100+ Sports Modes", "SpO2", "Heart Rate"],
            "intended_use": ["fitness", "calls", "notifications"],
            "tags": ["budget smartwatch", "indian brand", "fitness"]
        },
        "attributes": {
            "brand": "Noise",
            "price": 2999,
            "currency": "INR",
            "payment_options": ["cash", "credit_card"],
            "availability": {"in_stock": True}
        },
        "links": {"external_url": "https://amazon.in/dp/WATCH003"}
    },
    
    # Cameras
    {
        "product_id": "CAMERA001",
        "category": "camera",
        "semantic_text": {
            "title": "Canon EOS R6 Mark II Mirrorless Camera",
            "description": "24.2MP Full-Frame CMOS Sensor, 4K 60p Video, Up to 40fps Shooting",
            "features": ["24.2MP Full Frame", "4K 60fps Video", "40fps Burst", "In-Body Stabilization"],
            "intended_use": ["professional photography", "videography", "wildlife", "sports"],
            "tags": ["professional camera", "mirrorless", "full frame"]
        },
        "attributes": {
            "brand": "Canon",
            "price": 215990,
            "currency": "INR",
            "payment_options": ["cash", "credit_card"],
            "availability": {"in_stock": True}
        },
        "links": {"external_url": "https://amazon.in/dp/CAMERA001"}
    },
    {
        "product_id": "CAMERA002",
        "category": "camera",
        "semantic_text": {
            "title": "Sony Alpha 7C II Compact Full-Frame Camera",
            "description": "33MP Full-Frame Sensor, 4K 60p, World's Smallest Full-Frame System Camera",
            "features": ["33MP Full Frame", "Compact Design", "4K 60fps", "Real-time Eye AF"],
            "intended_use": ["travel photography", "street photography", "vlogging", "content creation"],
            "tags": ["compact camera", "mirrorless", "travel friendly"]
        },
        "attributes": {
            "brand": "Sony",
            "price": 189990,
            "currency": "INR",
            "payment_options": ["cash", "credit_card"],
            "availability": {"in_stock": True}
        },
        "links": {"external_url": "https://amazon.in/dp/CAMERA002"}
    },
    {
        "product_id": "CAMERA003",
        "category": "camera",
        "semantic_text": {
            "title": "Nikon Z50 Mirrorless Camera with 16-50mm Lens",
            "description": "20.9MP DX-Format CMOS Sensor, 4K UHD Video, Great for beginners",
            "features": ["20.9MP APS-C", "4K Video", "Touch Screen", "Eye-Detection AF"],
            "intended_use": ["beginner photography", "travel", "video", "everyday shooting"],
            "tags": ["entry level", "mirrorless", "beginner friendly"]
        },
        "attributes": {
            "brand": "Nikon",
            "price": 72990,
            "currency": "INR",
            "payment_options": ["cash", "credit_card"],
            "availability": {"in_stock": True}
        },
        "links": {"external_url": "https://amazon.in/dp/CAMERA003"}
    },
    
    # Speakers
    {
        "product_id": "SPEAKER001",
        "category": "speaker",
        "semantic_text": {
            "title": "JBL Flip 6 Portable Bluetooth Speaker",
            "description": "Powerful JBL Original Pro Sound, IP67 waterproof and dustproof, 12hr playtime",
            "features": ["JBL Pro Sound", "IP67 Waterproof", "12hr Battery", "PartyBoost"],
            "intended_use": ["outdoor", "pool party", "travel", "beach"],
            "tags": ["portable speaker", "waterproof", "bluetooth"]
        },
        "attributes": {
            "brand": "JBL",
            "price": 10999,
            "currency": "INR",
            "payment_options": ["cash", "credit_card"],
            "availability": {"in_stock": True}
        },
        "links": {"external_url": "https://amazon.in/dp/SPEAKER001"}
    },
    {
        "product_id": "SPEAKER002",
        "category": "speaker",
        "semantic_text": {
            "title": "Bose SoundLink Flex Bluetooth Speaker",
            "description": "Deep, clear, immersive sound with PositionIQ technology, IP67 waterproof",
            "features": ["PositionIQ", "IP67 Waterproof", "12hr Battery", "Built-in Mic"],
            "intended_use": ["outdoor", "hiking", "travel", "home"],
            "tags": ["premium speaker", "portable", "waterproof"]
        },
        "attributes": {
            "brand": "Bose",
            "price": 14990,
            "currency": "INR",
            "payment_options": ["cash", "credit_card"],
            "availability": {"in_stock": True}
        },
        "links": {"external_url": "https://amazon.in/dp/SPEAKER002"}
    },
    {
        "product_id": "SPEAKER003",
        "category": "speaker",
        "semantic_text": {
            "title": "Marshall Stanmore II Bluetooth Speaker",
            "description": "Iconic Marshall design with powerful sound, multi-host functionality",
            "features": ["80W Power", "Bluetooth 5.0", "Analog Controls", "Multi-host"],
            "intended_use": ["home audio", "living room", "music enthusiasts"],
            "tags": ["home speaker", "premium", "vintage design"]
        },
        "attributes": {
            "brand": "Marshall",
            "price": 32999,
            "currency": "INR",
            "payment_options": ["cash", "credit_card"],
            "availability": {"in_stock": True}
        },
        "links": {"external_url": "https://amazon.in/dp/SPEAKER003"}
    },
    
    # Drones
    {
        "product_id": "DRONE001",
        "category": "drone",
        "semantic_text": {
            "title": "DJI Mini 3 Pro with RC Controller",
            "description": "Ultralight 249g drone, 4K/60fps HDR Video, 34-min flight time, obstacle sensing",
            "features": ["249g Ultralight", "4K HDR Video", "34min Flight", "Tri-Directional Sensing"],
            "intended_use": ["aerial photography", "travel", "content creation", "vlogging"],
            "tags": ["beginner drone", "compact", "travel friendly"]
        },
        "attributes": {
            "brand": "DJI",
            "price": 89990,
            "currency": "INR",
            "payment_options": ["cash", "credit_card"],
            "availability": {"in_stock": True}
        },
        "links": {"external_url": "https://amazon.in/dp/DRONE001"}
    },
    {
        "product_id": "DRONE002",
        "category": "drone",
        "semantic_text": {
            "title": "DJI Air 3 Drone",
            "description": "Dual Primary Cameras, 46-min flight time, Omnidirectional Obstacle Sensing",
            "features": ["Dual Cameras", "46min Flight", "4K/60fps HDR", "O4 Transmission"],
            "intended_use": ["professional aerial", "filmmaking", "real estate", "events"],
            "tags": ["professional drone", "dual camera", "long flight"]
        },
        "attributes": {
            "brand": "DJI",
            "price": 109990,
            "currency": "INR",
            "payment_options": ["cash", "credit_card"],
            "availability": {"in_stock": True}
        },
        "links": {"external_url": "https://amazon.in/dp/DRONE002"}
    },
    
    # Smartphones (more variety)
    {
        "product_id": "PHONE001",
        "category": "smartphone",
        "semantic_text": {
            "title": "iPhone 15 Pro Max 256GB",
            "description": "A17 Pro chip, Titanium design, 48MP camera system, Action button",
            "features": ["A17 Pro Chip", "Titanium Design", "48MP Camera", "USB-C"],
            "intended_use": ["photography", "productivity", "gaming", "everyday use"],
            "tags": ["premium phone", "apple", "flagship"]
        },
        "attributes": {
            "brand": "Apple",
            "price": 159900,
            "currency": "INR",
            "payment_options": ["cash", "credit_card"],
            "availability": {"in_stock": True}
        },
        "links": {"external_url": "https://amazon.in/dp/PHONE001"}
    },
    {
        "product_id": "PHONE002",
        "category": "smartphone",
        "semantic_text": {
            "title": "Samsung Galaxy S24 Ultra 256GB",
            "description": "Galaxy AI features, 200MP camera, S Pen included, Titanium frame",
            "features": ["Galaxy AI", "200MP Camera", "S Pen", "Snapdragon 8 Gen 3"],
            "intended_use": ["photography", "productivity", "note taking", "gaming"],
            "tags": ["premium phone", "samsung", "flagship"]
        },
        "attributes": {
            "brand": "Samsung",
            "price": 134999,
            "currency": "INR",
            "payment_options": ["cash", "credit_card"],
            "availability": {"in_stock": True}
        },
        "links": {"external_url": "https://amazon.in/dp/PHONE002"}
    },
    {
        "product_id": "PHONE003",
        "category": "smartphone",
        "semantic_text": {
            "title": "OnePlus 12 256GB",
            "description": "Snapdragon 8 Gen 3, Hasselblad camera, 100W SUPERVOOC charging",
            "features": ["Snapdragon 8 Gen 3", "Hasselblad Camera", "100W Charging", "5400mAh Battery"],
            "intended_use": ["photography", "gaming", "fast charging", "everyday use"],
            "tags": ["flagship killer", "oneplus", "fast charging"]
        },
        "attributes": {
            "brand": "OnePlus",
            "price": 64999,
            "currency": "INR",
            "payment_options": ["cash", "credit_card"],
            "availability": {"in_stock": True}
        },
        "links": {"external_url": "https://amazon.in/dp/PHONE003"}
    },
    {
        "product_id": "PHONE004",
        "category": "smartphone",
        "semantic_text": {
            "title": "Google Pixel 8 Pro 128GB",
            "description": "Google Tensor G3, Best-in-class camera, 7 years of updates",
            "features": ["Tensor G3", "50MP Camera", "7yr Updates", "AI Features"],
            "intended_use": ["photography", "AI features", "clean android", "updates"],
            "tags": ["google phone", "camera phone", "pure android"]
        },
        "attributes": {
            "brand": "Google",
            "price": 106999,
            "currency": "INR",
            "payment_options": ["cash", "credit_card"],
            "availability": {"in_stock": True}
        },
        "links": {"external_url": "https://amazon.in/dp/PHONE004"}
    },
    {
        "product_id": "PHONE005",
        "category": "smartphone",
        "semantic_text": {
            "title": "Xiaomi 14 256GB",
            "description": "Leica optics, Snapdragon 8 Gen 3, 90W HyperCharge",
            "features": ["Leica Camera", "Snapdragon 8 Gen 3", "90W Charging", "Light Hunter 900"],
            "intended_use": ["photography", "value flagship", "fast charging"],
            "tags": ["budget flagship", "xiaomi", "leica"]
        },
        "attributes": {
            "brand": "Xiaomi",
            "price": 69999,
            "currency": "INR",
            "payment_options": ["cash", "credit_card"],
            "availability": {"in_stock": True}
        },
        "links": {"external_url": "https://amazon.in/dp/PHONE005"}
    },
    
    # PCs / Desktops
    {
        "product_id": "PC001",
        "category": "pc",
        "semantic_text": {
            "title": "Apple Mac Mini M2 Pro 16GB RAM 512GB",
            "description": "M2 Pro chip with 10-core CPU and 16-core GPU, compact desktop",
            "features": ["M2 Pro Chip", "16GB RAM", "512GB SSD", "10-core CPU"],
            "intended_use": ["content creation", "development", "office work", "video editing"],
            "tags": ["apple", "desktop", "compact"]
        },
        "attributes": {
            "brand": "Apple",
            "price": 112900,
            "currency": "INR",
            "payment_options": ["cash", "credit_card"],
            "availability": {"in_stock": True}
        },
        "links": {"external_url": "https://amazon.in/dp/PC001"}
    },
    {
        "product_id": "PC002",
        "category": "pc",
        "semantic_text": {
            "title": "ASUS ROG Strix G16 Gaming Desktop",
            "description": "Intel Core i7-13700KF, RTX 4070, 32GB DDR5, Gaming PC",
            "features": ["i7-13700KF", "RTX 4070", "32GB DDR5", "1TB NVMe"],
            "intended_use": ["gaming", "streaming", "content creation"],
            "tags": ["gaming pc", "asus rog", "high performance"]
        },
        "attributes": {
            "brand": "ASUS",
            "price": 189990,
            "currency": "INR",
            "payment_options": ["cash", "credit_card"],
            "availability": {"in_stock": True}
        },
        "links": {"external_url": "https://amazon.in/dp/PC002"}
    }
]

def main():
    # Load existing products
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        products = json.load(f)
    
    print(f"📦 Existing products: {len(products)}")
    
    # Count existing categories
    existing_categories = {}
    for p in products:
        cat = p.get("category", "unknown")
        existing_categories[cat] = existing_categories.get(cat, 0) + 1
    
    print(f"📊 Existing categories: {existing_categories}")
    
    # Add new products
    products.extend(NEW_PRODUCTS)
    
    print(f"➕ Added {len(NEW_PRODUCTS)} new products")
    
    # Count new categories
    new_categories = {}
    for p in products:
        cat = p.get("category", "unknown")
        new_categories[cat] = new_categories.get(cat, 0) + 1
    
    print(f"📊 New categories: {new_categories}")
    
    # Save updated catalog
    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved {len(products)} products to catalog")

if __name__ == "__main__":
    main()
