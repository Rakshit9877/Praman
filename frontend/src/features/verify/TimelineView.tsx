import { useState } from 'react';

type Era = 'foundation' | 'journeyman' | 'master';

export function TimelineView() {
  const [activeEra, setActiveEra] = useState<Era>('journeyman');

  return (
    <div className="w-full flex-1 flex flex-col justify-end pt-10">
      
      {/* Dynamic Data Overview (Top Left) */}
      <div className="w-full max-w-7xl mx-auto px-6 md:px-10 flex justify-between items-end mb-8 sm:mb-16 select-none relative z-20">
        <div className="flex flex-col max-w-lg">
          <div className="inline-flex items-center gap-2 mb-4">
            <span className="material-symbols-outlined text-[16px] text-primary">timeline</span>
            <span className="font-mono-data text-[10px] tracking-[0.2em] text-on-surface-variant uppercase font-medium">CHRONOMETRIC HISTORY</span>
          </div>
          <h1 className="font-display-hero text-3xl sm:text-[42px] font-medium tracking-tight text-[#F5F3ED] uppercase leading-[1.05]">
            10 YEARS OF <span className="text-primary font-semibold block sm:inline">PROVEN WORK.</span>
          </h1>
          <p className="font-body-sm text-[13px] sm:text-[14px] text-on-surface-variant/80 mt-4 max-w-md">
            Drag along the temporal axis to inspect cryptographically bound work history. Each node represents a mathematically verified shift, payment, or skill endorsement.
          </p>
        </div>
      </div>

      {/* THE TIMELINE APPARATUS (Lower half) */}
      <div className="relative w-full h-[400px] sm:h-[480px] bg-[#0A0B0B] border-t border-white/[0.05] overflow-hidden select-none">
        
        {/* Background Grid & Ambient Glow */}
        <div className="absolute inset-0 pointer-events-none opacity-[0.15] [background-image:linear-gradient(to_right,#242927_1px,transparent_1px),linear-gradient(to_bottom,#242927_1px,transparent_1px)] [background-size:24px_24px]"></div>
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[800px] h-[300px] bg-primary/[0.04] rounded-[100%] blur-[80px] pointer-events-none"></div>

        {/* Central Temporal Axis Line */}
        <div className="absolute top-[60%] left-0 w-full h-[1px] bg-white/[0.08] shadow-[0_0_10px_rgba(255,255,255,0.05)]"></div>
        <div className="absolute top-[60%] left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-primary/40 to-transparent scale-x-75 pointer-events-none"></div>

        {/* Interactive Timeline Track */}
        <div className="absolute inset-0 overflow-x-auto overflow-y-hidden snap-x snap-mandatory hide-scrollbar cursor-grab active:cursor-grabbing pb-10">
          <div className="w-[1800px] sm:w-[2400px] h-full relative px-[50vw]">
            
            {/* The Era Control Interface */}
            <div className="absolute top-8 left-1/2 -translate-x-1/2 flex items-center gap-1 bg-black/50 border border-white/10 rounded-full p-1 backdrop-blur-md z-30 sticky-nav">
              <button 
                className={`px-4 py-1.5 rounded-full font-mono-data text-[10px] uppercase tracking-wider transition-colors duration-200 cursor-pointer ${activeEra === 'foundation' ? 'bg-primary text-[#052B19] font-semibold' : 'text-on-surface-variant hover:text-white'}`}
                onClick={() => setActiveEra('foundation')}
              >
                2014—2017 (FOUNDATION)
              </button>
              <button 
                className={`px-4 py-1.5 rounded-full font-mono-data text-[10px] uppercase tracking-wider transition-colors duration-200 cursor-pointer ${activeEra === 'journeyman' ? 'bg-primary text-[#052B19] font-semibold' : 'text-on-surface-variant hover:text-white'}`}
                onClick={() => setActiveEra('journeyman')}
              >
                2018—2021 (JOURNEYMAN)
              </button>
              <button 
                className={`px-4 py-1.5 rounded-full font-mono-data text-[10px] uppercase tracking-wider transition-colors duration-200 cursor-pointer ${activeEra === 'master' ? 'bg-primary text-[#052B19] font-semibold' : 'text-on-surface-variant hover:text-white'}`}
                onClick={() => setActiveEra('master')}
              >
                2022—2024 (MASTER)
              </button>
            </div>

            {/* ERA: JOURNEYMAN (Visible active data) */}
            <div className={`transition-opacity duration-500 ${activeEra === 'journeyman' ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none absolute inset-0'}`}>
              
              {/* Data Node 1: Above Axis */}
              <div className="absolute top-[30%] left-[20%] group">
                <div className="absolute top-full left-1/2 -translate-x-1/2 h-[calc(30vh-20px)] w-[1px] bg-white/[0.1] group-hover:bg-primary/50 transition-colors"></div>
                <div className="bg-[#121413] border border-white/[0.1] rounded-lg p-3 w-48 shadow-xl group-hover:border-primary/50 group-hover:-translate-y-1 transition-all">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-mono-data text-[9px] text-primary">2018.11.04</span>
                    <span className="material-symbols-outlined text-[12px] text-primary">done_all</span>
                  </div>
                  <h4 className="font-mono-data text-[10px] text-white font-semibold mb-1 uppercase tracking-wide">CERTIFICATION ADDED</h4>
                  <p className="text-[11px] text-on-surface-variant/70 leading-tight">L&amp;T Construction issued Advanced Brickwork certificate.</p>
                </div>
                <div className="absolute top-[calc(30vh+25px)] left-1/2 -translate-x-1/2 w-3 h-3 rounded-full bg-[#121413] border-2 border-primary z-10 shadow-[0_0_10px_rgba(121,214,163,0.5)] group-hover:scale-125 transition-transform"></div>
              </div>

              {/* Data Node 2: Below Axis */}
              <div className="absolute top-[60%] left-[35%] group">
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 h-[12vh] w-[1px] bg-white/[0.1] group-hover:bg-primary/50 transition-colors"></div>
                <div className="absolute -top-[12vh] left-1/2 -translate-x-1/2 -translate-y-[6px] w-2 h-2 rounded-full bg-white/20 z-10 group-hover:bg-primary transition-colors"></div>
                <div className="bg-[#121413] border border-white/[0.1] rounded-lg p-3 w-44 shadow-xl mt-[12vh] group-hover:border-primary/50 group-hover:translate-y-1 transition-all">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-mono-data text-[9px] text-on-surface-variant">2019.06.12</span>
                    <span className="w-1.5 h-1.5 rounded-full bg-secondary-fixed"></span>
                  </div>
                  <h4 className="font-mono-data text-[10px] text-white font-semibold mb-1 uppercase tracking-wide">MAJOR PROJECT END</h4>
                  <p className="text-[11px] text-on-surface-variant/70 leading-tight">8,000 hrs logged at DLF Cyber City site.</p>
                </div>
              </div>

              {/* Data Node 3: Above Axis (Dense Activity Cluster) */}
              <div className="absolute top-[15%] left-[55%] group">
                <div className="absolute top-full left-1/2 -translate-x-1/2 h-[calc(45vh-20px)] w-[1px] bg-white/[0.1] group-hover:bg-primary/50 transition-colors"></div>
                <div className="bg-[#070808] border border-primary/30 rounded-lg p-4 w-60 shadow-[0_10px_30px_rgba(0,0,0,0.8)] group-hover:border-primary group-hover:-translate-y-1 transition-all relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-full h-0.5 bg-primary"></div>
                  <div className="flex justify-between items-center mb-3">
                    <span className="font-mono-data text-[9px] text-primary tracking-widest bg-primary/10 px-1.5 py-0.5 rounded">2020.03 — 2021.01</span>
                  </div>
                  <h4 className="font-mono-data text-[11px] text-white font-semibold mb-2 uppercase tracking-wider">SUPERVISOR PROMOTION</h4>
                  <div className="flex items-center gap-2 mb-2">
                    <div className="flex -space-x-2">
                      <div className="w-5 h-5 rounded-full bg-[#242927] border border-[#121413]"></div>
                      <div className="w-5 h-5 rounded-full bg-primary/20 border border-[#121413]"></div>
                      <div className="w-5 h-5 rounded-full bg-[#242927] border border-[#121413]"></div>
                    </div>
                    <span className="text-[10px] text-on-surface-variant">Consensus Verified</span>
                  </div>
                  <p className="text-[11px] text-on-surface-variant/80 leading-tight">Promoted to site supervisor overseeing 14 masons. Smart contract updated wage tier.</p>
                </div>
                <div className="absolute top-[calc(45vh+35px)] left-1/2 -translate-x-1/2 w-4 h-4 rounded-full bg-primary flex items-center justify-center z-10 shadow-[0_0_15px_#79D6A3] group-hover:scale-110 transition-transform">
                  <div className="w-1.5 h-1.5 rounded-full bg-[#070808]"></div>
                </div>
              </div>

            </div>

            {/* Empty states for other eras to show functionality */}
            <div className={`transition-opacity duration-500 absolute inset-0 flex items-center justify-center pointer-events-none ${activeEra !== 'journeyman' ? 'opacity-100' : 'opacity-0'}`}>
              <div className="font-mono-data text-xs text-on-surface-variant/50 tracking-widest uppercase flex flex-col items-center gap-3">
                <span className="material-symbols-outlined text-2xl">hourglass_empty</span>
                <span>CRYPTOGRAPHIC RECORDS ENCRYPTED</span>
              </div>
            </div>

          </div>
        </div>
        
        {/* Playhead Marker */}
        <div className="absolute top-[60%] left-1/2 -translate-x-1/2 -translate-y-1/2 w-0.5 h-[80px] bg-white pointer-events-none z-20"></div>
        <div className="absolute top-[60%] left-1/2 -translate-x-1/2 -translate-y-[45px] bg-white text-black font-mono-data text-[9px] px-1.5 py-0.5 rounded font-bold pointer-events-none z-20">NOW</div>
      </div>
    </div>
  );
}
