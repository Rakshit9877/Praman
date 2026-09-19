// contracts/schemas.py mirrored in TS
export type Trade = 'mason' | 'carpenter' | 'bar_bender' | 'plumber' | 'electrician' | 'painter' | 'welder' | 'tiler' | 'helper' | 'other';
export type SkillClass = 'unskilled' | 'semi_skilled' | 'skilled' | 'highly_skilled';
export type Mark = 'P' | 'A' | 'H' | '?';
export type EvidenceLevel = 'self_claim' | 'register' | 'attested';
export type Origin = 'live' | 'seeded';

export interface WorkerSession {
  worker_id: string;
  created_at: string;
}

export interface Job {
  job_id: string;
  kind: 'register' | 'voice';
  status: 'queued' | 'running' | 'done' | 'error';
  stage: string;
  progress: number;
  result?: any;
  error?: string;
}

export interface WorkRecord {
  record_id: string;
  worker_id: string;
  site_name: string;
  employer_name?: string;
  city?: string;
  role?: Trade;
  period_from: string;
  period_to: string;
  days_worked: number;
  day_marks: Record<string, string>;
  evidence: EvidenceLevel;
  origin: Origin;
  image_id?: string;
  cells_confirmed_by_worker: number;
  cells_auto_accepted: number;
  attestation_id?: string;
  attestation_status?: 'pending' | 'confirmed' | 'disputed' | 'unknown';
}

export interface AttestationView {
  token: string;
  record_id: string;
  worker_display_name: string;
  site_name: string;
  period_from: string;
  period_to: string;
  days_claimed: number;
  role?: Trade;
  status: 'pending' | 'confirmed' | 'disputed' | 'unknown';
  url: string;
  created_at: string;
}

export interface SignedPassport {
  payload_canonical: string;
  signature_b64: string;
  key_id: string;
  public_key_b64: string;
  verify_url: string;
}
