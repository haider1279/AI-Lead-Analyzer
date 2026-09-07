import React, { useState, useEffect } from 'react';
import {
  Plus,
} from 'lucide-react';
import { api } from '../services/api';
import { formatCurrency, getInitials } from '../utils/formatters';
import { PriorityBadge } from '../components/leads/PriorityBadge';
import { FollowUpIndicator } from '../components/leads/FollowUpIndicator';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { LeadFormModal } from '../components/leads/LeadFormModal';
import { PIPELINE_STATUSES } from '../utils/constants';

export function Pipeline({ onSelectLead }) {
  const [leads, setLeads] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [movingId, setMovingId] = useState(null);
  const [addModalOpen, setAddModalOpen] = useState(false);

  const fetchPipeline = async () => {
    setLoading(true);
    try {
      const [leadsData, usersData] = await Promise.all([
        api.leads.list(),
        api.auth.getUsers().catch(() => []),
      ]);
      setLeads(leadsData);
      setUsers(usersData);
    } catch (err) {
      alert(err.message || 'Failed to load pipeline.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPipeline();
  }, []);

  const handleStatusChange = async (leadId, newStatus) => {
    setMovingId(leadId);
    try {
      await api.leads.update(leadId, { status: newStatus });
      setLeads((prev) =>
        prev.map((l) => (l.id === leadId ? { ...l, status: newStatus } : l))
      );
    } catch (err) {
      alert(err.message || 'Failed to move lead.');
    } finally {
      setMovingId(null);
    }
  };

  if (loading) {
    return <LoadingSpinner text="Organizing sales pipeline board..." size="lg" />;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 glass-card p-4 rounded-2xl border border-slate-800">
        <div>
          <h2 className="text-base font-bold text-white tracking-tight">Visual Sales Pipeline (Kanban)</h2>
          <p className="text-xs text-slate-400">
            Track opportunities across stages from initial inquiry to Won / Lost
          </p>
        </div>

        <button
          onClick={() => setAddModalOpen(true)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-xl flex items-center gap-1.5 shadow-lg shadow-blue-500/20 transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>New Lead</span>
        </button>
      </div>

      <div className="flex gap-4 overflow-x-auto pb-6 scrollbar-thin">
        {PIPELINE_STATUSES.map((column) => {
          const colLeads = leads.filter((l) => l.status === column.id);
          const colValue = colLeads.reduce((acc, l) => acc + (parseFloat(l.budget) || 0), 0);

          return (
            <div
              key={column.id}
              className="w-72 shrink-0 glass-card rounded-2xl border border-slate-800 flex flex-col max-h-[75vh] bg-[#0f172a]/70"
            >
              <div className="p-3.5 border-b border-slate-800/80 flex items-center justify-between bg-slate-900/40 rounded-t-2xl">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-blue-500" />
                  <h3 className="text-xs font-bold text-white tracking-tight">{column.label}</h3>
                  <span className="text-[11px] font-bold px-2 py-0.2 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
                    {colLeads.length}
                  </span>
                </div>

                <span className="text-[11px] font-semibold text-emerald-400">
                  {formatCurrency(colValue)}
                </span>
              </div>

              <div className="p-2.5 space-y-2.5 overflow-y-auto flex-1">
                {colLeads.length === 0 ? (
                  <div className="py-8 text-center text-slate-600 text-xs italic">
                    No leads in this stage
                  </div>
                ) : (
                  colLeads.map((lead) => (
                    <div
                      key={lead.id}
                      onClick={() => onSelectLead(lead.id)}
                      className={`p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-blue-500/50 hover:shadow-lg transition-all cursor-pointer group space-y-2.5 ${
                        movingId === lead.id ? 'opacity-50 pointer-events-none' : ''
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <h4 className="text-xs font-bold text-white group-hover:text-blue-400 transition-colors line-clamp-1">
                          {lead.company_name}
                        </h4>
                        <PriorityBadge priority={lead.priority} />
                      </div>

                      <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">
                        {lead.project_title || 'Custom Software Solution'}
                      </p>

                      <div className="flex items-center justify-between pt-1 border-t border-slate-800/80 text-xs">
                        <span className="font-bold text-emerald-400 text-xs">
                          {formatCurrency(lead.budget, lead.currency)}
                        </span>

                        <FollowUpIndicator dateString={lead.follow_up_date} showDate={false} />
                      </div>

                      <div className="flex items-center justify-between pt-1 text-[11px] text-slate-500">
                        <div className="flex items-center gap-1.5 min-w-0">
                          <div className="w-4 h-4 rounded-full bg-slate-800 text-slate-300 flex items-center justify-center text-[9px] font-bold shrink-0">
                            {getInitials(lead.assigned_user?.name)}
                          </div>
                          <span className="truncate text-[10px]">
                            {lead.assigned_user?.name?.split(' ')[0] || 'Unassigned'}
                          </span>
                        </div>

                        <div onClick={(e) => e.stopPropagation()}>
                          <select
                            value={lead.status}
                            onChange={(e) => handleStatusChange(lead.id, e.target.value)}
                            className="bg-slate-950 border border-slate-700 text-[10px] text-slate-300 rounded-md px-1.5 py-0.5 outline-none font-medium hover:border-blue-500"
                          >
                            {PIPELINE_STATUSES.map((st) => (
                              <option key={st.id} value={st.id}>
                                Move: {st.label}
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>

      <LeadFormModal
        isOpen={addModalOpen}
        onClose={() => setAddModalOpen(false)}
        users={users}
        onSuccess={() => fetchPipeline()}
      />
    </div>
  );
}
