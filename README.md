# Healthcare Triage Assistant (Backend)

## Setup

1. Create virtualenv and install deps
2. Create `.env` (see `.env.example`)
3. Seed DB: `python utils/seed_db.py`
4. Run API: `uvicorn main:app --reload --port 8000`

## Endpoints

- `GET /health`
- `POST /api/triage/submit`
- `GET /api/triage/status/{patient_id}`
- `GET /api/doctors/dashboard?doctor_id=...`
- `POST /api/doctors/action`
