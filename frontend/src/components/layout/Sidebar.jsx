import React from 'react';
import {
  LayoutDashboard,
  Users2,
  KanbanSquare,
  Clock,
  CheckSquare,
  Settings,
  ShieldCheck,
  Sparkles,
  Compass,
  CheckCircle2,
  LogOut,
} from 'lucide-react';
import { useAuth } from '../../auth/AuthContext';
import { getInitials } from '../../utils/formatters';

export function Sidebar({ currentRoute, onNavigate, stats }) {
  const { user, isAdmin, logout } = useAuth();

  const navigation = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'find-leads', label: 'Find Leads (Radar)', icon: Compass },
    { id: 'verified-leads', label: 'Verified Directory', icon: CheckCircle2, badge: stats?.verified_leads_count || null, badgeClass: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' },
    { id: 'leads', label: 'CRM Leads', icon: Users2, badge: stats?.active_opportunities },
    { id: 'pipeline', label: 'Sales Pipeline', icon: KanbanSquare },
    {
      id: 'follow-ups',
      label: 'Follow-ups',
      icon: Clock,
      badge: stats?.follow_ups_overdue ? `${stats.follow_ups_overdue}!` : null,
      badgeClass: 'bg-rose-500/20 text-rose-300 border-rose-500/30',
    },
    { id: 'tasks', label: 'Tasks', icon: CheckSquare },
    ...(isAdmin ? [{ id: 'users', label: 'Team & Roles', icon: ShieldCheck }] : []),
    { id: 'settings', label: 'Settings', icon: Settings },
  ];


  return (
    <aside className="w-64 bg-[#080c16] border-r border-slate-800/80 flex flex-col justify-between shrink-0 h-screen sticky top-0">
      <div className="p-4 space-y-6">
        <div className="flex items-center gap-3 px-2 py-1">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-blue-500/25 text-white font-extrabold text-lg font-heading">
            E
          </div>
          <div>
            <h1 className="text-sm font-extrabold text-white tracking-tight font-heading">
              Euroshub Sales
            </h1>
            <span className="text-[10px] text-slate-400 font-medium">Lead Intelligence Hub</span>
          </div>
        </div>

        <nav className="space-y-1">
          {navigation.map((item) => {
            const Icon = item.icon;
            const active = currentRoute === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                  active
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/25 font-bold'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/80'
                }`}
              >
                <Icon className={`w-4 h-4 shrink-0 ${active ? 'text-white' : 'text-slate-400'}`} />
                <span className="flex-1 text-left">{item.label}</span>
                {item.badge && (
                  <span
                    className={`px-1.5 py-0.5 rounded-md text-[10px] font-bold border ${
                      item.badgeClass || 'bg-slate-800 text-slate-300 border-slate-700'
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      <div className="p-4 border-t border-slate-800/80 space-y-3 bg-[#080c16]/50">
        <div className="flex items-center justify-between p-2 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 rounded-full bg-slate-800 text-slate-200 border border-slate-700 flex items-center justify-center font-bold text-xs shrink-0">
              {getInitials(user?.name)}
            </div>
            <div className="min-w-0">
              <p className="text-xs font-bold text-white truncate">{user?.name || 'Euroshub Member'}</p>
              <span className="text-[10px] text-purple-400 font-semibold capitalize block">
                {isAdmin ? '👑 Admin' : '💼 Employee'}
              </span>
            </div>
          </div>

          <button
            onClick={logout}
            title="Log out"
            className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-slate-800 transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
