import type { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const location = useLocation();

  const getNavClass = (path: string) => {
    const isActive = location.pathname === path;
    if (isActive) {
      return "font-mono-data text-xs tracking-widest text-primary border-b border-primary py-1 uppercase";
    }
    return "font-mono-data text-xs tracking-widest text-[#737A75] hover:text-[#F5F3ED] transition-colors py-1 uppercase";
  };

  return (
    <div className="bg-[#070808] font-body-md text-[#F5F3ED] antialiased selection:bg-primary/20 selection:text-primary min-h-screen flex flex-col justify-between">
      {/* TOP NAVIGATION */}
      <header className="fixed top-0 w-full z-50 bg-[#070808]/85 backdrop-blur-xl border-b border-[#242927]">
        <div className="h-16 max-w-7xl mx-auto px-6 md:px-10 flex items-center justify-between gap-6">
          {/* Brand Logo & Wordmark */}
          <Link to="/" className="flex items-center gap-3 shrink-0 group">
            <div className="w-8 h-8 rounded border border-primary/40 flex items-center justify-center bg-primary/5 text-primary transition-transform duration-300 group-hover:scale-105">
              <span className="font-mono-data font-bold text-sm tracking-tighter">PR</span>
            </div>
            <span className="font-display-hero text-base font-semibold tracking-[0.2em] text-[#F5F3ED] uppercase">PRAMAN</span>
          </Link>

          {/* Minimal Navigation Links */}
          <nav className="hidden lg:flex items-center gap-7 h-full">
            <Link to="/" className={getNavClass('/')}>PRODUCT</Link>
            <Link to="/passport" className={getNavClass('/passport')}>PASSPORT</Link>
            <Link to="/proof-chain" className={getNavClass('/proof-chain')}>PRAMAN CHAIN</Link>
            <Link to="/scanner" className={getNavClass('/scanner')}>SCANNER</Link>
            <Link to="/evidence-web" className={getNavClass('/evidence-web')}>EVIDENCE WEB</Link>
            <Link to="/timeline" className={getNavClass('/timeline')}>TIMELINE</Link>
          </nav>

          {/* Verified Status Pill & Worker Avatar */}
          <div className="flex items-center gap-3 shrink-0">
            <div className="flex items-center gap-2 bg-[#0d0f0e] border border-[#242927] rounded-full px-3 py-1">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
              </span>
              <span className="font-mono-data text-[11px] font-semibold text-primary uppercase tracking-wider">92% VERIFIED</span>
            </div>
            <div className="w-8 h-8 rounded-full overflow-hidden border border-[#242927] p-0.5">
              <img 
                alt="Profile" 
                className="w-full h-full rounded-full object-cover grayscale brightness-90 hover:grayscale-0 transition-all duration-300" 
                src="https://lh3.googleusercontent.com/aida/AEtjO1UIkq6nGlB_ilLE8Xb75kgo-bP7UfGd5QN6BL-lnwhPAYEPeNsUYuw56iBhKINFsNabXsVvAsWWNCRjx6iuV5lKyVkhYoxDpCyKdi9p0t6zFZkmGVlkL7kDlmqmddpyOHQLjDRsLHhwwrvvn1Lap1QX9PZxHSmw2MU_weDILBm9VXyZLj9ISp6V0j07RbrzaMxUiNTDRpvz1AJRL5zMTAzzJxAuHFdBbcOpQVqkdTLMJGD0Gd-tQfRaFaHt" 
              />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="w-full pt-16 min-h-screen relative overflow-hidden flex flex-col items-center">
        {children}
      </main>

      {/* MINIMAL FOOTER */}
      <footer className="w-full bg-[#070808] border-t border-[#242927] py-6 select-none relative z-10">
        <div className="max-w-7xl mx-auto px-6 md:px-10 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="font-mono-data text-xs text-[#737A75] tracking-widest uppercase">PRAMAN // PORTABLE WORK IDENTITY</span>
          </div>
          <div className="flex items-center gap-2 border border-[#242927] bg-[#0d0f0e] px-3.5 py-1 rounded-full">
            <span className="material-symbols-outlined text-primary text-xs">lock</span>
            <span className="font-mono-data text-[10px] tracking-widest text-[#737A75] uppercase">CRYPTOGRAPHICALLY SEALED // NETWORK ACTIVE</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
