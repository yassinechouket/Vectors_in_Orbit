"""
Product Database Population Script
===================================
Scrubs and populates the Qdrant vector database with realistic product data.

This script:
1. Generates realistic product data across multiple categories
2. Creates embeddings using sentence-transformers (all-MiniLM-L6-v2)
3. Populates the Qdrant database with products and their vectors

Usage:
    python populate_database.py [--count 200] [--recreate]
"""

import os
import sys
import random
from typing import List, Dict, Any
from dataclasses import asdict
import argparse
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.qdrant.client import QdrantManager
from models.schemas import Product


# ============================================================
# PRODUCT DATA TEMPLATES
# ============================================================

# Image mapping for enhancement
CATEGORY_IMAGES = {
    "laptop": [
        "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1517336714731-489689fd1ca4?w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1593642702821-c8da6771f0c6?w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1611186871348-b1ce696e52c9?w=800&auto=format&fit=crop"
    ],
    "phone": [
        "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1592899677977-9c10ca588bbd?w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1598327105666-5b89351aff23?w=800&auto=format&fit=crop"
    ],
    "headphones": [
        "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1484704849700-f032a568e944?w=800&auto=format&fit=crop"
    ],
    "monitor": [
        "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1547394765-185e1e68f34e?w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1551643664-4054ff7a3b83?w=800&auto=format&fit=crop"
    ],
    "camera": [
        "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1502920917128-1aa500764cbd?w=800&auto=format&fit=crop"
    ]
}

PRODUCT_CATALOG = {
    "laptop": [
        {
            "name": "Dell XPS 13 Eco",
            "price": 799,
            "brand": "Dell",
            "description": "13-inch ultraportable laptop with 8th Gen Intel i5, 8GB RAM, 256GB SSD. Energy Star certified for eco-friendly computing. Perfect for coding and productivity work.",
            "rating": 4.7,
            "reviews_count": 5234,
            "eco_certified": True,
            "specs": {"processor": "Intel i5-8250U", "ram": "8GB", "storage": "256GB SSD", "screen": "13.3 FHD"},
            "image_url": random.choice(CATEGORY_IMAGES["laptop"])
        },
        {
            "name": "Lenovo ThinkPad E14",
            "price": 750,
            "brand": "Lenovo",
            "description": "Business laptop with AMD Ryzen 5, 16GB RAM, excellent keyboard for professionals. Durable build quality with military-grade testing.",
            "rating": 4.5,
            "reviews_count": 3821,
            "eco_certified": True,
            "specs": {"processor": "AMD Ryzen 5 4500U", "ram": "16GB", "storage": "512GB SSD", "screen": "14 FHD"},
            "image_url": random.choice(CATEGORY_IMAGES["laptop"])
        },
        {
            "name": "HP Pavilion 15 Gaming",
            "price": 899,
            "brand": "HP",
            "description": "Gaming laptop with NVIDIA GTX 1650, Intel i7, RGB keyboard. Great for gaming and content creation on a budget.",
            "rating": 4.3,
            "reviews_count": 2145,
            "eco_certified": False,
            "specs": {"processor": "Intel i7-10750H", "ram": "16GB", "storage": "512GB SSD", "gpu": "GTX 1650"},
            "image_url": random.choice(CATEGORY_IMAGES["laptop"])
        },
        {
            "name": "MacBook Air M2",
            "price": 1199,
            "brand": "Apple",
            "description": "Apple Silicon M2 chip, fanless design, incredible battery life. Perfect for developers and creative professionals.",
            "rating": 4.9,
            "reviews_count": 8923,
            "eco_certified": True,
            "specs": {"processor": "Apple M2", "ram": "8GB", "storage": "256GB SSD", "screen": "13.6 Retina"},
            "image_url": random.choice(CATEGORY_IMAGES["laptop"])
        },
        {
            "name": "ASUS ZenBook 14",
            "price": 849,
            "brand": "ASUS",
            "description": "Slim ultrabook with Intel i7, 16GB RAM, and NumberPad touchpad. Premium build quality for business professionals.",
            "rating": 4.6,
            "reviews_count": 4123,
            "eco_certified": False,
            "specs": {"processor": "Intel i7-1165G7", "ram": "16GB", "storage": "512GB SSD", "screen": "14 FHD"},
            "image_url": random.choice(CATEGORY_IMAGES["laptop"])
        },
        {
            "name": "Acer Aspire 5",
            "price": 549,
            "brand": "Acer",
            "description": "Budget-friendly laptop with Intel i5, perfect for students and everyday computing tasks. Great value for money.",
            "rating": 4.2,
            "reviews_count": 6234,
            "eco_certified": False,
            "specs": {"processor": "Intel i5-1135G7", "ram": "8GB", "storage": "256GB SSD", "screen": "15.6 FHD"},
            "image_url": random.choice(CATEGORY_IMAGES["laptop"])
        },
        {
            "name": "MSI GF65 Thin",
            "price": 1099,
            "brand": "MSI",
            "description": "Gaming laptop with RTX 3060, 144Hz display, excellent cooling system. High-performance gaming at an affordable price.",
            "rating": 4.4,
            "reviews_count": 2987,
            "eco_certified": False,
            "specs": {"processor": "Intel i7-10750H", "ram": "16GB", "storage": "512GB SSD", "gpu": "RTX 3060"},
        },
        {
            "name": "LG Gram 17",
            "price": 1499,
            "brand": "LG",
            "description": "Ultra-lightweight 17-inch laptop weighing only 2.98 lbs. Long battery life perfect for travel and productivity.",
            "rating": 4.8,
            "reviews_count": 1823,
            "eco_certified": True,
            "specs": {"processor": "Intel i7-1165G7", "ram": "16GB", "storage": "1TB SSD", "screen": "17 WQXGA"},
        },
    ],
    "monitor": [
        {
            "name": "Dell UltraSharp U2720Q",
            "price": 599,
            "brand": "Dell",
            "description": "27-inch 4K USB-C monitor with excellent color accuracy. IPS panel perfect for designers and photographers.",
            "rating": 4.7,
            "reviews_count": 3421,
            "eco_certified": True,
            "specs": {"size": "27 inch", "resolution": "4K UHD", "panel": "IPS", "refresh_rate": "60Hz"},
            "image_url": random.choice(CATEGORY_IMAGES["monitor"])
        },
        {
            "name": "LG 27GL850-B Gaming",
            "price": 449,
            "brand": "LG",
            "description": "27-inch 144Hz gaming monitor with 1ms response time and G-Sync. Perfect for competitive gaming.",
            "rating": 4.6,
            "reviews_count": 5634,
            "eco_certified": False,
            "specs": {"size": "27 inch", "resolution": "1440p", "panel": "IPS", "refresh_rate": "144Hz"},
            "image_url": random.choice(CATEGORY_IMAGES["monitor"])
        },
        {
            "name": "ASUS ROG Swift PG279Q",
            "price": 699,
            "brand": "ASUS",
            "description": "Premium gaming monitor with G-Sync, 165Hz, and stunning IPS display. Top-tier gaming experience.",
            "rating": 4.8,
            "reviews_count": 4234,
            "eco_certified": False,
            "specs": {"size": "27 inch", "resolution": "1440p", "panel": "IPS", "refresh_rate": "165Hz"},
            "image_url": random.choice(CATEGORY_IMAGES["monitor"])
        },
        {
            "name": "BenQ PD2700U Designer",
            "price": 549,
            "brand": "BenQ",
            "description": "4K monitor optimized for designers with CAD/CAM modes and 100% sRGB coverage.",
            "rating": 4.5,
            "reviews_count": 1923,
            "eco_certified": True,
            "specs": {"size": "27 inch", "resolution": "4K UHD", "panel": "IPS", "color_gamut": "100% sRGB"},
            "image_url": random.choice(CATEGORY_IMAGES["monitor"])
        },
        {
            "name": "Samsung Odyssey G5",
            "price": 299,
            "brand": "Samsung",
            "description": "Budget 144Hz curved gaming monitor with great value. 1440p resolution for immersive gaming.",
            "rating": 4.3,
            "reviews_count": 8234,
            "eco_certified": False,
            "specs": {"size": "27 inch", "resolution": "1440p", "panel": "VA", "refresh_rate": "144Hz"},
            "image_url": random.choice(CATEGORY_IMAGES["monitor"])
        },
    ],
    "headphones": [
        {
            "name": "Sony WH-1000XM5",
            "price": 399,
            "brand": "Sony",
            "description": "Industry-leading noise cancellation with exceptional sound quality. 30-hour battery life for audiophiles.",
            "rating": 4.9,
            "reviews_count": 12345,
            "eco_certified": True,
            "specs": {"type": "Over-ear", "wireless": True, "noise_canceling": True, "battery": "30 hours"},
            "image_url": random.choice(CATEGORY_IMAGES["headphones"])
        },
        {
            "name": "Bose QuietComfort 45",
            "price": 329,
            "brand": "Bose",
            "description": "Premium ANC headphones with legendary comfort. Perfect for long flights and commutes.",
            "rating": 4.7,
            "reviews_count": 9823,
            "eco_certified": False,
            "specs": {"type": "Over-ear", "wireless": True, "noise_canceling": True, "battery": "24 hours"},
            "image_url": random.choice(CATEGORY_IMAGES["headphones"])
        },
        {
            "name": "Apple AirPods Pro",
            "price": 249,
            "brand": "Apple",
            "description": "Active noise cancellation in compact earbuds. Seamless integration with Apple devices.",
            "rating": 4.8,
            "reviews_count": 23456,
            "eco_certified": True,
            "specs": {"type": "In-ear", "wireless": True, "noise_canceling": True, "battery": "6 hours"},
            "image_url": random.choice(CATEGORY_IMAGES["headphones"])
        },
        {
            "name": "Sennheiser HD 660S",
            "price": 499,
            "brand": "Sennheiser",
            "description": "Open-back audiophile headphones with reference sound quality. Perfect for critical listening.",
            "rating": 4.6,
            "reviews_count": 1823,
            "eco_certified": False,
            "specs": {"type": "Over-ear", "wireless": False, "impedance": "150 ohms", "driver": "42mm"},
        },
        {
            "name": "Anker Soundcore Life Q30",
            "price": 79,
            "brand": "Anker",
            "description": "Budget ANC headphones with impressive sound and 40-hour battery. Excellent value for money.",
            "rating": 4.5,
            "reviews_count": 15234,
            "eco_certified": False,
            "specs": {"type": "Over-ear", "wireless": True, "noise_canceling": True, "battery": "40 hours"},
        },
    ],
    "keyboard": [
        {
            "name": "Keychron K2 V2",
            "price": 89,
            "brand": "Keychron",
            "description": "Wireless mechanical keyboard with hot-swappable switches. Perfect for both Mac and Windows users.",
            "rating": 4.6,
            "reviews_count": 8234,
            "eco_certified": False,
            "specs": {"type": "Mechanical", "wireless": True, "switches": "Gateron", "layout": "75%"},
        },
        {
            "name": "Logitech MX Keys",
            "price": 99,
            "brand": "Logitech",
            "description": "Premium wireless keyboard with smart backlighting. Excellent for productivity and typing.",
            "rating": 4.7,
            "reviews_count": 12345,
            "eco_certified": True,
            "specs": {"type": "Membrane", "wireless": True, "battery": "10 days", "backlight": True},
        },
        {
            "name": "Corsair K95 RGB Platinum",
            "price": 199,
            "brand": "Corsair",
            "description": "Premium gaming keyboard with Cherry MX switches and RGB lighting. Dedicated macro keys for gaming.",
            "rating": 4.5,
            "reviews_count": 5634,
            "eco_certified": False,
            "specs": {"type": "Mechanical", "wireless": False, "switches": "Cherry MX", "rgb": True},
        },
        {
            "name": "Ducky One 2 Mini",
            "price": 109,
            "brand": "Ducky",
            "description": "Compact 60% mechanical keyboard with excellent build quality. Loved by enthusiasts and gamers.",
            "rating": 4.8,
            "reviews_count": 4231,
            "eco_certified": False,
            "specs": {"type": "Mechanical", "wireless": False, "switches": "Cherry MX", "layout": "60%"},
        },
    ],
    "mouse": [
        {
            "name": "Logitech MX Master 3S",
            "price": 99,
            "brand": "Logitech",
            "description": "Ultimate wireless productivity mouse with ultra-precise scrolling. Perfect for professionals and designers.",
            "rating": 4.8,
            "reviews_count": 15234,
            "eco_certified": True,
            "specs": {"type": "Wireless", "dpi": "8000", "buttons": 7, "rechargeable": True},
        },
        {
            "name": "Razer DeathAdder V3",
            "price": 69,
            "brand": "Razer",
            "description": "Legendary gaming mouse with ergonomic design. 30,000 DPI sensor for competitive gaming.",
            "rating": 4.7,
            "reviews_count": 8923,
            "eco_certified": False,
            "specs": {"type": "Wired", "dpi": "30000", "buttons": 8, "weight": "59g"},
        },
        {
            "name": "SteelSeries Rival 3",
            "price": 29,
            "brand": "SteelSeries",
            "description": "Budget gaming mouse with great sensor and RGB lighting. Excellent value for casual gamers.",
            "rating": 4.4,
            "reviews_count": 6234,
            "eco_certified": False,
            "specs": {"type": "Wired", "dpi": "8500", "buttons": 6, "rgb": True},
        },
    ],
    "tablet": [
        {
            "name": "iPad Air 2022",
            "price": 599,
            "brand": "Apple",
            "description": "M1 chip in a stunning 10.9-inch design. Perfect for students and creative professionals.",
            "rating": 4.8,
            "reviews_count": 9823,
            "eco_certified": True,
            "specs": {"processor": "Apple M1", "storage": "64GB", "screen": "10.9 inch", "stylus": "Apple Pencil 2"},
        },
        {
            "name": "Samsung Galaxy Tab S8",
            "price": 699,
            "brand": "Samsung",
            "description": "Premium Android tablet with S Pen included. 120Hz display for smooth scrolling.",
            "rating": 4.6,
            "reviews_count": 5634,
            "eco_certified": False,
            "specs": {"processor": "Snapdragon 8 Gen 1", "storage": "128GB", "screen": "11 inch", "refresh_rate": "120Hz"},
        },
        {
            "name": "Microsoft Surface Pro 9",
            "price": 999,
            "brand": "Microsoft",
            "description": "2-in-1 tablet that can replace your laptop. Intel i5 with Windows 11 for full productivity.",
            "rating": 4.5,
            "reviews_count": 3421,
            "eco_certified": False,
            "specs": {"processor": "Intel i5-1235U", "ram": "8GB", "storage": "256GB SSD", "screen": "13 inch"},
        },
    ],
    "smartphone": [
        {
            "name": "iPhone 15 Pro",
            "price": 999,
            "brand": "Apple",
            "description": "Titanium design with A17 Pro chip. Pro camera system with USB-C connectivity.",
            "rating": 4.8,
            "reviews_count": 12345,
            "eco_certified": True,
            "specs": {"processor": "A17 Pro", "storage": "128GB", "camera": "48MP", "screen": "6.1 OLED"},
        },
        {
            "name": "Samsung Galaxy S24",
            "price": 799,
            "brand": "Samsung",
            "description": "AI-powered flagship with excellent cameras. Long battery life and 120Hz display.",
            "rating": 4.7,
            "reviews_count": 8923,
            "eco_certified": False,
            "specs": {"processor": "Snapdragon 8 Gen 3", "storage": "256GB", "camera": "50MP", "screen": "6.2 AMOLED"},
        },
        {
            "name": "Google Pixel 8 Pro",
            "price": 899,
            "brand": "Google",
            "description": "Best Android camera with AI features. Pure Android experience with 7 years of updates.",
            "rating": 4.6,
            "reviews_count": 6234,
            "eco_certified": True,
            "specs": {"processor": "Tensor G3", "storage": "128GB", "camera": "50MP", "ai_features": True},
        },
    ],
    "smartwatch": [
        {
            "name": "Apple Watch Series 9",
            "price": 399,
            "brand": "Apple",
            "description": "Advanced health monitoring with always-on display. Seamless iPhone integration.",
            "rating": 4.8,
            "reviews_count": 15234,
            "eco_certified": True,
            "specs": {"display": "Always-on Retina", "battery": "18 hours", "health": "ECG, Blood Oxygen", "water_resistant": "50m"},
        },
        {
            "name": "Samsung Galaxy Watch 6",
            "price": 299,
            "brand": "Samsung",
            "description": "Stylish smartwatch with comprehensive health tracking. Works with Android and iOS.",
            "rating": 4.6,
            "reviews_count": 7823,
            "eco_certified": False,
            "specs": {"display": "AMOLED", "battery": "40 hours", "health": "Sleep tracking, Heart rate", "size": "44mm"},
        },
        {
            "name": "Garmin Fenix 7",
            "price": 699,
            "brand": "Garmin",
            "description": "Ultimate multisport GPS watch for athletes. Exceptional battery life up to 18 days.",
            "rating": 4.9,
            "reviews_count": 4123,
            "eco_certified": False,
            "specs": {"display": "MIP", "battery": "18 days", "gps": True, "sports_modes": "100+"},
        },
    ],
    "camera": [
        {
            "name": "Sony A7 IV",
            "price": 2499,
            "brand": "Sony",
            "description": "Full-frame mirrorless camera with 33MP sensor. Professional-grade for photo and video.",
            "rating": 4.9,
            "reviews_count": 3421,
            "eco_certified": False,
            "specs": {"sensor": "33MP Full-frame", "video": "4K 60fps", "autofocus": "759 points", "stabilization": "5-axis"},
        },
        {
            "name": "Canon EOS R6 Mark II",
            "price": 2399,
            "brand": "Canon",
            "description": "24MP full-frame with amazing autofocus. Perfect for wildlife and sports photography.",
            "rating": 4.8,
            "reviews_count": 2341,
            "eco_certified": False,
            "specs": {"sensor": "24MP Full-frame", "video": "4K 60fps", "fps": "40 fps", "iso": "102400"},
        },
    ],
}


# Store categories for different use cases
STORES = [
    "Amazon", "Best Buy", "Newegg", "B&H Photo", "Adorama",
    "Micro Center", "Target", "Walmart", "Apple Store", "Microsoft Store"
]


# ============================================================
# DATA GENERATION FUNCTIONS
# ============================================================

def generate_products_from_catalog() -> List[Dict[str, Any]]:
    """
    Generate product data from the catalog with variations.
    """
    products = []
    product_id = 1
    
    for category, items in PRODUCT_CATALOG.items():
        for base_product in items:
            # Create multiple variations with different stores and slight price variations
            num_variations = random.randint(1, 3)
            
            for i in range(num_variations):
                # Price variation: ±10%
                price_multiplier = random.uniform(0.9, 1.1)
                adjusted_price = round(base_product["price"] * price_multiplier, 2)
                
                product = {
                    "id": product_id,  # Use integer ID for Qdrant
                    "name": base_product["name"],
                    "price": adjusted_price,
                    "category": category,
                    "description": base_product["description"],
                    "store": random.choice(STORES),
                    "brand": base_product["brand"],
                    "rating": base_product["rating"] + random.uniform(-0.2, 0.2),
                    "reviews_count": base_product["reviews_count"] + random.randint(-500, 500),
                    "eco_certified": base_product["eco_certified"],
                    "in_stock": random.random() > 0.1,  # 90% in stock
                    "specs": base_product["specs"],
                    "image_url": base_product.get("image_url", f"https://example.com/images/{category}_{product_id}.jpg"),
                }
                
                # Clamp rating between 0 and 5
                product["rating"] = max(0, min(5, product["rating"]))
                product["reviews_count"] = max(0, product["reviews_count"])
                
                products.append(product)
                product_id += 1
    
    return products


def create_product_embedding_text(product: Dict[str, Any]) -> str:
    """
    Create a rich text representation of the product for embedding generation.
    This text captures all semantic information about the product.
    """
    parts = [
        f"Product: {product['name']}",
        f"Category: {product['category']}",
        f"Brand: {product['brand']}",
        f"Description: {product['description']}",
        f"Price: ${product['price']}",
    ]
    
    if product['eco_certified']:
        parts.append("Eco-friendly and environmentally certified")
    
    # Add specs
    if product['specs']:
        specs_text = " ".join([f"{k}: {v}" for k, v in product['specs'].items()])
        parts.append(f"Specifications: {specs_text}")
    
    return ". ".join(parts)


# ============================================================
# MAIN POPULATION LOGIC
# ============================================================

def populate_database(count: int = None, recreate: bool = False):
    """
    Main function to populate the Qdrant database.
    
    Args:
        count: Number of products to generate (None = all from catalog)
        recreate: Whether to recreate the collection (delete existing data)
    """
    print("=" * 60)
    print("Product Database Population Script")
    print("=" * 60)
    
    # Step 1: Initialize Qdrant connection
    print("\n[1/5] Connecting to Qdrant...")
    qdrant = QdrantManager()
    # Force REST API instead of gRPC for better compatibility
    qdrant._client = None
    from qdrant_client import QdrantClient
    qdrant._client = QdrantClient(
        host=qdrant.host,
        port=qdrant.port,
        prefer_grpc=False  # Use REST API
    )
    
    if not qdrant.health_check():
        print("❌ Error: Cannot connect to Qdrant!")
        print("Make sure Qdrant is running:")
        print("  docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant")
        return False
    
    print("✓ Connected to Qdrant successfully")
    
    # Step 2: Create/check collection
    print("\n[2/5] Setting up collection...")
    if recreate:
        print("⚠️  Recreating collection (existing data will be deleted)")
    
    success = qdrant.create_collection(recreate=recreate)
    if not success:
        print("❌ Error: Failed to create collection")
        return False
    
    collection_info = qdrant.get_collection_info()
    if collection_info:
        print(f"✓ Collection '{qdrant.COLLECTION_NAME}' ready")
        print(f"  Current points: {collection_info['points_count']}")
    
    # Step 3: Generate product data
    print("\n[3/5] Generating product data...")
    products = generate_products_from_catalog()
    
    if count:
        products = products[:count]
    
    print(f"✓ Generated {len(products)} products")
    print(f"  Categories: {', '.join(set(p['category'] for p in products))}")
    
    # Step 4: Generate embeddings
    print("\n[4/5] Generating embeddings...")
    print("  Loading sentence transformer model...")
    
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("✓ Model loaded")
    
    # Create embedding texts
    embedding_texts = [create_product_embedding_text(p) for p in products]
    
    print(f"  Encoding {len(embedding_texts)} products...")
    embeddings = model.encode(
        embedding_texts,
        show_progress_bar=True,
        convert_to_numpy=True
    )
    
    print(f"✓ Generated {len(embeddings)} embeddings ({embeddings.shape[1]}-dimensional)")
    
    # Step 5: Upload to Qdrant
    print("\n[5/5] Uploading to Qdrant...")
    
    # Upload in batches for better performance
    batch_size = 50
    total_uploaded = 0
    
    for i in tqdm(range(0, len(products), batch_size), desc="Uploading"):
        batch_products = products[i:i + batch_size]
        batch_embeddings = embeddings[i:i + batch_size].tolist()
        
        success = qdrant.upsert_products(
            products=batch_products,
            dense_vectors=batch_embeddings
        )
        
        if not success:
            print(f"❌ Error uploading batch {i // batch_size + 1}")
            return False
        
        total_uploaded += len(batch_products)
    
    print(f"\n✓ Successfully uploaded {total_uploaded} products")
    
    # Final status
    print("\n" + "=" * 60)
    print("Database Population Complete!")
    print("=" * 60)
    
    final_info = qdrant.get_collection_info()
    if final_info:
        print(f"\nCollection: {qdrant.COLLECTION_NAME}")
        print(f"  Total products: {final_info['points_count']}")
        print(f"  Status: {final_info['status']}")
    
    print("\n✓ Your vector database is ready for recommendations!")
    
    # Show some example products
    print("\nSample products:")
    for i, product in enumerate(products[:3], 1):
        print(f"\n  {i}. {product['name']}")
        print(f"     Category: {product['category']} | Price: ${product['price']}")
        print(f"     Brand: {product['brand']} | Rating: {product['rating']:.1f}/5.0")
    
    return True


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Populate Qdrant vector database with product data"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help="Number of products to generate (default: all from catalog)"
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Recreate collection (delete existing data)"
    )
    
    args = parser.parse_args()
    
    try:
        success = populate_database(count=args.count, recreate=args.recreate)
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
