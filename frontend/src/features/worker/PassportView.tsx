import { useState, useRef } from 'react';
import type { MouseEvent } from 'react';

export function PassportView() {
  const [isQrOpen, setIsQrOpen] = useState(false);
  const cardRef = useRef<HTMLDivElement>(null);
  const glareRef = useRef<HTMLDivElement>(null);

  const handleMouseMove = (e: MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const stage = e.currentTarget;
    const rect = stage.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    
    const rotateX = ((y - centerY) / centerY) * -10;
    const rotateY = ((x - centerX) / centerX) * 12;

    cardRef.current.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.015, 1.015, 1.015)`;
    
    if (glareRef.current) {
      glareRef.current.style.opacity = '1';
      glareRef.current.style.transform = `translate(${rotateY * 3}px, ${rotateX * 3}px)`;
    }
  };

  const handleMouseLeave = () => {
    if (!cardRef.current) return;
    cardRef.current.style.transform = 'rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)';
    if (glareRef.current) {
      glareRef.current.style.opacity = '0';
    }
  };

  const handleClick = () => {
    if (!cardRef.current) return;
    cardRef.current.style.transform = 'rotateY(180deg) scale3d(1.02, 1.02, 1.02)';
    setTimeout(() => {
      if (cardRef.current) {
        cardRef.current.style.transform = 'rotateY(0deg) scale3d(1, 1, 1)';
      }
    }, 650);
  };

  return (
    <>
      {/* Global Ambient Glow Layer */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] bg-primary/[0.045] rounded-full blur-[160px]"></div>
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[420px] h-[420px] bg-emerald-500/[0.035] rounded-full blur-[100px]"></div>
      </div>

      <div className="relative z-10 w-full flex-1 flex flex-col items-center justify-center py-10 px-4">
        {/* Top Sovereign Eyebrow */}
        <div className="flex items-center gap-2 mb-8 select-none">
          <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse shadow-[0_0_8px_#95f3be]"></span>
          <span className="font-label-stamp text-label-stamp uppercase tracking-[0.25em] text-on-surface-variant/80">
            SOVEREIGN CREDENTIAL // TIER 1 SEALED RECORD
          </span>
        </div>

        {/* 3D Perspective Wrapper */}
        <div 
          className="perspective-[1600px] w-full max-w-[490px] cursor-pointer select-none"
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
          onClick={handleClick}
        >
          {/* THE PASSPORT CARD (Crown Jewel) */}
          <div 
            ref={cardRef}
            className="relative w-full rounded-2xl bg-[#0e1010] p-7 sm:p-9 flex flex-col justify-between transition-transform duration-200 ease-out border border-white/[0.08] shadow-[0_30px_90px_-20px_rgba(0,0,0,0.95),0_0_0_1px_rgba(255,255,255,0.06),0_10px_40px_rgba(149,243,190,0.06)] passport-guilloche overflow-hidden group" 
            style={{ transformStyle: 'preserve-3d' }}
          >
            {/* Subtle Specular Reflection and Border Glow */}
            <div ref={glareRef} className="absolute inset-0 rounded-2xl pointer-events-none opacity-0 transition-opacity duration-300 passport-shimmer"></div>
            <div className="absolute inset-0 rounded-2xl pointer-events-none border border-primary/20 mix-blend-screen"></div>
            
            {/* 1. Header: Sovereign Identity & Swiss Micro-Security Chip */}
            <div className="relative z-10 flex items-start justify-between w-full pb-6">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-label-stamp text-xs font-bold tracking-[0.25em] text-primary uppercase">PROOF</span>
                  <span className="text-white/20 font-mono-data text-xs">/</span>
                  <span className="font-label-micro text-[10px] tracking-[0.2em] text-on-surface-variant uppercase font-medium">SOVEREIGN PASSPORT</span>
                </div>
                <div className="font-mono-data text-[10px] text-outline/80 tracking-wider">
                  HASH // 0x9f4a...d7b2
                </div>
              </div>
              <div className="flex items-center gap-2.5">
                <div className="relative w-7 h-7 rounded bg-white/[0.03] border border-white/10 flex items-center justify-center overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-tr from-primary/30 via-tertiary/20 to-secondary/20 opacity-80 mix-blend-screen animate-pulse"></div>
                  <span className="material-symbols-outlined text-primary text-base relative z-10 font-light">fingerprint</span>
                </div>
                <div className="w-6 h-5 rounded-sm bg-tertiary-container/20 border border-tertiary/30 flex flex-col justify-between p-[3px]">
                  <div className="h-[1.5px] w-full bg-tertiary/70 rounded-full"></div>
                  <div className="h-[1.5px] w-full bg-tertiary/70 rounded-full"></div>
                  <div className="h-[1.5px] w-full bg-tertiary/70 rounded-full"></div>
                </div>
              </div>
            </div>

            {/* 2. Hero Section: Biometric Portrait & Prominent Emerald Ring */}
            <div className="relative z-10 flex items-center justify-between gap-6 my-auto pt-2 pb-7">
              <div className="relative shrink-0">
                <div className="relative w-24 h-24 sm:w-28 sm:h-28 rounded-full p-[3px] bg-gradient-to-b from-primary/80 via-white/10 to-primary/40 shadow-[0_0_24px_rgba(149,243,190,0.25)]">
                  <div className="w-full h-full rounded-full overflow-hidden bg-surface-container-lowest relative">
                    <img alt="Rahul Kumar" className="w-full h-full object-cover grayscale contrast-115 group-hover:scale-105 transition-transform duration-700" src="https://lh3.googleusercontent.com/aida/AEtjO1UIkq6nGlB_ilLE8Xb75kgo-bP7UfGd5QN6BL-lnwhPAYEPeNsUYuw56iBhKINFsNabXsVvAsWWNCRjx6iuV5lKyVkhYoxDpCyKdi9p0t6zFZkmGVlkL7kDlmqmddpyOHQLjDRsLHhwwrvvn1Lap1QX9PZxHSmw2MU_weDILBm9VXyZLj9ISp6V0j07RbrzaMxUiNTDRpvz1AJRL5zMTAzzJxAuHFdBbcOpQVqkdTLMJGD0Gd-tQfRaFaHt"/>
                    <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent"></div>
                  </div>
                </div>
                <div className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 bg-[#070808] border border-primary/50 px-2 py-0.5 rounded-full flex items-center gap-1 shadow-lg">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary animate-ping"></span>
                  <span className="font-label-micro text-[8px] text-primary tracking-widest font-bold uppercase">LIVE</span>
                </div>
              </div>
              <div className="flex flex-col items-center text-center justify-center pl-2">
                <div className="relative w-24 h-24 flex items-center justify-center">
                  <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                    <circle className="text-white/[0.07]" cx="50" cy="50" fill="transparent" r="42" stroke="currentColor" strokeWidth="4"></circle>
                    <circle className="text-primary transition-all duration-1000 ease-out drop-shadow-[0_0_10px_rgba(149,243,190,0.6)]" cx="50" cy="50" fill="transparent" r="42" stroke="currentColor" strokeDasharray="263.89" strokeDashoffset="21.11" strokeLinecap="round" strokeWidth="4"></circle>
                  </svg>
                  <div className="absolute flex flex-col items-center justify-center">
                    <span className="font-headline-lg text-2xl sm:text-3xl font-semibold tracking-tight text-white leading-none">92<span className="text-xs font-mono-data text-primary align-top">%</span></span>
                    <span className="font-label-stamp text-[8px] sm:text-[9px] tracking-[0.2em] text-primary uppercase font-bold mt-1">VERIFIED</span>
                  </div>
                </div>
                <div className="flex items-center gap-1 mt-1 text-on-surface-variant/60">
                  <span className="material-symbols-outlined text-[12px] text-primary/80">verified_user</span>
                  <span className="font-mono-data text-[9px] tracking-wider uppercase">SEALED ZERO-KNOWLEDGE</span>
                </div>
              </div>
            </div>

            {/* 3. Monumental Typography */}
            <div className="relative z-10 pt-2 pb-6 border-b border-white/[0.07]">
              <h1 className="font-headline-lg text-3xl sm:text-[34px] font-semibold tracking-tight text-white uppercase leading-[1.05]">
                RAHUL KUMAR
              </h1>
              <p className="font-mono-data text-xs text-on-surface-variant tracking-[0.14em] uppercase mt-1.5 text-primary/90 font-medium">
                MASTER MASON & SITE ARTISAN
              </p>
            </div>

            {/* 4. 4 Supporting Facts */}
            <div className="relative z-10 py-5 grid grid-cols-4 gap-2 border-b border-white/[0.07]">
              <div className="flex flex-col">
                <span className="font-headline-md text-base sm:text-lg font-semibold text-white tracking-tight leading-none">10+</span>
                <span className="font-mono-data text-[9px] text-on-surface-variant/70 uppercase tracking-wider mt-1">YEARS</span>
              </div>
              <div className="flex flex-col border-l border-white/[0.08] pl-3">
                <span className="font-headline-md text-base sm:text-lg font-semibold text-white tracking-tight leading-none">14</span>
                <span className="font-mono-data text-[9px] text-on-surface-variant/70 uppercase tracking-wider mt-1">PROJECTS</span>
              </div>
              <div className="flex flex-col border-l border-white/[0.08] pl-3">
                <span className="font-headline-md text-base sm:text-lg font-semibold text-white tracking-tight leading-none">6</span>
                <span className="font-mono-data text-[9px] text-on-surface-variant/70 uppercase tracking-wider mt-1">EMPLOYERS</span>
              </div>
              <div className="flex flex-col border-l border-white/[0.08] pl-3">
                <span className="font-headline-md text-base sm:text-lg font-semibold text-white tracking-tight leading-none">2,840</span>
                <span className="font-mono-data text-[9px] text-on-surface-variant/70 uppercase tracking-wider mt-1">DAYS</span>
              </div>
            </div>

            {/* 5. Verified Skills Tags */}
            <div className="relative z-10 pt-5 pb-6">
              <span className="font-label-stamp text-[9px] uppercase tracking-[0.2em] text-outline block mb-3">ATTESTED CAPABILITIES</span>
              <div className="flex flex-wrap gap-2">
                <div className="inline-flex items-center gap-1.5 text-on-surface text-[11px] font-mono-data tracking-wider uppercase bg-white/[0.02] border border-white/[0.07] px-2.5 py-1 rounded-sm">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary shrink-0 shadow-[0_0_6px_#95f3be]"></span>
                  <span>BRICK MASONRY</span>
                </div>
                <div className="inline-flex items-center gap-1.5 text-on-surface text-[11px] font-mono-data tracking-wider uppercase bg-white/[0.02] border border-white/[0.07] px-2.5 py-1 rounded-sm">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary shrink-0 shadow-[0_0_6px_#95f3be]"></span>
                  <span>CONCRETE</span>
                </div>
                <div className="inline-flex items-center gap-1.5 text-on-surface text-[11px] font-mono-data tracking-wider uppercase bg-white/[0.02] border border-white/[0.07] px-2.5 py-1 rounded-sm">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary shrink-0 shadow-[0_0_6px_#95f3be]"></span>
                  <span>PLASTERING</span>
                </div>
                <div className="inline-flex items-center gap-1.5 text-on-surface text-[11px] font-mono-data tracking-wider uppercase bg-white/[0.02] border border-white/[0.07] px-2.5 py-1 rounded-sm">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary shrink-0 shadow-[0_0_6px_#95f3be]"></span>
                  <span>SITE SUPERVISION</span>
                </div>
              </div>
            </div>

            {/* 6. Card Footer */}
            <div className="relative z-10 pt-4 border-t border-white/[0.07] flex items-center justify-between">
              <div className="flex flex-col">
                <span className="font-label-stamp text-[8px] text-outline/80 uppercase tracking-widest">DECENTRALIZED ID</span>
                <span className="font-mono-data text-xs text-white tracking-widest mt-0.5">DID:PROOF:9812-441-A</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex flex-col items-end">
                  <span className="font-label-stamp text-[8px] text-outline/80 uppercase tracking-widest">ISSUED</span>
                  <span className="font-mono-data text-[10px] text-on-surface-variant">2024.08.14</span>
                </div>
                <div className="flex items-center text-primary/80">
                  <span className="material-symbols-outlined text-xl rotate-90">contactless</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Interactive Hint Outside Card */}
        <div className="mt-6 flex items-center gap-2 text-outline/70 select-none">
          <span className="material-symbols-outlined text-sm text-primary/70">3d_rotation</span>
          <span className="font-mono-data text-xs tracking-wider">Tap credential to inspect cryptographic micro-layers</span>
        </div>

        {/* Tactile Action Buttons Below */}
        <div className="mt-8 flex items-center justify-center gap-4 w-full max-w-[490px]">
          <button 
            className="flex-1 h-12 rounded-lg bg-primary text-on-primary font-mono-data text-xs uppercase tracking-[0.16em] font-semibold flex items-center justify-center gap-2 hover:bg-primary-container transition-all active:scale-[0.98] shadow-[0_0_25px_rgba(149,243,190,0.18)] cursor-pointer"
            onClick={(e) => {
              e.stopPropagation();
              const el = e.currentTarget.querySelector('span:last-child');
              if (el) {
                const original = el.textContent;
                el.textContent = 'COPIED TO CLIPBOARD';
                navigator.clipboard?.writeText(window.location.href);
                setTimeout(() => { el.textContent = original; }, 2000);
              }
            }}
          >
            <span className="material-symbols-outlined text-base">ios_share</span>
            <span>SHARE PASSPORT</span>
          </button>
          <button 
            className="flex-1 h-12 rounded-lg bg-[#0e1010] border border-white/[0.12] text-white hover:border-white/30 hover:bg-white/[0.03] font-mono-data text-xs uppercase tracking-[0.16em] font-medium flex items-center justify-center gap-2 transition-all active:scale-[0.98] cursor-pointer"
            onClick={() => setIsQrOpen(true)}
          >
            <span className="material-symbols-outlined text-base text-primary">qr_code_scanner</span>
            <span>GENERATE QR</span>
          </button>
        </div>
      </div>

      {/* Cryptographic QR Code Modal */}
      <div 
        className={`fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md transition-opacity duration-200 p-4 ${isQrOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`}
        onClick={() => setIsQrOpen(false)}
      >
        <div 
          className="relative w-full max-w-sm rounded-2xl bg-[#0e1010] border border-white/10 p-7 flex flex-col items-center text-center shadow-2xl"
          onClick={e => e.stopPropagation()}
        >
          <button 
            className="absolute top-5 right-5 text-on-surface-variant hover:text-white transition-colors cursor-pointer"
            onClick={() => setIsQrOpen(false)}
          >
            <span className="material-symbols-outlined text-xl">close</span>
          </button>
          <div className="flex items-center gap-2 mb-4">
            <span className="material-symbols-outlined text-primary text-sm">lock</span>
            <span className="font-label-stamp text-xs uppercase tracking-widest text-white">ZERO-KNOWLEDGE VERIFY</span>
          </div>
          
          <div className="p-4 rounded-xl bg-white flex items-center justify-center shadow-2xl my-2">
            <svg className="w-48 h-48 text-[#070808]" fill="currentColor" viewBox="0 0 100 100">
              <rect fill="none" height="24" rx="3" stroke="currentColor" strokeWidth="4" width="24" x="10" y="10"></rect>
              <rect height="12" width="12" x="16" y="16"></rect>
              <rect fill="none" height="24" rx="3" stroke="currentColor" strokeWidth="4" width="24" x="66" y="10"></rect>
              <rect height="12" width="12" x="72" y="16"></rect>
              <rect fill="none" height="24" rx="3" stroke="currentColor" strokeWidth="4" width="24" x="10" y="66"></rect>
              <rect height="12" width="12" x="16" y="72"></rect>
              <rect height="6" width="6" x="42" y="12"></rect>
              <rect height="6" width="6" x="52" y="12"></rect>
              <rect height="12" width="6" x="42" y="24"></rect>
              <rect height="6" width="12" x="12" y="42"></rect>
              <rect height="8" width="8" x="30" y="42"></rect>
              <rect height="8" width="8" x="46" y="44"></rect>
              <rect height="6" width="12" x="62" y="42"></rect>
              <rect height="12" width="6" x="82" y="42"></rect>
              <rect height="14" width="6" x="42" y="60"></rect>
              <rect height="6" width="10" x="56" y="64"></rect>
              <rect height="6" width="14" x="74" y="66"></rect>
              <rect height="10" width="8" x="52" y="78"></rect>
              <rect height="8" width="8" x="68" y="80"></rect>
              <rect height="10" width="6" x="84" y="78"></rect>
            </svg>
          </div>
          
          <p className="font-mono-data text-xs text-on-surface-variant/80 mt-4 tracking-tight">
            Scan through authorized site scanner to cryptographically validate work history & insurance status.
          </p>
          <div className="mt-5 w-full pt-4 border-t border-white/[0.08] flex justify-between items-center text-[11px] font-mono-data text-outline">
            <span>EXPIRES IN 04:59</span>
            <span className="text-primary flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></span> SYNCED
            </span>
          </div>
        </div>
      </div>
    </>
  );
}
