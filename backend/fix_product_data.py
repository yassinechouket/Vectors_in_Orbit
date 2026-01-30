"""
Fix products with missing prices, titles, brands and ensure data quality.
This script fixes:
1. Missing/empty product titles (uses description as fallback)
2. Missing brands
3. Missing prices
4. Ensures all required fields exist
"""

import json
from pathlib import Path

CATALOG_PATH = Path(__file__).parent.parent / "Web_app" / "public" / "data" / "reference_catalog_clean.json"

# Specific fixes for known problematic products
PRODUCT_FIXES = {
    "B07S3VLQZR": {
        "title": "Lenovo ThinkPad T440 Renewed 14-inch Laptop (4th Gen Core i5/8GB/500GB HDD)",
        "brand": "Lenovo",
        "price": 25000,
    },
    "B0BVR5761Y": {
        "title": "Dell Latitude 7390 Renewed 13.3-inch Touch Laptop (Core i5 8th Gen/8GB/256GB SSD)",
        "brand": "Dell",
        "price": 35990,
    },
    "B08J13QWCB": {
        "price": 89990,
    },
    "B0BC9R8XYZ": {
        "price": 42990,
    },
    "B0BC9VHH9F": {
        "price": 42990,
    },
}

def extract_brand_from_description(description: str) -> str:
    """Try to extract brand from description text."""
    known_brands = [
        "HP", "Dell", "Lenovo", "Asus", "Acer", "Apple", "Samsung", "Sony",
        "Microsoft", "MSI", "Razer", "LG", "Xiaomi", "OnePlus", "Huawei",
        "Honor", "Realme", "OPPO", "Vivo", "Google", "JBL", "Bose", "Boat",
        "Nothing", "RedMI", "Redmi"
    ]
    desc_upper = description.upper()
    for brand in known_brands:
        if brand.upper() in desc_upper:
            return brand
    return None


def main():
    print("🔧 Fixing product data...")
    
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        products = json.load(f)
    
    fixed_count = 0
    title_fixes = 0
    brand_fixes = 0
    price_fixes = 0
    
    for product in products:
        product_id = product.get("product_id", "")
        attrs = product.get("attributes", {})
        semantic = product.get("semantic_text", {})
        
        # Apply specific fixes if available
        if product_id in PRODUCT_FIXES:
            fixes = PRODUCT_FIXES[product_id]
            if "title" in fixes:
                semantic["title"] = fixes["title"]
                title_fixes += 1
                print(f"  ✓ Fixed title for {product_id}")
            if "brand" in fixes:
                attrs["brand"] = fixes["brand"]
                brand_fixes += 1
                print(f"  ✓ Fixed brand for {product_id}")
            if "price" in fixes:
                attrs["price"] = fixes["price"]
                price_fixes += 1
                print(f"  ✓ Fixed price for {product_id}")
            fixed_count += 1
        
        # Fix empty/short titles - use description as fallback
        title = semantic.get("title", "")
        if not title or len(title) < 10:
            description = semantic.get("description", "")
            if description:
                # Use first part of description as title
                new_title = description[:80].strip()
                if new_title.endswith(","):
                    new_title = new_title[:-1]
                semantic["title"] = new_title
                title_fixes += 1
                fixed_count += 1
                print(f"  ✓ Auto-fixed title for {product_id}: {new_title[:40]}...")
        
        # Fix missing brands
        if not attrs.get("brand"):
            description = semantic.get("description", "") + " " + semantic.get("title", "")
            extracted_brand = extract_brand_from_description(description)
            if extracted_brand:
                attrs["brand"] = extracted_brand
                brand_fixes += 1
                fixed_count += 1
                print(f"  ✓ Auto-fixed brand for {product_id}: {extracted_brand}")
        
        # Fix missing prices
        if attrs.get("price") is None:
            category = product.get("category", "laptop")
            default_prices = {
                "laptop": 35000,
                "headphones": 3000,
                "smartphone": 20000,
                "smartwatch": 15000,
                "camera": 50000,
                "speaker": 5000,
                "drone": 40000,
                "tablet": 25000,
                "pc": 80000,
            }
            attrs["price"] = default_prices.get(category.lower(), 30000)
            price_fixes += 1
            fixed_count += 1
            print(f"  ✓ Set default price for {product_id}: {attrs['price']} INR")
        
        # Ensure currency is set
        if not attrs.get("currency"):
            attrs["currency"] = "INR"
        
        # Ensure availability exists
        if "availability" not in attrs:
            attrs["availability"] = {"in_stock": True}
        
        product["attributes"] = attrs
        product["semantic_text"] = semantic
    
    # Save fixed data
    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Fix Summary:")
    print(f"   📝 Titles fixed: {title_fixes}")
    print(f"   🏷️  Brands fixed: {brand_fixes}")
    print(f"   💰 Prices fixed: {price_fixes}")
    print(f"   📦 Total products: {len(products)}")
    print(f"\n⚠️  Remember to re-upload products to Qdrant:")
    print(f"   python upload_products.py")

if __name__ == "__main__":
    main()
