import requests
import time

API_URL = "http://127.0.0.1:8000/api"

print("1. Health check...")
r = requests.get(f"{API_URL}/health")
print(r.status_code, r.text)

print("\n2. Create Job...")
files = {'file': ('jd.txt', 'Looking for a Senior Python Developer with React and SQL.')}
data = {'title': 'Senior Software Engineer'}
r = requests.post(f"{API_URL}/jobs", files=files, data=data)
print(r.status_code, r.text)
if r.status_code != 200:
    exit(1)
job_id = r.json()['id']

print(f"\n3. Start Ranking for {job_id}...")
r = requests.post(f"{API_URL}/rankings/{job_id}")
print(r.status_code, r.text)

print("\n4. Polling Ranking...")
for i in range(10):
    r = requests.get(f"{API_URL}/rankings/{job_id}/latest")
    status = r.json().get('status')
    print(status, r.status_code)
    if status in ['completed', 'failed', 'not_started']:
        break
    time.sleep(1)

if r.json().get('status') == 'completed':
    results = r.json().get('results', [])
    print(f"\nSUCCESS! Got {len(results)} candidates ranked!")
    if len(results) > 0:
        print("Top candidate:", results[0]['title'], "Score:", results[0]['final_score'])
else:
    print("\nFAILED:", r.text)
