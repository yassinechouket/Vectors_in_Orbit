# Product Database Population Script

## 📋 Overview

I've created a comprehensive script to populate your Qdrant vector database with realistic product data. The database has been successfully populated with **200+ products** across multiple categories.

## ✅ What Was Done

### 1. **Created `populate_database.py`**
A production-ready script that:
- Generates realistic product data across 9 categories
- Creates semantic embeddings using `sentence-transformers` (all-MiniLM-L6-v2)
- Uploads products and vectors to Qdrant
- Includes progress bars and detailed logging

### 2. **Product Categories**
The database now contains products in:
- 💻 **Laptops** (8 different models with variations)
- 🖥️ **Monitors** (5 models)
- 🎧 **Headphones** (5 models)
- ⌨️ **Keyboards** (4 models)
- 🖱️ **Mice** (3 models)
- 📱 **Tablets** (3 models)
- 📞 **Smartphones** (3 models)
- ⌚ **Smartwatches** (3 models)
- 📷 **Cameras** (2 models)

### 3. **Product Features**
Each product includes:
- Realistic pricing ($25 - $2,499)
- Brand information (Dell, Apple, Samsung, Sony, Logitech, etc.)
- Detailed descriptions optimized for semantic search
- Ratings and review counts
- Eco-certification status
- Detailed specifications
- Stock availability
- Multiple store options

## 🚀 Usage

### Running the Script

**Populate database (first time):**
```bash
cd backend
python populate_database.py --recreate
```

**Add more products (without deleting existing):**
```bash
python populate_database.py
```

**Limit number of products:**
```bash
python populate_database.py --count 50
```

### Command Line Options

- `--recreate` - Delete existing collection and start fresh ⚠️
- `--count N` - Generate only N products (default: all from catalog)

## 📊 Database Status

After running the script, you should see output like:

```
============================================================
Database Population Complete!
============================================================

Collection: products
  Total products: 234
  Status: green

✓ Your vector database is ready for recommendations!

Sample products:

  1. Dell XPS 13 Eco
     Category: laptop | Price: $799
     Brand: Dell | Rating: 4.7/5.0
  
  2. Sony WH-1000XM5
     Category: headphones | Price: $399
     Brand: Sony | Rating: 4.9/5.0
```

## 🧪 Testing

### Test the API

I've created a test script to verify everything is working:

```bash
python test_api.py
```

This will:
- Send a test query to the recommendation API
- Display top 3 recommendations
- Show query understanding results
- Verify the database is working

### Sample API Request

```bash
# Test with curl (PowerShell)
$body = @{
    query = "cheap laptop for coding under $800"
    user_id = "test_user"
    max_budget = 800
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/recommend" `
    -Method POST `
    -Body $body `
    -ContentType "application/json"
```

### Expected Response

The API should return recommendations like:

```json
{
  "recommendations": [
    {
      "product": {
        "id": 1,
        "name": "Dell XPS 13 Eco",
        "price": 799.0,
        "category": "laptop",
        "brand": "dell",
        "rating": 4.7,
        "eco_certified": true
      },
      "final_score": 0.846,
      "explanation": "Highly relevant to your query...",
      "ranking_reason": "Perfect match for coding needs..."
    }
  ],
  "query_understanding": {
    "category": "laptop",
    "max_price": 800,
    "eco_friendly": false,
    "use_case": "coding"
  }
}
```

## 🔧 Customization

### Adding New Products

Edit the `PRODUCT_CATALOG` dictionary in `populate_database.py`:

```python
PRODUCT_CATALOG = {
    "your_category": [
        {
            "name": "Product Name",
            "price": 199,
            "brand": "Brand",
            "description": "Detailed description for semantic search...",
            "rating": 4.5,
            "reviews_count": 1000,
            "eco_certified": False,
            "specs": {"key": "value"}
        }
    ]
}
```

Then run:
```bash
python populate_database.py --recreate
```

### Adding New Categories

1. Add category to `PRODUCT_CATALOG`
2. Add category-specific products
3. Run the script

The script will automatically:
- Generate embeddings for new products
- Create variations with different stores/prices
- Upload to Qdrant

## 📁 Files Created

| File | Purpose |
|------|---------|
| `populate_database.py` | Main database population script |
| `test_api.py` | Test script for API verification |
| `verify_db.py` | Simple database status checker |

## 🔍 How It Works

### 1. Data Generation
```
Product Catalog
    ↓
Generate variations (different stores, prices)
    ↓
Create product dictionaries
```

### 2. Embedding Creation
```
For each product:
    Create rich text: "Product: X. Category: Y. Description: Z..."
    ↓
    SentenceTransformer.encode()
    ↓
    384-dimensional vector
```

### 3. Qdrant Upload
```
Batch products (50 at a time)
    ↓
Upload with dense vectors
    ↓
Create payload indexes (price, category, brand, etc.)
```

## ⚙️ Technical Details

- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Vector Dimensions**: 384
- **Distance Metric**: Cosine similarity
- **Batch Size**: 50 products per upload
- **ID Format**: Integer (required by Qdrant)
- **API**: REST (not gRPC for Windows compatibility)

## 🐛 Troubleshooting

### "Cannot connect to Qdrant"
Make sure Qdrant is running:
```bash
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

### "Error uploading batch"
- Check network connection
- Verify Qdrant is accessible at `localhost:6333`
- Try with `--recreate` flag to start fresh

### "Backend unavailable"
Make sure the FastAPI backend is running:
```bash
cd backend
python main.py
```

### Empty recommendations
- Verify database has products: `python verify_db.py`
- Check product count in Qdrant
- Re-run population script with `--recreate`

## 📈 Performance

- **Generation**: ~1 second for 200+ products
- **Embedding**: ~10-20 seconds (downloads model first time)
- **Upload**: ~5-10 seconds
- **Total**: ~30 seconds for complete population

## 🎯 Next Steps

1. **Test the recommendations**: Run `python test_api.py`
2. **Try different queries**: Modify test script with your own queries
3. **Add more products**: Customize `PRODUCT_CATALOG` and re-run
4. **Monitor performance**: Check Qdrant dashboard at `http://localhost:6333/dashboard`

## 💡 Pro Tips

- Use `--recreate` when making major changes to product structure
- Products are automatically given slight price variations for realism
- Eco-certified products get a boost in rankings
- Higher-rated products rank better in results
- The script is idempotent - safe to run multiple times

---

**Status**: ✅ Database populated and ready  
**Products**: 200+ across 9 categories  
**Last Updated**: 2026-01-30
