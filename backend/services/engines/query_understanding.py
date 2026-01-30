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
from providers.deepseek_provider import DeepSeekProvider
from models.schemas import ParsedIntent, QueryEmbedding, SearchFilters
from prompts import system_prompt


class QueryUnderstandingEngine:
    """
    Extracts structured intent from natural language queries.
    
    Responsibilities:
    - Parse user query into structured intent (category, budget, preferences)
    - Generate dense semantic embedding
    - Generate sparse keyword vector (optional)
    - Build search filters for Qdrant
    """
    
    SYSTEM_PROMPT = system_prompt

    def __init__(
        self,
        provider: str = "deepseek",
        embedding_model: str = "all-MiniLM-L6-v2",
        **provider_kwargs,
    ):
        """
        Initialize the query understanding engine.
        
        Args:
            provider: Provider to use ("gemini", "llama", or "deepseek")
            embedding_model: Sentence transformer model for embeddings
            **provider_kwargs: Additional kwargs for the provider
        """
        # Initialize the selected provider
        if provider.lower() == "gemini":
            self.llm_provider = GeminiProvider(**provider_kwargs)
        elif provider.lower() == "llama":
            self.llm_provider = LlamaProvider(**provider_kwargs)
        elif provider.lower() == "deepseek":
            self.llm_provider = DeepSeekProvider(**provider_kwargs)
        else:
            raise ValueError(f"Unsupported provider: {provider}. Use 'gemini', 'llama', or 'deepseek'")
        
        self.embedding_model = SentenceTransformer(embedding_model)
    
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
            priority=self._sanitize_priority(result.get("priority", "balanced")),
            brand_preferences=result.get("brand_preferences", []),
            excluded_brands=result.get("excluded_brands", []),
            keywords=result.get("keywords", []),
        )
    
    def _rule_based_fallback(self, query: str) -> ParsedIntent:
        """Rule-based fallback when LLM is unavailable"""
        query_lower = query.lower()
        
        # Extract price
        max_price = None
        price_patterns = [
            r'under\s*\$?(\d+)',
            r'below\s*\$?(\d+)',
            r'less than\s*\$?(\d+)',
            r'max\s*\$?(\d+)',
            r'\$(\d+)\s*budget',
        ]
        for pattern in price_patterns:
            match = re.search(pattern, query_lower)
            if match:
                max_price = float(match.group(1))
                break
        
        # Extract category
        category = None
        categories = {
            "laptop": ["laptop", "notebook", "macbook", "chromebook"],
            "phone": ["phone", "smartphone", "iphone", "android"],
            "headphones": ["headphones", "earbuds", "earphones", "airpods"],
            "tablet": ["tablet", "ipad"],
            "camera": ["camera", "dslr", "mirrorless"],
            "monitor": ["monitor", "display", "screen"],
        }
        for cat, keywords in categories.items():
            if any(kw in query_lower for kw in keywords):
                category = cat
                break
        
        # Check for eco preference
        eco_friendly = any(word in query_lower for word in [
            "eco", "sustainable", "green", "environmental", "recyclable"
        ])
        
        # Determine priority
        priority = "balanced"
        if any(word in query_lower for word in ["cheap", "budget", "affordable"]):
            priority = "price"
        elif any(word in query_lower for word in ["best", "premium", "quality"]):
            priority = "quality"
        elif eco_friendly:
            priority = "eco"
        
        # Extract keywords
        stop_words = {"i", "want", "need", "looking", "for", "a", "an", "the", "me"}
        keywords = [w for w in query_lower.split() if w not in stop_words]
        
        return ParsedIntent(
            category=category,
            max_price=max_price,
            eco_friendly=eco_friendly,
            priority=priority,
            keywords=keywords,
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
    
    def build_search_filters(self, intent: ParsedIntent) -> SearchFilters:
        """
        Convert ParsedIntent to SearchFilters for Qdrant.
        
        Args:
            intent: Parsed user intent
            
        Returns:
            SearchFilters ready for Qdrant
        """
        return SearchFilters(
            max_price=intent.max_price,
            min_price=intent.min_price,
            category=intent.category,
            eco_certified=intent.eco_friendly if intent.eco_friendly else None,
            in_stock=True,
            excluded_brands=intent.excluded_brands,
        )

    def _sanitize_priority(self, priority: Any) -> str:
        """Ensure priority is a string"""
        if isinstance(priority, list):
            return priority[0] if priority else "balanced"
        return str(priority)
