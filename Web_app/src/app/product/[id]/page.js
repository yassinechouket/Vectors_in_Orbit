import fs from "fs";
import path from "path";
import Breadcrumbs from "@/app/components/Breadcrumbs";
import ProductActions from "@/app/components/ProductActions";

export default async function ProductPage({ params }) {
  const { id } = await params;

  const filePath = path.join(
    process.cwd(),
    "public",
    "data",
    "reference_catalog_clean.json"
  );

  const products = JSON.parse(fs.readFileSync(filePath, "utf-8"));
  const product = products.find(p => p.product_id === id);

  if (!product) {
    return (
      <div className="product-page">
        <div className="product-not-found">
          <div className="not-found-icon">🔍</div>
          <h2>Product not found</h2>
          <p>The product you're looking for doesn't exist or has been removed.</p>
          <a href="/" className="btn-primary">← Back to Products</a>
        </div>
      </div>
    );
  }

  const { semantic_text, attributes, links, category, product_id } = product;

  const getCategoryEmoji = (cat) => {
    const emojis = {
      laptop: "💻", phone: "📱", smartphone: "📱", headphones: "🎧",
      tablet: "📱", camera: "📷", watch: "⌚", smartwatch: "⌚",
      speaker: "🔊", drone: "🚁", pc: "🖥️"
    };
    return emojis[cat?.toLowerCase()] || "📦";
  };

  const getCategoryImage = (cat) => {
    const images = {
      laptop: "/images/laptop.png",
      phone: "/images/smartphone.png",
      smartphone: "/images/smartphone.png",
      headphones: "/images/headphones.png",
      camera: "/images/camera.png",
      smartwatch: "/images/smartwatch.png",
      watch: "/images/smartwatch.png",
      speaker: "/images/speaker.png",
      drone: "/images/drone.png",
      pc: "/images/pc.png",
    };
    return images[cat?.toLowerCase()] || "/images/laptop.png";
  };

  return (
    <div className="product-page">
      <Breadcrumbs
        category={category}
        brand={attributes.brand}
        title={semantic_text.title}
      />

      <div className="product-container">
        {/* Product Gallery */}
        <div className="product-gallery">
          <div className="product-main-image">
            <img 
              src={getCategoryImage(category)} 
              alt={semantic_text.title}
              className="product-img"
            />
            {attributes.availability?.in_stock && (
              <div className="stock-indicator">
                <span className="stock-dot"></span>
                <span>In Stock</span>
              </div>
            )}
          </div>
        </div>

        {/* Product Info */}
        <div className="product-info">
          <div className="product-header">
            <span className="product-brand-tag">
              <span className="brand-icon">🏷️</span>
              {attributes.brand}
            </span>
            <span className="product-category-tag">
              {getCategoryEmoji(category)} {category}
            </span>
          </div>

          <h1 className="product-title">{semantic_text.title}</h1>
          
          {/* Rating Preview */}
          <div className="product-rating-preview">
            <div className="stars">
              {'★★★★★'.split('').map((star, i) => (
                <span key={i} className={i < 4 ? 'filled' : ''}>★</span>
              ))}
            </div>
            <span className="rating-count">(128 reviews)</span>
            <span className="rating-separator">|</span>
            <span className="sold-count">🔥 Best Seller</span>
          </div>
          
          <ProductActions product={product} />
        </div>
      </div>

      {/* Product Details Grid */}
      <div className="product-details-grid">
        <div className="product-section description-section">
          <div className="section-header">
            <span className="section-icon">📝</span>
            <h3>Description</h3>
          </div>
          <div className="section-content">
            <p className="product-description">{semantic_text.description}</p>
          </div>
        </div>

        <div className="product-section features-section">
          <div className="section-header">
            <span className="section-icon">⭐</span>
            <h3>Key Features</h3>
          </div>
          <div className="section-content">
            <ul className="features-list">
              {(semantic_text.features || []).map((f, i) => (
                <li key={i}>
                  <span className="feature-check">✓</span>
                  <span className="feature-text">{f}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="product-section use-section">
          <div className="section-header">
            <span className="section-icon">🎯</span>
            <h3>Perfect For</h3>
          </div>
          <div className="section-content">
            <div className="intended-use-tags">
              {(semantic_text.intended_use || []).map((u, i) => (
                <span key={i} className="use-tag">
                  <span className="use-icon">✨</span>
                  {u}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="product-section tags-section">
          <div className="section-header">
            <span className="section-icon">🏷️</span>
            <h3>Tags</h3>
          </div>
          <div className="section-content">
            <div className="product-tags">
              {(semantic_text.tags || []).map((tag, i) => (
                <span key={i} className="tag">#{tag}</span>
              ))}
            </div>
          </div>
        </div>

        <details className="product-section technical-section">
          <summary className="section-header clickable">
            <span className="section-icon">🔧</span>
            <h3>Technical Details</h3>
            <span className="expand-icon">▼</span>
          </summary>
          <div className="section-content">
            <div className="tech-grid">
              <div className="tech-item">
                <span className="tech-label">Product ID</span>
                <span className="tech-value">{product_id}</span>
              </div>
              <div className="tech-item">
                <span className="tech-label">Category</span>
                <span className="tech-value">{category}</span>
              </div>
              <div className="tech-item">
                <span className="tech-label">Brand</span>
                <span className="tech-value">{attributes.brand}</span>
              </div>
              <div className="tech-item">
                <span className="tech-label">Payment Options</span>
                <span className="tech-value">{(attributes.payment_options || []).join(", ") || "N/A"}</span>
              </div>
            </div>
          </div>
        </details>
      </div>
    </div>
  );
}
