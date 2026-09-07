import React, { useState, useEffect } from 'react';
import {
  DollarSign,
  TrendingUp,
  FileText,
  Clock,
  ArrowUpRight,
  Flame,
  ChevronRight,
  AlertCircle,
  ShieldCheck,
  Compass,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  CartesianGrid,
} from 'recharts';
import { api } from '../services/api';
import { formatCurrency, formatDate, getInitials } from '../utils/formatters';
import { StatusBadge } from '../components/leads/StatusBadge';
import { FollowUpIndicator } from '../components/leads/FollowUpIndicator';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { Button } from '../components/common/Button';

const STATUS_COLORS = {
  NEW: '#3b82f6',
  CONTACTED: '#6366f1',
  QUALIFIED: '#06b6d4',
  PROPOSAL_SENT: '#a855f7',
  NEGOTIATION: '#f59e0b',
  WON: '#10b981',
  LOST: '#f43f5e',
};

const PIE_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#ec4899', '#64748b', '#14b8a6'];

export function Dashboard({ onNavigate, onSelectLead }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.dashboard.getStats();
      setStats(data);
    } catch (err) {
      setError(err.message || 'Failed to load dashboard statistics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  if (loading) {
    return <LoadingSpinner text="Computing pipeline metrics & KPI analytics..." size="lg" />;
  }

  if (error || !stats) {
    return (
      <div className="p-6 glass-card rounded-2xl border border-rose-500/30 text-center my-6">
        <AlertCircle className="w-8 h-8 text-rose-400 mx-auto mb-2" />
        <h3 className="text-base font-bold text-white mb-1">Failed to load metrics</h3>
        <p className="text-xs text-slate-400 mb-4">{error}</p>
        <Button variant="primary" size="sm" onClick={fetchStats}>
          Retry
        </Button>
      </div>
    );
  }

  const kpis = [
    {
      label: 'Total Pipeline Value',
      value: formatCurrency(stats.total_pipeline_value),
      subtext: `${stats.active_opportunities || 0} active opportunities`,
      icon: DollarSign,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10 border-emerald-500/20',
    },
    {
      label: 'Conversion Rate',
      value: `${stats.conversion_rate || 0}%`,
      subtext: `${stats.won_leads || 0} won vs ${stats.lost_leads || 0} lost`,
      icon: TrendingUp,
      color: 'text-blue-400',
      bg: 'bg-blue-500/10 border-blue-500/20',
    },
    {
      label: 'Proposals & Negotiation',
      value: (stats.proposals_sent || 0) + (stats.negotiation || 0),
      subtext: `${stats.proposals_sent || 0} proposals sent • ${stats.negotiation || 0} in review`,
      icon: FileText,
      color: 'text-purple-400',
      bg: 'bg-purple-500/10 border-purple-500/20',
    },
    {
      label: 'Overdue Follow-ups',
      value: stats.follow_ups_overdue || 0,
      subtext: `${stats.follow_ups_today || 0} due today`,
      icon: Clock,
      color: (stats.follow_ups_overdue || 0) > 0 ? 'text-rose-400' : 'text-slate-400',
      bg: (stats.follow_ups_overdue || 0) > 0 ? 'bg-rose-500/10 border-rose-500/20' : 'bg-slate-800/40 border-slate-800',
    },
    {
      label: 'Verified Lead Integrity',
      value: `${stats.verification_rate || 0}%`,
      subtext: `${stats.verified_leads_count || 0} accepted (70%+)`,
      icon: ShieldCheck,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10 border-emerald-500/20',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Verified Discovery Banner */}
      <div className="p-4 rounded-2xl glass-panel border border-blue-500/20 bg-gradient-to-r from-blue-950/40 via-indigo-950/20 to-slate-900/60 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-500/20 border border-blue-500/30 flex items-center justify-center text-blue-400 shrink-0">
            <Compass className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-white tracking-tight font-heading">
              AI Verified Lead Discovery Platform Active
            </h4>
            <p className="text-[11px] text-slate-400">
              Import custom datasets, execute DNS/MX verification, and discover high-value prospects worldwide.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onNavigate('verified-leads')}
            className="text-xs border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/10"
          >
            <ShieldCheck className="w-3.5 h-3.5 mr-1.5" />
            Verified Directory
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => onNavigate('find-leads')}
            className="text-xs"
          >
            <Compass className="w-3.5 h-3.5 mr-1.5" />
            Find Leads Radar
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {kpis.map((kpi, idx) => {
          const Icon = kpi.icon;
          return (
            <div
              key={idx}
              className="glass-card p-4 rounded-2xl border border-slate-800/90 relative overflow-hidden transition-all hover:border-slate-700"
            >
              <div className="flex items-center justify-between gap-2 mb-2">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider truncate">
                  {kpi.label}
                </span>
                <div className={`w-7 h-7 rounded-lg flex items-center justify-center border ${kpi.bg} ${kpi.color} shrink-0`}>
                  <Icon className="w-3.5 h-3.5" />
                </div>
              </div>
              <div className="text-xl font-extrabold text-white font-heading tracking-tight mb-0.5">
                {kpi.value}
              </div>
              <p className="text-[10px] text-slate-500 font-medium truncate">{kpi.subtext}</p>
            </div>
          );
        })}
      </div>


      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass-card p-6 rounded-2xl border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-sm font-bold text-white tracking-tight">Pipeline Funnel by Stage</h3>
              <p className="text-xs text-slate-400">Opportunity volume and deal value across lifecycle</p>
            </div>
            <button
              onClick={() => onNavigate('pipeline')}
              className="text-xs font-semibold text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors"
            >
              <span>View Kanban</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.leads_by_status || []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="status" stroke="#64748b" fontSize={10} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={10} tickLine={false} allowDecimals={false} />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="p-3 rounded-xl bg-slate-900 border border-slate-700 shadow-xl text-xs space-y-1">
                          <p className="font-bold text-white">{data.status}</p>
                          <p className="text-blue-400 font-semibold">Count: {data.count} leads</p>
                          <p className="text-emerald-400 font-semibold">Value: {formatCurrency(data.value)}</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {stats.leads_by_status?.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={STATUS_COLORS[entry.status] || '#3b82f6'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-card p-6 rounded-2xl border border-slate-800 flex flex-col justify-between">
          <div className="mb-4">
            <h3 className="text-sm font-bold text-white tracking-tight">Acquisition by Source</h3>
            <p className="text-xs text-slate-400">Inbound channel breakdown</p>
          </div>

          <div className="h-52 w-full relative flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={stats.leads_by_source || []}
                  dataKey="count"
                  nameKey="source"
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={3}
                >
                  {stats.leads_by_source?.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-700 shadow-xl text-xs">
                          <p className="font-bold text-white">{data.source}</p>
                          <p className="text-slate-300">{data.count} leads ({formatCurrency(data.value)})</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="flex flex-wrap gap-2 justify-center pt-2">
            {stats.leads_by_source?.slice(0, 5).map((s, idx) => (
              <div key={idx} className="flex items-center gap-1.5 text-[11px] text-slate-400">
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: PIE_COLORS[idx % PIE_COLORS.length] }} />
                <span>{s.source} ({s.count})</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-amber-400" />
              <h3 className="text-sm font-bold text-white tracking-tight">Urgent Follow-ups Radar</h3>
            </div>
            <button
              onClick={() => onNavigate('follow-ups')}
              className="text-xs font-semibold text-blue-400 hover:text-blue-300 flex items-center gap-1"
            >
              <span>View All</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {stats.urgent_follow_ups?.length > 0 ? (
            <div className="space-y-2.5">
              {stats.urgent_follow_ups.map((lead) => (
                <div
                  key={lead.id}
                  onClick={() => onSelectLead(lead.id)}
                  className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 flex items-center justify-between cursor-pointer transition-all group"
                >
                  <div className="min-w-0 pr-3">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="text-xs font-bold text-white truncate group-hover:text-blue-400 transition-colors">
                        {lead.company_name}
                      </h4>
                      <StatusBadge status={lead.status} />
                    </div>
                    <p className="text-[11px] text-slate-400 truncate">
                      {lead.project_title || 'Software Opportunity'}
                    </p>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <FollowUpIndicator dateString={lead.follow_up_date} />
                    <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-slate-300 transition-colors" />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-500 text-xs">
              🎉 Great job! No overdue or pending follow-ups scheduled for today.
            </div>
          )}
        </div>

        <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Flame className="w-4 h-4 text-orange-400" />
              <h3 className="text-sm font-bold text-white tracking-tight">Live Activity Log</h3>
            </div>
            <button
              onClick={() => onNavigate('leads')}
              className="text-xs font-semibold text-blue-400 hover:text-blue-300 flex items-center gap-1"
            >
              <span>Explore Leads</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {stats.recent_activities?.length > 0 ? (
            <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
              {stats.recent_activities.map((act) => (
                <div
                  key={act.id}
                  onClick={() => onSelectLead(act.lead_id)}
                  className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 flex items-start gap-3 cursor-pointer transition-all group"
                >
                  <div className="w-7 h-7 rounded-lg bg-slate-800 text-slate-300 flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
                    {getInitials(act.user?.name)}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2 mb-0.5">
                      <span className="text-xs font-bold text-white group-hover:text-blue-400 transition-colors truncate">
                        {act.lead_company_name ? `${act.lead_company_name}: ` : ''}{act.title}
                      </span>
                      <span className="text-[10px] text-slate-500 shrink-0">{formatDate(act.activity_date)}</span>
                    </div>
                    {act.description && (
                      <p className="text-[11px] text-slate-400 line-clamp-1">{act.description}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-500 text-xs">
              No recent activities recorded yet.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
