import os
import json
import uuid
import datetime
import secrets
from pathlib import Path
from fastapi import FastAPI, UploadFile, Form, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from contracts.schemas import ConfirmRegisterIn, CreateAttestationIn, AttestationResponseIn, IssuePassportIn, PassportPayload, PassportWorker, AttestationView, SignedPassport, Origin, EvidenceLevel
from backend.app import db, storage, jobs, signing
from ai_core import api as ai

app = FastAPI(title="Praman Backend")

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
    sig_info = signing.sign_payload("{}")
    return {
        "key_id": sig_info["key_id"],
        "public_key_b64": sig_info["public_key_b64"]
    }

@app.get("/api/wage-table")
def get_wage_table():
    path = Path("contracts/wage_table.json")
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}

@app.post("/api/workers/session")
def create_session():
    worker_id = str(uuid.uuid4())
    session = {
        "worker_id": worker_id,
        "created_at": datetime.datetime.now(datetime.UTC).isoformat()
    }
    db.save_doc(worker_id, "session", session)
    return session

@app.post("/api/voice")
def post_voice(
    audio: UploadFile = File(None),
    worker_id: str = Form(...),
    transcript_override: str = Form(None)
):
    audio_path = None
    if audio:
        audio_path = storage.save_upload_file(audio, "voice_")
    
    job_id = jobs.create_job("voice")
    
    async def task():
        result = await ai.process_voice(
            audio_path, 
            transcript_override=transcript_override, 
            progress=jobs.get_progress_callback(job_id)
        )
        # Save claim to DB for worker
        db.save_doc(f"claim_{worker_id}", "claim", result.model_dump(mode="json") if hasattr(result, "model_dump") else result)
        return result
        
    jobs.dispatch_job(job_id, task())
    return {"job_id": job_id}

@app.post("/api/registers")
def post_registers(
    image: UploadFile = File(...),
    worker_id: str = Form(...),
    target_name: str = Form(None)
):
    image_path = storage.save_upload_file(image, "reg_")
    job_id = jobs.create_job("register")
    
    async def task():
        result = await ai.read_register(
            image_path,
            target_name=target_name,
            progress=jobs.get_progress_callback(job_id)
        )
        return result
        
    jobs.dispatch_job(job_id, task())
    return {"job_id": job_id}

@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    job = db.get_doc(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.post("/api/registers/{extraction_id}/confirm")
def confirm_register(extraction_id: str, payload: ConfirmRegisterIn):
    job = db.get_doc(extraction_id) # Using job_id from frontend since job result holds extraction
    # Wait, the job_id is NOT the extraction_id.
    # But for simplicity, we search all jobs for the extraction result.
    extraction = None
    for j in db.get_docs_by_type("job"):
        if j.get("result") and isinstance(j["result"], dict) and j["result"].get("extraction_id") == extraction_id:
            extraction = j["result"]
            break
            
    if not extraction:
        # Fallback to fixture if in mock mode and not found
        extraction = load_fixture("Job_register").get("result")
        if not extraction:
            raise HTTPException(status_code=404, detail="Extraction not found")
    
    # Needs to convert dict to model for ai function
    from contracts.schemas import RegisterExtraction
    extraction_model = RegisterExtraction.model_validate(extraction)
    
    record = ai.build_work_record(extraction_model, payload, worker_id=payload.worker_id)
    record_dict = record.model_dump(mode="json")
    db.save_doc(f"record_{record.record_id}", "record", record_dict)
    
    records_dicts = db.get_docs_by_type("record")
    from contracts.schemas import WorkRecord
    records = [WorkRecord.model_validate(r) for r in records_dicts if r.get("worker_id") == payload.worker_id]
    
    claim_dict = db.get_doc(f"claim_{payload.worker_id}")
    claim = None
    if claim_dict:
        from contracts.schemas import VoiceClaim
        claim = VoiceClaim.model_validate(claim_dict)
        
    report = ai.reconcile(claim, records)
    
    return {
        "record": record_dict,
        "report": report.model_dump(mode="json")
    }

@app.get("/api/workers/{worker_id}/records")
def get_records(worker_id: str):
    records = [r for r in db.get_docs_by_type("record") if r.get("worker_id") == worker_id]
    if AI_MODE == "mock" and not records:
        records = load_fixture("WorkRecordList") or []
    return records

@app.post("/api/attestations")
def create_attestation(payload: CreateAttestationIn):
    token = secrets.token_urlsafe(12)
    record_dict = db.get_doc(f"record_{payload.record_id}")
    
    if not record_dict and AI_MODE == "mock":
        fix = load_fixture("AttestationView")
        fix["token"] = token
        db.save_doc(f"attest_{token}", "attestation", fix)
        return fix
        
    if not record_dict:
        raise HTTPException(status_code=404, detail="Record not found")
        
    # Get worker name from voice claim if available, else just a placeholder
    worker_name = "Worker"
    claim_dict = db.get_doc(f"claim_{record_dict['worker_id']}")
    if claim_dict and claim_dict.get("name"):
        worker_name = claim_dict["name"]
        
    view = AttestationView(
        token=token,
        record_id=payload.record_id,
        worker_display_name=worker_name,
        site_name=record_dict["site_name"],
        period_from=record_dict["period_from"],
        period_to=record_dict["period_to"],
        days_claimed=record_dict["days_worked"],
        role=record_dict.get("role"),
        status="pending",
        url=f"http://localhost:5173/attest/{token}",
        created_at=datetime.datetime.now(datetime.UTC)
    )
    view_dict = view.model_dump(mode="json")
    db.save_doc(f"attest_{token}", "attestation", view_dict)
    
    record_dict["attestation_status"] = "pending"
    db.save_doc(f"record_{payload.record_id}", "record", record_dict)
    
    return view_dict

@app.get("/api/attestations/{token}")
def get_attestation(token: str):
    view = db.get_doc(f"attest_{token}")
    if not view:
        if AI_MODE == "mock":
            return load_fixture("AttestationView")
        raise HTTPException(status_code=404, detail="Attestation not found")
    return view

@app.post("/api/attestations/{token}/respond")
def respond_attestation(token: str, payload: AttestationResponseIn):
    view = db.get_doc(f"attest_{token}")
    if not view:
        raise HTTPException(status_code=404, detail="Attestation not found")
        
    view["status"] = payload.decision
    db.save_doc(f"attest_{token}", "attestation", view)
    
    record = db.get_doc(f"record_{view['record_id']}")
    if record:
        record["attestation_status"] = payload.decision
        if payload.decision == "confirmed":
            record["evidence"] = EvidenceLevel.attested.value
        db.save_doc(f"record_{view['record_id']}", "record", record)
        
    return view

@app.post("/api/passports")
def issue_passport(payload: IssuePassportIn):
    records_dicts = [r for r in db.get_docs_by_type("record") if r.get("worker_id") == payload.worker_id]
    if not records_dicts and AI_MODE == "mock":
        return load_fixture("SignedPassport")
        
    from contracts.schemas import WorkRecord, VoiceClaim
    records = [WorkRecord.model_validate(r) for r in records_dicts]
    
    claim_dict = db.get_doc(f"claim_{payload.worker_id}")
    claim = VoiceClaim.model_validate(claim_dict) if claim_dict else None
    
    report = ai.reconcile(claim, records)
    trust_res, wages = ai.score_passport(claim, records, report)
    
    passport_payload = PassportPayload(
        passport_id=str(uuid.uuid4()),
        issued_at=datetime.datetime.now(datetime.UTC),
        worker=PassportWorker(
            worker_ref=payload.worker_id,
            display_name=claim.name if claim and claim.name else "Unknown Worker",
            trade=claim.trade if claim else None
        ),
        records=[{
            "site_name": r.site_name,
            "employer_name": r.employer_name,
            "city": r.city,
            "role": r.role,
            "period_from": r.period_from,
            "period_to": r.period_to,
            "days_worked": r.days_worked,
            "evidence": r.evidence,
            "origin": r.origin
        } for r in records],
        verified_days=report.verified_days,
        verified_sites=report.verified_sites,
        attested_sites=report.attested_sites,
        claimed_years=report.claimed_years,
        evidenced_span_years=report.evidenced_span_years,
        trust=trust_res,
        wage_bands=wages,
        flags=report.flags
    )
    
    canonical = signing.canonicalize(passport_payload)
    sig_info = signing.sign_payload(canonical)
    
    signed = SignedPassport(
        payload_canonical=canonical,
        signature_b64=sig_info["signature_b64"],
        key_id=sig_info["key_id"],
        public_key_b64=sig_info["public_key_b64"],
        verify_url=f"http://localhost:5173/verify/{passport_payload.passport_id}"
    )
    
    db.save_doc(f"passport_{passport_payload.passport_id}", "passport", signed.model_dump(mode="json"))
    return signed

@app.get("/api/passports/{passport_id}")
def get_passport(passport_id: str):
    passport = db.get_doc(f"passport_{passport_id}")
    if not passport:
        if AI_MODE == "mock":
            return load_fixture("SignedPassport")
        raise HTTPException(status_code=404, detail="Passport not found")
    return passport

@app.get("/api/files/{image_id}")
def get_file(image_id: str):
    # In a real app we'd map image_id to the actual file path.
    # For now, let's just return a placeholder or look up storage
    # Actually, the job saves to storage and returns image_url = /api/files/xxx
    path = storage.get_file_path(image_id)
    if os.path.exists(path):
        return FileResponse(path)
    raise HTTPException(status_code=404, detail="File not found")

@app.post("/api/demo/seed")
def demo_seed():
    worker_id = "demo-worker-123"
    db.save_doc(worker_id, "session", {"worker_id": worker_id})
    
    # Load 4 valid seeded records from fixture
    records = load_fixture("WorkRecordList")
    for r in records:
        r["worker_id"] = worker_id
        db.save_doc(f"record_{r['record_id']}", "record", r)
        
    return {"status": "seeded", "worker_id": worker_id}

@app.post("/api/demo/reset")
def demo_reset():
    db.delete_all()
    return {"status": "reset"}
