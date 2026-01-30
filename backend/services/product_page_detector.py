"""
Product Page Detection Service

Detects if HTML is a product page and extracts structured information
using Schema.org, OpenGraph, and pattern matching.
"""
from typing import Optional, Dict, Any, List
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
from urllib.parse import urlparse

from schemas.product_detection import (
    ProductPageDetection,
    ExtractedProductInfo,
    ProductPageResponse
)


class ProductPageDetector:
    """Detects and extracts product information from e-commerce pages"""
    
    # Common e-commerce platforms and their patterns
    ECOMMERCE_PLATFORMS = {
        'amazon': r'amazon\.(com|co\.uk|de|fr|ca|in)',
        'ebay': r'ebay\.(com|co\.uk|de|fr)',
        'shopify': r'\.myshopify\.com',
        'woocommerce': r'woocommerce',
        'etsy': r'etsy\.com',
        'walmart': r'walmart\.com',
        'target': r'target\.com',
        'aliexpress': r'aliexpress\.com',
    }
    
    def detect_product_page(self, html: str, url: str) -> ProductPageDetection:
        """
        Detect if the HTML represents a product page
        
        Args:
            html: HTML content
            url: Page URL
            
        Returns:
            ProductPageDetection with confidence score
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try multiple detection methods
        schema_org_result = self._detect_schema_org(soup)
        opengraph_result = self._detect_opengraph(soup)
        pattern_result = self._detect_by_patterns(soup, url)
        
        # Determine best result
        results = [
            ('schema.org', schema_org_result),
            ('opengraph', opengraph_result),
            ('pattern_match', pattern_result)
        ]
        
        # Use highest confidence detection
        best_source, best_confidence = max(results, key=lambda x: x[1])
        
        return ProductPageDetection(
            is_product_page=best_confidence > 0.5,
            confidence=best_confidence,
            source=best_source
        )
    
    def extract_product_info(self, html: str, url: str) -> Optional[ExtractedProductInfo]:
        """
        Extract structured product information from HTML
        
        Args:
            html: HTML content
            url: Page URL
            
        Returns:
            ExtractedProductInfo or None if extraction fails
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try Schema.org first (most reliable)
        info = self._extract_from_schema_org(soup)
        
        # Fall back to OpenGraph
        if not info or not info.name:
            og_info = self._extract_from_opengraph(soup)
            if og_info:
                info = self._merge_product_info(info, og_info) if info else og_info
        
        # Fall back to pattern matching
        if not info or not info.name:
            pattern_info = self._extract_from_patterns(soup, url)
            if pattern_info:
                info = self._merge_product_info(info, pattern_info) if info else pattern_info
        
        if info:
            info.url = url
        
        return info
    
    def enhance_prompt_with_context(
        self, 
        query: str, 
        product_info: ExtractedProductInfo
    ) -> str:
        """
        Enhance a search query with product context using broad characteristics + specific features.
        Target format: "[Category] [Brand] [Key Specs] [Adjectives]"
        """
        parts = []
        
        # 1. Start with Category (Broad context)
        if product_info.category:
            parts.append(product_info.category)
        
        # 2. Add Brand if available
        if product_info.brand:
            parts.append(product_info.brand)
        
        # 3. Add Key Specs (Attributes)
        if product_info.specifications:
            # Extract values that look like features (not too long, string or number)
            for k, v in list(product_info.specifications.items())[:4]:
                if isinstance(v, (str, int, float)) and len(str(v)) < 30:
                    parts.append(str(v))
        
        # 4. Add Name (but less emphasized than before to avoid overfitting)
        if product_info.name:
            # Clean name: remove special chars, keep meaningful words
            clean_name = re.sub(r'[^\w\s]', '', product_info.name)
            parts.append(clean_name)
            
        # 5. Add Price context
        if product_info.price:
            parts.append(f"around ${int(product_info.price)}")

        # Construct Query
        context_str = " ".join(parts)
        
        if query:
            return f"{query} {context_str}"
        else:
            return f"Find similar {context_str}"
    
    def _detect_schema_org(self, soup: BeautifulSoup) -> float:
        """Detect product page using Schema.org markup"""
        # Look for JSON-LD
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                if self._is_product_schema(data):
                    return 0.95  # High confidence
            except (json.JSONDecodeError, AttributeError):
                continue
        
        # Look for microdata
        if soup.find(attrs={'itemtype': re.compile(r'schema\.org/Product')}):
            return 0.90
        
        return 0.0
    
    def _detect_opengraph(self, soup: BeautifulSoup) -> float:
        """Detect product page using OpenGraph meta tags"""
        og_type = soup.find('meta', property='og:type')
        if og_type and 'product' in og_type.get('content', '').lower():
            return 0.85
        
        # Check for product-related og tags
        product_tags = soup.find_all('meta', property=re.compile(r'product:'))
        if len(product_tags) >= 2:
            return 0.80
        
        return 0.0
    
    def _detect_by_patterns(self, soup: BeautifulSoup, url: str) -> float:
        """Detect product page using common patterns"""
        score = 0.0
        
        # Check URL patterns
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path.lower()
        
        # Known e-commerce platforms
        for platform, pattern in self.ECOMMERCE_PLATFORMS.items():
            if re.search(pattern, domain):
                score += 0.3
                break
        
        # URL path patterns
        if re.search(r'/(product|item|p|dp)/|/[0-9]{8,}', path):
            score += 0.2
        
        # Check for common product page elements
        if soup.find(class_=re.compile(r'(product|item)-(title|name)', re.I)):
            score += 0.1
        
        if soup.find(class_=re.compile(r'(product|item)-(price|cost)', re.I)):
            score += 0.1
        
        if soup.find(class_=re.compile(r'add-to-(cart|basket|bag)', re.I)):
            score += 0.1
        
        if soup.find(attrs={'id': re.compile(r'(buy|purchase|add.*cart)', re.I)}):
            score += 0.1
        
        return min(score, 1.0)
    
    def _extract_from_schema_org(self, soup: BeautifulSoup) -> Optional[ExtractedProductInfo]:
        """Extract product info from Schema.org markup"""
        # Try JSON-LD first
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                product_data = self._find_product_in_schema(data)
                if product_data:
                    return self._parse_schema_product(product_data)
            except (json.JSONDecodeError, AttributeError):
                continue
        
        # Try microdata
        product_elem = soup.find(attrs={'itemtype': re.compile(r'schema\.org/Product')})
        if product_elem:
            return self._parse_microdata_product(product_elem)
        
        return None
    
    def _extract_from_opengraph(self, soup: BeautifulSoup) -> Optional[ExtractedProductInfo]:
        """Extract product info from OpenGraph meta tags"""
        info = ExtractedProductInfo()
        
        # Extract basic info
        og_tags = {
            'title': 'name',
            'description': 'description',
            'image': 'images',
            'product:price:amount': 'price',
            'product:price:currency': 'currency',
            'product:brand': 'brand',
            'product:category': 'category',
        }
        
        for og_prop, field in og_tags.items():
            tag = soup.find('meta', property=f'og:{og_prop}')
            if tag and tag.get('content'):
                content = tag['content']
                if field == 'images':
                    info.images = [content]
                elif field == 'price':
                    try:
                        info.price = float(content)
                    except ValueError:
                        pass
                else:
                    setattr(info, field, content)
        
        return info if info.name else None
    
    def _extract_from_patterns(self, soup: BeautifulSoup, url: str) -> Optional[ExtractedProductInfo]:
        """Extract product info using common HTML patterns"""
        info = ExtractedProductInfo()
        
        # Product name
        name_selectors = [
            {'class_': re.compile(r'product.*title', re.I)},
            {'id': re.compile(r'product.*title', re.I)},
            {'itemprop': 'name'},
        ]
        for selector in name_selectors:
            elem = soup.find(['h1', 'h2', 'span', 'div'], **selector)
            if elem:
                info.name = elem.get_text(strip=True)
                break
        
        # Price
        price_selectors = [
            {'class_': re.compile(r'price', re.I)},
            {'itemprop': 'price'},
        ]
        for selector in price_selectors:
            elem = soup.find(['span', 'div', 'p'], **selector)
            if elem:
                price_text = elem.get_text(strip=True)
                price_match = re.search(r'[\$£€]?\s*([0-9]+[.,][0-9]{2})', price_text)
                if price_match:
                    try:
                        info.price = float(price_match.group(1).replace(',', ''))
                        break
                    except ValueError:
                        pass
        
        # Images
        img_tag = soup.find('img', class_=re.compile(r'product.*image', re.I))
        if img_tag and img_tag.get('src'):
            info.images = [img_tag['src']]
        
        return info if info.name else None
    
    def _is_product_schema(self, data: Any) -> bool:
        """Check if schema data represents a product"""
        if isinstance(data, dict):
            type_val = data.get('@type', '').lower()
            if 'product' in type_val:
                return True
            # Check nested structures
            for value in data.values():
                if self._is_product_schema(value):
                    return True
        elif isinstance(data, list):
            return any(self._is_product_schema(item) for item in data)
        return False
    
    def _find_product_in_schema(self, data: Any) -> Optional[Dict]:
        """Find product object in schema data"""
        if isinstance(data, dict):
            if 'product' in data.get('@type', '').lower():
                return data
            for value in data.values():
                result = self._find_product_in_schema(value)
                if result:
                    return result
        elif isinstance(data, list):
            for item in data:
                result = self._find_product_in_schema(item)
                if result:
                    return result
        return None
    
    def _parse_schema_product(self, data: Dict) -> ExtractedProductInfo:
        """Parse Schema.org product data"""
        info = ExtractedProductInfo()
        
        info.name = data.get('name')
        info.description = data.get('description')
        info.brand = data.get('brand', {}).get('name') if isinstance(data.get('brand'), dict) else data.get('brand')
        info.category = data.get('category')
        info.sku = data.get('sku')
        
        # Price
        offers = data.get('offers', {})
        if isinstance(offers, dict):
            info.price = self._safe_float(offers.get('price'))
            info.currency = offers.get('priceCurrency')
            info.availability = offers.get('availability', '').split('/')[-1]
        
        # Images
        image = data.get('image')
        if isinstance(image, str):
            info.images = [image]
        elif isinstance(image, list):
            info.images = image
        
        # Rating
        rating = data.get('aggregateRating', {})
        if rating:
            info.rating = self._safe_float(rating.get('ratingValue'))
            info.review_count = self._safe_int(rating.get('reviewCount'))
        
        return info
    
    def _parse_microdata_product(self, elem) -> ExtractedProductInfo:
        """Parse microdata product element"""
        info = ExtractedProductInfo()
        
        # Extract itemprop values
        for prop in ['name', 'description', 'brand', 'category', 'sku']:
            prop_elem = elem.find(attrs={'itemprop': prop})
            if prop_elem:
                setattr(info, prop, prop_elem.get_text(strip=True))
        
        # Price
        price_elem = elem.find(attrs={'itemprop': 'price'})
        if price_elem:
            info.price = self._safe_float(price_elem.get('content') or price_elem.get_text(strip=True))
        
        # Images
        img_elem = elem.find('img', attrs={'itemprop': 'image'})
        if img_elem:
            info.images = [img_elem.get('src', '')]
        
        return info
    
    def _merge_product_info(
        self, 
        base: ExtractedProductInfo, 
        additional: ExtractedProductInfo
    ) -> ExtractedProductInfo:
        """Merge two product info objects, preferring non-null values from base"""
        for field in base.model_fields:
            base_val = getattr(base, field)
            add_val = getattr(additional, field)
            
            if base_val is None and add_val is not None:
                setattr(base, field, add_val)
            elif field == 'images' and add_val:
                base.images = list(set(base.images + add_val))
            elif field == 'specifications' and add_val:
                base.specifications.update(add_val)
        
        return base
    
    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        """Safely convert value to float"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def _safe_int(value: Any) -> Optional[int]:
        """Safely convert value to int"""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None


# Singleton instance
product_detector = ProductPageDetector()
