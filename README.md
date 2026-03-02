# PitchPulse Backend Runbook

## Overview
This is the backend for **PitchPulse — Club Readiness & Injury Risk Triage**. It is built with FastAPI, uses PostgreSQL for the core database, and integrates with Actian VectorAI DB for semantic search and AI RAG pipelines.

## Running Locally

1. **Environment Variables**: Create a `.env` file in this directory based on `.env.example`.
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Start the Server**:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8765
   ```
4. **Access the API**: The API will be available at `http://localhost:8765`.

## Key Demo Endpoints

- **Swagger Documentation**: `http://localhost:8000/docs`

### Demo Data Initialization
For the hackathon, you can prepopulate the database with demo data (Real Madrid squad + fixtures) without hitting the real API-FOOTBALL limits.

1. Create a workspace (Admin/Manager): `POST /api/v1/workspaces/request_access` -> returns `{id}`.
2. Run initial sync: `POST /api/v1/sync/workspace/{id}/initial?use_demo=true`.
3. View Home Screen: `GET /api/v1/workspaces/{id}/home`.

### Metric Computation trigger
To simulate a match finishing and metrics re-calculating (the "Dev Button"):
1. `POST /api/v1/sync/fixtures/poll_once?use_demo=true`
2. This will parse the demo match stats, compute ACWR, Monotony, Strain, Risk Score, and Readiness, and upsert the weekly embeddings into Vector DB.

## Actian VectorAI DB Integrations
The Vector DB client is in `backend/services/vector_db.py`. 
- By default, if `VECTOR_DB_URL` is omitted, it falls back to a safe `LocalFallbackVectorStore` for offline development.
- When you get the official Actian credentials, place them in the `.env` file to activate the real SDK usage.

## Folder Structure
- `/api`: FastAPI route handlers (Auth, Workspaces, Players, Fixtures, Sync, Admin).
- `/core`: Settings, Firebase Security auth, DB connection.
- `/models`: SQLAlchemy definitions.
- `/schemas`: Pydantic input/output contracts.
- `/services`: Core logic (Metrics Engine, Data Provider Adapter, Vector DB Client).
- `/ai`: Keerthi's domain (Gemini prompts/stubs).
- `/demo_data`: Local JSONs to guarantee the demo works offline.
