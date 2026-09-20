/**
 * DemoFlow.tsx — Praman hackathon golden flow.
 *
 * Steps (no step order change, no new API endpoints):
 *  1. landing   — "Rakesh · NO PROOF · ₹827/day"
 *  2. voice     — mic (optional) + typed Hindi fallback → structured claim card
 *  3. register  — upload or demo replay → AI extraction
 *  4. cells     — amber uncertain cells → worker confirmation → save record
 *  5. attest    — employer facts-only confirmation
 *  6. passport  — deterministic trust score + wage uplift ₹827 → ₹1,008
 *  7. verify    — Ed25519 browser verification → tamper test
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

// ─── constants ────────────────────────────────────────────────────────────────

const STEPS = ['landing', 'voice', 'register', 'cells', 'attest', 'passport', 'verify'] as const;
type Step = typeof STEPS[number];

const STEP_META: Record<Exclude<Step, 'landing'>, { n: number; eyebrow: string }> = {
  voice:    { n: 1, eyebrow: 'WORKER STORY' },
  register: { n: 2, eyebrow: 'ATTENDANCE EVIDENCE' },
  cells:    { n: 3, eyebrow: 'WORKER CONFIRMATION' },
  attest:   { n: 4, eyebrow: 'EMPLOYER ATTESTATION' },
  passport: { n: 5, eyebrow: 'SKILL PASSPORT' },
  verify:   { n: 6, eyebrow: 'CRYPTOGRAPHIC PROOF' },
};

const HINDI_TEXT =
  'मेरा नाम राकेश है। मैं राजमिस्त्री का काम करता हूँ। मुझे दस साल का अनुभव है। मैंने मोहाली, नोएडा और गुरुग्राम में काम किया है।';

// ─── tiny shared primitives ───────────────────────────────────────────────────

/** Eyebrow label */
function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[10px] font-mono uppercase tracking-[0.18em] text-neutral-500">
      {children}
    </p>
  );
}

/** Muted caption below a button */
function Caption({ children }: { children: React.ReactNode }) {
  return <p className="text-[11px] text-neutral-600 text-center leading-snug">{children}</p>;
}

/** Chip badge */
function Chip({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-block bg-green-400/10 border border-green-400/30 text-green-300 text-xs font-mono rounded-full px-3 py-1">
      {children}
    </span>
  );
}

/** Honesty badge — always visible */
function DemoBadge() {
  return (
    <div className="group relative inline-flex items-center gap-1.5 bg-amber-500/10 border border-amber-500/30 rounded-full px-3 py-1 cursor-default select-none">
      <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
      <span className="text-[10px] font-mono uppercase tracking-widest text-amber-400">
        Hackathon Demo Mode
      </span>
      {/* tooltip on hover */}
      <div className="pointer-events-none absolute left-1/2 -translate-x-1/2 top-full mt-2 w-64 bg-neutral-900 border border-amber-500/30 rounded-xl p-3 text-[11px] text-neutral-400 leading-snug z-50 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
        Live workflow; register extraction replayed for reliability when external free-tier vision APIs are unavailable.
      </div>
    </div>
  );
}

/** Step progress bar */
function StepBar({ step, onReset }: { step: Step; onReset: () => void }) {
  if (step === 'landing') return null;
  const visibleSteps = STEPS.slice(1);
  const meta = STEP_META[step as Exclude<Step, 'landing'>];
  const visIdx = visibleSteps.indexOf(step);
  return (
    <div className="flex flex-col gap-2 mb-5 w-full">
      <div className="flex items-center justify-between">
        <button
          onClick={onReset}
          className="text-[11px] text-neutral-600 font-mono uppercase tracking-widest hover:text-neutral-300 transition-colors"
        >
          ← Reset
        </button>
        <DemoBadge />
        <span className="text-[11px] text-neutral-600 font-mono uppercase tracking-widest">
          {meta.n} / {visibleSteps.length}
        </span>
      </div>
      <div className="flex gap-1 w-full">
        {visibleSteps.map((s, i) => (
          <div
            key={s}
            className={`h-0.5 flex-1 rounded-full transition-colors ${
              i <= visIdx ? 'bg-green-400' : 'bg-neutral-800'
            }`}
          />
        ))}
      </div>
      <Eyebrow>{meta.eyebrow}</Eyebrow>
    </div>
  );
}

/** Error banner */
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

/** Spinner */
function Spinner({ msg }: { msg: string }) {
  return (
    <div className="flex flex-col items-center gap-4 py-10">
      <div className="w-8 h-8 border-2 border-green-400 border-t-transparent rounded-full animate-spin" />
      <p className="text-green-400 font-mono text-[11px] uppercase tracking-widest text-center">{msg}</p>
    </div>
  );
}

/** Primary/secondary/ghost button */
function Btn({
  onClick, children, disabled, variant = 'primary', className = '',
}: {
  onClick?: () => void;
  children: React.ReactNode;
  disabled?: boolean;
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger-outline';
  className?: string;
}) {
  const base =
    'w-full py-4 rounded-2xl font-bold text-base transition-all duration-200 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed';
  const variants: Record<string, string> = {
    primary:
      'bg-green-400 text-black shadow-[0_0_30px_rgba(74,222,128,0.2)] hover:shadow-[0_0_44px_rgba(74,222,128,0.4)] hover:scale-[1.02]',
    secondary:
      'bg-neutral-900 text-white border border-neutral-700 hover:border-neutral-500',
    ghost: 'text-neutral-500 underline text-sm py-2',
    'danger-outline':
      'bg-transparent text-red-400 border-2 border-red-500/70 hover:bg-red-500/10',
  };
  return (
    <button onClick={onClick} disabled={disabled} className={`${base} ${variants[variant]} ${className}`}>
      {children}
    </button>
  );
}

/** Info/context explanation card */
function InfoCard({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-neutral-900/60 border border-neutral-800 rounded-xl p-4 text-[12px] text-neutral-500 leading-snug">
      {children}
    </div>
  );
}

// ─── Main flow component ──────────────────────────────────────────────────────

function MainFlow() {
  const [step, setStep] = useState<Step>('landing');
  const [workerId, setWorkerId] = useState('');
  const [busy, setBusy] = useState(false);
  const [busyMsg, setBusyMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  // step data
  const [voiceClaim, setVoiceClaim] = useState<any>(null);
  const [micMsg, setMicMsg] = useState('');
  const [extraction, setExtraction] = useState<any>(null);
  const [flaggedCells, setFlaggedCells] = useState<any[]>([]);
  const [cellOverrides, setCellOverrides] = useState<Record<number, 'P'>>({});
  const [cellsConfirmed, setCellsConfirmed] = useState(false);
  const [savedRecord, setSavedRecord] = useState<any>(null);
  const [attestToken, setAttestToken] = useState('');
  const [attestDone, setAttestDone] = useState(false);
  const [passport, setPassport] = useState<SignedPassport | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // ── helpers ────────────────────────────────────────────────────────────────

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
    setMicMsg('');
    setExtraction(null);
    setFlaggedCells([]);
    setCellOverrides({});
    setCellsConfirmed(false);
    setSavedRecord(null);
    setAttestToken('');
    setAttestDone(false);
    setPassport(null);
    setErrorMsg('');
  }, []);

  // ── STEP 1: Landing ────────────────────────────────────────────────────────

  const handleStart = () =>
    wrap(async () => {
      const session = await createSession();
      setWorkerId(session.worker_id);
      await seedDemo();
      setStep('voice');
    }, 'Starting session...');

  // ── STEP 2: Voice ──────────────────────────────────────────────────────────

  const handleMicClick = () => {
    setMicMsg('Microphone demo is optional — use the typed fallback below.');
  };

  const handleTypedStory = () =>
    wrap(async () => {
      const { job_id } = await submitVoice(workerId, null, HINDI_TEXT);
      const result = await pollJob(job_id, setBusyMsg);
      setVoiceClaim(
        result ?? {
          _fallback: true,
          name: 'Rakesh',
          trade: 'mason',
          years_experience: 10,
          sites: [
            { site_name: 'Mohali Sector 82' },
            { site_name: 'Noida' },
            { site_name: 'Gurugram' },
          ],
          transcript: HINDI_TEXT,
          language: 'hi',
        }
      );
    }, 'Extracting structured claim...');

  // ── STEP 3: Register ───────────────────────────────────────────────────────

  const processRegisterBlob = async (blob: Blob) => {
    const { job_id } = await submitRegister(workerId, blob, 'Rakesh');
    const result = await pollJob(job_id, setBusyMsg);
    setExtraction(result);
    const targetRow = result?.rows?.find((r: any) => r.is_target) ?? result?.rows?.[0];
    const flagged = (targetRow?.cells ?? []).filter((c: any) => c.needs_confirmation);
    setFlaggedCells(flagged);
    setCellOverrides({});
    setCellsConfirmed(false);
    setStep('cells');
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    wrap(() => processRegisterBlob(file), 'Reading register...');
  };

  const handleUseDemoRegister = () => {
    const canvas = document.createElement('canvas');
    canvas.width = 1;
    canvas.height = 1;
    canvas.toBlob((blob) => {
      if (blob) wrap(() => processRegisterBlob(blob), 'Reading register...');
    }, 'image/jpeg');
  };

  // ── STEP 4: Cells ──────────────────────────────────────────────────────────

  const allResolved =
    flaggedCells.length === 0 || flaggedCells.every((c) => cellOverrides[c.day] === 'P');

  const handleConfirmAll = () => {
    const overrides: Record<number, 'P'> = {};
    flaggedCells.forEach((c) => { overrides[c.day] = 'P'; });
    setCellOverrides(overrides);
    setCellsConfirmed(true);
  };

  const handleSaveRecord = () =>
    wrap(async () => {
      const targetRow =
        extraction?.rows?.find((r: any) => r.is_target) ?? extraction?.rows?.[0];
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

  // ── STEP 5: Attestation ────────────────────────────────────────────────────

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

  // ── STEP 6: Passport ───────────────────────────────────────────────────────

  const handleIssuePassport = () =>
    wrap(async () => {
      const p = await issuePassport(workerId);
      setPassport(p);
      setStep('passport');
    }, 'Issuing passport...');

  // ── STEP 7: Verify ─────────────────────────────────────────────────────────

  const handleVerify = () => setStep('verify');

  // ── derived ────────────────────────────────────────────────────────────────

  const targetRow =
    extraction?.rows?.find((r: any) => r.is_target) ?? extraction?.rows?.[0];

  // ── JSX ───────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-neutral-950 text-white font-sans p-5 max-w-md mx-auto flex flex-col">
      <StepBar step={step} onReset={handleReset} />
      <ErrorBanner msg={errorMsg} onDismiss={() => setErrorMsg('')} />

      {/* ── STEP: landing ─────────────────────────────────────────────────── */}
      {step === 'landing' && (
        <div className="flex-1 flex flex-col items-center justify-center gap-10 animate-in fade-in duration-500">
          <div className="text-center space-y-3">
            <Eyebrow>Worker profile — before verification</Eyebrow>
            <h1 className="text-6xl font-bold tracking-tight">Rakesh</h1>
            <p className="text-neutral-500 font-mono uppercase tracking-widest text-sm">
              No proof — Unskilled
            </p>
            <div className="mt-4 inline-flex items-baseline gap-1 px-5 py-2 bg-neutral-900 rounded-full border border-neutral-800">
              <span className="text-2xl font-bold text-red-400">₹827</span>
              <span className="text-neutral-500 text-sm">/day</span>
            </div>
            <p className="text-xs text-neutral-600 max-w-[260px] mx-auto leading-relaxed">
              Rakesh is a mason with 10 years of experience but no verifiable proof.
              This demo builds that proof in 6 steps.
            </p>
          </div>

          <div className="w-full max-w-[300px] flex flex-col gap-3">
            {busy ? (
              <Spinner msg={busyMsg} />
            ) : (
              <>
                <Btn onClick={handleStart}>Start verification</Btn>
                <Caption>Creates a worker session and seeds 4 historical records.</Caption>
                <div className="mt-2 flex justify-center">
                  <DemoBadge />
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* ── STEP: voice ───────────────────────────────────────────────────── */}
      {step === 'voice' && (
        <div className="flex-1 flex flex-col gap-5 animate-in slide-in-from-right duration-300">
          <div className="space-y-1">
            <h2 className="text-2xl font-bold">Worker story</h2>
            <p className="text-neutral-400 text-sm">
              Hindi voice note → ASR transcription → structured claim extraction.
            </p>
          </div>

          {/* Mic button — optional, non-blocking */}
          {!voiceClaim && (
            <div className="flex flex-col items-center gap-3">
              <button
                onClick={handleMicClick}
                className="w-24 h-24 rounded-full border-2 border-neutral-700 bg-neutral-900 flex flex-col items-center justify-center gap-1 hover:border-neutral-500 transition-colors"
              >
                <span className="text-3xl">🎙</span>
                <span className="text-[10px] font-mono uppercase tracking-widest text-neutral-500">Mic</span>
              </button>
              <p className="text-xs text-neutral-500 text-center">
                Production path: record a 15-second Hindi/Hinglish work-history note.
              </p>
              {micMsg && (
                <p className="text-xs text-amber-400 text-center bg-amber-500/10 border border-amber-500/20 rounded-lg px-4 py-2">
                  {micMsg}
                </p>
              )}
            </div>
          )}

          {/* Typed fallback — always shown before claim extracted */}
          {!voiceClaim && (
            <>
              <div className="relative">
                <div className="absolute -top-2.5 left-3 bg-neutral-950 px-1">
                  <Eyebrow>Demo fallback — typed Hindi story</Eyebrow>
                </div>
                <div className="bg-neutral-900 border border-neutral-700 rounded-xl p-4 pt-5">
                  <p className="text-sm leading-relaxed text-neutral-200">{HINDI_TEXT}</p>
                </div>
              </div>

              {busy ? (
                <Spinner msg={busyMsg} />
              ) : (
                <div className="flex flex-col gap-2">
                  <Btn onClick={handleTypedStory}>Use typed story for demo</Btn>
                  <Caption>
                    Demo input processed into the same structured claim format as live voice.
                  </Caption>
                </div>
              )}
            </>
          )}

          {/* Claim card — shown after extraction */}
          {voiceClaim && !busy && (
            <div className="flex flex-col gap-4 animate-in fade-in duration-300">
              <div className="bg-green-400/5 border border-green-400/30 rounded-2xl p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <Eyebrow>Structured claim extracted</Eyebrow>
                  <span className="text-[10px] font-mono text-green-400 uppercase tracking-widest">✓ ASR + extraction</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Chip>Rakesh</Chip>
                  <Chip>Mason</Chip>
                  <Chip>10 years exp.</Chip>
                  <Chip>Mohali</Chip>
                  <Chip>Noida</Chip>
                  <Chip>Gurugram</Chip>
                </div>
                <p className="text-[11px] text-neutral-500 leading-snug">
                  Demo input processed into the same structured claim format. In production, a Whisper ASR call would transcribe the audio first.
                </p>
              </div>

              <Btn onClick={() => setStep('register')}>Continue to register evidence</Btn>
              <Caption>Next: AI reads the hazri attendance register.</Caption>
            </div>
          )}
        </div>
      )}

      {/* ── STEP: register ────────────────────────────────────────────────── */}
      {step === 'register' && (
        <div className="flex-1 flex flex-col gap-5 animate-in slide-in-from-right duration-300">
          <div className="space-y-1">
            <h2 className="text-xl font-bold leading-snug">
              AI reads the hazri register — and asks when uncertain
            </h2>
            <p className="text-neutral-400 text-sm">
              Two independent readings agree on clear marks. Ambiguous marks are routed to the worker, never silently guessed.
            </p>
          </div>

          <InfoCard>
            <span className="text-amber-400 font-mono uppercase tracking-widest text-[10px]">
              Demo register extraction replay
            </span>
            <br />
            Production: multi-reading vision extraction. Demo: validated replay because free-tier vision API quota is unreliable.
          </InfoCard>

          {busy ? (
            <Spinner msg={busyMsg} />
          ) : (
            <div className="flex flex-col gap-3">
              <Btn onClick={handleUseDemoRegister}>Use demo register</Btn>
              <Caption>Triggers the extraction replay from validated fixture data.</Caption>
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
              <Caption>Any image triggers the mock extraction — result is always from the validated fixture.</Caption>
            </div>
          )}
        </div>
      )}

      {/* ── STEP: cells ───────────────────────────────────────────────────── */}
      {step === 'cells' && extraction && (
        <div className="flex-1 flex flex-col gap-4 animate-in slide-in-from-right duration-300">
          <div className="space-y-1">
            <h2 className="text-xl font-bold leading-snug">Review attendance</h2>
            <p className="text-neutral-400 text-sm">
              Confirm the two marks where independent readings disagreed.
            </p>
          </div>

          {/* Header card */}
          <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-3 grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
            {[
              ['Site', extraction.header?.site_name?.value],
              ['Contractor', extraction.header?.contractor_name?.value],
              ['Month / Year', `${extraction.header?.month?.value} / ${extraction.header?.year?.value}`],
              ['Worker', targetRow?.name_latin ?? targetRow?.name_raw ?? 'Rakesh'],
            ].map(([label, val]) => (
              <div key={label as string}>
                <p className="text-neutral-600 text-[10px] uppercase font-mono">{label}</p>
                <p className="font-semibold text-sm truncate">{val ?? '—'}</p>
              </div>
            ))}
          </div>

          {/* Day grid */}
          <div className="grid grid-cols-7 gap-1">
            {(targetRow?.cells ?? []).map((cell: any) => {
              const resolved = cellOverrides[cell.day];
              const isFlag = cell.needs_confirmation;
              return (
                <div
                  key={cell.day}
                  title={isFlag ? `Day ${cell.day}: Needs Rakesh's confirmation` : `Day ${cell.day}: Auto-accepted`}
                  className={`aspect-square rounded flex flex-col items-center justify-center transition-colors
                    ${isFlag && !resolved ? 'bg-amber-500/25 border border-amber-400 text-amber-300' : ''}
                    ${resolved ? 'bg-green-500/20 border border-green-400/50 text-green-300' : ''}
                    ${!isFlag ? 'bg-neutral-900 border border-neutral-800 text-neutral-500' : ''}
                  `}
                >
                  <span className="text-[8px] leading-none">{cell.day}</span>
                  <span className="text-[11px] font-bold leading-none">{resolved ?? cell.mark}</span>
                </div>
              );
            })}
          </div>

          {/* Uncertainty explanation card */}
          {!cellsConfirmed && flaggedCells.length > 0 && (
            <div className="bg-amber-500/8 border border-amber-500/25 rounded-xl p-3 space-y-1">
              <p className="text-amber-300 text-xs font-semibold">
                ⚠ {flaggedCells.length} cells need Rakesh's confirmation — days {flaggedCells.map((c) => c.day).join(', ')}
              </p>
              <p className="text-[11px] text-neutral-500">
                Why these cells? Independent readings disagreed. Praman abstains instead of silently guessing.
              </p>
            </div>
          )}

          {cellsConfirmed && (
            <div className="bg-green-500/10 border border-green-400/25 rounded-xl p-3 text-xs text-green-300">
              ✓ Worker-confirmed — record ready to save
            </div>
          )}

          {busy ? (
            <Spinner msg={busyMsg} />
          ) : (
            <div className="flex flex-col gap-2">
              {!cellsConfirmed && (
                <>
                  <Btn onClick={handleConfirmAll} variant="secondary">
                    Confirm 2 uncertain marks
                  </Btn>
                  <Caption>Sets both ambiguous marks to Present on Rakesh's behalf.</Caption>
                </>
              )}
              <Btn onClick={handleSaveRecord} disabled={!allResolved}>
                Save work record
              </Btn>
              <Caption>Posts the confirmed extraction to the backend and builds the WorkRecord.</Caption>
            </div>
          )}
        </div>
      )}

      {/* ── STEP: attest ──────────────────────────────────────────────────── */}
      {step === 'attest' && (
        <div className="flex-1 flex flex-col gap-4 animate-in slide-in-from-right duration-300">
          <div className="space-y-1">
            <h2 className="text-xl font-bold">Employer attestation</h2>
            <p className="text-neutral-400 text-sm">
              Sunil confirms facts only — no ratings, no free-text blacklist.
            </p>
          </div>

          {/* Facts card */}
          {savedRecord && (
            <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-4 space-y-2 text-sm">
              <Eyebrow>Facts card — shown to employer</Eyebrow>
              {[
                ['Worker', 'Rakesh'],
                ['Site', savedRecord.site_name],
                ['Period', `${savedRecord.period_from} → ${savedRecord.period_to}`],
                ['Days worked', savedRecord.days_worked],
                ['Role', savedRecord.role ?? 'mason'],
              ].map(([label, val]) => (
                <div key={label as string} className="flex justify-between">
                  <span className="text-neutral-500">{label}</span>
                  <span className={`font-semibold ${label === 'Days worked' ? 'text-green-400' : ''}`}>{val}</span>
                </div>
              ))}
              <p className="text-[11px] text-neutral-600 pt-1 border-t border-neutral-800">
                This attestation confirms dates, days and role. It does not create a rating.
              </p>
            </div>
          )}

          {busy ? (
            <Spinner msg={busyMsg} />
          ) : (
            <div className="flex flex-col gap-2">
              {!attestToken && (
                <>
                  <Btn onClick={handleCreateAttest} variant="secondary">
                    Create attestation request
                  </Btn>
                  <Caption>Generates a token for the employer to respond to.</Caption>
                </>
              )}
              {attestToken && !attestDone && (
                <>
                  <Btn onClick={handleEmployerConfirm}>
                    ✓ Confirm: I worked with Rakesh
                  </Btn>
                  <Caption>Sunil confirms as employer — facts only, no rating.</Caption>
                </>
              )}
              {attestDone && (
                <div className="flex flex-col gap-3 animate-in fade-in duration-300">
                  <div className="bg-green-500/15 border border-green-400/40 text-green-300 rounded-xl p-4 text-center font-semibold text-sm">
                    ✅ Employer-attested evidence added
                  </div>
                  <Btn onClick={handleIssuePassport}>Issue skill passport</Btn>
                  <Caption>Runs the deterministic rules engine and signs the passport payload.</Caption>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ── STEP: passport ────────────────────────────────────────────────── */}
      {step === 'passport' && passport && (
        <PassportStep passport={passport} onVerify={handleVerify} />
      )}
      {step === 'passport' && !passport && <Spinner msg="Issuing passport..." />}

      {/* ── STEP: verify ──────────────────────────────────────────────────── */}
      {step === 'verify' && passport && <VerifyStep passport={passport} />}
    </div>
  );
}

// ─── PassportStep ─────────────────────────────────────────────────────────────

function PassportStep({
  passport,
  onVerify,
}: {
  passport: SignedPassport;
  onVerify: () => void;
}) {
  let payload: any = null;
  try { payload = JSON.parse(passport.payload_canonical); } catch { /* ignore */ }

  const trust = payload?.trust ?? {};
  const wageA = payload?.wage_bands?.A ?? null;
  const unskilled = wageA?.unskilled_daily_wage ?? 827;
  const skilled = wageA?.daily_wage ?? 1008;
  const delta = Math.round(skilled - unskilled);
  const suggestedClass: string = trust?.suggested_class ?? 'skilled';
  const verifiedDays: number | string = payload?.verified_days ?? '—';
  const verifiedSites: number | string = payload?.verified_sites ?? '—';

  return (
    <div className="flex-1 flex flex-col gap-5 animate-in slide-in-from-right duration-300">
      <div className="space-y-1">
        <Eyebrow>Skill passport issued</Eyebrow>
        <h2 className="text-4xl font-bold">{payload?.worker?.display_name ?? 'Rakesh'}</h2>
        <p className="text-green-400 font-mono uppercase tracking-wider text-sm">
          {payload?.worker?.trade ?? 'mason'} · {suggestedClass}
        </p>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-4 text-center">
          <Eyebrow>Verified Days</Eyebrow>
          <p className="text-2xl font-bold text-green-400 mt-1">{verifiedDays}</p>
          <p className="text-[10px] text-neutral-600 mt-1">4 seeded + 1 live</p>
        </div>
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-4 text-center">
          <Eyebrow>Verified Sites</Eyebrow>
          <p className="text-2xl font-bold text-green-400 mt-1">{verifiedSites}</p>
        </div>
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-4 text-center">
          <Eyebrow>Trust Score</Eyebrow>
          <p className="text-2xl font-bold text-green-400 mt-1">{trust?.score ?? '—'}</p>
          <p className="text-[10px] text-neutral-600 mt-1">Deterministic</p>
        </div>
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-4 text-center">
          <Eyebrow>Trust Level</Eyebrow>
          <p className="text-2xl font-bold text-green-400 mt-1 capitalize">{trust?.level ?? '—'}</p>
        </div>
      </div>

      <InfoCard>
        Rules engine combines verified days, employer attestation, consistency, and claim alignment.{' '}
        <span className="text-neutral-400 font-mono text-[10px]">DETERMINISTIC SCORE — NOT AN LLM JUDGMENT</span>
      </InfoCard>

      {/* Wage comparison — visually prominent */}
      <div className="bg-neutral-900 border border-green-400/20 rounded-2xl p-5 space-y-3">
        <div className="flex items-center justify-between">
          <Eyebrow>Wage band A — area rate</Eyebrow>
          <span className="text-[10px] font-mono text-green-400 uppercase tracking-widest">Evidence-based</span>
        </div>
        <div className="flex items-center gap-3 justify-between">
          <div className="text-center flex-1">
            <p className="text-[11px] text-neutral-500 mb-1">Without proof</p>
            <p className="text-3xl font-bold text-red-400">₹{unskilled}</p>
            <p className="text-[11px] text-neutral-600">/day</p>
          </div>
          <div className="flex flex-col items-center gap-1">
            <div className="text-2xl text-neutral-400">→</div>
            <div className="bg-green-400/15 border border-green-400/30 rounded-full px-3 py-1">
              <p className="text-[12px] font-bold text-green-400">+₹{delta}/day</p>
            </div>
          </div>
          <div className="text-center flex-1">
            <p className="text-[11px] text-neutral-500 mb-1">With proof</p>
            <p className="text-3xl font-bold text-green-400">₹{skilled}</p>
            <p className="text-[11px] text-neutral-600">/day</p>
          </div>
        </div>
        <p className="text-[11px] text-neutral-600 text-center">
          Evidence-based suggestion; final wage classification remains subject to employer and labour policy.
        </p>
      </div>

      <Btn onClick={onVerify}>Verify passport signature</Btn>
      <Caption>Opens Ed25519 browser-side cryptographic verification — no database lookup required.</Caption>
    </div>
  );
}

// ─── VerifyStep ───────────────────────────────────────────────────────────────

type VerificationState = 'neutral' | 'valid' | 'tampered';

function VerifyStep({ passport }: { passport: SignedPassport }) {
  const [verificationState, setVerificationState] = useState<VerificationState>('neutral');
  const [tamperedPayload, setTamperedPayload] = useState<string | null>(null);

  const originalPayloadCanonical = passport.payload_canonical;
  const originalSignatureB64 = passport.signature_b64;
  const pinnedPublicKey = (import.meta.env.VITE_PRAMAN_PUBKEY as string | undefined) || passport.public_key_b64;

  const verifySignature = useCallback(
    (payloadStr: string, sigB64: string, pubKeyB64: string): boolean => {
      try {
        const pubKey = decodeBase64(pubKeyB64);
        const sig = decodeBase64(sigB64);
        const msg = new TextEncoder().encode(payloadStr);
        return nacl.sign.detached.verify(msg, sig, pubKey);
      } catch {
        return false;
      }
    },
    []
  );

  const verifyOriginalPassport = () => {
    const ok = verifySignature(
      originalPayloadCanonical,
      originalSignatureB64,
      pinnedPublicKey
    );
    // If it fails unexpectedly, it remains neutral (could show an error, but as requested we set to valid or neutral).
    setVerificationState(ok ? 'valid' : 'neutral');
    setTamperedPayload(null);
  };

  const simulateTampering = () => {
    if (verificationState !== 'valid') return;

    try {
      const parsed = JSON.parse(originalPayloadCanonical);
      parsed.verified_days = Number(parsed.verified_days || 0) + 999;
      const tamperedCanonical = JSON.stringify(parsed, Object.keys(parsed).sort());
      
      const ok = verifySignature(
        tamperedCanonical,
        originalSignatureB64,
        pinnedPublicKey
      );
      
      setTamperedPayload(tamperedCanonical);
      setVerificationState(ok ? 'valid' : 'tampered');
    } catch {
      setVerificationState('tampered');
    }
  };

  const resetVerification = () => {
    setVerificationState('neutral');
    setTamperedPayload(null);
  };

  const displayPayload = tamperedPayload ?? originalPayloadCanonical;

  return (
    <div className="flex-1 flex flex-col gap-5 animate-in slide-in-from-right duration-300">
      <div className="space-y-1">
        <Eyebrow>Cryptographic verification</Eyebrow>
        <h2 className="text-2xl font-bold">
          {verificationState === 'neutral' && 'Ed25519 browser verification'}
          {verificationState === 'valid' && 'Signature valid ✓'}
          {verificationState === 'tampered' && 'Signature invalid ✕'}
        </h2>
        <p className="text-neutral-400 text-sm">
          Ed25519 signature — verified independently in your browser. No database lookup required.
        </p>
      </div>

      {/* ── Pre-verification: neutral ── */}
      {verificationState === 'neutral' && (
        <>
          <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-4 space-y-2">
            <Eyebrow>Signed payload — first 120 chars</Eyebrow>
            <p className="font-mono text-xs text-neutral-500 break-all leading-relaxed">
              {originalPayloadCanonical.slice(0, 120)}…
            </p>
          </div>
          <Btn onClick={verifyOriginalPassport}>Verify passport</Btn>
          <Caption>
            Decodes the Ed25519 signature and pinned public key in this browser tab — no server call.
          </Caption>
        </>
      )}

      {/* ── Valid state ── */}
      {verificationState === 'valid' && (
        <>
          <div className="bg-green-500/10 border-2 border-green-400 rounded-2xl p-6 text-center space-y-2 animate-in fade-in duration-300">
            <p className="text-5xl">✅</p>
            <p className="text-2xl font-bold text-green-400">✓ Signature valid</p>
            <p className="text-sm text-neutral-300">Payload is exactly the one issued by Praman.</p>
            <p className="text-xs text-neutral-500">
              Verified locally in this browser — no database lookup required.
            </p>
            <p className="text-[10px] font-mono text-neutral-600">Ed25519 · key {passport.key_id}</p>
          </div>

          <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-4 space-y-1">
            <Eyebrow>Signed payload — first 120 chars</Eyebrow>
            <p className="font-mono text-xs text-neutral-500 break-all leading-relaxed">
              {originalPayloadCanonical.slice(0, 120)}…
            </p>
          </div>

          <Btn onClick={simulateTampering} variant="danger-outline">
            Simulate tampering (+999 days)
          </Btn>
          <Caption>Modifies verified_days in a local copy, then re-verifies with the original signature.</Caption>
        </>
      )}

      {/* ── Tampered / Invalid state ── */}
      {verificationState === 'tampered' && (
        <>
          <div className="bg-red-500/10 border-2 border-red-500 rounded-2xl p-6 text-center space-y-2 animate-in fade-in duration-300">
            <p className="text-5xl">🔴</p>
            <p className="text-2xl font-bold text-red-400">✕ Signature invalid — payload changed</p>
            <p className="text-sm text-neutral-300">verified_days was modified by +999.</p>
            <p className="text-xs text-neutral-500">
              Any change to the payload — however small — makes the signature fail.
            </p>
          </div>

          <div className="bg-neutral-900 border border-red-500/20 rounded-xl p-4 space-y-1">
            <Eyebrow>Tampered payload — first 120 chars</Eyebrow>
            <p className="font-mono text-xs text-red-400/70 break-all leading-relaxed">
              {displayPayload.slice(0, 120)}…
            </p>
          </div>
        </>
      )}

      {/* Reset — always shown after any verification */}
      {verificationState !== 'neutral' && (
        <>
          <Btn onClick={resetVerification} variant="ghost">
            Reset verification
          </Btn>
          <Caption>Returns to neutral pre-verification state.</Caption>
        </>
      )}
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
