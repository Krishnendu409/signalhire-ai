"""
Canonical Job Description configuration — single source of truth.

The actual released challenge JD is "Senior AI Engineer — Founding Team @ Redrob"
(embeddings, retrieval, ranking, LLMs, fine-tuning, vector DBs, evaluation frameworks).
Previously every ranker (engine.py, run_ranking.py, feature_extractor.py,
final_ranking_experiment.py) hardcoded a *different* generic "Search Engineer" query, which
(a) let the three systems drift apart and (b) optimized the wrong target.

The JD's participant note is explicit that the dataset is adversarial: ranking by AI-keyword
count is the WRONG answer. These lists encode who the JD actually wants and who it penalizes —
product-company applied-ML experience over keyword presence; not consulting-only, not
pure-research, not off-domain title-holders with a stuffed skills list; and behavioral
availability matters.

All term lists are lowercase; matching is expected to use word-boundary regex.
"""

# ---------------------------------------------------------------------------
# Deterministic "today". The most recent last_active_date present in the dataset
# (measured across the full 100k pool). Used for recency scoring instead of the wall
# clock so that runs are byte-for-byte reproducible (Stage-3 requirement).
# ---------------------------------------------------------------------------
REFERENCE_DATE = "2026-05-27"

JD_TITLE = "Senior AI Engineer — Founding Team @ Redrob"

# Rich natural-language JD text, phrased to mirror how candidates are embedded
# (headline | title | summary + skills + career). Used to precompute jd_embedding.npy.
JD_EMBED_TEXT = (
    "Senior AI Engineer, applied machine learning, founding team. "
    "Owns the intelligence layer: ranking, retrieval and matching systems. "
    "Embeddings-based retrieval, hybrid dense plus lexical search, vector databases "
    "(FAISS, Pinecone, Qdrant, Weaviate, Milvus, Elasticsearch, OpenSearch), "
    "sentence-transformers, BGE, E5, learning to rank, recommendation systems, "
    "NDCG MRR MAP evaluation, A/B testing, LLM fine-tuning LoRA QLoRA PEFT, "
    "NLP, information retrieval, deep learning, Python, PyTorch, TensorFlow, XGBoost. "
    "Production experience shipping search and ranking to real users at scale at a "
    "product company, not pure research, not consulting services."
)

# ---------------------------------------------------------------------------
# Content keywords (from the JD "absolutely need" + "like to have" lists).
# ---------------------------------------------------------------------------
KEYWORDS = [
    "embeddings", "embedding", "retrieval", "ranking", "recommendation", "recommender",
    "semantic search", "vector search", "hybrid search", "information retrieval",
    "learning to rank", "learning-to-rank", "sentence-transformers", "sentence transformers",
    "bge", "e5", "faiss", "pinecone", "weaviate", "qdrant", "milvus", "elasticsearch",
    "opensearch", "nlp", "natural language", "llm", "large language model", "fine-tuning",
    "fine tuning", "lora", "qlora", "peft", "ndcg", "mrr", "a/b test", "xgboost", "lightgbm",
    "transformer", "bert", "rag", "python", "machine learning", "deep learning",
    "pytorch", "tensorflow", "recommender systems",
]

# Target-role title tokens — identify genuine ML/AI/IR practitioners (word-boundary matched).
TITLE_TERMS = [
    "machine learning", "ml engineer", "ai engineer", "ai research", "ai specialist",
    "applied scientist", "applied ml", "data scientist", "nlp", "search", "relevance",
    "recommendation", "ranking", "research engineer", "ml",
]

# Core ML competency skills — matched (as substrings) against the candidate's actual skill
# NAMES. Tuned to the vocabulary that genuinely appears in the data (measured across the pool),
# so skill_coverage discriminates real practitioners instead of collapsing toward zero.
REQ_SKILLS = [
    "python", "pytorch", "tensorflow", "deep learning", "nlp", "machine learning",
    "data science", "feature engineering", "mlops", "transformers",
]

# Rare, high-signal specialist skills for THIS role: retrieval / ranking / vector search /
# LLM tooling. A candidate who lists even a few of these (e.g. "Qdrant", "Semantic Search",
# "Hugging Face Transformers") is a strong true-positive for the Senior AI Engineer JD — these
# are exactly the retrieval/ranking practitioners the JD wants, and they are uncommon in the pool.
SPECIALIST_SKILLS = [
    "faiss", "pinecone", "qdrant", "weaviate", "milvus", "opensearch", "elasticsearch",
    "semantic search", "vector search", "hugging face", "transformers", "learning to rank",
    "recommender", "recommendation", "information retrieval", "retrieval", "embeddings",
    "rag", "llm", "fine-tuning", "bge", "e5", "sentence-transformers",
]

# Ideal seniority. JD: 6-8 ideal, 5-9 band, "range not a requirement".
SENIORITY_YEARS = 7
SENIORITY_MIN = 5
SENIORITY_MAX = 9

# ---------------------------------------------------------------------------
# Penalty / disqualifier signals (JD "explicitly do NOT want" + participant note).
# ---------------------------------------------------------------------------

# Off-domain job titles that host the keyword-stuffer traps (the 12 large ~5.7k-each
# non-technical buckets measured in the real data). A profile with these titles plus an
# AI-heavy skills list is the exact trap the JD warns about.
OFFDOMAIN_TITLES = [
    "hr manager", "human resource", "recruiter", "marketing manager", "content writer",
    "graphic designer", "accountant", "sales executive", "sales manager", "customer support",
    "operations manager", "business analyst", "civil engineer", "mechanical engineer",
    "project manager", "product manager",
]

# Genuinely relevant titles even if rare — used to recognise hidden gems / true positives.
RELEVANT_TITLES = [
    "ml engineer", "machine learning", "ai research", "ai engineer", "ai specialist",
    "data scientist", "recommendation systems engineer", "applied scientist", "nlp engineer",
    "search engineer", "relevance engineer", "data engineer", "analytics engineer",
    "backend engineer", "software engineer", "senior software engineer (ml)",
]

# CV / speech / robotics — JD down-weights these unless the profile ALSO shows NLP/IR.
NARROW_DOMAIN_TITLES = ["computer vision", "speech", "robotics", "image"]

# Indian consulting / IT-services firms. JD disqualifies *consulting-only* careers (entire
# career at services firms, no product-company experience). Expanded well beyond the original 6.
CONSULTING_FIRMS = [
    "tcs", "tata consultancy", "infosys", "wipro", "accenture", "cognizant", "capgemini",
    "tech mahindra", "hcl", "ltimindtree", "lti", "mindtree", "mphasis", "l&t infotech",
    "larsen & toubro", "hexaware", "cybage", "birlasoft", "coforge", "mastek", "zensar",
    "ntt data", "nttdata", "dxc", "igate", "syntel", "sonata software",
]

# Pure-research markers. JD disqualifies research-only (no production deployment). Applied
# ONLY when the profile shows no production/product signal (see PRODUCTION_MARKERS).
RESEARCH_ONLY_MARKERS = [
    "research assistant", "research scholar", "postdoc", "post-doc", "phd researcher",
    "phd student", "academia", "academic", "university of", "laboratory", "professor",
    "lecturer",
]

# Signals of real production/product work that CANCEL the research-only penalty.
PRODUCTION_MARKERS = [
    "production", "deployed", "shipped", "at scale", "users", "latency", "throughput",
    "pipeline", "api", "service", "real-time", "real time", "product", "customers",
]

# Preferred locations. JD: Pune/Noida preferred; Hyderabad/Mumbai/Delhi NCR/Bangalore welcome;
# outside India case-by-case with no visa sponsorship.
INDIA_CITIES = [
    "pune", "noida", "hyderabad", "mumbai", "delhi", "gurgaon", "gurugram", "bangalore",
    "bengaluru", "ncr", "chennai", "kolkata", "ahmedabad", "indore", "jaipur", "chandigarh",
    "coimbatore", "kochi", "trivandrum", "bhubaneswar", "vizag", "india",
]
PREFERRED_CITIES = ["pune", "noida", "hyderabad", "mumbai", "delhi", "gurgaon", "gurugram",
                    "bangalore", "bengaluru", "ncr"]

# ---------------------------------------------------------------------------
# Convenience dict mirroring the historical `jd_data` shape the rankers already consume,
# so existing call sites keep working after importing this module.
# ---------------------------------------------------------------------------
JD_CONFIG = {
    "family": "AI Engineer",
    "keywords": KEYWORDS,
    "title_terms": TITLE_TERMS,
    "req_skills": REQ_SKILLS,
    "seniority_years": SENIORITY_YEARS,
}
