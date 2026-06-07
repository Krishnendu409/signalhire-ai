from fastapi.testclient import TestClient
from server import app
import time

client = TestClient(app)

def test():
    print("Testing API Integration...")
    
    jd_req = {
        "family": "Search Engineer",
        "keywords": ["faiss", "pinecone", "elasticsearch", "search", "ranking", "retrieval", "machine learning", "python"],
        "title_terms": ["search", "retrieval", "relevance", "ranking", "nlp", "machine learning", "ai", "data scientist", "ml"],
        "req_skills": ["python", "elasticsearch", "faiss", "machine learning", "nlp", "deep learning", "pytorch", "tensorflow", "scikit-learn"]
    }
    
    # 1. Start Investigation
    resp = client.post("/api/investigations", json=jd_req)
    assert resp.status_code == 200
    data = resp.json()
    inv_id = data["investigation_id"]
    print(f"Started investigation: {inv_id}")
    
    # 2. Poll Status
    # In TestClient, BackgroundTasks run synchronously in the background (or rather, after the response is returned, the task runs).
    # Since TestClient blocks until the background tasks finish for the request, the task should already be done when post returns!
    status_resp = client.get(f"/api/investigations/{inv_id}/status")
    assert status_resp.status_code == 200
    print(f"Status: {status_resp.json()['status']}")
    
    # 3. Get Results
    res_resp = client.get(f"/api/investigations/{inv_id}/results")
    assert res_resp.status_code == 200
    results = res_resp.json()["results"]
    print(f"Got {len(results)} results.")
    
    print("Top 1 candidate:", results[0]['title'], "- Score:", results[0]['final_score'])
    print("ALL API TESTS PASSED.")

if __name__ == "__main__":
    test()
