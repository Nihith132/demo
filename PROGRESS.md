# AI4 Healthcare Triage MVP — Progress & Handoff (17 Apr 2026)

This document summarizes the current MVP implementation status, what was changed, what is working, what is broken, and how a teammate can continue.

> Repo/workspace root: `/Users/rohanpagadala/Desktop/ai4`

---

## 1) System overview

### Goals (MVP)
- Full-stack triage system with separate **Patient** and **Doctor** flows.
- Backend: **FastAPI + SQLAlchemy**, Groq LLM agents, Supabase Postgres (cloud DB).
- Patient auth: **Firebase Google sign-in** (browser gets Firebase ID token; backend verifies).
- Doctor auth: **username (doctor name) + password**, backend issues JWT.
- Patient can upload PDFs, submit symptom description, book appointment.
- Doctor sees dashboard and analytics and can add prerequisites.

---

## 2) Backend status (FastAPI)

### Location
- Entry: `main.py`
- Routers: `routers/`
- DB models: `models/db_models.py`
- Firebase verification: `utils/firebase_auth.py`
- PDF extraction: `utils/pdf_extract.py`

### Implemented endpoints
#### Auth
- Doctor login: `POST /api/auth/login` → JWT
- Patient session/identity:
  - `POST /api/patient-auth/session` (validates Firebase ID token + upserts `PatientUser`)
  - `GET /api/patient-auth/me`

#### Patient
- `POST /api/patient/submit` (Firebase auth required)
- `GET /api/patient/history` (Firebase auth required; ownership enforced)
- `GET /api/patient/doctors?patient_id=...` (Firebase auth required)
- `POST /api/patient/book` (Firebase auth required)

#### Doctor
- `GET /api/doctors/dashboard` (JWT required)
- `GET /api/doctors/analytics` (JWT required)
- `GET /api/doctors/patient/{patient_id}` (JWT required)
- `POST /api/doctors/action` (JWT required; adds prerequisite)

#### Files (new)
- `GET /api/files/patient/pdf/signed-url?patient_id=...` (Firebase auth + ownership)
- `GET /api/files/doctor/pdf/signed-url?patient_id=...` (JWT auth + assigned doctor)

### Supabase Postgres
- Backend uses `DATABASE_URL` (Supabase Postgres connection string).
- Models include: `Doctor`, `PatientRecord`, `Appointment`, `PatientUser`.

### PDF storage (partially migrated)
- In `routers/patient.py`, PDF upload now **prefers Supabase Storage** if configured:
  - Uploads a PDF to Supabase Storage using a service key.
  - Stores a URI like `supabase://<bucket>/<object_path>` in `uploaded_file_uris_json`.
- If Supabase Storage env vars aren’t set, it **falls back to local disk**.

**Important limitation:**
- Background PDF extraction with `pypdf` currently runs only if the PDF exists on local disk.
- For cloud PDFs: background task currently routes department based on the symptom description only.

### CORS (fixed)
- Added CORS middleware in `main.py` to allow browser calls from Next.js dev origin.
- This fixed browser preflight failures (`OPTIONS ... 405`) that were causing “Failed to fetch”.

### Firebase Admin robustness (improved)
- `utils/firebase_auth.py` now supports:
  - `FIREBASE_SERVICE_ACCOUNT_PATH` (recommended)
  - `FIREBASE_SERVICE_ACCOUNT_JSON` (only works if it is valid one-line JSON)
- Added diagnostic logging for token verification failures:
  - logs `firebase_verify_id_token_failed: <ExceptionType>: <message>` without printing tokens.

---

## 3) Frontend status (Next.js App Router)

### Location
- Frontend root: `frontend-next/`
- Patient page: `src/app/patient/page.tsx`
- Doctor login: `src/app/doctor/login/page.tsx`
- Doctor dashboard: `src/app/doctor/page.tsx`
- Firebase client wrapper: `src/lib/firebase_client.ts`
- API wrapper: `src/lib/http.ts`
- Backend URL config: `src/lib/config.ts`

### Implemented flows
#### Patient
- Google sign-in with Firebase popup.
- After sign-in, sends ID token to backend:
  - `POST /api/patient-auth/session` with `Authorization: Bearer <idToken>`
- Patient can load history, submit intake, load doctors, book.

#### Doctor
- Login with doctor name + password:
  - Calls `POST /api/auth/login` (form-encoded)
- Stores JWT in `localStorage` and uses it for doctor endpoints.

### Firebase client env validation (improved)
- `src/lib/firebase_client.ts` validates required `NEXT_PUBLIC_FIREBASE_*` env vars and throws a clearer error if missing.

### Patient sign-in error handling (improved)
- `src/app/patient/page.tsx` wraps the `signInWithPopup` flow in try/catch so Firebase errors show in the UI rather than crashing the app.

---

## 4) Current runtime setup

### Backend
- Dev server is running on **port 8002** during local testing.
- Frontend is configured to call backend at `http://localhost:8002` by default.

### Frontend
- Next dev server runs on **port 3000**.

---

## 5) Known issues (as of now)

### A) Patient backend returns `Invalid Firebase token` (401)
Symptoms:
- Patient UI shows: `Invalid Firebase token`
- Backend logs show `/api/patient-auth/session` returning 401.

Root cause:
- Backend Firebase Admin credentials are **not properly loaded** from `.env`.
- The current `.env` contains a **multiline** `FIREBASE_SERVICE_ACCOUNT_JSON={\n ... }`.
  - `python-dotenv` typically does not load multiline JSON reliably.
  - A runtime check indicated both `FIREBASE_SERVICE_ACCOUNT_PATH` and `FIREBASE_SERVICE_ACCOUNT_JSON` are not being set in the backend process.

Fix:
- Use `FIREBASE_SERVICE_ACCOUNT_PATH=/absolute/path/to/service_account.json` in backend `.env`.

### B) Cloud PDF extraction is incomplete
- Cloud upload works if Supabase Storage keys are configured, but extraction uses file path.
- Next step: download the PDF from Supabase signed URL into a temp file in background tasks, then run `pypdf`.

---

## 6) What env vars are required

### Backend (`/Users/rohanpagadala/Desktop/ai4/.env`)
Required:
- `DATABASE_URL` (Supabase Postgres)
- `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXPIRES_MINUTES`
- `GROQ_API_KEY`

Firebase (choose one):
- Recommended:
  - `FIREBASE_SERVICE_ACCOUNT_PATH=/abs/path/service_account.json`
- Alternative (discouraged):
  - `FIREBASE_SERVICE_ACCOUNT_JSON=<one-line JSON>`
- And:
  - `FIREBASE_PROJECT_ID=ai4imp`

Supabase Storage (optional, for cloud PDFs):
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_STORAGE_BUCKET` (default `patient-uploads`)
- `SUPABASE_SIGNED_URL_EXPIRES_SECONDS` (default `3600`)

### Frontend (`frontend-next/.env.local`)
Required:
- `NEXT_PUBLIC_BACKEND_URL=http://localhost:8002`
- `NEXT_PUBLIC_FIREBASE_API_KEY=...`
- `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=...`
- `NEXT_PUBLIC_FIREBASE_PROJECT_ID=...`
- `NEXT_PUBLIC_FIREBASE_APP_ID=...`

---

## 7) Step-by-step continuation guide (teammate)

### Step 1 — Fix patient auth verification (highest priority)
1. Save Firebase service account json to a file on disk (do not commit). Example:
   - `/Users/rohanpagadala/Desktop/ai4/firebase-service-account.json`
2. Update backend `.env`:
   - Remove the multiline `FIREBASE_SERVICE_ACCOUNT_JSON={...}` block entirely.
   - Add:
     - `FIREBASE_SERVICE_ACCOUNT_PATH=/Users/rohanpagadala/Desktop/ai4/firebase-service-account.json`
3. Restart backend.
4. Test from browser:
   - Open `http://localhost:3000/patient`
   - Sign in with Google
   - Verify `POST /api/patient-auth/session` returns 200

If it still fails:
- Check backend logs for `firebase_verify_id_token_failed: ...` and fix based on the error.

### Step 2 — Ensure Google provider is enabled
- Firebase Console → Authentication → Sign-in method → Google → Enabled.
- Authentication → Settings → Authorized domains includes `localhost`.

### Step 3 — Finish cloud PDF extraction (optional but recommended)
- When PDF stored in Supabase (`supabase://bucket/path`), in background task:
  1. Create signed URL.
  2. Download to temp file.
  3. Run `extract_text_from_pdf(temp_path)`.

### Step 4 — Add UI to view/download PDFs (optional)
- Add "View PDF" button in patient history and doctor patient detail.
- Call signed-url endpoints:
  - patient: `/api/files/patient/pdf/signed-url?patient_id=...`
  - doctor: `/api/files/doctor/pdf/signed-url?patient_id=...`

### Step 5 — Production hardening (later)
- Use env-driven CORS origins.
- Use HTTPS.
- Replace service-role storage access where possible.
- Move uploaded_file_uris_json from `str(list)` to JSON (`json.dumps`) for safety.

---

## 8) Files changed/added in this iteration

### Backend
- Modified: `main.py`
  - Added CORS middleware
  - Registered files router
- Modified: `routers/patient.py`
  - Supabase Storage upload attempt + fallback
  - Added description-only background task for cloud PDFs
- Added: `routers/files.py`
  - Secure signed-url endpoints
- Added: `utils/supabase_storage.py`
  - Upload + signed URL helpers
- Modified: `utils/firebase_auth.py`
  - Added `FIREBASE_SERVICE_ACCOUNT_PATH` support
  - Added better verification error diagnostics
- Updated: `.env.example`
  - Documented Supabase Storage vars
  - Documented `FIREBASE_SERVICE_ACCOUNT_PATH`

### Frontend
- Modified: `src/lib/config.ts`
  - Default backend URL points to `http://localhost:8002`
- Updated: `.env.local.example`
  - Backend URL default updated to 8002
- Modified: `src/lib/firebase_client.ts`
  - Added validation for missing env vars
- Modified: `src/app/patient/page.tsx`
  - try/catch around Google sign-in to prevent runtime crash
- Updated: `frontend-next/.env.local`
  - Added Firebase web app config values

---

## 9) How to run locally

### Backend
- Activate venv and run uvicorn:
  - `uvicorn main:app --reload --host 0.0.0.0 --port 8002`

### Frontend
- From `frontend-next/`:
  - `npm run dev -- --port 3000`

---

## 10) Support / next debugging info

When debugging patient auth, capture:
- Backend log line: `firebase_verify_id_token_failed: ...`
- Browser network response for `/api/patient-auth/session`

---
