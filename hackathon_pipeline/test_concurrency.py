import urllib.request
import urllib.error
import json
import time
from concurrent.futures import ThreadPoolExecutor

API_URL = "http://localhost:8000/api/investigations"
STATUS_URL = "http://localhost:8000/api/investigations/{}/status"

base_jd = {
    'family': 'Sales Manager',
    'keywords': ['sales', 'crm', 'b2b', 'revenue', 'quota', 'pipeline'],
    'title_terms': ['sales', 'revenue', 'business development'],
    'req_skills': ['sales', 'b2b', 'crm']
}

def run_investigation(idx):
    start_time = time.time()
    try:
        # 1. Post request
        req = urllib.request.Request(API_URL, method='POST')
        req.add_header('Content-Type', 'application/json')
        data = json.dumps(base_jd).encode('utf-8')
        
        with urllib.request.urlopen(req, data=data) as resp:
            resp_data = json.loads(resp.read().decode('utf-8'))
            inv_id = resp_data.get("investigation_id")
            if not inv_id:
                return {"idx": idx, "success": False, "error": "No ID"}
        
        # 2. Poll status
        while True:
            try:
                status_req = urllib.request.Request(STATUS_URL.format(inv_id))
                with urllib.request.urlopen(status_req) as status_resp:
                    status_data = json.loads(status_resp.read().decode('utf-8'))
                    status = status_data.get("status")
                    if status == "COMPLETED":
                        end_time = time.time()
                        return {"idx": idx, "success": True, "time": end_time - start_time}
                    elif status == "FAILED":
                        return {"idx": idx, "success": False, "error": "Failed status"}
            except urllib.error.HTTPError as e:
                # 400 when results are accessed before completion, but status endpoint shouldn't throw 400
                if e.code != 400:
                    raise e
            
            time.sleep(1)
            
    except Exception as e:
        return {"idx": idx, "success": False, "error": str(e)}

def run_batch(num_requests):
    print(f"\nRunning batch of {num_requests} concurrent requests...")
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=num_requests) as executor:
        results = list(executor.map(run_investigation, range(num_requests)))
        
    total_time = time.time() - start_time
    successes = [r for r in results if r["success"]]
    failures = [r for r in results if not r["success"]]
    
    print(f"Total time: {total_time:.2f}s")
    print(f"Success rate: {len(successes)}/{num_requests}")
    if successes:
        avg_time = sum(r["time"] for r in successes) / len(successes)
        print(f"Average response time per task: {avg_time:.2f}s")
    if failures:
        print(f"Failures: {failures}")

def main():
    # Wait for server to be ready? We assume it's running.
    batches = [1, 5, 10, 20]
    for b in batches:
        run_batch(b)

if __name__ == "__main__":
    main()
