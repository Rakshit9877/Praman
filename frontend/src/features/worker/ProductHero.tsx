import { Link } from 'react-router-dom';

export function ProductHero() {
  return (
    <>
      {/* Fine Architectural Cross-Grid Background */}
      <div className="absolute inset-0 pointer-events-none opacity-25 [background-image:linear-gradient(to_right,#242927_1px,transparent_1px),linear-gradient(to_bottom,#242927_1px,transparent_1px)] [background-size:128px_128px]"></div>
      
      {/* Soft radial ambient lighting centered behind the Orbit visual */}
      <div className="absolute top-[48%] left-1/2 -translate-x-1/2 -translate-y-1/2 w-[720px] h-[720px] rounded-full bg-[#79D6A3]/[0.035] blur-[120px] pointer-events-none"></div>
      
      <div className="relative z-10 w-full max-w-7xl mx-auto px-6 md:px-10 flex flex-col items-center">
        {/* HERO TYPOGRAPHY & ACTIONS TIER (Monumental yet restrained) */}
        <section className="w-full pt-14 md:pt-20 pb-4 text-center flex flex-col items-center select-none">
          {/* Registry Protocol Micro Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#242927] bg-[#0d0f0e]/80 mb-6">
            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></span>
            <span className="font-mono-data text-[10px] tracking-[0.2em] text-primary uppercase font-medium">REGISTRY PROTOCOL V.04</span>
            <span className="text-[#434c47] font-mono-data text-[10px]">/</span>
            <span className="font-mono-data text-[10px] tracking-[0.16em] text-[#737A75] uppercase">SOVEREIGN WORK IDENTITY</span>
          </div>
          
          {/* Monumental Headline */}
          <h1 className="font-display-hero text-4xl sm:text-5xl md:text-[68px] md:leading-[1.08] font-medium tracking-tight text-[#F5F3ED] uppercase max-w-4xl mx-auto">
            YOUR WORK SHOULD<br/>
            TRAVEL <span className="text-primary font-semibold">WITH YOU.</span>
          </h1>
          
          {/* One-line refined supporting statement */}
          <p className="font-body-lg text-sm sm:text-base md:text-lg text-[#737A75] font-normal tracking-normal max-w-xl mx-auto mt-4 mb-8">
            A portable identity built from the work you’ve already done.
          </p>
          
          {/* Minimalist Actions */}
          <div className="flex flex-row items-center justify-center gap-4 sm:gap-6">
            <Link to="/passport" className="group inline-flex items-center gap-2.5 bg-primary text-[#052B19] font-mono-data text-xs font-semibold uppercase tracking-wider px-6 py-3 rounded-full hover:brightness-110 active:scale-[0.98] transition-all duration-200 shadow-[0_0_24px_rgba(121,214,163,0.22)]">
              <span className="w-1.5 h-1.5 rounded-full bg-[#052B19]"></span>
              <span>VIEW PASSPORT</span>
            </Link>
            <Link to="/proof-chain" className="group inline-flex items-center gap-1.5 text-[#F5F3ED] hover:text-primary font-mono-data text-xs uppercase tracking-wider px-4 py-3 transition-colors duration-200">
              <span>HOW IT WORKS</span>
              <span className="material-symbols-outlined text-sm transition-transform duration-200 group-hover:translate-x-1">arrow_forward</span>
            </Link>
          </div>
        </section>

        {/* THE HERO ORBIT: COMMANDING HERO VISUAL */}
        <section className="relative w-full max-w-[880px] h-[580px] sm:h-[660px] md:h-[720px] mx-auto flex items-center justify-center my-2 select-none">
          {/* SVG CONCENTRIC ORBITAL RINGS & TELEMETRY LINES */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none" fill="none" viewBox="0 0 880 720">
            <defs>
              <radialGradient cx="50%" cy="50%" id="orbit-glow" r="50%">
                <stop offset="0%" stopColor="#79D6A3" stopOpacity="0.12"></stop>
                <stop offset="100%" stopColor="#79D6A3" stopOpacity="0"></stop>
              </radialGradient>
              <linearGradient gradientUnits="userSpaceOnUse" id="ray-grad-tl" x1="440" x2="160" y1="360" y2="170">
                <stop offset="0%" stopColor="#79D6A3" stopOpacity="0.5"></stop>
                <stop offset="60%" stopColor="#242927" stopOpacity="0.7"></stop>
                <stop offset="100%" stopColor="#242927" stopOpacity="0.1"></stop>
              </linearGradient>
              <linearGradient gradientUnits="userSpaceOnUse" id="ray-grad-tr" x1="440" x2="720" y1="360" y2="190">
                <stop offset="0%" stopColor="#79D6A3" stopOpacity="0.5"></stop>
                <stop offset="60%" stopColor="#242927" stopOpacity="0.7"></stop>
                <stop offset="100%" stopColor="#242927" stopOpacity="0.1"></stop>
              </linearGradient>
              <linearGradient gradientUnits="userSpaceOnUse" id="ray-grad-bl" x1="440" x2="170" y1="360" y2="540">
                <stop offset="0%" stopColor="#79D6A3" stopOpacity="0.5"></stop>
                <stop offset="60%" stopColor="#242927" stopOpacity="0.7"></stop>
                <stop offset="100%" stopColor="#242927" stopOpacity="0.1"></stop>
              </linearGradient>
              <linearGradient gradientUnits="userSpaceOnUse" id="ray-grad-br" x1="440" x2="710" y1="360" y2="530">
                <stop offset="0%" stopColor="#79D6A3" stopOpacity="0.5"></stop>
                <stop offset="60%" stopColor="#242927" stopOpacity="0.7"></stop>
                <stop offset="100%" stopColor="#242927" stopOpacity="0.1"></stop>
              </linearGradient>
            </defs>
            <circle cx="440" cy="360" fill="url(#orbit-glow)" r="220"></circle>
            <line opacity="0.6" stroke="#242927" strokeDasharray="3 7" strokeWidth="1" x1="440" x2="440" y1="40" y2="680"></line>
            <line opacity="0.6" stroke="#242927" strokeDasharray="3 7" strokeWidth="1" x1="60" x2="820" y1="360" y2="360"></line>
            <line stroke="url(#ray-grad-tl)" strokeWidth="0.85" x1="440" x2="160" y1="360" y2="170"></line>
            <line stroke="url(#ray-grad-tr)" strokeWidth="0.85" x1="440" x2="720" y1="360" y2="190"></line>
            <line stroke="url(#ray-grad-bl)" strokeWidth="0.85" x1="440" x2="170" y1="360" y2="540"></line>
            <line stroke="url(#ray-grad-br)" strokeWidth="0.85" x1="440" x2="710" y1="360" y2="530"></line>
            <circle cx="440" cy="360" opacity="0.45" r="320" stroke="#242927" strokeDasharray="6 14" strokeWidth="1"></circle>
            <circle cx="440" cy="360" opacity="0.8" r="235" stroke="#242927" strokeWidth="1"></circle>
            <circle cx="440" cy="360" opacity="0.25" r="235" stroke="#79D6A3" strokeDasharray="40 180" strokeWidth="1"></circle>
            <circle cx="440" cy="360" opacity="0.75" r="162" stroke="#242927" strokeDasharray="2 6" strokeWidth="1"></circle>
            <circle cx="440" cy="360" opacity="0.6" r="124" stroke="#242927" strokeWidth="2.5"></circle>
            <circle cx="440" cy="360" opacity="0.18" r="124" stroke="#79D6A3" strokeDasharray="779.11" strokeDashoffset="62.33" strokeLinecap="round" strokeWidth="6" transform="rotate(-90 440 360)"></circle>
            <circle cx="440" cy="360" id="verification-orbit-arc" r="124" stroke="#79D6A3" strokeDasharray="779.11" strokeDashoffset="62.33" strokeLinecap="round" strokeWidth="2.5" style={{ transition: 'stroke-dashoffset 2.6s cubic-bezier(0.16, 1, 0.3, 1)', filter: 'drop-shadow(0 0 10px rgba(121, 214, 163, 0.65))' }} transform="rotate(-90 440 360)"></circle>
            <g transform="rotate(241 440 360)">
              <circle className="animate-ping" cx="564" cy="360" fill="#79D6A3" opacity="0.3" r="5"></circle>
              <circle cx="564" cy="360" fill="#79D6A3" r="3"></circle>
            </g>
            <line stroke="#79D6A3" strokeWidth="1.5" x1="440" x2="440" y1="228" y2="236"></line>
            <line stroke="#434c47" strokeWidth="1.5" x1="440" x2="440" y1="484" y2="492"></line>
            <line stroke="#434c47" strokeWidth="1.5" x1="308" x2="316" y1="360" y2="360"></line>
            <line stroke="#434c47" strokeWidth="1.5" x1="564" x2="572" y1="360" y2="360"></line>
          </svg>

          {/* FLOATING PRAMAN NODES */}
          <div className="node-float-1 absolute top-[12%] left-[4%] sm:left-[8%] md:left-[9%] z-20 flex items-center gap-3 cursor-pointer group">
            <div className="flex flex-col text-left">
              <span className="font-display-hero text-xl sm:text-2xl md:text-[28px] font-medium text-[#F5F3ED] tracking-tight group-hover:text-primary transition-colors duration-200">10+ YEARS</span>
              <span className="font-mono-data text-[11px] uppercase tracking-[0.18em] text-[#737A75] mt-0.5">EXPERIENCE ANCHOR</span>
            </div>
            <div className="relative flex items-center justify-center shrink-0">
              <span className="w-3 h-3 rounded-full bg-primary/20 animate-ping absolute"></span>
              <span className="w-2 h-2 rounded-full bg-primary shadow-[0_0_10px_#79D6A3]"></span>
            </div>
          </div>

          <div className="node-float-2 absolute top-[16%] right-[4%] sm:right-[8%] md:right-[9%] z-20 flex items-center gap-3 cursor-pointer group">
            <div className="relative flex items-center justify-center shrink-0">
              <span className="w-3 h-3 rounded-full bg-primary/20 animate-ping absolute"></span>
              <span className="w-2 h-2 rounded-full bg-primary shadow-[0_0_10px_#79D6A3]"></span>
            </div>
            <div className="flex flex-col text-left">
              <span className="font-display-hero text-xl sm:text-2xl md:text-[28px] font-medium text-[#F5F3ED] tracking-tight group-hover:text-primary transition-colors duration-200">14 PROJECTS</span>
              <span className="font-mono-data text-[11px] uppercase tracking-[0.18em] text-[#737A75] mt-0.5">CIVIL & METRO SCALE</span>
            </div>
          </div>

          <div className="node-float-3 absolute bottom-[18%] left-[4%] sm:left-[8%] md:left-[10%] z-20 flex items-center gap-3 cursor-pointer group">
            <div className="flex flex-col text-right">
              <span className="font-display-hero text-xl sm:text-2xl md:text-[28px] font-medium text-[#F5F3ED] tracking-tight group-hover:text-primary transition-colors duration-200">6 EMPLOYERS</span>
              <span className="font-mono-data text-[11px] uppercase tracking-[0.18em] text-[#737A75] mt-0.5">CONSORTIUM VERIFIED</span>
            </div>
            <div className="relative flex items-center justify-center shrink-0">
              <span className="w-3 h-3 rounded-full bg-primary/20 animate-ping absolute"></span>
              <span className="w-2 h-2 rounded-full bg-primary shadow-[0_0_10px_#79D6A3]"></span>
            </div>
          </div>

          <div className="node-float-4 absolute bottom-[16%] right-[4%] sm:right-[8%] md:right-[10%] z-20 flex items-center gap-3 cursor-pointer group">
            <div className="relative flex items-center justify-center shrink-0">
              <span className="w-3 h-3 rounded-full bg-primary/20 animate-ping absolute"></span>
              <span className="w-2 h-2 rounded-full bg-primary shadow-[0_0_10px_#79D6A3]"></span>
            </div>
            <div className="flex flex-col text-left">
              <span className="font-display-hero text-xl sm:text-2xl md:text-[28px] font-medium text-[#F5F3ED] tracking-tight group-hover:text-primary transition-colors duration-200">2,840 DAYS</span>
              <span className="font-mono-data text-[11px] uppercase tracking-[0.18em] text-[#737A75] mt-0.5">BIOMETRIC ATTENDANCE</span>
            </div>
          </div>

          {/* THE CENTRAL IDENTITY SEAL: RAHUL KUMAR */}
          <div className="relative z-30 flex flex-col items-center text-center">
            <div className="relative w-56 h-56 md:w-60 md:h-60 rounded-full p-2 flex items-center justify-center">
              <div className="absolute inset-0 rounded-full border border-[#242927] bg-[#070808]/90"></div>
              <div className="relative w-full h-full rounded-full overflow-hidden border border-[#242927]">
                <img alt="Rahul Kumar - Master Mason & Site Artisan" className="w-full h-full object-cover grayscale contrast-110 brightness-95 transition-all duration-700 hover:grayscale-0 hover:scale-105" src="https://lh3.googleusercontent.com/aida/AEtjO1UIkq6nGlB_ilLE8Xb75kgo-bP7UfGd5QN6BL-lnwhPAYEPeNsUYuw56iBhKINFsNabXsVvAsWWNCRjx6iuV5lKyVkhYoxDpCyKdi9p0t6zFZkmGVlkL7kDlmqmddpyOHQLjDRsLHhwwrvvn1Lap1QX9PZxHSmw2MU_weDILBm9VXyZLj9ISp6V0j07RbrzaMxUiNTDRpvz1AJRL5zMTAzzJxAuHFdBbcOpQVqkdTLMJGD0Gd-tQfRaFaHt"/>
                <div className="absolute inset-0 bg-gradient-to-t from-[#070808]/75 via-transparent to-transparent pointer-events-none"></div>
              </div>
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 z-40 inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#070808] border border-primary/60 shadow-[0_0_14px_rgba(121,214,163,0.3)]">
                <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></span>
                <span className="font-mono-data text-[10px] font-bold tracking-[0.16em] text-primary uppercase">92% VERIFIED</span>
              </div>
              <div className="absolute -bottom-2.5 left-1/2 -translate-x-1/2 z-40 inline-flex items-center px-2.5 py-0.5 rounded-full bg-[#070808] border border-[#242927]">
                <span className="font-mono-data text-[9px] text-[#737A75] tracking-widest uppercase">DID:IN//9032-B</span>
              </div>
            </div>
            <div className="mt-6 flex flex-col items-center">
              <h2 className="font-display-hero text-2xl md:text-3xl font-medium tracking-wide text-[#F5F3ED] uppercase">
                RAHUL KUMAR
              </h2>
              <div className="flex items-center gap-2 mt-1.5 font-mono-data text-xs tracking-[0.2em] uppercase">
                <span className="text-primary font-medium">MASTER MASON & SITE ARTISAN</span>
                <span className="text-[#434c47]">•</span>
                <span className="text-[#737A75]">DELHI NCR</span>
              </div>
            </div>
          </div>
        </section>

        {/* BOTTOM ENCLAVE & CRYPTOGRAPHIC TELEMETRY STRIP */}
        <section className="w-full max-w-5xl mx-auto border-t border-[#242927] pt-6 pb-16 flex flex-col sm:flex-row items-center justify-between gap-4 font-mono-data text-[11px] text-[#737A75]">
          <div className="flex items-center gap-3">
            <span className="w-1.5 h-1.5 rounded-full bg-primary"></span>
            <span className="tracking-widest uppercase">ENCLAVE: HARDWARE SECURED</span>
            <span className="text-[#242927]">|</span>
            <span className="tracking-widest uppercase">ZERO-KNOWLEDGE WITNESS: CONFIRMED</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="tracking-widest uppercase">STANDARDS: ISO/IEC 7810 ID-1</span>
            <span className="text-primary font-semibold tracking-widest uppercase">OFFLINE P2P READY</span>
          </div>
        </section>
      </div>
    </>
  );
}
