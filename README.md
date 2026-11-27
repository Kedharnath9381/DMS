# Disaster Recovery RTO Verification Framework

Starter scaffold: React + Vite frontend, FastAPI backend, SQLite database.

## Run backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
API: http://127.0.0.1:8000
Swagger: http://127.0.0.1:8000/docs

## Run frontend
```bash
cd frontend
npm install
npm run dev
```

The first version is intentionally a scaffold. Experiment execution (Restic backup/restore) will be implemented in the next phase.
