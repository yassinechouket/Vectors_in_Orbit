# Context-Aware FinCommerce Recommendation Engine 

**Production-ready AI recommendation system** with semantic search, behavioral learning, and financial intelligence.

## 🎯 Features

### Core Capabilities
-  **Semantic Search**: Vector embeddings with Qdrant hybrid search (dense + sparse)
-  **LLM Query Understanding**: Natural language parsing with GPT-4o-mini
-  **Financial Filtering**: Budget constraints and value-for-money optimization
-  **Behavioral Learning**: User preference learning with temporal decay
-  **Session Context**: Device, time-of-day, and browsing pattern awareness
-  **Collaborative Filtering**: "Users like you" recommendations
-  **Explainable AI**: Human-readable reasons for each recommendation
-  **Exploration/Exploitation**: 10% diversity boost to prevent filter bubbles

### Advanced Enhancements
-  **Temporal Decay**: Exponential decay (30-day half-life) for preference freshness
-  **Category Isolation**: Separate preferences per product category
-  **Smooth Confidence**: Sigmoid confidence curve (no hard thresholds)
-  **Multi-Factor Ranking**: Semantic + Value + Preference + Reviews + Behavior + Context
-  **Real-time Feedback Loop**: Continuous learning from user interactions

## 🏗️ Architecture

### 8-Step Recommendation Pipeline

```
User Query → (1) Query Understanding → (2) Qdrant Search → 
(3) Financial Filter → (4) Re-Ranking → (5) Explainability → 
(6) Response Formatter → (7) Feedback Loop → Results
```

### Services Architecture

1. **Orchestrator** (`services/engines/orchestrator.py`)
   - Coordinates entire 8-step pipeline
   - Manages component lifecycle
   - Provides health checks and analytics

2. **Query Understanding** (`services/engines/query_understanding.py`)
   - LLM-based intent extraction (GPT-4o-mini)
   - Embedding generation (SentenceTransformers)
   - Search filter creation

3. **Qdrant Integration** (`services/qdrant/`)
   - Hybrid vector search (dense + sparse)
   - Payload filtering (price, category, stock)
   - Collection management

4. **Financial Filter** (`services/engines/financial_filter.py`)
   - Budget compliance checks
   - Value-for-money calculations
   - Availability filtering

5. **Re-Ranking Engine** (`services/engines/reranking.py`)
   - Multi-factor scoring (4 base factors + 3 enhancement boosts)
   - Behavior-aware boosting (max ±5%)
   - Session context boosting (max ±3%)
   - Collaborative filtering (max ±2%)

6. **Feedback Loop** (`services/engines/feedback_loop.py`)
   - User behavior tracking
   - Temporal decay implementation
   - Category-specific preference profiles
   - Collaborative signal generation

7. **Explainability** (`services/engines/explainability.py`)
   - Human-readable reason generation
   - Evidence extraction
   - Confidence scoring

## 🚀 Quick Start

### Prerequisites
```bash
# Required:
- Python 3.10+
- OpenAI ,Gemeni API Key

### Installation

1. **Install Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Start Qdrant Vector Database**
   ```bash
   docker run -p 6333:6333 qdrant/qdrant
   ```

3. **Configure Environment**
   ```bash
   # Set OpenAI API key
   export OPENAI_API_KEY="your-key-here"
   
   # Or create .env file (if using)
   echo "OPENAI_API_KEY=your-key-here" > .env
   ```

4. **Run the Server**
   ```bash
   # Development mode
   python main.py
   
   # Or with uvicorn
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Initialize Qdrant Collection**
   ```bash
   # Using API
   curl -X POST http://localhost:8000/qdrant/setup
   
   # Or visit http://localhost:8000/docs and use /qdrant/setup endpoint
   ```

Server runs at: **http://localhost:8000**  
API Docs: **http://localhost:8000/docs**



## 🔧 How It Works

### Complete Workflow Example

**Input:** User searches "cheap eco laptop for coding under $800"

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Query Understanding (query_understanding.py)       │
├─────────────────────────────────────────────────────────────┤
│ • LLM extracts: category=laptop, max_price=800,            │
│   eco_friendly=true, use_case=coding                       │
│ • Generates 384-dim embedding vector                       │
│ • Creates Qdrant payload filters                           │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Qdrant Hybrid Search (hybrid_search.py)            │
├─────────────────────────────────────────────────────────────┤
│ • Dense similarity (70%) + Sparse keywords (30%)           │
│ • Filters: price≤800, eco_certified=true, in_stock=true    │
│ • Returns top 20 semantically relevant products            │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Financial Filter (financial_filter.py)             │
├─────────────────────────────────────────────────────────────┤
│ • Hard budget limit enforcement                            │
│ • Availability checks                                      │
│ • Brand exclusions (if any)                                │
│ • Returns top 10 budget-compliant products                 │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Enhanced Re-Ranking (reranking.py)                 │
├─────────────────────────────────────────────────────────────┤
│ Base Score (90%):                                          │
│   • Semantic similarity: 40%                               │
│   • Value-for-money: 30%                                   │
│   • Preference match: 20%                                  │
│   • Review quality: 10%                                    │
│                                                             │
│ Enhancement Boosts (max 10%):                              │
│   • Behavior boost: ±5% (user preferences, temporal)       │
│   • Context boost: ±3% (session, device, time)             │
│   • Collaborative boost: ±2% (co-purchase, trending)       │
│                                                             │
│ Exploration: 10% chance to boost unknown brands            │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: Explainability (explainability.py)                 │
├─────────────────────────────────────────────────────────────┤
│ • Generate human-readable reasons                          │
│ • Extract evidence (specs, reviews, certifications)        │
│ • Calculate confidence scores                              │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 6: Response Formatting (response_formatter.py)        │
├─────────────────────────────────────────────────────────────┤
│ • Format for UI consumption                                │
│ • Add budget insights (savings, value rating)              │
│ • Include processing metadata                              │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 7: Feedback Loop (feedback_loop.py)                   │
├─────────────────────────────────────────────────────────────┤
│ • Track user clicks/purchases                              │
│ • Apply temporal decay (30-day half-life)                  │
│ • Update category-specific profiles                        │
│ • Generate collaborative signals                           │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
backend/
├── main.py                           # FastAPI app & API endpoints
├── requirements.txt                  # Python dependencies
├── test_enhancements.py              # Enhancement test suite
│
├── config/
│   └── recommendation_config.py      # Pipeline configuration
│
├── models/
│   └── schemas.py                    # Data models (Pydantic/dataclass)
│       ├── Product, UserBehaviorProfile
│       ├── CategoryProfile, SessionContext
│       ├── FinancialConstraints, ParsedIntent
│       └── Recommendation, RecommendationResponse
│
├── services/
│   ├── engines/                      # Core recommendation logic
│   │   ├── orchestrator.py          # Main pipeline coordinator
│   │   ├── query_understanding.py   # LLM intent extraction
│   │   ├── financial_filter.py      # Budget filtering
│   │   ├── reranking.py             # Multi-factor scoring
│   │   ├── explainability.py        # Reason generation
│   │   ├── feedback_loop.py         # Behavioral learning
│   │   └── response_formatter.py    # UI formatting
│   │
│   └── qdrant/                       # Vector database
│       ├── client.py                # Qdrant connection
│       └── hybrid_search.py         # Hybrid vector search
│
├── prompts/
│   └── prompts.py                    # LLM prompt templates
│
├── helpers/
│   ├── embedding_helper.py          # Embedding generation
│   ├── logger.py                    # Logging utilities
│   └── demo_intelligent_recommendations.py
│
├── utils/
│   └── constants.py                 # Constants & enums
│
└── docs/
    ├── ENHANCEMENTS_GUIDE.md        # Feature documentation
    ├── BEHAVIOR_AWARE_DESIGN.md     # Design principles
    └── PROJECT_OVERVIEW.md          # Complete system guide
```

