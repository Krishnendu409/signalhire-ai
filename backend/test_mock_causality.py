from fastapi import FastAPI, Form, File, UploadFile
from fastapi.testclient import TestClient

app = FastAPI()

@app.post("/api/jobs")
async def create_job(title: str = Form(...), file: UploadFile = File(...)):
    return {"id": "job-success-123", "title": title}

client = TestClient(app)

print("--- PROOF 1: CURRENT FRONTEND LOGIC ---")
print("Frontend uses JSON and a trailing slash (which might be 405 or 422 depending on trailing slash handling).")
# Test with JSON
response = client.post("/api/jobs", json={
    "title": "Senior Search Engineer",
    "description": "Role: Senior Search Engineer...",
    "department": "Engineering"
})
print("Request Body (JSON):", response.request.content.decode())
print("Response Status:", response.status_code)
print("Response Body:", response.json())
print("jobId variable (data.id):", response.json().get("id"))

print("\n--- PROOF 2: FIXED FRONTEND LOGIC ---")
print("Frontend uses FormData as required by FastAPI's Form(...) and File(...) dependencies.")
response = client.post(
    "/api/jobs",
    data={"title": "Senior Search Engineer"},
    files={"file": ("jd.txt", b"Role: Senior Search Engineer...", "text/plain")}
)
print("Request Headers Content-Type:", response.request.headers.get("Content-Type"))
print("Response Status:", response.status_code)
print("Response Body:", response.json())
print("jobId variable (data.id):", response.json().get("id"))
