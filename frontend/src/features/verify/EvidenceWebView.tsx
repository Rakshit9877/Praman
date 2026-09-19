import { useState } from 'react';

export function EvidenceWebView() {
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  const handleNodeClick = (nodeId: string) => {
    setSelectedNode(nodeId);
  };

  const closeNodeInfo = () => {
    setSelectedNode(null);
  };

  return (
    <>
      {/* Background Mesh */}
      <div className="absolute inset-0 pointer-events-none opacity-[0.08] [background-image:radial-gradient(#242927_1px,transparent_1px)] [background-size:32px_32px]"></div>

      {/* Screen Layout: Split Panel */}
      <div className="w-full flex-1 flex flex-col lg:flex-row relative z-10 h-[calc(100vh-130px)]">
        
        {/* LEFT/TOP PANEL: The Constellation Canvas */}
        <div className="w-full lg:flex-1 relative border-b lg:border-b-0 lg:border-r border-[#242927] h-[50vh] lg:h-full bg-[#040505] overflow-hidden select-none">
          
          <div className="absolute top-6 left-6 z-20">
            <h2 className="font-display-hero text-2xl font-semibold text-white uppercase tracking-tight">MACRO NETWORK VIEW</h2>
            <p className="font-mono-data text-[10px] text-primary tracking-widest mt-1 uppercase">370 ACTIVE NODES // SECTOR 44</p>
          </div>

          <div className="absolute top-6 right-6 z-20 flex gap-2">
            <button className="w-8 h-8 bg-white/5 border border-white/10 rounded flex items-center justify-center text-white hover:bg-white/10 cursor-pointer">
              <span className="material-symbols-outlined text-sm">zoom_in</span>
            </button>
            <button className="w-8 h-8 bg-white/5 border border-white/10 rounded flex items-center justify-center text-white hover:bg-white/10 cursor-pointer">
              <span className="material-symbols-outlined text-sm">zoom_out</span>
            </button>
          </div>

          {/* THE SVG GRAPH VIEW */}
          <div className="absolute inset-0 flex items-center justify-center cursor-grab active:cursor-grabbing">
            <svg className="w-full h-full min-w-[800px] min-h-[600px] scale-[1.1]" viewBox="0 0 1000 800">
              {/* Edges */}
              <g stroke="#242927" strokeWidth="1.5">
                <line x1="500" x2="300" y1="400" y2="250"></line>
                <line x1="500" x2="700" y1="400" y2="220"></line>
                <line x1="500" x2="250" y1="400" y2="550"></line>
                <line x1="500" x2="650" y1="400" y2="600"></line>
                <line x1="300" x2="200" y1="250" y2="150"></line>
                <line x1="300" x2="150" y1="250" y2="350"></line>
                <line x1="700" x2="850" y1="220" y2="180"></line>
                <line x1="700" x2="800" y1="220" y2="380"></line>
                <line className="animate-flow-emerald" stroke="#79D6A3" strokeWidth="2" x1="500" x2="800" y1="400" y2="380"></line>
                <line x1="250" x2="150" y1="550" y2="480"></line>
                <line x1="250" x2="280" y1="550" y2="700"></line>
                <line className="animate-flow-terracotta" stroke="#E76F51" strokeWidth="2" x1="250" x2="150" y1="550" y2="480"></line>
                <line x1="650" x2="800" y1="600" y2="550"></line>
                <line x1="650" x2="580" y1="600" y2="720"></line>
              </g>

              {/* Nodes */}
              <g>
                <circle className="cursor-pointer transition-transform hover:scale-125 hover:fill-primary" cx="200" cy="150" fill="#E76F51" r="10"></circle>
                <circle className="cursor-pointer transition-transform hover:scale-125 hover:fill-primary" cx="150" cy="350" fill="#5E6561" r="8"></circle>
                
                <circle className="cursor-pointer transition-transform hover:scale-125 hover:fill-primary" cx="300" cy="250" fill="#79D6A3" onClick={() => handleNodeClick('agency-01')} r="16"></circle>
                
                <circle className="cursor-pointer transition-transform hover:scale-125 hover:fill-primary" cx="850" cy="180" fill="#5E6561" r="9"></circle>
                <circle className="cursor-pointer transition-transform hover:scale-125 hover:fill-primary" cx="800" cy="380" fill="#79D6A3" onClick={() => handleNodeClick('rahul')} r="14"></circle>
                <circle className="cursor-pointer transition-transform hover:scale-125 hover:fill-primary" cx="700" cy="220" fill="#5E6561" r="18"></circle>

                <circle className="cursor-pointer transition-transform hover:scale-125 hover:fill-primary" cx="150" cy="480" fill="#E76F51" r="12"></circle>
                <circle className="cursor-pointer transition-transform hover:scale-125 hover:fill-primary" cx="280" cy="700" fill="#5E6561" r="7"></circle>
                <circle className="cursor-pointer transition-transform hover:scale-125 hover:fill-primary" cx="250" cy="550" fill="#79D6A3" r="14"></circle>

                <circle className="cursor-pointer transition-transform hover:scale-125 hover:fill-primary" cx="800" cy="550" fill="#79D6A3" r="11"></circle>
                <circle className="cursor-pointer transition-transform hover:scale-125 hover:fill-primary" cx="580" cy="720" fill="#5E6561" r="15"></circle>
                <circle className="cursor-pointer transition-transform hover:scale-125 hover:fill-primary" cx="650" cy="600" fill="#E76F51" r="16"></circle>

                <g className="cursor-pointer" onClick={() => handleNodeClick('dlf')}>
                  <circle cx="500" cy="400" fill="#121413" r="28" stroke="#79D6A3" strokeWidth="2"></circle>
                  <circle className="animate-ping opacity-30" cx="500" cy="400" fill="#79D6A3" r="28"></circle>
                  <text fill="#fff" fontFamily="JetBrains Mono" fontSize="10" textAnchor="middle" x="500" y="404">DLF</text>
                </g>
              </g>

              {/* Labels (Visible on hover state in real app, static here for UI) */}
              <g className="pointer-events-none" fill="#737A75" fontFamily="Inter" fontSize="11" letterSpacing="0.05em">
                <text x="325" y="254">L&amp;T Agency</text>
                <text fill="#79D6A3" x="820" y="384">R. Kumar</text>
                <text x="725" y="224">Site 4</text>
              </g>
            </svg>
          </div>

          <div className="absolute bottom-6 left-6 z-20 flex gap-4 font-mono-data text-[9px] text-[#737A75] uppercase">
            <div className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-[#79D6A3]"></span> Verified / Active</div>
            <div className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-[#E76F51]"></span> Flagged / Disputed</div>
            <div className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-[#5E6561]"></span> Pending Sync</div>
          </div>
        </div>

        {/* RIGHT/BOTTOM PANEL: Details Inspector */}
        <div className={`w-full lg:w-[420px] shrink-0 bg-[#070808] h-[50vh] lg:h-full flex flex-col border-l border-white/5 transition-transform duration-300 ${selectedNode ? 'translate-x-0' : 'translate-x-full lg:translate-x-0 opacity-50 pointer-events-none lg:opacity-100 lg:pointer-events-auto'}`}>
          <div className="p-6 border-b border-[#242927] flex justify-between items-center bg-[#0d0f0e]">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-sm text-primary">data_object</span>
              <span className="font-mono-data text-xs uppercase tracking-widest text-white">NODE INSPECTOR</span>
            </div>
            {selectedNode && (
              <button onClick={closeNodeInfo} className="lg:hidden text-white/50 hover:text-white cursor-pointer">
                <span className="material-symbols-outlined">close</span>
              </button>
            )}
          </div>
          
          <div className="p-6 flex-1 overflow-y-auto">
            {selectedNode === 'rahul' ? (
              <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
                <div>
                  <h3 className="font-display-hero text-3xl font-medium text-white uppercase tracking-tight">R. KUMAR</h3>
                  <p className="font-mono-data text-[10px] text-[#737A75] uppercase mt-1">DID:IN//9032-B • MASTER MASON</p>
                </div>
                
                <div className="bg-[#121413] border border-white/5 rounded-lg p-4">
                  <h4 className="font-mono-data text-[9px] text-[#737A75] uppercase tracking-widest mb-3">CONNECTION METRICS</h4>
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-body-sm text-xs text-white">Direct Employers</span>
                    <span className="font-mono-data text-xs text-primary">6 Nodes</span>
                  </div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-body-sm text-xs text-white">Co-workers Attested</span>
                    <span className="font-mono-data text-xs text-primary">14 Nodes</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="font-body-sm text-xs text-white">Centrality Score</span>
                    <span className="font-mono-data text-xs text-white">0.84 (High)</span>
                  </div>
                </div>

                <div>
                  <h4 className="font-mono-data text-[9px] text-[#737A75] uppercase tracking-widest mb-3">RECENT EDGES (TRANSACTIONS)</h4>
                  <div className="flex gap-3 mb-3 pb-3 border-b border-white/5">
                    <span className="material-symbols-outlined text-primary text-base">arrow_right_alt</span>
                    <div>
                      <div className="font-body-sm text-xs text-white">DLF Projects Ltd.</div>
                      <div className="font-mono-data text-[9px] text-[#737A75] mt-1">Shift Payment • 2024.09.12</div>
                    </div>
                  </div>
                  <div className="flex gap-3 mb-3 pb-3 border-b border-white/5">
                    <span className="material-symbols-outlined text-primary text-base">sync_alt</span>
                    <div>
                      <div className="font-body-sm text-xs text-white">S. Patel (Supervisor)</div>
                      <div className="font-mono-data text-[9px] text-[#737A75] mt-1">Mutual Attestation • 2024.09.10</div>
                    </div>
                  </div>
                </div>
              </div>
            ) : selectedNode === 'dlf' ? (
              <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
                <div>
                  <h3 className="font-display-hero text-3xl font-medium text-white uppercase tracking-tight">DLF PROJECTS</h3>
                  <p className="font-mono-data text-[10px] text-primary uppercase mt-1">ENTERPRISE ANCHOR NODE</p>
                </div>
                <div className="bg-[#121413] border border-white/5 rounded-lg p-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-body-sm text-xs text-white">Total Active Workers</span>
                    <span className="font-mono-data text-xs text-primary">3,492</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="font-body-sm text-xs text-white">Compliance Score</span>
                    <span className="font-mono-data text-xs text-white">99.8%</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-[#737A75] opacity-60">
                <span className="material-symbols-outlined text-4xl mb-3">touch_app</span>
                <span className="font-mono-data text-[10px] uppercase tracking-widest text-center">Select a node on the canvas<br/>to inspect connections.</span>
              </div>
            )}
          </div>
          
          <div className="p-4 border-t border-[#242927] bg-[#070808]">
            <button className="w-full h-10 bg-white/5 hover:bg-white/10 text-white font-mono-data text-[10px] tracking-widest uppercase transition-colors rounded">
              EXPORT GRAPH DATA
            </button>
          </div>
        </div>

      </div>
    </>
  );
}
