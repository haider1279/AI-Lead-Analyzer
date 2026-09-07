import React from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

export function MainLayout({
  children,
  currentRoute,
  onNavigate,
  title,
  onOpenAddLead,
  stats,
}) {
  return (
    <div className="flex min-h-screen bg-[#080c16] text-slate-100 selection:bg-blue-600 selection:text-white">
      <Sidebar
        currentRoute={currentRoute}
        onNavigate={onNavigate}
        stats={stats}
      />

      <div className="flex-1 flex flex-col min-w-0">
        <Header
          title={title}
          onOpenAddLead={onOpenAddLead}
          stats={stats}
        />

        <main className="flex-1 p-8 max-w-7xl w-full mx-auto animate-fadeIn">
          {children}
        </main>
      </div>
    </div>
  );
}
