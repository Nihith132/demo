from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from routers import auth, doctors, patient, patient_auth
from routers import files as files_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Healthcare Triage Assistant API",
    description="Agentic multi-modal patient triage system",
    version="1.0.0",
)

# CORS for local dev (Next.js on :3000 calling FastAPI on :8002)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(patient.router, prefix="/api/patient", tags=["Patient Dashboard"])
app.include_router(doctors.router, prefix="/api/doctors", tags=["Doctors"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(patient_auth.router, prefix="/api/patient-auth", tags=["Patient Auth"])
app.include_router(files_router.router, prefix="/api/files", tags=["Files"])


@app.get("/health")
def health_check():
    return {"status": "ok"}
