import React from 'react';

export function PageShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-50 flex justify-center">
      <div className="w-full max-w-md bg-white shadow-sm min-h-screen flex flex-col relative overflow-hidden">
        <main className="flex-1 flex flex-col">{children}</main>
      </div>
    </div>
  );
}
