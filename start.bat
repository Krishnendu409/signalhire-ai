@echo off
echo Starting SignalHire AI Pipeline...

echo Starting FastAPI Backend...
cd hackathon_pipeline
start cmd /k "python -m uvicorn server:app --host 0.0.0.0 --port 8000"

echo Starting Next.js Frontend...
cd ../frontend
start cmd /k "npm run start"

echo Pipeline is running!
echo Frontend: http://localhost:3000
echo Backend: http://localhost:8000
