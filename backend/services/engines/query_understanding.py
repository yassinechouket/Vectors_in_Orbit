import os
import json
import re
import sys
from typing import Optional, Dict, Any, List
from sentence_transformers import SentenceTransformer

# Add providers to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from providers.gemini_provider import GeminiProvider
from providers.llama_provider import LlamaProvider
from models.schemas import ParsedIntent, QueryEmbedding, SearchFilters
from prompts.prompts import system_prompt_text


class QueryUnderstandingEngine:
    """
    Extracts structured intent from natural language queries.
    
    Responsibilities:
    - Parse user query into structured intent (category, budget, preferences)
    - Generate dense semantic embedding
    - Generate sparse keyword vector (optional)
    - Build search filters for Qdrant
    """
    
    SYSTEM_PROMPT = system_prompt_text
    
    # Category synonyms - map various terms to standard categories in Qdrant
    CATEGORY_SYNONYMS = {
        # PC/Desktop variations
        "pc": ["pc", "laptop", "desktop", "computer"],
        "desktop": ["pc", "laptop", "desktop", "computer"],
        "computer": ["pc", "laptop", "desktop", "computer"],
        "gaming pc": ["pc", "laptop"],
        "mac": ["pc", "laptop"],
        "macbook": ["laptop"],
        "notebook": ["laptop"],
        "ultrabook": ["laptop"],
        "chromebook": ["laptop"],
        
        # Phone variations
        "phone": ["smartphone"],
        "mobile": ["smartphone"],
        "iphone": ["smartphone"],
        "android": ["smartphone"],
        "samsung phone": ["smartphone"],
        "pixel": ["smartphone"],
        "oneplus": ["smartphone"],
        "xiaomi": ["smartphone"],
        
        # Headphone variations
        "earphones": ["headphones"],
        "earbuds": ["headphones"],
        "airpods": ["headphones"],
        "headset": ["headphones"],
        
        # Watch variations
        "watch": ["smartwatch"],
        "apple watch": ["smartwatch"],
        "galaxy watch": ["smartwatch"],
        "fitness band": ["smartwatch"],
        "fitness tracker": ["smartwatch"],
        
        # Camera variations
        "dslr": ["camera"],
        "mirrorless": ["camera"],
        
        # Speaker variations
        "bluetooth speaker": ["speaker"],
        "portable speaker": ["speaker"],
        "soundbar": ["speaker"],
    }

    def __init__(
        self,
        provider: str = "gemini",
        embedding_model: str = "all-MiniLM-L6-v2",
        **provider_kwargs,
    ):
        """
        Initialize the query understanding engine.
        
        Args:
            provider: Provider to use ("gemini" or "llama")
            embedding_model: Sentence transformer model for embeddings
            **provider_kwargs: Additional kwargs for the provider
        """
        # Initialize the selected provider
        if provider.lower() == "gemini":
            self.llm_provider = GeminiProvider(**provider_kwargs)
        elif provider.lower() == "llama":
            self.llm_provider = LlamaProvider(**provider_kwargs)
        else:
            raise ValueError(f"Unsupported provider: {provider}. Use 'gemini' or 'llama'")
        
        # Load embedding model from cache (offline mode)
        self.embedding_model = SentenceTransformer(embedding_model, local_files_only=True)
    
    async def understand(self, query: str) -> ParsedIntent:
        """
        Parse user query and extract structured intent.
        
        Args:
            query: Natural language user query
            
        Returns:
            ParsedIntent with extracted information
        """
        # Try LLM extraction first
        try:
            intent = await self._llm_extract_intent(query)
            
            # Get rule-based fallback to fill in any missing fields
            fallback = self._rule_based_fallback(query)
            
            # Merge: use LLM values, but fallback for missing critical fields
            if intent.max_price is None and fallback.max_price is not None:
                intent.max_price = fallback.max_price
            if intent.min_price is None and fallback.min_price is not None:
                intent.min_price = fallback.min_price
            if not intent.brand_preferences and fallback.brand_preferences:
                intent.brand_preferences = fallback.brand_preferences
            if intent.category is None and fallback.category is not None:
                intent.category = fallback.category
                
        except Exception as e:
            print(f"LLM extraction failed, using fallback: {e}")
            intent = self._rule_based_fallback(query)
        
        return intent
    
    async def _llm_extract_intent(self, query: str) -> ParsedIntent:
        """Use LLM to extract structured intent"""
        
        # Call the provider with system and user prompts
        response_content = await self.llm_provider(
            prompt=query,
            system=self.SYSTEM_PROMPT,
            temperature=0.1,
        )
        
        # Extract JSON from response (some providers may wrap it in markdown)
        json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', response_content, re.DOTALL)
        if json_match:
            response_content = json_match.group(1)
        
        result = json.loads(response_content)
        
        return ParsedIntent(
            category=result.get("category"),
            max_price=result.get("max_price"),
            min_price=result.get("min_price"),
            eco_friendly=result.get("eco_friendly", False),
            preferences=result.get("preferences", []),
            use_case=result.get("use_case"),
            priority=result.get("priority", "balanced"),
            brand_preferences=result.get("brand_preferences", []),
            excluded_brands=result.get("excluded_brands", []),
            keywords=result.get("keywords", []),
        )
    
    def _rule_based_fallback(self, query: str) -> ParsedIntent:
        """Rule-based fallback when LLM is unavailable"""
        query_lower = query.lower()
        
        # Extract price - all prices are in TND
        max_price = None
        min_price = None
        
        # Check for TND price ranges: "between 2000 and 3000 TND" or "2000-3000 TND"
        tnd_range = re.search(r'(?:between\s*)?(\d+)\s*(?:and|-|to)\s*(\d+)\s*(?:tnd)?', query_lower)
        if tnd_range:
            min_price = float(tnd_range.group(1))
            max_price = float(tnd_range.group(2))
        
        # Check for max price patterns: "under 500", "below 2000", "less than 1000"
        if max_price is None:
            tnd_max = re.search(r'(?:under|below|less\s*than|max|up\s*to|budget)\s*(\d+)\s*(?:tnd)?', query_lower)
            if tnd_max:
                max_price = float(tnd_max.group(1))
        
        # Check for standalone TND price: "500 TND", "2000tnd"
        if max_price is None:
            tnd_single = re.search(r'(\d+)\s*tnd', query_lower)
            if tnd_single:
                max_price = float(tnd_single.group(1))
        
        # Check for USD prices and convert to TND (1 USD ≈ 3 TND)
        if max_price is None:
            price_patterns = [
                r'under\s*\$(\d+)',
                r'below\s*\$(\d+)',
                r'less than\s*\$(\d+)',
                r'\$(\d+)\s*budget',
                r'\$(\d+)',
            ]
            for pattern in price_patterns:
                match = re.search(pattern, query_lower)
                if match:
                    max_price = float(match.group(1)) * 3  # USD to TND
                    break
        
        # Extract brand preferences from query
        brand_preferences = []
        brand_keywords = {
            "apple": ["apple", "macbook", "iphone", "ipad", "airpods", "mac mini", "imac"],
            "samsung": ["samsung", "galaxy"],
            "lenovo": ["lenovo", "thinkpad", "ideapad"],
            "hp": ["hp", "pavilion", "envy", "spectre", "omen", "victus"],
            "asus": ["asus", "rog", "vivobook", "zenbook"],
            "dell": ["dell", "xps", "inspiron", "alienware"],
            "sony": ["sony", "xperia", "alpha"],
            "google": ["google", "pixel"],
            "dji": ["dji", "mavic"],
            "nikon": ["nikon"],
            "canon": ["canon", "eos"],
        }
        for brand, keywords in brand_keywords.items():
            if any(kw in query_lower for kw in keywords):
                brand_preferences.append(brand)
        
        # Extract category
        category = None
        categories = {
            "laptop": ["laptop", "notebook", "macbook", "chromebook", "ultrabook", "thinkpad", "ideapad", "vivobook"],
            "smartphone": ["phone", "smartphone", "iphone", "android", "mobile", "galaxy s", "pixel"],
            "headphones": ["headphone", "headphones", "earbuds", "earphones", "airpods", "earphone", "wireless headphone", "bluetooth headphone", "wireless earbuds", "wireless"],
            "smartwatch": ["smartwatch", "watch", "wearable", "fitness band", "apple watch", "galaxy watch"],
            "camera": ["camera", "dslr", "mirrorless", "photography"],
            "speaker": ["speaker", "speakers", "bluetooth speaker", "soundbar", "audio"],
            "drone": ["drone", "drones", "quadcopter", "aerial", "mavic"],
            "pc": ["pc", "desktop", "computer", "mac mini", "imac"],
        }
        for cat, keywords in categories.items():
            if any(kw in query_lower for kw in keywords):
                category = cat
                break
        
        # Special case: "wireless" alone likely means headphones
        if category is None and "wireless" in query_lower:
            category = "headphones"
        
        # Check for eco preference
        eco_friendly = any(word in query_lower for word in [
            "eco", "sustainable", "green", "environmental", "recyclable"
        ])
        
        # Determine priority
        priority = "balanced"
        if any(word in query_lower for word in ["cheap", "budget", "affordable", "low cost", "inexpensive"]):
            priority = "price"
        elif any(word in query_lower for word in ["best", "premium", "quality", "top", "high-end", "pro"]):
            priority = "quality"
        elif eco_friendly:
            priority = "eco"
        
        # Extract keywords
        stop_words = {"i", "want", "need", "looking", "for", "a", "an", "the", "me", "to", "with"}
        keywords = [w for w in query_lower.split() if w not in stop_words]
        
        return ParsedIntent(
            category=category,
            max_price=max_price,
            min_price=min_price,
            eco_friendly=eco_friendly,
            priority=priority,
            keywords=keywords,
            brand_preferences=brand_preferences,
        )
    
    def generate_embedding(self, query: str, intent: ParsedIntent) -> QueryEmbedding:
        """
        Generate dense embedding for semantic search.
        
        Args:
            query: Original user query
            intent: Parsed intent for context
            
        Returns:
            QueryEmbedding with dense vector
        """
        # Build enriched text for embedding
        enriched_text = self._build_embedding_text(query, intent)
        
        # Generate dense embedding
        dense_vector = self.embedding_model.encode(enriched_text).tolist()
        
        # Generate sparse vector (simple TF-based)
        sparse_vector = self._build_sparse_vector(intent.keywords)
        
        return QueryEmbedding(
            dense_vector=dense_vector,
            sparse_vector=sparse_vector,
            text_for_embedding=enriched_text,
        )
    
    def _build_embedding_text(self, query: str, intent: ParsedIntent) -> str:
        """Build enriched text for better embeddings"""
        parts = [query]
        
        if intent.category:
            parts.append(f"category: {intent.category}")
        
        if intent.use_case:
            parts.append(f"for {intent.use_case}")
        
        if intent.preferences:
            parts.append(" ".join(intent.preferences))
        
        return " ".join(parts)
    
    def _build_sparse_vector(
        self, 
        keywords: List[str],
        vocab_size: int = 10000
    ) -> Dict[str, float]:
        """
        Build simple sparse vector for keyword matching.
        Uses hash-based vocabulary mapping.
        """
        if not keywords:
            return {}
        
        sparse = {}
        for keyword in keywords:
            # Simple hash-based index
            idx = hash(keyword.lower()) % vocab_size
            sparse[str(idx)] = sparse.get(str(idx), 0) + 1.0
        
        # Normalize
        max_val = max(sparse.values()) if sparse else 1
        return {k: v / max_val for k, v in sparse.items()}
    
    # Category synonyms - map various terms to standard categories in Qdrant
    CATEGORY_SYNONYMS = {
        # PC/Desktop variations -> search both pc and laptop
        "pc": ["pc", "laptop"],
        "desktop": ["pc", "laptop"],
        "computer": ["pc", "laptop"],
        "gaming pc": ["pc", "laptop"],
        "mac": ["pc", "laptop"],
        "macbook": ["laptop"],
        "notebook": ["laptop"],
        "ultrabook": ["laptop"],
        "chromebook": ["laptop"],
        
        # Phone variations -> smartphone
        "phone": ["smartphone"],
        "mobile": ["smartphone"],
        "iphone": ["smartphone"],
        "android": ["smartphone"],
        "samsung phone": ["smartphone"],
        "pixel": ["smartphone"],
        "oneplus": ["smartphone"],
        "xiaomi": ["smartphone"],
        
        # Headphone variations
        "earphones": ["headphones"],
        "earbuds": ["headphones"],
        "airpods": ["headphones"],
        "headset": ["headphones"],
        
        # Watch variations
        "watch": ["smartwatch"],
        "apple watch": ["smartwatch"],
        "galaxy watch": ["smartwatch"],
        "fitness band": ["smartwatch"],
        "fitness tracker": ["smartwatch"],
        
        # Camera variations
        "dslr": ["camera"],
        "mirrorless": ["camera"],
        
        # Speaker variations
        "bluetooth speaker": ["speaker"],
        "portable speaker": ["speaker"],
        "soundbar": ["speaker"],
    }
    
    def build_search_filters(self, intent: ParsedIntent) -> SearchFilters:
        """
        Convert ParsedIntent to SearchFilters for Qdrant.
        Uses category synonyms to expand search scope.
        
        Args:
            intent: Parsed user intent
            
        Returns:
            SearchFilters ready for Qdrant
        """
        # Prices should already be in TND from the LLM/fallback parser
        # No conversion needed
        max_price_tnd = intent.max_price
        min_price_tnd = intent.min_price
        
        # Expand category using synonyms - return ALL matching categories
        expanded_categories = []
        if intent.category:
            category_lower = intent.category.lower()
            if category_lower in self.CATEGORY_SYNONYMS:
                # Use ALL synonym categories for OR search
                expanded_categories = self.CATEGORY_SYNONYMS[category_lower]
            else:
                expanded_categories = [category_lower]
        
        return SearchFilters(
            max_price=max_price_tnd,
            min_price=min_price_tnd,
            categories=expanded_categories,
            # Don't filter by eco_certified as most products don't have this field
            eco_certified=None,
            # Don't require in_stock by default - let the search be less restrictive
            in_stock=None,
            excluded_brands=intent.excluded_brands,
        )
