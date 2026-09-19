import { useState } from 'react';

export function ScannerView() {
  const [isCommitted, setIsCommitted] = useState(false);

  const handleCommit = () => {
    setIsCommitted(true);
    setTimeout(() => setIsCommitted(false), 3000);
  };

  return (
    <div className="w-full flex-1 flex items-center justify-center py-12 px-6">
      
      <div className="w-full max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-[1fr_440px] gap-10 lg:gap-16 items-center">
        
        {/* LEFT COLUMN: THE OPTICAL SCAN BED (Star of the show) */}
        <div className="relative w-full aspect-square max-w-[600px] mx-auto lg:mx-0 rounded-3xl bg-[#070808] border border-white/[0.05] p-6 sm:p-10 shadow-[0_0_80px_rgba(0,0,0,0.8)] overflow-hidden select-none group">
          
          {/* Subtle grid bed */}
          <div className="absolute inset-0 pointer-events-none opacity-[0.15] [background-image:linear-gradient(to_right,#242927_1px,transparent_1px),linear-gradient(to_bottom,#242927_1px,transparent_1px)] [background-size:32px_32px]"></div>

          {/* Corner Registration Marks */}
          <div className="absolute top-6 left-6 w-8 h-8 border-t-2 border-l-2 border-primary/40 rounded-tl-lg"></div>
          <div className="absolute top-6 right-6 w-8 h-8 border-t-2 border-r-2 border-primary/40 rounded-tr-lg"></div>
          <div className="absolute bottom-6 left-6 w-8 h-8 border-b-2 border-l-2 border-primary/40 rounded-bl-lg"></div>
          <div className="absolute bottom-6 right-6 w-8 h-8 border-b-2 border-r-2 border-primary/40 rounded-br-lg"></div>

          {/* The Document Being Scanned */}
          <div className="relative w-[85%] h-[90%] mx-auto bg-white rounded-md shadow-2xl overflow-hidden mt-2 p-6 flex flex-col grayscale contrast-125 opacity-90 transition-all duration-500 group-hover:grayscale-[0.5]">
            <div className="flex justify-between items-start border-b-2 border-black pb-4 mb-4">
              <h3 className="font-serif text-2xl font-bold tracking-tight uppercase">DLF Projects Ltd.</h3>
              <div className="text-right">
                <div className="font-mono text-[9px] uppercase tracking-widest font-bold">WORK AUTHORIZATION</div>
                <div className="font-mono text-[9px] text-gray-500">REF: DLF-24-991A</div>
              </div>
            </div>
            <div className="space-y-3 font-mono text-[10px]">
              <div className="grid grid-cols-3 border-b border-gray-200 pb-2">
                <span className="text-gray-500">CONTRACTOR:</span>
                <span className="col-span-2 font-bold">RAHUL KUMAR (DID:IN//9032-B)</span>
              </div>
              <div className="grid grid-cols-3 border-b border-gray-200 pb-2">
                <span className="text-gray-500">ROLE/TIER:</span>
                <span className="col-span-2 font-bold">MASTER MASON (TIER 1)</span>
              </div>
              <div className="grid grid-cols-3 border-b border-gray-200 pb-2">
                <span className="text-gray-500">SHIFT DATA:</span>
                <span className="col-span-2 font-bold">2024.09.12 // 08:00 - 18:30 // SECTOR 44</span>
              </div>
            </div>
            
            {/* The signature ink */}
            <div className="mt-auto pt-6 grid grid-cols-2 gap-8">
              <div>
                <div className="border-b border-gray-400 h-10 w-full mb-1 flex items-end">
                  <span className="font-signature text-xl text-blue-800 italic -mb-1 opacity-80">R. Kumar</span>
                </div>
                <span className="font-mono text-[8px] text-gray-500">WORKER SIGNATURE</span>
              </div>
              <div>
                <div className="border-b border-gray-400 h-10 w-full mb-1 flex items-end">
                  <span className="font-signature text-xl text-black italic -mb-1 opacity-90">S. Patel</span>
                </div>
                <span className="font-mono text-[8px] text-gray-500">SUPERVISOR APPROVAL</span>
              </div>
            </div>
          </div>

          {/* THE SWEEPING AI LASER (Optical Reading) */}
          <div className="absolute inset-x-0 h-32 bg-gradient-to-b from-transparent via-primary/20 to-primary/60 mix-blend-screen pointer-events-none laser-line z-20">
            <div className="absolute bottom-0 w-full h-[2px] bg-primary shadow-[0_0_20px_#95f3be,0_0_40px_#95f3be]"></div>
          </div>

          {/* Floating Data Extraction Tooltips (Appear dynamically as laser sweeps) */}
          <div className="absolute top-[35%] left-[55%] bg-[#0d0f0e]/90 border border-primary/50 backdrop-blur-md rounded-lg p-2.5 z-30 shadow-xl opacity-0 group-hover:opacity-100 transition-opacity duration-700 delay-300">
            <div className="flex items-center gap-1.5 mb-1 text-primary">
              <span className="material-symbols-outlined text-[12px]">fingerprint</span>
              <span className="font-mono-data text-[8px] uppercase tracking-widest font-bold">DID MATCH</span>
            </div>
            <span className="font-mono-data text-[10px] text-white">DID:IN//9032-B</span>
          </div>

          <div className="absolute bottom-[20%] left-[20%] bg-[#0d0f0e]/90 border border-primary/50 backdrop-blur-md rounded-lg p-2.5 z-30 shadow-xl opacity-0 group-hover:opacity-100 transition-opacity duration-700 delay-700">
            <div className="flex items-center gap-1.5 mb-1 text-primary">
              <span className="material-symbols-outlined text-[12px]">edit_document</span>
              <span className="font-mono-data text-[8px] uppercase tracking-widest font-bold">SIGNATURE VALID</span>
            </div>
            <span className="font-mono-data text-[10px] text-white">S. Patel (0x8F2...1A)</span>
          </div>

        </div>

        {/* RIGHT COLUMN: EXTRACTION LOGIC & ACTIONS */}
        <div className="flex flex-col">
          
          <div className="inline-flex items-center gap-2 mb-4">
            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></span>
            <span className="font-mono-data text-[10px] tracking-[0.2em] text-on-surface-variant uppercase font-medium">OPTICAL INGESTION</span>
          </div>
          
          <h2 className="font-display-hero text-3xl sm:text-4xl font-medium tracking-tight text-[#F5F3ED] uppercase leading-[1.1] mb-6">
            DIGITIZE. EXTRACT.<br />
            <span className="text-primary font-semibold">CRYPTOGRAPHICALLY SEAL.</span>
          </h2>
          
          <p className="font-body-sm text-[14px] text-on-surface-variant/80 mb-10 leading-relaxed">
            Our AI models visually inspect paper records—parsing handwriting, dates, and stamps—translating analogue truth into a verifiable on-chain claim.
          </p>

          {/* Telemetry Output Box */}
          <div className="bg-[#0A0B0B] border border-white/[0.08] rounded-xl p-5 mb-8 font-mono-data text-xs flex flex-col gap-3 shadow-inner">
            <div className="flex items-center justify-between border-b border-white/[0.05] pb-2">
              <span className="text-[#737A75]">Confidence Score</span>
              <span className="text-primary font-bold">98.4%</span>
            </div>
            <div className="flex items-center justify-between border-b border-white/[0.05] pb-2">
              <span className="text-[#737A75]">Entities Extracted</span>
              <span className="text-white">12 Attributes</span>
            </div>
            <div className="flex items-center justify-between border-b border-white/[0.05] pb-2">
              <span className="text-[#737A75]">Anomaly Detection</span>
              <span className="text-white flex items-center gap-1">
                <span className="material-symbols-outlined text-[14px] text-primary">check_circle</span>
                CLEAN
              </span>
            </div>
            <div className="flex items-center justify-between pt-1">
              <span className="text-[#737A75]">ZKP Target Hash</span>
              <span className="text-white bg-white/5 px-1.5 py-0.5 rounded truncate max-w-[120px]">0x7F9...E2A</span>
            </div>
          </div>

          {/* Action Button */}
          <button 
            className={`h-14 rounded-lg font-mono-data text-xs uppercase tracking-[0.16em] font-semibold flex items-center justify-center gap-2 transition-all active:scale-[0.98] cursor-pointer ${
              isCommitted 
                ? 'bg-[#121413] border border-primary text-primary'
                : 'bg-primary text-[#052B19] hover:brightness-110 shadow-[0_0_25px_rgba(149,243,190,0.18)]'
            }`}
            onClick={handleCommit}
            disabled={isCommitted}
          >
            {isCommitted ? (
              <>
                <span className="material-symbols-outlined text-base">verified</span>
                <span>COMMITTED TO CHAIN</span>
              </>
            ) : (
              <>
                <span className="material-symbols-outlined text-base">lock</span>
                <span>COMMIT TO PASSPORT</span>
              </>
            )}
          </button>
          
        </div>

      </div>
    </div>
  );
}
