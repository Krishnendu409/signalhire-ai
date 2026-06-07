import requests
import time
import json
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

print("=== SECTION 5: E2E Verification ===")

for jd_name, payload in base_jds.items():
    print(f"\n--- Testing {jd_name} ---")
    start = time.time()
    resp = requests.post("http://localhost:8000/api/investigations", json=payload)
    if resp.status_code != 200:
        print("Failed to start investigation:", resp.text)
        continue
    
    inv_id = resp.json()["investigation_id"]
    print("Investigation ID:", inv_id)
    
    while True:
        status_resp = requests.get(f"http://localhost:8000/api/investigations/{inv_id}/status").json()
        if status_resp["status"] == "COMPLETED":
            break
        elif status_resp["status"] == "FAILED":
            print("Investigation Failed!")
            break
        time.sleep(2)
        
    end = time.time()
    print(f"Runtime: {end - start:.2f} seconds")
    
    results = requests.get(f"http://localhost:8000/api/investigations/{inv_id}/results").json()["results"]
    print("Top 5 Candidates:")
    for i in range(5):
        c = results[i]
        print(f"  {i+1}. {c['candidate_id']} | {c['title']} | Score: {c['final_score']:.3f}")
        
    if jd_name == 'Search Engineer':
        print("\n=== SECTION 6: Explainability Verification (Search Engineer Rank 1) ===")
        print(json.dumps(results[0], indent=2))
        
print("\n=== SECTION 7: Failure Testing ===")
print("1. Empty Payload")
resp = requests.post("http://localhost:8000/api/investigations", json={})
print("Status Code:", resp.status_code)
print("Response:", resp.text)

print("\n2. Missing Fields")
resp = requests.post("http://localhost:8000/api/investigations", json={"family": "Search Engineer"})
print("Status Code:", resp.status_code)
print("Response:", resp.text)

print("\n3. Invalid Schema Types")
resp = requests.post("http://localhost:8000/api/investigations", json={"family": "Search Engineer", "keywords": "string_not_list", "title_terms": [], "req_skills": []})
print("Status Code:", resp.status_code)
print("Response:", resp.text)
