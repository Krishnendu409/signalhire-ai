import time
import json
from engine import RankingEngine

base_jds = {
    'Search Engineer': {
        'family': 'Search Engineer',
        'keywords': ['faiss', 'pinecone', 'elasticsearch', 'search', 'ranking', 'retrieval', 'machine learning', 'python'],
        'title_terms': ["Search Engineer", "Relevance Engineer", "Information Retrieval", "Machine Learning Engineer - Search", "AI Engineer - Search", "Ranking Engineer"],
        'req_skills': ["faiss", "pinecone", "elasticsearch", "solr", "lucence", "weaviate", "qdrant", "milvus", "vector database", "bm25", "learning-to-rank", "ltr", "semantic search", "tf-idf", "hybrid search", "ann", "approximate nearest neighbor", "rag", "retrieval augmented generation"]
    },
    'Frontend Engineer': {
        'family': 'Frontend Engineer',
        'keywords': ['react', 'vue', 'css', 'html', 'javascript', 'frontend', 'ui', 'typescript'],
        'title_terms': ["Frontend Engineer", "UI Engineer", "React Developer", "Vue Developer", "Web Developer", "Client-side Engineer"],
        'req_skills': ["react", "vue", "angular", "svelte", "javascript", "typescript", "html", "css", "tailwind", "sass", "webpack", "vite", "redux", "next.js", "nuxt", "dom", "frontend", "ui/ux"]
    },
    'Sales Manager': {
        'family': 'Sales Manager',
        'keywords': ['sales', 'crm', 'b2b', 'revenue', 'quota', 'pipeline', 'account', 'business development'],
        'title_terms': ["Sales Manager", "Account Executive", "Business Development Manager", "Sales Director", "VP of Sales", "Revenue Manager"],
        'req_skills': ["sales", "b2b", "crm", "salesforce", "hubspot", "quota", "pipeline", "outbound", "inbound", "lead generation", "negotiation", "closing", "prospecting", "account management"]
    }
}

engine = RankingEngine()

for jd_name, payload in base_jds.items():
    print(f"\n--- Testing {jd_name} ---")
    start = time.time()
    results = engine.run_pipeline(payload)
    end = time.time()
    print(f"Runtime: {end - start:.2f} seconds")
    
    print("Top 5 Candidates:")
    for i in range(5):
        c = results[i]
        print(f"  {i+1}. {c['candidate_id']} | {c['title']} | Score: {c['final_score']:.3f}")
        
    counts = {'Sales': 0, 'HR': 0, 'Marketing': 0, 'Engineer': 0, 'Other': 0}
    for c in results[:100]:
        t = str(c['title']).lower()
        if 'engineer' in t or 'developer' in t:
            counts['Engineer'] += 1
        elif any(x in t for x in ['sales', 'account executive', 'business development', 'revenue', 'customer success']):
            counts['Sales'] += 1
        elif 'hr' in t or 'human resources' in t or 'recruiter' in t:
            counts['HR'] += 1
        elif 'marketing' in t:
            counts['Marketing'] += 1
        else:
            counts['Other'] += 1
    
    print(f"Top 100 Distribution: Sales {counts['Sales']}%, HR {counts['HR']}%, Marketing {counts['Marketing']}%, Engineer {counts['Engineer']}%, Other {counts['Other']}%")
