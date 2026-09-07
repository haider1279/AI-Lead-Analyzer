import React, { useState, useEffect, useCallback } from 'react';
import { AuthProvider, useAuth } from './auth/AuthContext';
import { ProtectedRoute } from './auth/ProtectedRoute';
import { MainLayout } from './components/layout/MainLayout';

// Pages
import { Login } from './pages/Login';
import { SignUp } from './pages/SignUp';
import { Dashboard } from './pages/Dashboard';
import { FindLeads } from './pages/FindLeads';
import { VerifiedLeads } from './pages/VerifiedLeads';
import { Leads } from './pages/Leads';
import { LeadDetail } from './pages/LeadDetail';
import { Pipeline } from './pages/Pipeline';
import { FollowUps } from './pages/FollowUps';
import { Tasks } from './pages/Tasks';
import { Reports } from './pages/Reports';
import { Settings } from './pages/Settings';
import { Users } from './pages/Users';
import { api } from './services/api';

// ─── Route Titles ─────────────────────────────────────────────────────────────

const ROUTE_TITLES = {
  dashboard: 'Dashboard',
  'find-leads': 'Find Leads · Radar',
  'verified-leads': 'Verified Directory',
  leads: 'CRM Leads',
  pipeline: 'Sales Pipeline',
  'follow-ups': 'Follow-ups',
  tasks: 'Tasks',
  reports: 'Reports & Analytics',
  users: 'Team Management',
  settings: 'Settings',
};

// ─── Inner App (has auth context) ────────────────────────────────────────────

function AppInner() {
  const { user, loading } = useAuth();
  const [route, setRoute] = useState('dashboard');
  const [selectedLeadId, setSelectedLeadId] = useState(null);
  const [stats, setStats] = useState(null);
  const [openAddLead, setOpenAddLead] = useState(false);

  // Determine initial route from hash
  useEffect(() => {
    const hash = window.location.hash.replace('#/', '').replace('#', '');
    if (hash === 'login' || hash === 'signup') {
      setRoute(hash);
    } else if (hash && ROUTE_TITLES[hash]) {
      setRoute(hash);
    }
  }, []);

  // Sync hash to route
  useEffect(() => {
    window.location.hash = `#/${route}`;
  }, [route]);

  // Fetch dashboard stats for sidebar badges
  const fetchStats = useCallback(async () => {
    if (!user) return;
    try {
      const data = await api.dashboard.getStats();
      setStats(data);
    } catch {
      // Non-critical
    }
  }, [user]);

  useEffect(() => {
    fetchStats();
    // Refresh every 3 minutes
    const interval = setInterval(fetchStats, 3 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchStats]);

  const navigate = useCallback((newRoute) => {
    setSelectedLeadId(null);
    setOpenAddLead(false);
    setRoute(newRoute);
  }, []);

  const selectLead = useCallback((leadId) => {
    setSelectedLeadId(leadId);
    setRoute('lead-detail');
  }, []);

  // Loading state
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

  // Auth pages (no layout)
  if (!user || route === 'login' || route === 'signup') {
    if (route === 'signup') {
      return (
        <SignUp
          onNavigateLogin={() => navigate('login')}
          onSignUpSuccess={() => navigate('dashboard')}
        />
      );
    }
    return (
      <Login
        onNavigateSignUp={() => navigate('signup')}
        onLoginSuccess={() => navigate('dashboard')}
      />
    );
  }

  // Authenticated: render with layout
  const title = route === 'lead-detail' ? 'Lead Detail' : (ROUTE_TITLES[route] || 'Euroshub');

  return (
    <ProtectedRoute>
      <MainLayout
        currentRoute={route}
        onNavigate={navigate}
        title={title}
        onOpenAddLead={() => { navigate('leads'); setOpenAddLead(true); }}
        stats={stats}
      >
        {route === 'dashboard' && (
          <Dashboard onNavigate={navigate} onSelectLead={selectLead} />
        )}

        {route === 'find-leads' && (
          <FindLeads onNavigate={navigate} />
        )}

        {route === 'verified-leads' && (
          <VerifiedLeads onSelectLead={selectLead} onNavigate={navigate} />
        )}

        {route === 'leads' && (
          <Leads onSelectLead={selectLead} initialOpenAdd={openAddLead} />
        )}

        {route === 'lead-detail' && selectedLeadId && (
          <LeadDetail
            leadId={selectedLeadId}
            onBack={() => navigate('leads')}
            onNavigate={navigate}
          />
        )}

        {route === 'pipeline' && (
          <Pipeline onSelectLead={selectLead} onNavigate={navigate} />
        )}

        {route === 'follow-ups' && (
          <FollowUps onSelectLead={selectLead} />
        )}

        {route === 'tasks' && (
          <Tasks onSelectLead={selectLead} />
        )}

        {route === 'reports' && (
          <Reports onNavigate={navigate} />
        )}

        {route === 'users' && (
          <ProtectedRoute requireAdmin={false}>
            <Users />
          </ProtectedRoute>
        )}

        {route === 'settings' && (
          <Settings onNavigate={navigate} />
        )}
      </MainLayout>
    </ProtectedRoute>
  );
}

// ─── App Root ─────────────────────────────────────────────────────────────────

export default function App() {
  return (
    <AuthProvider>
      <AppInner />
    </AuthProvider>
  );
}
