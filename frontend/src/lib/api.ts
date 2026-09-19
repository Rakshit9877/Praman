import type { WorkerSession, Job, WorkRecord, SignedPassport } from './types';

const API_BASE = '/api';

export async function createSession(): Promise<WorkerSession> {
  const res = await fetch(`${API_BASE}/workers/session`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to create session');
  return res.json();
}

export async function submitVoice(workerId: string, audioBlob: Blob): Promise<{ job_id: string }> {
  const formData = new FormData();
  formData.append('worker_id', workerId);
  formData.append('audio', audioBlob, 'audio.webm');
  
  const res = await fetch(`${API_BASE}/voice`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error('Failed to submit voice');
  return res.json();
}

export async function submitRegister(workerId: string, imageBlob: Blob): Promise<{ job_id: string }> {
  const formData = new FormData();
  formData.append('worker_id', workerId);
  formData.append('image', imageBlob, 'register.jpg');
  
  const res = await fetch(`${API_BASE}/registers`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error('Failed to submit register');
  return res.json();
}

export async function getJob(jobId: string): Promise<Job> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}`);
  if (!res.ok) throw new Error('Failed to get job status');
  return res.json();
}

export async function getRecords(workerId: string): Promise<WorkRecord[]> {
  const res = await fetch(`${API_BASE}/workers/${workerId}/records`);
  if (!res.ok) throw new Error('Failed to get records');
  return res.json();
}

export async function issuePassport(workerId: string): Promise<SignedPassport> {
  const res = await fetch(`${API_BASE}/passports`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ worker_id: workerId })
  });
  if (!res.ok) throw new Error('Failed to issue passport');
  return res.json();
}
