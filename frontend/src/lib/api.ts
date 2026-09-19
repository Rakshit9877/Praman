import type { WorkerSession, Job, WorkRecord, SignedPassport } from './types';

const API_BASE = '/api';

async function apiFetch(url: string, options?: RequestInit): Promise<Response> {
  const res = await fetch(url, options);
  if (!res.ok) {
    let detail = '';
    try { detail = (await res.clone().json()).detail ?? ''; } catch { /* ignore */ }
    throw new Error(detail || `HTTP ${res.status} — ${url}`);
  }
  return res;
}

export async function createSession(): Promise<WorkerSession> {
  const res = await apiFetch(`${API_BASE}/workers/session`, { method: 'POST' });
  return res.json();
}

export async function seedDemo(): Promise<{ worker_id: string }> {
  const res = await apiFetch(`${API_BASE}/demo/seed`, { method: 'POST' });
  return res.json();
}

export async function resetDemo(): Promise<void> {
  await apiFetch(`${API_BASE}/demo/reset`, { method: 'POST' });
}

export async function submitVoice(
  workerId: string,
  audioBlob: Blob | null,
  transcriptOverride?: string
): Promise<{ job_id: string }> {
  const formData = new FormData();
  formData.append('worker_id', workerId);
  if (audioBlob) formData.append('audio', audioBlob, 'audio.webm');
  if (transcriptOverride) formData.append('transcript_override', transcriptOverride);
  const res = await apiFetch(`${API_BASE}/voice`, { method: 'POST', body: formData });
  return res.json();
}

export async function submitRegister(
  workerId: string,
  imageBlob: Blob,
  targetName?: string
): Promise<{ job_id: string }> {
  const formData = new FormData();
  formData.append('worker_id', workerId);
  formData.append('image', imageBlob, 'register.jpg');
  if (targetName) formData.append('target_name', targetName);
  const res = await apiFetch(`${API_BASE}/registers`, { method: 'POST', body: formData });
  return res.json();
}

export async function getJob(jobId: string): Promise<Job> {
  const res = await apiFetch(`${API_BASE}/jobs/${jobId}`);
  return res.json();
}

export async function getRecords(workerId: string): Promise<WorkRecord[]> {
  const res = await apiFetch(`${API_BASE}/workers/${workerId}/records`);
  return res.json();
}

export async function confirmRegister(
  extractionId: string,
  body: object
): Promise<{ record: WorkRecord; report: object }> {
  const res = await apiFetch(`${API_BASE}/registers/${extractionId}/confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return res.json();
}

export async function createAttestation(
  recordId: string,
  employerName: string
): Promise<{ token: string; record_id: string; status: string }> {
  const res = await apiFetch(`${API_BASE}/attestations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ record_id: recordId, employer_name: employerName }),
  });
  return res.json();
}

export async function getAttestation(
  token: string
): Promise<{ token: string; status: string; worker_display_name: string; site_name: string; days_claimed: number; role: string }> {
  const res = await apiFetch(`${API_BASE}/attestations/${token}`);
  return res.json();
}

export async function respondAttestation(
  token: string,
  decision: string,
  employerName: string
): Promise<object> {
  const res = await apiFetch(`${API_BASE}/attestations/${token}/respond`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ decision, employer_name: employerName }),
  });
  return res.json();
}

export async function issuePassport(workerId: string): Promise<SignedPassport> {
  const res = await apiFetch(`${API_BASE}/passports`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ worker_id: workerId }),
  });
  return res.json();
}

export async function pollJob(
  jobId: string,
  onProgress: (msg: string) => void
): Promise<any> {
  return new Promise((resolve, reject) => {
    const interval = setInterval(async () => {
      try {
        const job = await getJob(jobId);
        if (job.status === 'done') {
          clearInterval(interval);
          resolve(job.result);
        } else if (job.status === 'error') {
          clearInterval(interval);
          reject(new Error(job.error || 'Job failed'));
        } else {
          onProgress(`${job.stage} (${Math.round(job.progress * 100)}%)`);
        }
      } catch (err) {
        clearInterval(interval);
        reject(err);
      }
    }, 700);
  });
}
