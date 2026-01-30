"""
Debug script to test populate database and capture errors
"""
import sys
import traceback
from sentence_transformers import SentenceTransformer

# Add to path
sys.path.insert(0, '.')

from services.qdrant.client import QdrantManager

def test_populate():
    print("=" * 60)
    print("DEBUG: Testing Populate Database")
    print("=" * 60)
    
    # Test 1: Connection
    print("\n[1/4] Testing Qdrant connection...")
    qdrant = QdrantManager()
    
    if not qdrant.health_check():
        print("❌ ERROR: Cannot connect to Qdrant")
        return False
    
    print("✓ Connected to Qdrant")
    
    # Test 2: Create collection
    print("\n[2/4] Creating collection...")
    try:
        success = qdrant.create_collection(recreate=True)
        if not success:
            print("❌ ERROR: Failed to create collection")
            return False
        print("✓ Collection created")
    except Exception as e:
        print(f"❌ ERROR creating collection: {e}")
        traceback.print_exc()
        return False
    
    # Test 3: Create sample products
    print("\n[3/4] Creating sample products...")
    products = [
        {
            "id": 1,
            "name": "Test Laptop",
            "price": 999.99,
            "category": "laptop",
            "description": "A test laptop for debugging",
            "store": "Test Store",
            "brand": "TestBrand",
            "rating": 4.5,
            "reviews_count": 100,
            "eco_certified": True,
            "in_stock": True,
            "specs": {"ram": "8GB", "storage": "256GB"},
            "image_url": "https://example.com/test.jpg"
        },
        {
            "id": 2,
            "name": "Test Monitor",
            "price": 299.99,
            "category": "monitor",
            "description": "A test monitor for debugging",
            "store": "Test Store",
            "brand": "TestBrand",
            "rating": 4.3,
            "reviews_count": 50,
            "eco_certified": False,
            "in_stock": True,
            "specs": {"size": "24 inch", "resolution": "1080p"},
            "image_url": "https://example.com/test2.jpg"
        }
    ]
    
    print(f"  Created {len(products)} test products")
    
    # Test 4: Generate embeddings
    print("\n[4/4] Generating embeddings and uploading...")
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        texts = [f"{p['name']} {p['description']}" for p in products]
        embeddings = model.encode(texts, convert_to_numpy=True).tolist()
        
        print(f"  Generated {len(embeddings)} embeddings")
        print(f"  Embedding dimension: {len(embeddings[0])}")
        
        # Try to upsert
        print("\n  Attempting upsert...")
        success = qdrant.upsert_products(
            products=products,
            dense_vectors=embeddings
        )
        
        if not success:
            print("❌ ERROR: Upsert returned False")
            return False
        
        print("✓ Upsert completed")
        
    except Exception as e:
        print(f"❌ ERROR during upsert: {e}")
        traceback.print_exc()
        return False
    
    # Test 5: Verify data
    print("\n[5/5] Verifying data in Qdrant...")
    try:
        # Try to get info directly from client
        print("  Attempting to get collection info...")
        try:
            raw_info = qdrant.client.get_collection(qdrant.COLLECTION_NAME)
            print(f"  Raw info: {raw_info}")
            print(f"  Points count: {raw_info.points_count}")
        except Exception as e:
            print(f"  ❌ ERROR getting raw collection info: {e}")
            traceback.print_exc()
        
        info = qdrant.get_collection_info()
        if info:
            print(f"\n  Collection: {qdrant.COLLECTION_NAME}")
            print(f"  Points count: {info['points_count']}")
            print(f"  Status: {info['status']}")
            
            if info['points_count'] > 0:
                print("\n✅ SUCCESS! Data uploaded successfully")
                return True
            else:
                print("\n❌ ERROR: No data in collection!")
                return False
        else:
            print("❌ ERROR: Could not get collection info (returned None)")
            return False
            
    except Exception as e:
        print(f"❌ ERROR verifying data: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = test_populate()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)
