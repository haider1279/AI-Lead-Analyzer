import React, { useState, useEffect } from 'react';
import {
  CheckCircle,
} from 'lucide-react';
import { api } from '../services/api';
import { getFollowUpState, getInitials, formatCurrency } from '../utils/formatters';
import { StatusBadge } from '../components/leads/StatusBadge';
import { PriorityBadge } from '../components/leads/PriorityBadge';
import { FollowUpIndicator } from '../components/leads/FollowUpIndicator';
import { AddActivityModal } from '../components/activities/AddActivityModal';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { EmptyState } from '../components/common/EmptyState';
import { Button } from '../components/common/Button';

export function FollowUps({ onSelectLead }) {
  const [leads, setLeads] = useState([]);
  const [users, setUsers] = useState([]);
  const [activeTab, setActiveTab] = useState('all');
  const [assigneeFilter, setAssigneeFilter] = useState('');
  const [loading, setLoading] = useState(true);

  const [selectedLeadId, setSelectedLeadId] = useState(null);
  const [activityOpen, setActivityOpen] = useState(false);

  const fetchLeads = async () => {
    setLoading(true);
    try {
      const [leadsData, usersData] = await Promise.all([
        api.leads.list(),
        api.auth.getUsers().catch(() => []),
      ]);
      setLeads(leadsData);
      setUsers(usersData);
    } catch (err) {
      alert(err.message || 'Failed to load follow-ups.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeads();
  }, []);

  const activeFollowUpLeads = leads
    .filter((l) => l.follow_up_date && l.status !== 'WON' && l.status !== 'LOST')
    .filter((l) => (!assigneeFilter ? true : String(l.assigned_to) === String(assigneeFilter)))
    .map((l) => {
      const stateObj = getFollowUpState(l.follow_up_date);
      return { ...l, followUpState: stateObj?.state };
    });

  const overdueList = activeFollowUpLeads.filter((l) => l.followUpState === 'overdue');
  const todayList = activeFollowUpLeads.filter((l) => l.followUpState === 'today');
  const upcomingList = activeFollowUpLeads.filter((l) => l.followUpState === 'upcoming');

  const displayedList =
    activeTab === 'overdue'
      ? overdueList
      : activeTab === 'today'
      ? todayList
      : activeTab === 'upcoming'
      ? upcomingList
      : activeFollowUpLeads;

  const handleMarkComplete = async (leadId) => {
    try {
      await api.leads.update(leadId, { follow_up_date: null });
      setLeads((prev) =>
        prev.map((l) => (l.id === leadId ? { ...l, follow_up_date: null } : l))
      );
      setSelectedLeadId(leadId);
      setActivityOpen(true);
    } catch (err) {
      alert(err.message || 'Failed to complete follow up.');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 glass-card p-4 rounded-2xl border border-slate-800">
        <div>
          <h2 className="text-base font-bold text-white tracking-tight">Follow-ups Radar</h2>
          <p className="text-xs text-slate-400">
            Track upcoming, scheduled, and overdue client touchpoints
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-400 font-medium">Filter Assignee:</span>
          <select
            value={assigneeFilter}
            onChange={(e) => setAssigneeFilter(e.target.value)}
            className="bg-slate-900 border border-slate-800 text-slate-300 rounded-xl px-3 py-1.5 outline-none"
          >
            <option value="">All Employees</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>
                {u.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <button
          onClick={() => setActiveTab('all')}
          className={`p-4 rounded-2xl border text-left transition-all ${
            activeTab === 'all'
              ? 'bg-blue-600/15 text-blue-400 border-blue-500/30'
              : 'glass-card text-slate-400 border-slate-800 hover:border-slate-700'
          }`}
        >
          <span className="text-[11px] font-bold uppercase tracking-wider block mb-1">All Scheduled</span>
          <span className="text-2xl font-extrabold text-white font-heading">
            {activeFollowUpLeads.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab('overdue')}
          className={`p-4 rounded-2xl border text-left transition-all ${
            activeTab === 'overdue'
              ? 'bg-rose-600/15 text-rose-400 border-rose-500/30'
              : 'glass-card text-slate-400 border-slate-800 hover:border-slate-700'
          }`}
        >
          <div className="flex items-center justify-between mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider block text-rose-400">🔴 Overdue</span>
          </div>
          <span className="text-2xl font-extrabold text-rose-400 font-heading">
            {overdueList.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab('today')}
          className={`p-4 rounded-2xl border text-left transition-all ${
            activeTab === 'today'
              ? 'bg-amber-600/15 text-amber-400 border-amber-500/30'
              : 'glass-card text-slate-400 border-slate-800 hover:border-slate-700'
          }`}
        >
          <div className="flex items-center justify-between mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider block text-amber-400">🟡 Due Today</span>
          </div>
          <span className="text-2xl font-extrabold text-amber-400 font-heading">
            {todayList.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab('upcoming')}
          className={`p-4 rounded-2xl border text-left transition-all ${
            activeTab === 'upcoming'
              ? 'bg-emerald-600/15 text-emerald-400 border-emerald-500/30'
              : 'glass-card text-slate-400 border-slate-800 hover:border-slate-700'
          }`}
        >
          <div className="flex items-center justify-between mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider block text-emerald-400">🟢 Upcoming</span>
          </div>
          <span className="text-2xl font-extrabold text-emerald-400 font-heading">
            {upcomingList.length}
          </span>
        </button>
      </div>

      {loading ? (
        <LoadingSpinner text="Analyzing follow-up schedules..." size="md" />
      ) : displayedList.length === 0 ? (
        <EmptyState
          title="No follow-ups in this radar state"
          description="All scheduled touchpoints are in sync! Check the other tabs or schedule new follow-ups on active leads."
        />
      ) : (
        <div className="space-y-3">
          {displayedList.map((lead) => (
            <div
              key={lead.id}
              className="glass-card p-4 rounded-2xl border border-slate-800 hover:border-slate-700 flex flex-wrap items-center justify-between gap-4 transition-all"
            >
              <div className="min-w-0 max-w-lg">
                <div className="flex items-center gap-2 mb-1">
                  <button
                    onClick={() => onSelectLead(lead.id)}
                    className="text-xs font-bold text-white hover:text-blue-400 transition-colors truncate"
                  >
                    {lead.company_name}
                  </button>
                  <StatusBadge status={lead.status} />
                  <PriorityBadge priority={lead.priority} />
                </div>

                <p className="text-[11px] text-slate-400 truncate">
                  {lead.project_title || 'Software Opportunity'} • {lead.contact_name || 'Client stakeholder'} • {formatCurrency(lead.budget, lead.currency)}
                </p>
              </div>

              <div className="flex items-center gap-3 text-xs shrink-0">
                <FollowUpIndicator dateString={lead.follow_up_date} />

                {lead.assigned_user && (
                  <div className="hidden sm:flex items-center gap-1.5 text-slate-400 text-[11px]">
                    <div className="w-5 h-5 rounded-full bg-slate-800 text-slate-300 flex items-center justify-center text-[10px] font-bold">
                      {getInitials(lead.assigned_user.name)}
                    </div>
                    <span>{lead.assigned_user.name}</span>
                  </div>
                )}

                <Button
                  variant="emerald"
                  size="sm"
                  onClick={() => handleMarkComplete(lead.id)}
                  icon={CheckCircle}
                >
                  Complete & Log
                </Button>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onSelectLead(lead.id)}
                >
                  View Lead
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedLeadId && (
        <AddActivityModal
          isOpen={activityOpen}
          onClose={() => {
            setActivityOpen(false);
            setSelectedLeadId(null);
          }}
          leadId={selectedLeadId}
          onSuccess={() => {
            fetchLeads();
          }}
        />
      )}
    </div>
  );
}
