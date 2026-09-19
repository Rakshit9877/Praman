import React, { useState, useRef, useEffect } from 'react';
import { Routes, Route, useParams } from 'react-router-dom';
import { QRCodeSVG } from 'qrcode.react';
import { createSession, submitVoice, submitRegister, getJob, issuePassport } from '../../lib/api';
import { PassportView } from '../worker/PassportView';

// Stub of translations for this component
const t = (key: string) => {
  const strings: Record<string, string> = {
    "landing.title": "Rakesh",
    "landing.subtitle": "No proof — Unskilled",
    "landing.wage": "₹827/day",
    "landing.start": "Start verification",
    "voice.title": "Tell us about your work",
    "voice.instruction": "Press the mic and speak in Hindi.",
    "voice.recording": "Recording...",
    "voice.processing": "Processing voice...",
    "voice.next": "Next Step",
    "register.title": "Upload Hazri Register",
    "register.instruction": "Take a photo of your attendance page.",
    "register.capture": "Open Camera",
    "register.processing": "Reading register...",
    "register.next": "Next Step",
    "attest.title": "Employer Attestation",
    "attest.instruction": "Show this QR code to your Thekedar to confirm.",
    "attest.waiting": "Waiting for confirmation...",
    "attest.confirmed": "Attestation confirmed!",
    "passport.title": "Generating Passport",
    "passport.processing": "Issuing secure passport...",
    "passport.success": "Passport Issued",
    "errors.network": "Network error occurred.",
    "errors.retry": "Try Again"
  };
  return strings[key] || key;
};

// Polling helper
async function pollJob(jobId: string, setProgress: (msg: string) => void): Promise<any> {
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
          setProgress(`Stage: ${job.stage} (${Math.round(job.progress * 100)}%)`);
        }
      } catch (err) {
        clearInterval(interval);
        reject(err);
      }
    }, 700);
  });
}

function MainFlow() {
  const [step, setStep] = useState<'landing' | 'voice' | 'register' | 'attest' | 'passport'>('landing');
  const [workerId, setWorkerId] = useState<string>('');
  const [recording, setRecording] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [passportData, setPassportData] = useState<any>(null);
  const [attestToken, setAttestToken] = useState('');

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<BlobPart[]>([]);

  // 1. Landing
  const handleStart = async () => {
    try {
      setErrorMsg('');
      const session = await createSession();
      setWorkerId(session.worker_id);
      
      // Also seed demo data so Rakesh has 4 seeded sites
      await fetch('/api/demo/seed', { method: 'POST' });
      
      setStep('voice');
    } catch (err) {
      setErrorMsg(t('errors.network'));
    }
  };

  // 2. Voice
  const handleVoiceToggle = async () => {
    if (!recording) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorderRef.current = mediaRecorder;
        audioChunksRef.current = [];

        mediaRecorder.ondataavailable = (e) => {
          if (e.data.size > 0) audioChunksRef.current.push(e.data);
        };

        mediaRecorder.onstop = async () => {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          setStatusMsg(t('voice.processing'));
          try {
            const { job_id } = await submitVoice(workerId, audioBlob);
            await pollJob(job_id, setStatusMsg);
            setStatusMsg('');
            setStep('register');
          } catch (err) {
            setErrorMsg(t('errors.network'));
            setStatusMsg('');
          }
        };

        mediaRecorder.start();
        setRecording(true);
      } catch (err) {
        setErrorMsg('Microphone access denied.');
      }
    } else {
      mediaRecorderRef.current?.stop();
      setRecording(false);
    }
  };

  // 3. Register
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    setStatusMsg(t('register.processing'));
    try {
      const { job_id } = await submitRegister(workerId, file);
      const extraction = await pollJob(job_id, setStatusMsg);
      
      // Auto-confirm register logic (mocked for demo flow speed)
      await fetch(`/api/registers/${extraction.extraction_id || job_id}/confirm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          worker_id: workerId,
          target_row_index: 0,
          corrections: [] // assuming no needs_confirmation for golden path
        })
      });
      
      // Auto-create attestation
      const res = await fetch(`/api/attestations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ record_id: "demo-record-id", employer_name: "Sunil Thekedar" }) // Mocked payload
      });
      const attest = await res.json();
      setAttestToken(attest.token);
      
      setStatusMsg('');
      setStep('attest');
    } catch (err) {
      setErrorMsg(t('errors.network'));
      setStatusMsg('');
    }
  };

  // 4. Attest Auto-polling
  useEffect(() => {
    if (step === 'attest' && attestToken) {
      const interval = setInterval(async () => {
        try {
          const res = await fetch(`/api/attestations/${attestToken}`);
          const data = await res.json();
          if (data.status === 'confirmed') {
            clearInterval(interval);
            setStatusMsg(t('attest.confirmed'));
            
            // Auto issue passport
            setTimeout(async () => {
              setStep('passport');
              setStatusMsg(t('passport.processing'));
              const passport = await issuePassport(workerId);
              setPassportData(passport);
              setStatusMsg('');
            }, 1500);
          }
        } catch (err) {
           // ignore poll errors
        }
      }, 2000);
      return () => clearInterval(interval);
    }
  }, [step, attestToken, workerId]);

  return (
    <div className="min-h-screen bg-neutral-950 text-white font-sans p-6 max-w-md mx-auto relative flex flex-col">
      
      {errorMsg && (
        <div className="bg-red-500/20 text-red-300 p-4 rounded-lg mb-4 text-center border border-red-500/30">
          <p>{errorMsg}</p>
          <button onClick={() => setErrorMsg('')} className="mt-2 text-xs font-mono-data tracking-wider uppercase border border-red-500/50 px-3 py-1 rounded">
            {t('errors.retry')}
          </button>
        </div>
      )}

      {step === 'landing' && (
        <div className="flex-1 flex flex-col items-center justify-center space-y-8 animate-in fade-in zoom-in duration-500">
          <div className="text-center space-y-2">
            <h1 className="text-5xl font-bold tracking-tight">{t('landing.title')}</h1>
            <p className="text-neutral-400 font-mono-data uppercase tracking-widest">{t('landing.subtitle')}</p>
            <div className="inline-block mt-4 px-4 py-2 bg-neutral-900 rounded-full border border-neutral-800 text-xl font-medium text-red-400">
              {t('landing.wage')}
            </div>
          </div>
          <button 
            onClick={handleStart}
            className="w-full max-w-[280px] bg-primary text-black font-bold py-5 rounded-2xl text-xl hover:scale-105 transition-transform shadow-[0_0_40px_rgba(34,197,94,0.3)] active:scale-95"
          >
            {t('landing.start')}
          </button>
        </div>
      )}

      {step === 'voice' && (
        <div className="flex-1 flex flex-col items-center justify-center space-y-12 animate-in slide-in-from-right duration-300">
          <div className="text-center space-y-3">
            <h2 className="text-3xl font-bold">{t('voice.title')}</h2>
            <p className="text-neutral-400">{t('voice.instruction')}</p>
          </div>
          
          <button 
            onClick={handleVoiceToggle}
            className={`w-40 h-40 rounded-full flex items-center justify-center transition-all duration-300 ${recording ? 'bg-red-500 animate-pulse scale-110 shadow-[0_0_50px_rgba(239,68,68,0.5)]' : 'bg-neutral-800 hover:bg-neutral-700'}`}
          >
            <span className="material-symbols-outlined text-6xl">mic</span>
          </button>
          
          <div className="h-10 text-primary font-mono-data text-sm tracking-wider uppercase text-center">
            {recording ? t('voice.recording') : statusMsg}
          </div>
          
          {/* Fallback to skip voice in dev */}
          {!recording && !statusMsg && (
             <button onClick={() => setStep('register')} className="text-xs text-neutral-600 underline">Skip Step (Dev)</button>
          )}
        </div>
      )}

      {step === 'register' && (
        <div className="flex-1 flex flex-col items-center justify-center space-y-12 animate-in slide-in-from-right duration-300">
          <div className="text-center space-y-3">
            <h2 className="text-3xl font-bold">{t('register.title')}</h2>
            <p className="text-neutral-400">{t('register.instruction')}</p>
          </div>
          
          <div className="relative w-full max-w-[280px]">
            <input 
              type="file" 
              accept="image/*" 
              capture="environment" 
              onChange={handleFileChange}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" 
            />
            <div className="w-full bg-primary text-black font-bold py-5 rounded-2xl text-xl text-center shadow-[0_0_40px_rgba(34,197,94,0.3)] flex items-center justify-center gap-3">
              <span className="material-symbols-outlined">photo_camera</span>
              {t('register.capture')}
            </div>
          </div>
          
          <div className="h-10 text-primary font-mono-data text-sm tracking-wider uppercase text-center">
            {statusMsg}
          </div>
        </div>
      )}

      {step === 'attest' && (
        <div className="flex-1 flex flex-col items-center justify-center space-y-12 animate-in slide-in-from-right duration-300">
          <div className="text-center space-y-3">
            <h2 className="text-3xl font-bold">{t('attest.title')}</h2>
            <p className="text-neutral-400">{t('attest.instruction')}</p>
          </div>
          
          <div className="bg-white p-6 rounded-2xl">
             <QRCodeSVG value={`http://localhost:5173/demo/attest/${attestToken}`} size={220} />
          </div>
          
          <div className="h-10 text-primary font-mono-data text-sm tracking-wider uppercase text-center">
            {statusMsg || t('attest.waiting')}
          </div>
          
          {/* Fallback to simulate employer tap */}
          <button onClick={async () => {
             await fetch(`/api/attestations/${attestToken}/respond`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ decision: 'confirmed', employer_name: 'Simulated Tap' })
             });
          }} className="text-xs text-neutral-600 underline">Simulate Employer Tap</button>
        </div>
      )}

      {step === 'passport' && (
        <div className="flex-1 flex flex-col animate-in slide-in-from-right duration-300">
           {passportData ? (
             <div className="mt-8 scale-90 origin-top">
                <PassportView />
             </div>
           ) : (
             <div className="flex-1 flex flex-col items-center justify-center">
               <span className="material-symbols-outlined text-6xl text-primary animate-spin mb-6">autorenew</span>
               <h2 className="text-2xl font-bold">{t('passport.title')}</h2>
               <p className="text-primary font-mono-data mt-4 uppercase tracking-widest">{statusMsg}</p>
             </div>
           )}
        </div>
      )}

    </div>
  );
}

function VerifyStep() {
  const { id } = useParams();
  
  return (
    <div className="min-h-screen bg-neutral-950 flex flex-col items-center justify-center p-6 text-white text-center">
      <span className="material-symbols-outlined text-6xl text-primary mb-6">verified_user</span>
      <h1 className="text-3xl font-bold mb-2">Cryptographic Signature Valid</h1>
      <p className="text-neutral-400 mb-8">Passport ID: <span className="font-mono-data text-xs">{id}</span></p>
      
      <div className="bg-neutral-900 border border-neutral-800 p-6 rounded-2xl w-full max-w-sm">
        <p className="text-neutral-500 uppercase font-mono-data text-xs tracking-widest mb-1">Suggested Wage</p>
        <p className="text-4xl text-primary font-bold">₹1,008/day</p>
        <p className="text-sm text-green-400 mt-2">+₹181 vs unskilled baseline</p>
      </div>
    </div>
  );
}

function AttestStep() {
  const { token } = useParams();
  const [done, setDone] = useState(false);
  
  const handleConfirm = async () => {
    await fetch(`/api/attestations/${token}/respond`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ decision: 'confirmed', employer_name: 'Sunil Thekedar' })
    });
    setDone(true);
  };
  
  if (done) return <div className="min-h-screen bg-primary text-black flex items-center justify-center text-3xl font-bold p-6 text-center">Confirmed! Thank you.</div>;
  
  return (
    <div className="min-h-screen bg-white text-black p-6 flex flex-col items-center justify-center space-y-8">
      <h1 className="text-3xl font-bold">Verify Rakesh</h1>
      <p className="text-gray-600 text-center text-lg">Did Rakesh work with you at <strong>Delhi NCR Site</strong> for 142 days as a Mason?</p>
      
      <button onClick={handleConfirm} className="w-full bg-green-500 text-white font-bold py-5 rounded-2xl text-xl shadow-lg">
        Yes, I confirm
      </button>
      <button className="w-full bg-gray-200 text-black font-bold py-5 rounded-2xl text-xl">
        No, this is wrong
      </button>
    </div>
  );
}

export function DemoFlow() {
  return (
    <Routes>
      <Route path="/" element={<MainFlow />} />
      <Route path="/verify/:id" element={<VerifyStep />} />
      <Route path="/attest/:token" element={<AttestStep />} />
    </Routes>
  );
}
