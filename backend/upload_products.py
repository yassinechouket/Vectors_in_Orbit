"""
Upload Products to Qdrant Database

This script reads the product catalog and uploads all products to the Qdrant
vector database for AI-powered recommendations.
"""

import json
import hashlib
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer

# Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "products")
CATALOG_PATH = Path(__file__).parent.parent / "Web_app" / "public" / "data" / "reference_catalog_clean.json"

# Image mapping for categories
CATEGORY_IMAGES = {
    "laptop": "/images/laptop.png",
    "smartphone": "/images/smartphone.png",
    "phone": "/images/smartphone.png",
    "headphones": "/images/headphones.png",
    "earbuds": "/images/headphones.png",
    "camera": "/images/camera.png",
    "smartwatch": "/images/smartwatch.png",
    "watch": "/images/smartwatch.png",
    "speaker": "/images/speaker.png",
    "drone": "/images/drone.png",
    "pc": "/images/pc.png",
    "computer": "/images/pc.png",
    "default": "/images/laptop.png"  # Fallback image
}

# Currency conversion: INR to TND (1 TND ≈ 27 INR)
INR_TO_TND = 27.0


def get_image_for_category(category: str) -> str:
    """Get image path for a category."""
    if not category:
        return CATEGORY_IMAGES["default"]
    return CATEGORY_IMAGES.get(category.lower(), CATEGORY_IMAGES["default"])


def convert_price_to_tnd(price_inr: float) -> float:
    """Convert INR price to TND."""
    if not price_inr:
        return 0
    return round(price_inr / INR_TO_TND, 2)


def string_to_int_id(string_id: str) -> int:
    """Convert string ID to integer using MD5 hash."""
    hash_object = hashlib.md5(string_id.encode())
    hash_hex = hash_object.hexdigest()
    return int(hash_hex[:16], 16)


def build_semantic_text(product: dict) -> str:
    """Build semantic text for embedding from product data."""
    semantic = product.get("semantic_text", {})
    attrs = product.get("attributes", {})
    
    parts = [
        semantic.get("title", ""),
        semantic.get("description", ""),
        " ".join(semantic.get("features", [])),
        " ".join(semantic.get("intended_use", [])),
        " ".join(semantic.get("tags", [])),
        f"Brand: {attrs.get('brand', '')}",
        f"Category: {product.get('category', '')}",
        f"Price: {attrs.get('price', '')} {attrs.get('currency', '')}"
    ]
    
    return " ".join(filter(None, parts))


def main():
    print("🚀 Matcha AI - Product Upload Script")
    print("=" * 50)
    
    # Load products
    print(f"\n📦 Loading products from: {CATALOG_PATH}")
    if not CATALOG_PATH.exists():
        print(f"❌ Error: Catalog file not found at {CATALOG_PATH}")
        return
    
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        products = json.load(f)
    
    print(f"   Found {len(products)} products")
    
    # Initialize Qdrant client
    print(f"\n🔌 Connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}")
    try:
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        collections = client.get_collections()
        print(f"   Connected! Found {len(collections.collections)} collections")
    except Exception as e:
        print(f"❌ Error connecting to Qdrant: {e}")
        print("   Make sure Qdrant is running: docker-compose up -d")
        return
    
    # Load embedding model
    print("\n🧠 Loading embedding model...")
    try:
        model = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
    except Exception:
        print("   Model not cached, downloading...")
        model = SentenceTransformer("all-MiniLM-L6-v2")
    
    vector_size = model.get_sentence_embedding_dimension()
    print(f"   Model loaded! Vector size: {vector_size}")
    
    # Create or recreate collection
    print(f"\n📁 Setting up collection: {COLLECTION_NAME}")
    try:
        client.delete_collection(COLLECTION_NAME)
        print("   Deleted existing collection")
    except:
        pass
    
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=vector_size,
            distance=models.Distance.COSINE
        )
    )
    print(f"   Created collection with COSINE distance")
    
    # Prepare points
    print("\n⚡ Generating embeddings and preparing data...")
    points = []
    
    for i, product in enumerate(products):
        product_id = product.get("product_id", f"product_{i}")
        semantic_text = build_semantic_text(product)
        category = product.get("category", "")
        
        # Generate embedding
        embedding = model.encode(semantic_text).tolist()
        
        # Get attributes and convert price to TND
        attrs = product.get("attributes", {})
        original_price = attrs.get("price", 0)
        tnd_price = convert_price_to_tnd(original_price)
        
        # Build updated attributes with TND price
        updated_attrs = {
            **attrs,
            "price": tnd_price,
            "currency": "TND",
            "original_price_inr": original_price
        }
        
        # Get image URL based on category
        image_url = get_image_for_category(category)
        
        # Create point
        point = models.PointStruct(
            id=string_to_int_id(product_id),
            vector=embedding,
            payload={
                "product_id": product_id,
                "category": category,
                "semantic_text": product.get("semantic_text", {}),
                "attributes": updated_attrs,
                "links": product.get("links", {}),
                "image_url": image_url
            }
        )
        points.append(point)
        
        if (i + 1) % 10 == 0 or i == len(products) - 1:
            print(f"   Processed {i + 1}/{len(products)} products (Price: {original_price} INR → {tnd_price} TND)")
    
    # Upload to Qdrant
    print("\n📤 Uploading to Qdrant...")
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=batch
        )
        print(f"   Uploaded batch {i // batch_size + 1}/{(len(points) + batch_size - 1) // batch_size}")
    
    # Verify
    print("\n✅ Upload complete!")
    info = client.get_collection(COLLECTION_NAME)
    print(f"   Collection: {COLLECTION_NAME}")
    print(f"   Points count: {info.points_count}")
    print(f"   Vector size: {info.config.params.vectors.size}")
    
    # Test search
    print("\n🔍 Testing search with query: 'laptop for programming'")
    test_query = "laptop for programming"
    test_vector = model.encode(test_query).tolist()
    
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=test_vector,
        limit=3
    )
    
    print("   Top 3 results:")
    for i, result in enumerate(results.points):
        title = result.payload.get("semantic_text", {}).get("title", "Unknown")[:50]
        brand = result.payload.get("attributes", {}).get("brand", "Unknown")
        print(f"   {i + 1}. [{result.score:.4f}] {brand} - {title}...")
    
    print("\n🎉 All done! Your products are ready for AI recommendations.")


if __name__ == "__main__":
    main()
