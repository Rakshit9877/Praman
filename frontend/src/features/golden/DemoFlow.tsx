/**
 * DemoFlow.tsx — Complete end-to-end hackathon demo.
 *
 * Steps:
 *  1. landing       — "Rakesh · NO PROOF · ₹827/day"
 *  2. voice         — typed Hindi fallback, sends transcript_override
 *  3. register      — file upload or "Use demo register" (1×1 px blob)
 *  4. cells         — derived amber cells, "Confirm all flagged" → "Save work record"
 *  5. attest        — employer "Confirm: I worked with Rakesh"
 *  6. passport      — wage delta ₹827 → ₹1,008
 *  7. verify        — Ed25519 browser verify + tamper test
 */
import React, { useState, useCallback, useRef } from 'react';
import { Routes, Route } from 'react-router-dom';
import nacl from 'tweetnacl';
import { decodeBase64 } from 'tweetnacl-util';
import {
  createSession, seedDemo,
  submitVoice, submitRegister,
  pollJob, confirmRegister,
  createAttestation, respondAttestation,
  issuePassport,
} from '../../lib/api';
import type { SignedPassport } from '../../lib/types';

// ─── tiny shared primitives ─────────────────────────────────────────────────

const STEPS = ['landing', 'voice', 'register', 'cells', 'attest', 'passport', 'verify'] as const;
type Step = typeof STEPS[number];

const STEP_LABELS: Record<Step, string> = {
  landing: 'Worker story',
  voice: 'Worker story',
  register: 'Attendance register',
  cells: 'Confirm cells',
  attest: 'Employer confirmation',
  passport: 'Skill passport',
  verify: 'Cryptographic proof',
};

const HINDI_TEXT =
  'मेरा नाम राकेश है। मैं राजमिस्त्री का काम करता हूँ। मुझे दस साल का अनुभव है। मैंने मोहाली, नोएडा और गुरुग्राम में काम किया है।';

// ─── Step indicator ──────────────────────────────────────────────────────────

function StepBar({ step, onReset }: { step: Step; onReset: () => void }) {
  if (step === 'landing') return null;
  const visibleSteps = STEPS.slice(1); // exclude landing
  const visIdx = visibleSteps.indexOf(step);
  return (
    <div className="flex items-center justify-between mb-6 w-full">
      <button
        onClick={onReset}
        className="text-xs text-neutral-500 uppercase font-mono tracking-widest hover:text-white transition-colors"
      >
        ← Reset
      </button>
      <span className="text-xs text-neutral-500 font-mono uppercase tracking-widest">
        {visIdx + 1} / {visibleSteps.length} — {STEP_LABELS[step]}
      </span>
      <div className="flex gap-1">
        {visibleSteps.map((s, i) => (
          <div
            key={s}
            className={`h-1 w-4 rounded-full transition-colors ${
              i <= visIdx ? 'bg-green-400' : 'bg-neutral-700'
            }`}
          />
        ))}
      </div>
    </div>
  );
}

// ─── Error banner ────────────────────────────────────────────────────────────

function ErrorBanner({ msg, onDismiss }: { msg: string; onDismiss: () => void }) {
  if (!msg) return null;
  return (
    <div className="bg-red-500/20 border border-red-500/40 text-red-300 rounded-xl p-4 mb-4 text-sm flex flex-col gap-2">
      <p>{msg}</p>
      <button
        onClick={onDismiss}
        className="self-end text-xs font-mono uppercase tracking-wider border border-red-400/40 px-3 py-1 rounded-lg hover:bg-red-400/10"
      >
        Retry
      </button>
    </div>
  );
}

// ─── Spinner ─────────────────────────────────────────────────────────────────

function Spinner({ msg }: { msg: string }) {
  return (
    <div className="flex flex-col items-center gap-4 py-12">
      <div className="w-10 h-10 border-2 border-green-400 border-t-transparent rounded-full animate-spin" />
      <p className="text-green-400 font-mono text-xs uppercase tracking-widest text-center">{msg}</p>
    </div>
  );
}

// ─── Btn ──────────────────────────────────────────────────────────────────────

function Btn({
  onClick, children, disabled, variant = 'primary', className = '',
}: {
  onClick?: () => void;
  children: React.ReactNode;
  disabled?: boolean;
  variant?: 'primary' | 'secondary' | 'ghost';
  className?: string;
}) {
  const base =
    'w-full py-4 rounded-2xl font-bold text-base transition-all duration-200 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed';
  const variants = {
    primary: 'bg-green-400 text-black shadow-[0_0_30px_rgba(74,222,128,0.25)] hover:shadow-[0_0_40px_rgba(74,222,128,0.4)] hover:scale-[1.02]',
    secondary: 'bg-neutral-800 text-white border border-neutral-700 hover:bg-neutral-700',
    ghost: 'text-neutral-400 underline text-sm',
  };
  return (
    <button onClick={onClick} disabled={disabled} className={`${base} ${variants[variant]} ${className}`}>
      {children}
    </button>
  );
}

// ─── Main flow component ─────────────────────────────────────────────────────

function MainFlow() {
  const [step, setStep] = useState<Step>('landing');
  const [workerId, setWorkerId] = useState('');
  const [busy, setBusy] = useState(false);
  const [busyMsg, setBusyMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  // step-specific data
  const [_voiceClaim, setVoiceClaim] = useState<any>(null);
  const [extraction, setExtraction] = useState<any>(null);
  const [flaggedCells, setFlaggedCells] = useState<any[]>([]);
  const [cellOverrides, setCellOverrides] = useState<Record<number, 'P'>>({});
  const [savedRecord, setSavedRecord] = useState<any>(null);
  const [attestToken, setAttestToken] = useState('');
  const [attestDone, setAttestDone] = useState(false);
  const [passport, setPassport] = useState<SignedPassport | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // ── helpers ──────────────────────────────────────────────────────────────

  const wrap = useCallback(async (fn: () => Promise<void>, loadingMsg = 'Processing...') => {
    setBusy(true);
    setBusyMsg(loadingMsg);
    setErrorMsg('');
    try {
      await fn();
    } catch (err: any) {
      setErrorMsg(err?.message || 'Unknown error');
    } finally {
      setBusy(false);
      setBusyMsg('');
    }
  }, []);

  const handleReset = useCallback(() => {
    setStep('landing');
    setWorkerId('');
    setVoiceClaim(null);
    setExtraction(null);
    setFlaggedCells([]);
    setCellOverrides({});
    setSavedRecord(null);
    setAttestToken('');
    setAttestDone(false);
    setPassport(null);
    setErrorMsg('');
  }, []);

  // ── STEP 1: Landing ──────────────────────────────────────────────────────

  const handleStart = () =>
    wrap(async () => {
      const session = await createSession();
      setWorkerId(session.worker_id);
      // Seed once so passport has history
      await seedDemo();
      setStep('voice');
    }, 'Starting...');

  // ── STEP 2: Voice ────────────────────────────────────────────────────────

  const handleTypedStory = () =>
    wrap(async () => {
      const { job_id } = await submitVoice(workerId, null, HINDI_TEXT);
      const result = await pollJob(job_id, setBusyMsg);
      if (result) {
        setVoiceClaim(result);
      } else {
        // Demo fallback if voice endpoint returns null
        setVoiceClaim({
          _fallback: true,
          name: 'Rakesh',
          trade: 'mason',
          years_experience: 10,
          sites: [{ site_name: 'Mohali Sector 82' }, { site_name: 'Noida' }, { site_name: 'Gurugram' }],
          transcript: HINDI_TEXT,
          language: 'hi',
        });
      }
      setStep('register');
    }, 'Processing story...');

  // ── STEP 3: Register ─────────────────────────────────────────────────────

  const processRegisterBlob = async (blob: Blob) => {
    const { job_id } = await submitRegister(workerId, blob, 'Rakesh');
    const result = await pollJob(job_id, setBusyMsg);
    const ext = result;
    setExtraction(ext);

    // Derive flagged cells from the first (target) row
    const targetRow = ext?.rows?.find((r: any) => r.is_target) ?? ext?.rows?.[0];
    const flagged = (targetRow?.cells ?? []).filter((c: any) => c.needs_confirmation);
    setFlaggedCells(flagged);
    setCellOverrides({});
    setStep('cells');
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    wrap(() => processRegisterBlob(file), 'Reading register...');
  };

  const handleUseDemoRegister = () => {
    // Create a minimal 1×1 white JPEG as a placeholder — mock backend ignores the image
    const canvas = document.createElement('canvas');
    canvas.width = 1; canvas.height = 1;
    canvas.toBlob((blob) => {
      if (blob) wrap(() => processRegisterBlob(blob), 'Reading register...');
    }, 'image/jpeg');
  };

  // ── STEP 4: Cells ────────────────────────────────────────────────────────

  const allResolved = flaggedCells.length === 0 || flaggedCells.every((c) => cellOverrides[c.day] === 'P');

  const handleConfirmAll = () => {
    const overrides: Record<number, 'P'> = {};
    flaggedCells.forEach((c) => { overrides[c.day] = 'P'; });
    setCellOverrides(overrides);
  };

  const handleSaveRecord = () =>
    wrap(async () => {
      const targetRow = extraction?.rows?.find((r: any) => r.is_target) ?? extraction?.rows?.[0];
      const rowIndex = targetRow?.row_index ?? 0;
      const corrections = flaggedCells.map((c) => ({
        row_index: rowIndex,
        day: c.day,
        mark: cellOverrides[c.day] ?? 'P',
      }));

      const header = extraction?.header ?? {};
      const body = {
        worker_id: workerId,
        target_row_index: rowIndex,
        corrections,
        site_name: header.site_name?.value ?? 'Mohali Sector 82',
        employer_name: header.contractor_name?.value ?? 'Sunil',
        city: 'Mohali',
        month: parseInt(header.month?.value ?? '7', 10),
        year: parseInt(header.year?.value ?? '2026', 10),
        role: 'mason',
      };

      const { record } = await confirmRegister(extraction.extraction_id, body);
      setSavedRecord(record);
      setStep('attest');
    }, 'Saving work record...');

  // ── STEP 5: Attestation ──────────────────────────────────────────────────

  const handleCreateAttest = () =>
    wrap(async () => {
      const recordId = savedRecord?.record_id;
      if (!recordId) throw new Error('No record saved');
      const attest = await createAttestation(recordId, 'Sunil');
      setAttestToken(attest.token);
    }, 'Creating attestation...');

  const handleEmployerConfirm = () =>
    wrap(async () => {
      await respondAttestation(attestToken, 'confirmed', 'Sunil');
      setAttestDone(true);
    }, 'Confirming...');

  // ── STEP 6: Passport ─────────────────────────────────────────────────────

  const handleIssuePassport = () =>
    wrap(async () => {
      const p = await issuePassport(workerId);
      setPassport(p);
      setStep('passport');
    }, 'Issuing passport...');

  // ── STEP 7: Verify ───────────────────────────────────────────────────────

  const handleVerify = () => setStep('verify');

  // ── render helpers ───────────────────────────────────────────────────────

  const targetRow =
    extraction?.rows?.find((r: any) => r.is_target) ?? extraction?.rows?.[0];

  // ── JSX ──────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-neutral-950 text-white font-sans p-5 max-w-md mx-auto flex flex-col">
      <StepBar step={step} onReset={handleReset} />
      <ErrorBanner msg={errorMsg} onDismiss={() => setErrorMsg('')} />

      {/* ── STEP: landing ───────────────────────────────────────────────── */}
      {step === 'landing' && (
        <div className="flex-1 flex flex-col items-center justify-center gap-10 animate-in fade-in duration-500">
          <div className="text-center space-y-3">
            <p className="text-neutral-500 font-mono text-xs uppercase tracking-widest">Worker profile</p>
            <h1 className="text-6xl font-bold tracking-tight">Rakesh</h1>
            <p className="text-neutral-400 font-mono uppercase tracking-widest text-sm">No proof — Unskilled</p>
            <div className="mt-4 inline-block px-5 py-2 bg-neutral-900 rounded-full border border-neutral-800">
              <span className="text-2xl font-bold text-red-400">₹827</span>
              <span className="text-neutral-400 text-sm">/day</span>
            </div>
          </div>
          <div className="w-full max-w-[280px] flex flex-col gap-3">
            {busy ? <Spinner msg={busyMsg} /> : (
              <Btn onClick={handleStart}>Start verification</Btn>
            )}
          </div>
        </div>
      )}

      {/* ── STEP: voice ─────────────────────────────────────────────────── */}
      {step === 'voice' && (
        <div className="flex-1 flex flex-col gap-6 animate-in slide-in-from-right duration-300">
          <div className="text-center space-y-2">
            <h2 className="text-2xl font-bold">Tell us your work story</h2>
            <p className="text-neutral-400 text-sm">We'll extract your skills, trade, and sites.</p>
          </div>

          <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-4">
            <p className="text-xs text-neutral-500 uppercase font-mono tracking-widest mb-2">Story text (Hindi)</p>
            <p className="text-base leading-relaxed text-neutral-200">{HINDI_TEXT}</p>
          </div>

          {busy ? <Spinner msg={busyMsg} /> : (
            <div className="flex flex-col gap-3">
              <Btn onClick={handleTypedStory}>Continue with typed story</Btn>
              <p className="text-center text-xs text-neutral-600">Microphone not required for this demo</p>
            </div>
          )}
        </div>
      )}

      {/* ── STEP: register ──────────────────────────────────────────────── */}
      {step === 'register' && (
        <div className="flex-1 flex flex-col gap-6 animate-in slide-in-from-right duration-300">
          <div className="text-center space-y-2">
            <h2 className="text-2xl font-bold">Upload Hazri Register</h2>
            <p className="text-neutral-400 text-sm">Take a photo of the attendance page or use the demo register.</p>
          </div>

          {busy ? <Spinner msg={busyMsg} /> : (
            <div className="flex flex-col gap-3">
              <Btn onClick={handleUseDemoRegister}>Use demo register</Btn>

              <div className="relative">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleFileChange}
                  className="absolute inset-0 opacity-0 cursor-pointer w-full h-full z-10"
                />
                <Btn variant="secondary">📷 Upload your own register image</Btn>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── STEP: cells ─────────────────────────────────────────────────── */}
      {step === 'cells' && extraction && (
        <div className="flex-1 flex flex-col gap-5 animate-in slide-in-from-right duration-300">
          <div className="text-center space-y-1">
            <h2 className="text-2xl font-bold">Review Attendance</h2>
            <p className="text-neutral-400 text-sm">Confirm the highlighted uncertain days.</p>
          </div>

          {/* Header */}
          <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-4 grid grid-cols-2 gap-2 text-sm">
            <div>
              <p className="text-neutral-500 text-xs uppercase font-mono">Site</p>
              <p className="font-semibold">{extraction.header?.site_name?.value ?? '—'}</p>
            </div>
            <div>
              <p className="text-neutral-500 text-xs uppercase font-mono">Contractor</p>
              <p className="font-semibold">{extraction.header?.contractor_name?.value ?? '—'}</p>
            </div>
            <div>
              <p className="text-neutral-500 text-xs uppercase font-mono">Month / Year</p>
              <p className="font-semibold">
                {extraction.header?.month?.value ?? '—'} / {extraction.header?.year?.value ?? '—'}
              </p>
            </div>
            <div>
              <p className="text-neutral-500 text-xs uppercase font-mono">Worker</p>
              <p className="font-semibold">{targetRow?.name_latin ?? targetRow?.name_raw ?? 'Rakesh'}</p>
            </div>
          </div>

          {/* Day grid */}
          <div className="grid grid-cols-7 gap-1">
            {(targetRow?.cells ?? []).map((cell: any) => {
              const resolved = cellOverrides[cell.day];
              const isFlag = cell.needs_confirmation;
              return (
                <div
                  key={cell.day}
                  className={`aspect-square rounded flex flex-col items-center justify-center text-xs font-mono transition-colors
                    ${isFlag && !resolved ? 'bg-amber-500/30 border border-amber-400 text-amber-300' : ''}
                    ${resolved ? 'bg-green-500/20 border border-green-400 text-green-300' : ''}
                    ${!isFlag ? 'bg-neutral-800 text-neutral-400' : ''}
                  `}
                >
                  <span className="text-[9px] leading-none">{cell.day}</span>
                  <span className="font-bold leading-none">{resolved ?? cell.mark}</span>
                </div>
              );
            })}
          </div>

          {flaggedCells.length > 0 && (
            <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-3 text-sm text-amber-300">
              ⚠ {flaggedCells.length} uncertain cells — days {flaggedCells.map((c) => c.day).join(', ')}
            </div>
          )}

          {busy ? <Spinner msg={busyMsg} /> : (
            <div className="flex flex-col gap-3">
              {!allResolved && (
                <Btn onClick={handleConfirmAll} variant="secondary">
                  ✓ Confirm all flagged cells as Present
                </Btn>
              )}
              <Btn onClick={handleSaveRecord} disabled={!allResolved}>
                Save work record
              </Btn>
            </div>
          )}
        </div>
      )}

      {/* ── STEP: attest ────────────────────────────────────────────────── */}
      {step === 'attest' && (
        <div className="flex-1 flex flex-col gap-5 animate-in slide-in-from-right duration-300">
          <div className="text-center space-y-2">
            <h2 className="text-2xl font-bold">Employer Confirmation</h2>
            <p className="text-neutral-400 text-sm">Ask Sunil (the contractor) to confirm the work.</p>
          </div>

          {/* Record card */}
          {savedRecord && (
            <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-4 space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-neutral-500">Worker</span>
                <span className="font-semibold">Rakesh</span>
              </div>
              <div className="flex justify-between">
                <span className="text-neutral-500">Site</span>
                <span className="font-semibold">{savedRecord.site_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-neutral-500">Period</span>
                <span>{savedRecord.period_from} → {savedRecord.period_to}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-neutral-500">Days worked</span>
                <span className="font-bold text-green-400">{savedRecord.days_worked}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-neutral-500">Role</span>
                <span>{savedRecord.role ?? 'mason'}</span>
              </div>
            </div>
          )}

          {busy ? <Spinner msg={busyMsg} /> : (
            <div className="flex flex-col gap-3">
              {!attestToken && (
                <Btn onClick={handleCreateAttest} variant="secondary">
                  Create attestation request
                </Btn>
              )}
              {attestToken && !attestDone && (
                <Btn onClick={handleEmployerConfirm}>
                  ✓ Confirm: I worked with Rakesh
                </Btn>
              )}
              {attestDone && (
                <div className="flex flex-col gap-3">
                  <div className="bg-green-500/20 border border-green-400/40 text-green-300 rounded-xl p-4 text-center font-semibold">
                    ✅ Employer confirmed
                  </div>
                  <Btn onClick={handleIssuePassport}>Issue skill passport</Btn>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ── STEP: passport ──────────────────────────────────────────────── */}
      {step === 'passport' && passport && (
        <PassportStep passport={passport} workerId={workerId} onVerify={handleVerify} />
      )}
      {step === 'passport' && !passport && <Spinner msg="Issuing passport..." />}

      {/* ── STEP: verify ────────────────────────────────────────────────── */}
      {step === 'verify' && passport && (
        <VerifyStep passport={passport} />
      )}
    </div>
  );
}

// ─── PassportStep ─────────────────────────────────────────────────────────────

function PassportStep({
  passport,
  onVerify,
}: {
  passport: SignedPassport;
  workerId: string;
  onVerify: () => void;
}) {
  let payload: any = null;
  try { payload = JSON.parse(passport.payload_canonical); } catch { /* ignore */ }

  const trust = payload?.trust ?? {};
  const wageA = payload?.wage_bands?.A ?? null;
  const unskilled = wageA?.unskilled_daily_wage ?? 827;
  const skilled = wageA?.daily_wage ?? 1008;
  const delta = skilled - unskilled;
  const suggestedClass = trust?.suggested_class ?? payload?.worker?.trade ?? 'skilled';
  const verifiedDays = payload?.verified_days ?? '—';
  const verifiedSites = payload?.verified_sites ?? '—';

  return (
    <div className="flex-1 flex flex-col gap-5 animate-in slide-in-from-right duration-300">
      <div className="text-center space-y-1">
        <p className="text-neutral-500 font-mono text-xs uppercase tracking-widest">Skill Passport Issued</p>
        <h2 className="text-4xl font-bold">{payload?.worker?.display_name ?? 'Rakesh'}</h2>
        <p className="text-green-400 font-mono uppercase tracking-wider text-sm">
          {payload?.worker?.trade ?? 'mason'} · {suggestedClass}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-4 text-center">
          <p className="text-neutral-500 text-xs uppercase font-mono mb-1">Verified Days</p>
          <p className="text-2xl font-bold text-green-400">{verifiedDays}</p>
        </div>
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-4 text-center">
          <p className="text-neutral-500 text-xs uppercase font-mono mb-1">Verified Sites</p>
          <p className="text-2xl font-bold text-green-400">{verifiedSites}</p>
        </div>
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-4 text-center">
          <p className="text-neutral-500 text-xs uppercase font-mono mb-1">Trust Score</p>
          <p className="text-2xl font-bold text-green-400">{trust?.score ?? '—'}</p>
        </div>
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-4 text-center">
          <p className="text-neutral-500 text-xs uppercase font-mono mb-1">Trust Level</p>
          <p className="text-2xl font-bold text-green-400 capitalize">{trust?.level ?? '—'}</p>
        </div>
      </div>

      {/* Wage comparison */}
      <div className="bg-neutral-900 border border-green-400/20 rounded-2xl p-5">
        <p className="text-xs text-neutral-500 uppercase font-mono tracking-widest mb-3">Wage band A (Area)</p>
        <div className="flex items-center gap-4 justify-between">
          <div className="text-center">
            <p className="text-xs text-neutral-500 mb-1">Unskilled</p>
            <p className="text-2xl font-bold text-red-400">₹{unskilled}</p>
            <p className="text-xs text-neutral-500">/day</p>
          </div>
          <div className="flex flex-col items-center">
            <p className="text-2xl">→</p>
            <p className="text-xs text-green-400 font-mono">+₹{delta}</p>
          </div>
          <div className="text-center">
            <p className="text-xs text-neutral-500 mb-1">Skilled</p>
            <p className="text-2xl font-bold text-green-400">₹{skilled}</p>
            <p className="text-xs text-neutral-500">/day</p>
          </div>
        </div>
      </div>

      <Btn onClick={onVerify}>Verify passport signature</Btn>
    </div>
  );
}

// ─── VerifyStep ───────────────────────────────────────────────────────────────

function VerifyStep({ passport }: { passport: SignedPassport }) {
  const [status, setStatus] = useState<'valid' | 'tampered' | null>(null);
  const [tamperedPayload, setTamperedPayload] = useState<string | null>(null);

  const verify = useCallback(
    (payloadStr: string, sigB64: string): boolean => {
      try {
        const pinnedKey = import.meta.env.VITE_PRAMAN_PUBKEY as string | undefined;
        const pubKeyB64 = pinnedKey || passport.public_key_b64;
        const pubKey = decodeBase64(pubKeyB64);
        const sig = decodeBase64(sigB64);
        const msg = new TextEncoder().encode(payloadStr);
        return nacl.sign.detached.verify(msg, sig, pubKey);
      } catch {
        return false;
      }
    },
    [passport.public_key_b64]
  );

  const handleVerify = () => {
    const ok = verify(passport.payload_canonical, passport.signature_b64);
    setStatus(ok ? 'valid' : 'tampered');
    setTamperedPayload(null);
  };

  const handleTamper = () => {
    try {
      const parsed = JSON.parse(passport.payload_canonical);
      parsed.verified_days = (parsed.verified_days ?? 0) + 999;
      const tampered = JSON.stringify(parsed, Object.keys(parsed).sort());
      setTamperedPayload(tampered);
      const ok = verify(tampered, passport.signature_b64);
      setStatus(ok ? 'valid' : 'tampered');
    } catch {
      setStatus('tampered');
    }
  };

  const handleReset = () => {
    setStatus(null);
    setTamperedPayload(null);
  };

  const isVerified = status === 'valid' && !tamperedPayload;

  return (
    <div className="flex-1 flex flex-col gap-5 animate-in slide-in-from-right duration-300">
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-bold">Cryptographic Verification</h2>
        <p className="text-neutral-400 text-sm">Ed25519 signature — verified in your browser.</p>
      </div>

      {status === null && (
        <Btn onClick={handleVerify}>Verify passport</Btn>
      )}

      {status === 'valid' && !tamperedPayload && (
        <div className="bg-green-500/15 border-2 border-green-400 rounded-2xl p-6 text-center space-y-2">
          <p className="text-5xl">✅</p>
          <p className="text-2xl font-bold text-green-400">Signature valid</p>
          <p className="text-xs text-neutral-400 font-mono">Ed25519 · key {passport.key_id}</p>
        </div>
      )}

      {status === 'tampered' && (
        <div className="bg-red-500/15 border-2 border-red-500 rounded-2xl p-6 text-center space-y-2">
          <p className="text-5xl">🔴</p>
          <p className="text-2xl font-bold text-red-400">Signature invalid — payload changed</p>
          <p className="text-xs text-neutral-400 font-mono">
            verified_days was modified by +999
          </p>
        </div>
      )}

      <div className="flex flex-col gap-3">
        {isVerified && (
          <Btn onClick={handleTamper} variant="secondary">
            Simulate tampering
          </Btn>
        )}
        {status !== null && (
          <Btn onClick={handleReset} variant="ghost">
            Reset verification
          </Btn>
        )}
      </div>

      <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-4">
        <p className="text-xs text-neutral-500 uppercase font-mono tracking-widest mb-2">
          {tamperedPayload ? 'Tampered payload (first 120 chars)' : 'Signed payload (first 120 chars)'}
        </p>
        <p className="font-mono text-xs text-neutral-400 break-all">
          {(tamperedPayload ?? passport.payload_canonical).slice(0, 120)}…
        </p>
      </div>
    </div>
  );
}

// ─── Route wrapper ────────────────────────────────────────────────────────────

export function DemoFlow() {
  return (
    <Routes>
      <Route path="/*" element={<MainFlow />} />
    </Routes>
  );
}
