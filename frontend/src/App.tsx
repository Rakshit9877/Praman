import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import React, { Suspense } from 'react';

// Lazy loaded routes (will be implemented by other agents)
const WorkerHome = React.lazy(() => import('./features/worker/Home').catch(() => ({ default: () => <div>Worker Home Stub</div> })));
const VoiceFlow = React.lazy(() => import('./features/worker/VoiceFlow').catch(() => ({ default: () => <div>Voice Flow Stub</div> })));
const RegisterFlow = React.lazy(() => import('./features/worker/RegisterFlow').catch(() => ({ default: () => <div>Register Flow Stub</div> })));
const PassportView = React.lazy(() => import('./features/worker/PassportView').catch(() => ({ default: () => <div>Passport View Stub</div> })));

const AttestView = React.lazy(() => import('./features/attest/AttestView').catch(() => ({ default: () => <div>Attest View Stub</div> })));
const VerifyView = React.lazy(() => import('./features/verify/VerifyView').catch(() => ({ default: () => <div>Verify View Stub</div> })));

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<div className="flex items-center justify-center min-h-screen">Loading...</div>}>
        <Routes>
          <Route path="/" element={<Navigate to="/worker" replace />} />
          
          <Route path="/worker">
            <Route index element={<WorkerHome />} />
            <Route path="voice" element={<VoiceFlow />} />
            <Route path="register" element={<RegisterFlow />} />
            <Route path="passport" element={<PassportView />} />
          </Route>
          
          <Route path="/attest/:token" element={<AttestView />} />
          <Route path="/verify/:id" element={<VerifyView />} />
          
          <Route path="*" element={<div>404 Not Found</div>} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
