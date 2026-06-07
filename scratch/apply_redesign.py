import os

# 1. Modify feature_extractor.py
with open("hackathon_pipeline/feature_extractor.py", "r") as f:
    text = f.read()

# Expand Retrieval Keywords
text = text.replace(
    "'candidate matching', 'document retrieval'",
    "'candidate matching', 'document retrieval',\n            'dense retrieval', 'sparse retrieval', 'hybrid retrieval', 'catalog search'"
)

# Expand Ranking Keywords
text = text.replace(
    "'relevance', 'reranking', 're-ranking'",
    "'relevance', 'reranking', 're-ranking',\n            'relevance engineering', 'search infrastructure',\n            'product discovery', 'search quality'"
)

# Expand Vector DB Keywords
text = text.replace(
    "'vector store', 'chromadb', 'annoy', 'hnsw'",
    "'vector store', 'chromadb', 'annoy', 'hnsw',\n            'faiss', 'lucene', 'ann', 'approximate nearest neighbor',\n            'inverted index', 'vector index', 'embedding infrastructure'"
)

# Fix FEATURE_COLS
text = text.replace(
    "'semantic_sim', 'bm25_score', 'rrf_score',",
    "'semantic_sim', 'bm25_score', 'lexical_semantic_divergence',"
)

with open("hackathon_pipeline/feature_extractor.py", "w") as f:
    f.write(text)


# 2. Modify train_lightgbm.py
with open("hackathon_pipeline/train_lightgbm.py", "r") as f:
    text = f.read()

# Chunking logic injection
chunking_logic = """
    # Semantic Sim with Chunking
    print("Embedding JD chunks and candidates...")
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
    
    tokens = tokenizer.encode(jd_text, add_special_tokens=False)
    chunk_size = 350
    jd_chunks = [tokenizer.decode(tokens[i:i+chunk_size]) for i in range(0, len(tokens), chunk_size)]
    
    query_embs = embedder.encode(jd_chunks, convert_to_numpy=True)
    doc_embs = embedder.encode(corpus_texts, convert_to_numpy=True)
    
    sim_matrix = doc_embs.dot(query_embs.T)
    similarities = sim_matrix.max(axis=1)
    features_df['semantic_sim'] = similarities
"""

text = text.replace(
    """    # Semantic Sim
    print("Computing real embeddings for 10k training samples (this may take 2-4 minutes)...")
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    query_emb = embedder.encode([jd_text], convert_to_numpy=True)[0]
    doc_embs = embedder.encode(corpus_texts, convert_to_numpy=True)
    similarities = doc_embs.dot(query_emb)
    features_df['semantic_sim'] = similarities""",
    chunking_logic
)

lexical_div_logic = """
    # Lexical-Semantic Divergence
    bm25_pct = rankdata(bm25_all, method='average') / len(bm25_all)
    sem_pct = rankdata(similarities, method='average') / len(similarities)
    features_df['lexical_semantic_divergence'] = bm25_pct - sem_pct
"""

text = text.replace(
    """    # RRF
    bm25_ranks = len(bm25_all) - rankdata(bm25_all, method='average') + 1
    semantic_ranks = len(similarities) - rankdata(similarities, method='average') + 1
    features_df['rrf_score'] = (1.0 / (60 + bm25_ranks)) + (1.0 / (60 + semantic_ranks))""",
    lexical_div_logic
)

pseudo_label_logic = """
        # New Pseudo-Label Design: Retrieval + Production + Consistency + Hireability + Leadership + Rare Expert Signals
        retrieval_factor = norm_sim[i] * 2.0 + norm_bm25[i] * 1.0
        
        final_score = (
            retrieval_factor +
            row['production_ml_score'] * 0.5 + 
            row['hireability_score'] * 0.5 +
            row['career_consistency_score'] * 0.5 +
            row['leadership_score'] * 0.3 +
            row['evaluation_framework_score'] * 1.5 + 
            row['ranking_experience_score'] * 1.0 +
            row['vector_db_score'] * 0.5 -
            row['is_research_only'] * 1.0 -
            row['is_langchain_only'] * 1.0
        )
"""
import re
text = re.sub(r"        # Core JD alignment.*?final_score = core \+ soft \+ trust \+ penalties \+ query", pseudo_label_logic, text, flags=re.DOTALL)

with open("hackathon_pipeline/train_lightgbm.py", "w") as f:
    f.write(text)


# 3. Modify run_ranking.py
with open("hackathon_pipeline/run_ranking.py", "r") as f:
    text = f.read()

chunking_logic_run = """
    # JD Chunking for Semantic Search
    print("Encoding query chunks for semantic retrieval...")
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
    
    tokens = tokenizer.encode(jd_text, add_special_tokens=False)
    chunk_size = 350
    jd_chunks = [tokenizer.decode(tokens[i:i+chunk_size]) for i in range(0, len(tokens), chunk_size)]
    
    query_embs = embedder.encode(jd_chunks, convert_to_numpy=True).astype(np.float16)
    
    # Compute max similarity across all chunks
    sim_matrix = embeddings.dot(query_embs.T)
    similarities = sim_matrix.max(axis=1)
"""

text = text.replace(
    """    print("Encoding query for semantic retrieval...")
    query_emb = embedder.encode([jd_text], convert_to_numpy=True)[0].astype(np.float16)
    similarities = embeddings.dot(query_emb)""",
    chunking_logic_run
)

rrf_replacement = """
    print("\n[Stage 2.5] Computing Lexical-Semantic Divergence...")
    from scipy.stats import rankdata
    
    candidate_id_to_idx = {cid: i for i, cid in enumerate(candidate_ids)}
    
    # Calculate global percentiles for the union set candidates
    bm25_ranks = rankdata(bm25_all, method='average') / len(bm25_all)
    semantic_ranks = rankdata(similarities, method='average') / len(similarities)
    
    div_dict = {}
    bm25_dict = {}
    sem_dict = {}
    for cid in union_ids:
        idx = candidate_id_to_idx[cid]
        div_dict[cid] = bm25_ranks[idx] - semantic_ranks[idx]
        bm25_dict[cid] = bm25_all[idx]
        sem_dict[cid] = similarities[idx]

    union_df['lexical_semantic_divergence'] = union_df['candidate_id'].map(div_dict)
    union_df['bm25_score'] = union_df['candidate_id'].map(bm25_dict)
    union_df['semantic_sim'] = union_df['candidate_id'].map(sem_dict)
"""
text = re.sub(r"    print\(\"\\n\[Stage 2\.5\] Computing Reciprocal Rank Fusion \(RRF\)\.\.\.\"\).*?union_df\['semantic_sim'\] = union_df\['candidate_id'\]\.map\(sem_dict\)", rrf_replacement, text, flags=re.DOTALL)

feature_df_update = """
    features_df['lexical_semantic_divergence'] = union_df['lexical_semantic_divergence'].values
    features_df['bm25_score'] = union_df['bm25_score'].values
    features_df['semantic_sim'] = union_df['semantic_sim'].values
    features_df['candidate_id'] = union_df['candidate_id'].values
"""
text = re.sub(r"    features_df\['rrf_score'\].*?features_df\['candidate_id'\] = union_df\['candidate_id'\]\.values", feature_df_update, text, flags=re.DOTALL)

heuristic_override_replacement = """
    # STAGE 3.5: Linear Additive Residual for Evaluation Frameworks
    # Replaces the unstable 1.5x multiplier. Adds a calibrated boost before normalization.
    features_df['score'] = scores + (features_df['evaluation_framework_score'] * 1.5)
"""
text = re.sub(r"    # STAGE 3\.5: Heuristic Override.*?features_df\['score'\] = scores \* eval_bonus", heuristic_override_replacement, text, flags=re.DOTALL)

with open("hackathon_pipeline/run_ranking.py", "w") as f:
    f.write(text)

print("Codebase updated successfully!")
