import os
import json
import datetime
from pathlib import Path
from contracts.schemas import (
    WorkerSession, Job, RegisterExtraction, RegisterHeader, ReadField,
    RegisterRow, DayCell, Mark, ConfirmRegisterOut, WorkRecord, EvidenceLevel,
    Origin, ReconciliationReport, Trade, AttestationView, SignedPassport,
    PassportPayload, PassportWorker, PassportRecordSummary, TrustResult, SkillClass, WageBand
)
from backend.app.signing import canonicalize
import nacl.signing
import nacl.encoding
import base64

seed_b64 = "dNSkWxVzwRXV3cMKFpISpcfODr4RGnbYjgkXtmu/xf4="
seed = base64.b64decode(seed_b64)
signing_key = nacl.signing.SigningKey(seed)
key_id = "4334b749"
pubkey_b64 = "YSsKhbl341iL9PP7OzR9EnriZ2UA1jseN3nvC7JDdfI="

def save_fixture(name: str, model):
    if isinstance(model, list):
        data = [m.model_dump(mode="json") for m in model]
    else:
        data = model.model_dump(mode="json")
    Path(f"contracts/fixtures/{name}.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

def main():
    os.makedirs("contracts/fixtures", exist_ok=True)
    
    # WorkerSession
    session = WorkerSession(worker_id="w-123", created_at=datetime.datetime.now(datetime.UTC))
    save_fixture("WorkerSession", session)
    
    # RegisterExtraction
    read_field = ReadField(value="Test", confidence=1.0)
    header = RegisterHeader(site_name=read_field, contractor_name=read_field, month=ReadField(value="1", confidence=1.0), year=ReadField(value="2026", confidence=1.0))
    cells = [DayCell(day=1, mark=Mark.present, confidence=0.9, needs_confirmation=False)]
    row = RegisterRow(row_index=1, name_raw="Rakesh", computed_total=1.0, cells=cells)
    ext = RegisterExtraction(extraction_id="ext-1", image_id="img-1", header=header, rows=[row], n_samples=3, models=["m1"])
    
    job_reg = Job(job_id="j-1", kind="register", status="done", result=ext)
    save_fixture("Job_register", job_reg)
    
    # WorkRecord
    record = WorkRecord(
        record_id="rec-1", worker_id="w-123", site_name="Test Site", period_from=datetime.date(2026,1,1),
        period_to=datetime.date(2026,1,31), days_worked=26.0, evidence=EvidenceLevel.register, origin=Origin.live
    )
    save_fixture("WorkRecordList", [record])
    
    # ConfirmRegisterOut
    report = ReconciliationReport(verified_days=26.0, verified_sites=1, attested_sites=0, evidenced_span_years=0.1)
    confirm_out = ConfirmRegisterOut(record=record, report=report)
    save_fixture("ConfirmRegisterOut", confirm_out)
    
    # AttestationView
    attest = AttestationView(
        token="t-123", record_id="rec-1", worker_display_name="Rakesh", site_name="Test Site",
        period_from=datetime.date(2026,1,1), period_to=datetime.date(2026,1,31), days_claimed=26.0,
        status="pending", url="http://localhost:5173/attest/t-123", created_at=datetime.datetime.now(datetime.UTC)
    )
    save_fixture("AttestationView", attest)
    
    # SignedPassport
    worker = PassportWorker(worker_ref="ref-123", display_name="Rakesh", trade=Trade.mason)
    rec_sum = PassportRecordSummary(site_name="Test Site", period_from=datetime.date(2026,1,1), period_to=datetime.date(2026,1,31), days_worked=26.0, evidence=EvidenceLevel.register, origin=Origin.live)
    trust = TrustResult(score=80, level="high", breakdown={"coverage":40}, suggested_class=SkillClass.skilled, class_reason="Passed")
    wage = WageBand(area="A", suggested_class=SkillClass.skilled, daily_wage=1008.0, unskilled_daily_wage=827.0, delta_per_day=181.0, delta_pct=21.8, monthly_delta_26d=4706.0, source="Test", effective_from=datetime.date(2026,4,1), effective_to=datetime.date(2026,9,30))
    payload = PassportPayload(
        passport_id="pass-123", issued_at=datetime.datetime.now(datetime.UTC), worker=worker, records=[rec_sum],
        verified_days=26.0, verified_sites=1, attested_sites=0, evidenced_span_years=0.1,
        trust=trust, wage_bands={"A": wage}
    )
    
    canonical = canonicalize(payload)
    sig = signing_key.sign(canonical.encode("utf-8"))
    sig_b64 = base64.b64encode(sig.signature).decode('utf-8')
    
    passport = SignedPassport(
        payload_canonical=canonical, signature_b64=sig_b64, key_id=key_id, public_key_b64=pubkey_b64, verify_url="http://localhost:5173/verify/pass-123"
    )
    save_fixture("SignedPassport", passport)
    print("Fixtures created successfully.")

if __name__ == "__main__":
    main()
