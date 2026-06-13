import httpx
import json

def test_json_post():
    print("--- 1. CURRENT REQUEST (JSON) ---")
    url = "http://localhost:8000/api/jobs"
    payload = {
        "title": "Senior Search Engineer",
        "description": "Role: Senior Search Engineer...",
        "department": "Engineering"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer demo-token-placeholder" # Bypass 401 to show the 422 error
    }
    
    response = httpx.post(url, json=payload, headers=headers)
    
    print("Request Headers:", dict(response.request.headers))
    print("Request Body:", response.request.content.decode('utf-8'))
    print("Response Status:", response.status_code)
    print("Full Response Body:", response.text)
    
    data = response.json()
    job_id = data.get('id')
    print("data.id:", job_id)
    print("jobId variable immediately before redirect:", job_id)

def test_formdata_post():
    print("\n--- 2. FIXED REQUEST (FormData) ---")
    url = "http://localhost:8000/api/jobs"
    
    headers = {
        "Authorization": "Bearer demo-token-placeholder"
    }
    
    data = {
        "title": "Senior Search Engineer"
    }
    files = {
        "file": ("jd.txt", b"Role: Senior Search Engineer...", "text/plain")
    }
    
    response = httpx.post(url, data=data, files=files, headers=headers)
    
    print("Request Headers:", dict(response.request.headers))
    print("Response Status:", response.status_code)
    
    try:
        data_json = response.json()
        job_id = data_json.get('id')
        print("data.id:", job_id)
    except Exception as e:
        print("Failed to parse JSON:", e)

test_json_post()
test_formdata_post()
