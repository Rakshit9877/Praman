import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import React, { Suspense } from 'react';
import { Layout } from './components/Layout';

// Lazy loaded routes
const ProductHero = React.lazy(() => import('./features/worker/ProductHero').then(m => ({ default: m.ProductHero })));
const PassportView = React.lazy(() => import('./features/worker/PassportView').then(m => ({ default: m.PassportView })));
const ProofChainView = React.lazy(() => import('./features/verify/ProofChainView').then(m => ({ default: m.ProofChainView })));
const TimelineView = React.lazy(() => import('./features/verify/TimelineView').then(m => ({ default: m.TimelineView })));
const ScannerView = React.lazy(() => import('./features/attest/ScannerView').then(m => ({ default: m.ScannerView })));
const EvidenceWebView = React.lazy(() => import('./features/verify/EvidenceWebView').then(m => ({ default: m.EvidenceWebView })));

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Suspense fallback={<div className="flex items-center justify-center min-h-screen text-primary font-mono-data tracking-widest text-xs">INITIALIZING SECURE ENCLAVE...</div>}>
          <Routes>
            <Route path="/" element={<ProductHero />} />
            <Route path="/passport" element={<PassportView />} />
            <Route path="/proof-chain" element={<ProofChainView />} />
            <Route path="/timeline" element={<TimelineView />} />
            <Route path="/scanner" element={<ScannerView />} />
            <Route path="/evidence-web" element={<EvidenceWebView />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
