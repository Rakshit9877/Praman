"""contracts/schemas.py — SINGLE SOURCE OF TRUTH for every data shape.
Change only via a PR labelled `contract-change`. Mirror changes in frontend/src/lib/types.ts.
Fictional data only. No Aadhaar, no phone numbers in anything that gets signed."""
from __future__ import annotations
from datetime import date, datetime
from enum import Enum
from typing import Literal, Optional, Union
from pydantic import BaseModel, Field

SCHEMA_VERSION = "1.0"

# ---------- enums ----------
class Trade(str, Enum):
    mason = "mason"; carpenter = "carpenter"; bar_bender = "bar_bender"; plumber = "plumber"
    electrician = "electrician"; painter = "painter"; welder = "welder"; tiler = "tiler"
    helper = "helper"; other = "other"

class SkillClass(str, Enum):
    unskilled = "unskilled"; semi_skilled = "semi_skilled"; skilled = "skilled"; highly_skilled = "highly_skilled"

class Mark(str, Enum):
    present = "P"; absent = "A"; half = "H"; unreadable = "?"

class EvidenceLevel(str, Enum):
    self_claim = "self_claim"      # voice only
    register = "register"          # register page read + worker confirmed uncertain cells
    attested = "attested"          # + employer confirmed

class Origin(str, Enum):
    live = "live"; seeded = "seeded"

# ---------- register reading ----------
class ReadField(BaseModel):
    value: Optional[str] = None
    confidence: float = Field(0.0, ge=0, le=1)   # agreement across readings
    needs_confirmation: bool = False
    alternatives: list[str] = []

class DayCell(BaseModel):
    day: int = Field(ge=1, le=31)
    mark: Mark
    confidence: float = Field(ge=0, le=1)        # = share of readings that voted for `mark`
    needs_confirmation: bool
    alternatives: list[Mark] = []
    reasons: list[str] = []                      # readers_disagree | unreadable | total_mismatch

class RegisterRow(BaseModel):
    row_index: int
    name_raw: str                                 # exactly as written (Devanagari stays Devanagari)
    name_latin: Optional[str] = None              # romanised by the reader, used for matching
    name_match_score: float = 0.0                 # 0..1 vs target name
    is_target: bool = False
    bbox: Optional[list[float]] = None            # [x0,y0,x1,y1] fractions of preprocessed image
    cells: list[DayCell]
    written_total: Optional[float] = None
    computed_total: float
    total_consistent: Optional[bool] = None

class RegisterHeader(BaseModel):
    site_name: ReadField
    contractor_name: ReadField
    month: ReadField                              # "1"..."12"
    year: ReadField

class RegisterExtraction(BaseModel):
    extraction_id: str
    image_id: str
    image_url: Optional[str] = None               # filled by backend (preprocessed image)
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    header: RegisterHeader
    rows: list[RegisterRow]
    n_samples: int
    models: list[str]
    warnings: list[str] = []
    elapsed_s: float = 0.0

# ---------- voice ----------
class ClaimedSite(BaseModel):
    site_name: Optional[str] = None
    city: Optional[str] = None
    employer_name: Optional[str] = None
    approx_from_year: Optional[int] = None
    approx_to_year: Optional[int] = None

class VoiceClaim(BaseModel):
    claim_id: str
    transcript: str
    language: str = "hi"
    name: Optional[str] = None
    trade: Optional[Trade] = None
    years_experience: Optional[float] = None
    sites: list[ClaimedSite] = []
    confidence: float = 0.0
    asr_backend: str = ""

# ---------- work records, reconciliation, trust ----------
class WorkRecord(BaseModel):
    record_id: str
    worker_id: str
    site_name: str
    employer_name: Optional[str] = None
    city: Optional[str] = None
    role: Optional[Trade] = None
    period_from: date
    period_to: date
    days_worked: float                            # P=1, H=0.5
    day_marks: dict[str, str] = {}                # ISO date -> "P"|"H" (worked days only)
    evidence: EvidenceLevel
    origin: Origin = Origin.live
    image_id: Optional[str] = None
    cells_confirmed_by_worker: int = 0
    cells_auto_accepted: int = 0
    attestation_id: Optional[str] = None
    attestation_status: Optional[Literal["pending", "confirmed", "disputed", "unknown"]] = None

class Flag(BaseModel):
    code: str                                     # SAME_DAY_TWO_SITES | TOTAL_MISMATCH | DATE_INVALID | CLAIM_EXCEEDS_EVIDENCE | TRADE_MISMATCH
    severity: Literal["info", "warn", "conflict"]
    message: str
    record_ids: list[str] = []

class ReconciliationReport(BaseModel):
    verified_days: float
    verified_sites: int
    attested_sites: int
    evidenced_span_years: float                   # verified_days / 260 (work-years)
    claimed_years: Optional[float] = None
    flags: list[Flag] = []

class TrustResult(BaseModel):
    score: int = Field(ge=0, le=100)
    level: Literal["low", "medium", "high"]
    breakdown: dict[str, float]                   # coverage, attestation, consistency, claim_alignment
    suggested_class: SkillClass
    class_reason: str

class WageBand(BaseModel):
    area: Literal["A", "B", "C"]
    suggested_class: SkillClass
    daily_wage: float
    unskilled_daily_wage: float
    delta_per_day: float
    delta_pct: float
    monthly_delta_26d: float
    source: str
    effective_from: date
    effective_to: date

# ---------- API in/out ----------
class WorkerSession(BaseModel):
    worker_id: str
    created_at: datetime

class Job(BaseModel):
    job_id: str
    kind: Literal["register", "voice"]
    status: Literal["queued", "running", "done", "error"]
    stage: str = ""                                # preprocess | reading 1/3 ... | cross-check | done
    progress: float = 0.0
    result: Optional[Union[RegisterExtraction, VoiceClaim]] = None
    error: Optional[str] = None

class CellCorrection(BaseModel):
    row_index: int
    day: int
    mark: Mark

class ConfirmRegisterIn(BaseModel):
    worker_id: str
    target_row_index: int
    corrections: list[CellCorrection] = []        # MUST cover every needs_confirmation cell of the target row
    site_name: Optional[str] = None
    employer_name: Optional[str] = None
    city: Optional[str] = None
    month: Optional[int] = None
    year: Optional[int] = None
    role: Optional[Trade] = None

class ConfirmRegisterOut(BaseModel):
    record: WorkRecord
    report: ReconciliationReport

class CreateAttestationIn(BaseModel):
    record_id: str
    employer_name: Optional[str] = None

class AttestationView(BaseModel):
    token: str
    record_id: str
    worker_display_name: str
    site_name: str
    period_from: date
    period_to: date
    days_claimed: float
    role: Optional[Trade] = None
    status: Literal["pending", "confirmed", "disputed", "unknown"]
    url: str
    created_at: datetime

class AttestationResponseIn(BaseModel):
    decision: Literal["confirmed", "disputed", "unknown"]
    employer_name: str
    corrected_from: Optional[date] = None
    corrected_to: Optional[date] = None
    # DESIGN: no free text and no rating fields. Facts only. Do not add any.

class IssuePassportIn(BaseModel):
    worker_id: str

# ---------- passport ----------
class PassportWorker(BaseModel):
    worker_ref: str                                # random id; never Aadhaar/phone
    display_name: str                              # first name (+ initial)
    trade: Optional[Trade] = None

class PassportRecordSummary(BaseModel):
    site_name: str
    employer_name: Optional[str] = None
    city: Optional[str] = None
    role: Optional[Trade] = None
    period_from: date
    period_to: date
    days_worked: float
    evidence: EvidenceLevel
    origin: Origin

class PassportPayload(BaseModel):                 # <- this is what gets signed
    schema_version: str = SCHEMA_VERSION
    passport_id: str
    issued_at: datetime
    worker: PassportWorker
    records: list[PassportRecordSummary]
    verified_days: float
    verified_sites: int
    attested_sites: int
    claimed_years: Optional[float] = None
    evidenced_span_years: float
    trust: TrustResult
    wage_bands: dict[str, WageBand]                # keys "A","B","C"
    flags: list[Flag] = []
    issuer: str = "Praman (hackathon demo)"

class SignedPassport(BaseModel):
    payload_canonical: str    # exact UTF-8 string that was signed = json.dumps(payload.model_dump(mode="json"),...)
    signature_b64: str        # Ed25519 detached signature over payload_canonical.encode("utf-8")
    key_id: str                # first 8 hex chars of sha256(public key bytes)
    public_key_b64: str        # convenience only. Verifiers MUST pin the issuer key.
    verify_url: str
