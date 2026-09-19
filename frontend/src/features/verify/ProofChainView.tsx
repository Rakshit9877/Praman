export function ProofChainView() {
  return (
    <>
      <div className="absolute inset-0 pointer-events-none opacity-20 [background-image:linear-gradient(to_right,#242927_1px,transparent_1px),linear-gradient(to_bottom,#242927_1px,transparent_1px)] [background-size:64px_64px]"></div>
      
      <div className="w-full max-w-7xl mx-auto px-6 md:px-10 py-12 lg:py-20 flex flex-col xl:flex-row gap-12 lg:gap-20 items-start relative z-10">
        
        {/* LEFT COLUMN: THE NARRATIVE */}
        <div className="w-full xl:w-[480px] shrink-0 pt-4 xl:sticky xl:top-32 select-none">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-primary/20 bg-primary/5 mb-6">
            <span className="material-symbols-outlined text-[14px] text-primary">link</span>
            <span className="font-mono-data text-[10px] tracking-[0.2em] text-primary uppercase font-medium">CRYPTOGRAPHIC LEDGER</span>
          </div>
          
          <h1 className="font-display-hero text-4xl sm:text-[46px] font-medium tracking-tight text-[#F5F3ED] uppercase leading-[1.05] mb-5">
            THE CONTINUOUS<br />
            <span className="text-primary font-semibold">PRAMAN CHAIN.</span>
          </h1>
          
          <p className="font-body-lg text-[15px] sm:text-base text-on-surface-variant/90 leading-relaxed mb-8">
            Every shift worked, every skill demonstrated, every payment received is cryptographically bound into an unbroken chain of evidence. It is a sovereign record that belongs entirely to you.
          </p>

          <div className="space-y-4">
            <div className="flex items-start gap-4 p-4 rounded-xl border border-white/[0.08] bg-white/[0.02]">
              <div className="mt-1 flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary">
                <span className="material-symbols-outlined text-[18px]">verified</span>
              </div>
              <div>
                <h3 className="font-mono-data text-xs font-semibold uppercase tracking-widest text-[#F5F3ED] mb-1.5">MULTI-PARTY CONSENSUS</h3>
                <p className="font-body-sm text-[13px] text-on-surface-variant">Claims are only finalized when the worker, supervisor, and agency mathematically sign the day's record.</p>
              </div>
            </div>
            
            <div className="flex items-start gap-4 p-4 rounded-xl border border-white/[0.08] bg-white/[0.02]">
              <div className="mt-1 flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary">
                <span className="material-symbols-outlined text-[18px]">all_inclusive</span>
              </div>
              <div>
                <h3 className="font-mono-data text-xs font-semibold uppercase tracking-widest text-[#F5F3ED] mb-1.5">ZERO-KNOWLEDGE TRUTH</h3>
                <p className="font-body-sm text-[13px] text-on-surface-variant">Prove you have 10+ years of masonry experience to a new employer without revealing past wages or exact locations.</p>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: THE CHAIN VISUALIZATION */}
        <div className="w-full flex-1 relative flex justify-center xl:justify-end min-h-[600px] select-none">
          {/* SVG RIBBON OF TRUTH (Background connector) */}
          <svg className="absolute left-[20px] md:left-[360px] top-[40px] bottom-0 w-full md:w-[600px] h-[700px] pointer-events-none hidden sm:block" fill="none" viewBox="0 0 600 700">
            <path className="animate-flow-emerald" d="M30 40 C 200 40, 200 240, 300 240 C 400 240, 400 440, 500 440" stroke="#79D6A3" strokeWidth="2.5"></path>
            <path d="M30 40 C 200 40, 200 240, 300 240 C 400 240, 400 440, 500 440" stroke="#242927" strokeDasharray="4 6" strokeWidth="1"></path>
          </svg>

          <div className="relative w-full max-w-lg flex flex-col gap-12 sm:gap-24 pt-4 pb-20">
            
            {/* NODE 1: THE GENESIS (PAST) */}
            <div className="relative group flex items-start gap-5 sm:gap-0 sm:block">
              {/* Mobile Connector Line */}
              <div className="absolute left-[19px] top-10 bottom-[-48px] w-0.5 bg-gradient-to-b from-primary to-[#242927] sm:hidden"></div>
              
              <div className="relative sm:absolute sm:left-0 sm:top-1/2 sm:-translate-y-1/2 sm:-translate-x-[70px] z-20 shrink-0">
                <div className="w-10 h-10 rounded-full border border-primary bg-[#0d0f0e] flex items-center justify-center shadow-[0_0_15px_rgba(121,214,163,0.3)]">
                  <span className="material-symbols-outlined text-[18px] text-primary">history</span>
                </div>
              </div>
              <div className="flex-1 rounded-2xl bg-[#0d0f0e] border border-primary/30 p-5 sm:p-6 shadow-[0_10px_30px_rgba(0,0,0,0.5)] transition-transform duration-300 group-hover:-translate-y-1 group-hover:border-primary/60 relative z-10 overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-primary/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div className="flex items-center justify-between mb-4 border-b border-white/[0.08] pb-3">
                  <div className="font-mono-data text-[10px] tracking-widest text-[#737A75] uppercase">ANCHOR // 0x2A...8F1</div>
                  <div className="font-mono-data text-[10px] text-primary border border-primary/20 px-2 py-0.5 rounded">2018.11.04</div>
                </div>
                <h4 className="font-display-hero text-xl text-[#F5F3ED] uppercase tracking-tight mb-2">APPRENTICESHIP LOGGED</h4>
                <p className="font-body-sm text-[13px] text-on-surface-variant">L&amp;T Construction • Site Sector 44</p>
                <div className="mt-4 pt-4 border-t border-white/[0.05] flex items-center gap-3">
                  <span className="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center text-white/40 text-[10px]">A1</span>
                  <span className="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center text-white/40 text-[10px]">S2</span>
                  <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center text-primary border border-primary/40">
                    <span className="material-symbols-outlined text-[12px]">done_all</span>
                  </div>
                </div>
              </div>
            </div>

            {/* NODE 2: THE PRESENT (ACTIVE FOCUS) */}
            <div className="relative group flex items-start gap-5 sm:gap-0 sm:block sm:ml-auto">
              <div className="absolute left-[19px] top-10 bottom-[-48px] w-0.5 bg-[#242927] sm:hidden"></div>
              
              <div className="relative sm:absolute sm:left-0 sm:top-1/2 sm:-translate-y-1/2 sm:-translate-x-[70px] z-20 shrink-0">
                <div className="w-10 h-10 rounded-full border border-white/20 bg-[#0d0f0e] flex items-center justify-center group-hover:border-primary/50 transition-colors">
                  <span className="w-2.5 h-2.5 rounded-full bg-primary animate-pulse shadow-[0_0_8px_#79D6A3]"></span>
                </div>
              </div>
              <div className="flex-1 sm:w-[380px] rounded-2xl bg-white/[0.02] border border-white/[0.1] p-5 sm:p-6 transition-all duration-300 group-hover:bg-[#0d0f0e] group-hover:border-primary/40">
                <div className="flex items-center justify-between mb-4 border-b border-white/[0.08] pb-3">
                  <div className="font-mono-data text-[10px] tracking-widest text-[#737A75] uppercase group-hover:text-primary transition-colors">PENDING BLOCK</div>
                  <div className="font-mono-data text-[10px] text-on-surface-variant">TODAY</div>
                </div>
                <h4 className="font-display-hero text-xl text-[#F5F3ED] uppercase tracking-tight mb-2">SHIFT COMPLETION</h4>
                <p className="font-body-sm text-[13px] text-on-surface-variant mb-4">DLF Phase 3 • Block B • Masonry Lead</p>
                
                {/* Micro-Interaction: Awaiting Signatures */}
                <div className="bg-black/40 rounded-lg p-3 border border-white/[0.05]">
                  <div className="font-mono-data text-[9px] uppercase tracking-wider text-outline mb-2">REQUIRED SIGNATURES</div>
                  <div className="flex flex-col gap-2">
                    <div className="flex items-center justify-between">
                      <span className="font-body-sm text-[12px] text-white">Rahul K. (Self)</span>
                      <span className="material-symbols-outlined text-[14px] text-primary">check_circle</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="font-body-sm text-[12px] text-on-surface-variant">Supervisor (DLF)</span>
                      <span className="font-mono-data text-[9px] text-[#737A75] border border-[#242927] px-1.5 py-0.5 rounded uppercase">AWAITING</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* NODE 3: THE FUTURE (PROJECTED) */}
            <div className="relative group flex items-start gap-5 sm:gap-0 sm:block">
              <div className="relative sm:absolute sm:left-0 sm:top-1/2 sm:-translate-y-1/2 sm:-translate-x-[70px] z-20 shrink-0">
                <div className="w-10 h-10 rounded-full border border-dashed border-[#242927] bg-transparent flex items-center justify-center">
                  <span className="material-symbols-outlined text-[18px] text-[#434c47]">lock_clock</span>
                </div>
              </div>
              <div className="flex-1 rounded-2xl bg-transparent border border-dashed border-[#242927] p-5 sm:p-6 opacity-60">
                <div className="flex items-center justify-between mb-4 border-b border-white/[0.05] pb-3">
                  <div className="font-mono-data text-[10px] tracking-widest text-[#434c47] uppercase">FUTURE STATE</div>
                  <div className="font-mono-data text-[10px] text-[#434c47]">FRIDAY</div>
                </div>
                <h4 className="font-display-hero text-xl text-[#737A75] uppercase tracking-tight mb-2">WEEKLY WAGE SETTLEMENT</h4>
                <p className="font-body-sm text-[13px] text-[#434c47]">Smart contract trigger on 5 accumulated shifts.</p>
              </div>
            </div>

          </div>
        </div>
      </div>
    </>
  );
}
