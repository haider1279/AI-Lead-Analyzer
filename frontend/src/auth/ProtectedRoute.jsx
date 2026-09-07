import React from 'react';
import { useAuth } from './AuthContext';

export function ProtectedRoute({ children, requireAdmin = false }) {
  const { user, loading, isAdmin } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0b0f19]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
          <p className="text-slate-400 text-sm font-medium">Loading Euroshub Sales Hub...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    // If no user, show login prompt or redirect
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0b0f19] px-4">
        <div className="glass-card p-8 rounded-2xl max-w-md w-full text-center border border-slate-800">
          <h2 className="text-xl font-bold text-white mb-2">Session Expired or Required</h2>
          <p className="text-slate-400 text-sm mb-6">Please sign in to access Euroshub Lead Management.</p>
          <a
            href="#/login"
            className="inline-block px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold rounded-xl shadow-lg shadow-blue-500/25 transition-all"
          >
            Go to Login
          </a>
        </div>
      </div>
    );
  }

  if (requireAdmin && !isAdmin) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center px-4">
        <div className="glass-card p-8 rounded-2xl max-w-md text-center border border-slate-800">
          <div className="w-12 h-12 rounded-2xl bg-rose-500/10 text-rose-400 flex items-center justify-center mx-auto mb-4">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h3 className="text-lg font-bold text-white mb-2">Access Restricted</h3>
          <p className="text-slate-400 text-sm mb-6">
            This area requires Administrator permissions. Your current role is <b>{user.role}</b>.
          </p>
          <button
            onClick={() => window.history.back()}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-lg transition-all"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return children;
}
