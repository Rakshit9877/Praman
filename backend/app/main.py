import os
import json
import uuid
import datetime
from pathlib import Path
from fastapi import FastAPI, UploadFile, Form, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Praman Backend Skeleton")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AI_MODE = os.getenv("AI_MODE", "mock")

def load_fixture(name: str):
    path = Path(f"contracts/fixtures/{name}.json")
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}

@app.get("/api/health")
def health():
    return {"ok": True, "ai_mode": AI_MODE}

@app.get("/api/pubkey")
def pubkey():
    return {
        "key_id": "dummy",
        "public_key_b64": "dummy"
    }

@app.get("/api/wage-table")
def get_wage_table():
    path = Path("contracts/wage_table.json")
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}

@app.post("/api/workers/session")
def create_session():
    return load_fixture("WorkerSession") or {
        "worker_id": str(uuid.uuid4()),
        "created_at": datetime.datetime.now(datetime.UTC).isoformat()
    }

@app.post("/api/voice")
def post_voice(
    audio: UploadFile = File(...),
    worker_id: str = Form(...),
    transcript_override: str = Form(None)
):
    return {"job_id": str(uuid.uuid4())}

@app.post("/api/registers")
def post_registers(
    image: UploadFile = File(...),
    worker_id: str = Form(...),
    target_name: str = Form(None)
):
    return {"job_id": str(uuid.uuid4())}

# Simple mock for jobs
job_polls = {}

@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    polls = job_polls.get(job_id, 0)
    job_polls[job_id] = polls + 1
    
    if polls < 2:
        return {
            "job_id": job_id,
            "kind": "register",
            "status": "running",
            "stage": f"reading {polls + 1}/3",
            "progress": 0.3 * (polls + 1)
        }
    else:
        job = load_fixture("Job_register")
        if job:
            job["job_id"] = job_id
            return job
        return {
            "job_id": job_id,
            "kind": "register",
            "status": "done",
            "stage": "done",
            "progress": 1.0,
            "result": {}
        }

@app.post("/api/registers/{extraction_id}/confirm")
def confirm_register(extraction_id: str, payload: dict):
    return load_fixture("ConfirmRegisterOut") or {}

@app.get("/api/workers/{worker_id}/records")
def get_records(worker_id: str):
    records = load_fixture("WorkRecordList")
    return records if records else []

@app.post("/api/attestations")
def create_attestation(payload: dict):
    return load_fixture("AttestationView") or {}

@app.get("/api/attestations/{token}")
def get_attestation(token: str):
    return load_fixture("AttestationView") or {}

@app.post("/api/attestations/{token}/respond")
def respond_attestation(token: str, payload: dict):
    return load_fixture("AttestationView") or {}

@app.post("/api/passports")
def issue_passport(payload: dict):
    return load_fixture("SignedPassport") or {}

@app.get("/api/passports/{passport_id}")
def get_passport(passport_id: str):
    return load_fixture("SignedPassport") or {}

@app.get("/api/files/{image_id}")
def get_file(image_id: str):
    # Dummy placeholder image logic
    return "placeholder"

@app.post("/api/demo/seed")
def demo_seed():
    return {"status": "seeded"}

@app.post("/api/demo/reset")
def demo_reset():
    return {"status": "reset"}
