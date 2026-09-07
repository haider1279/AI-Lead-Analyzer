import React, { useState, useEffect } from 'react';
import {
  Search,
  Plus,
  Download,
  Trash2,
  Edit2,
  ChevronRight,
  RotateCcw,
} from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../auth/AuthContext';
import { formatCurrency, formatDate, getInitials } from '../utils/formatters';
import { StatusBadge } from '../components/leads/StatusBadge';
import { PriorityBadge } from '../components/leads/PriorityBadge';
import { FollowUpIndicator } from '../components/leads/FollowUpIndicator';
import { LeadFormModal } from '../components/leads/LeadFormModal';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { EmptyState } from '../components/common/EmptyState';
import { Button } from '../components/common/Button';
import { PIPELINE_STATUSES, PRIORITIES, LEAD_SOURCES } from '../utils/constants';

export function Leads({ onSelectLead, initialOpenAdd = false }) {
  const { isAdmin } = useAuth();

  const [leads, setLeads] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [sourceFilter, setSourceFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [assignedFilter, setAssignedFilter] = useState('');
  const [followUpFilter, setFollowUpFilter] = useState('');

  const [formOpen, setFormOpen] = useState(initialOpenAdd);
  const [editingLead, setEditingLead] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const [exporting, setExporting] = useState(false);

  const fetchLeads = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (search.trim()) params.search = search.trim();
      if (statusFilter) params.status = statusFilter;
      if (sourceFilter) params.source = sourceFilter;
      if (priorityFilter) params.priority = priorityFilter;
      if (assignedFilter) params.assigned_to = assignedFilter;
      if (followUpFilter) params.follow_up_state = followUpFilter;

      const [leadsData, usersData] = await Promise.all([
        api.leads.list(params),
        api.auth.getUsers().catch(() => []),
      ]);

      setLeads(leadsData);
      setUsers(usersData);
    } catch (err) {
      setError(err.message || 'Failed to fetch leads list.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeads();
  }, [search, statusFilter, sourceFilter, priorityFilter, assignedFilter, followUpFilter]);

  const handleInlineStatusChange = async (leadId, newStatus) => {
    try {
      await api.leads.update(leadId, { status: newStatus });
      setLeads((prev) =>
        prev.map((l) => (l.id === leadId ? { ...l, status: newStatus } : l))
      );
    } catch (err) {
      alert(err.message || 'Failed to update status.');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to permanently delete this lead? This will also remove related activities and proposals.')) {
      return;
    }
    setDeletingId(id);
    try {
      await api.leads.delete(id);
      setLeads((prev) => prev.filter((l) => l.id !== id));
    } catch (err) {
      alert(err.message || 'Failed to delete lead.');
    } finally {
      setDeletingId(null);
    }
  };

  const handleExportCsv = async () => {
    setExporting(true);
    try {
      await api.reports.exportCsv();
    } catch (err) {
      alert(err.message || 'Failed to export CSV.');
    } finally {
      setExporting(false);
    }
  };

  const clearFilters = () => {
    setSearch('');
    setStatusFilter('');
    setSourceFilter('');
    setPriorityFilter('');
    setAssignedFilter('');
    setFollowUpFilter('');
  };

  const hasActiveFilters = Boolean(
    search || statusFilter || sourceFilter || priorityFilter || assignedFilter || followUpFilter
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 glass-card p-4 rounded-2xl border border-slate-800">
        <div>
          <h2 className="text-base font-bold text-white tracking-tight">Leads Directory</h2>
          <p className="text-xs text-slate-400">
            Showing {leads.length} recorded {leads.length === 1 ? 'opportunity' : 'opportunities'}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={handleExportCsv}
            loading={exporting}
            icon={Download}
          >
            Export CSV
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={() => {
              setEditingLead(null);
              setFormOpen(true);
            }}
            icon={Plus}
          >
            New Lead
          </Button>
        </div>
      </div>

      <div className="glass-card p-4 rounded-2xl border border-slate-800 space-y-3">
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search company, contact person, email, or project title..."
            className="w-full bg-slate-900/90 border border-slate-800 focus:border-blue-500 rounded-xl pl-10 pr-4 py-2 text-xs text-white placeholder-slate-500 outline-none transition-all"
          />
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2.5 pt-1">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-900 border border-slate-800 text-slate-300 text-xs rounded-xl px-3 py-2 outline-none"
          >
            <option value="">All Statuses</option>
            {PIPELINE_STATUSES.map((s) => (
              <option key={s.id} value={s.id}>
                {s.label}
              </option>
            ))}
          </select>

          <select
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value)}
            className="bg-slate-900 border border-slate-800 text-slate-300 text-xs rounded-xl px-3 py-2 outline-none"
          >
            <option value="">All Sources</option>
            {LEAD_SOURCES.map((src) => (
              <option key={src} value={src}>
                {src}
              </option>
            ))}
          </select>

          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="bg-slate-900 border border-slate-800 text-slate-300 text-xs rounded-xl px-3 py-2 outline-none"
          >
            <option value="">All Priorities</option>
            {PRIORITIES.map((p) => (
              <option key={p.id} value={p.id}>
                {p.label} Priority
              </option>
            ))}
          </select>

          <select
            value={assignedFilter}
            onChange={(e) => setAssignedFilter(e.target.value)}
            className="bg-slate-900 border border-slate-800 text-slate-300 text-xs rounded-xl px-3 py-2 outline-none"
          >
            <option value="">All Assignees</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>
                {u.name}
              </option>
            ))}
          </select>

          <select
            value={followUpFilter}
            onChange={(e) => setFollowUpFilter(e.target.value)}
            className="bg-slate-900 border border-slate-800 text-slate-300 text-xs rounded-xl px-3 py-2 outline-none"
          >
            <option value="">All Follow-ups</option>
            <option value="overdue">🔴 Overdue</option>
            <option value="today">🟡 Due Today</option>
            <option value="upcoming">🟢 Upcoming</option>
          </select>
        </div>

        {hasActiveFilters && (
          <div className="flex items-center justify-between pt-1 border-t border-slate-800/60 text-xs">
            <span className="text-slate-400 text-[11px]">Active filters applied</span>
            <button
              onClick={clearFilters}
              className="text-blue-400 hover:text-blue-300 flex items-center gap-1 font-semibold text-[11px]"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Clear all filters</span>
            </button>
          </div>
        )}
      </div>

      {loading ? (
        <LoadingSpinner text="Loading leads..." size="md" />
      ) : leads.length === 0 ? (
        <EmptyState
          title="No leads found"
          description={
            hasActiveFilters
              ? 'No opportunities match your selected filter criteria. Try clearing or adjusting filters.'
              : 'You have not recorded any leads yet. Create your first sales lead to start tracking.'
          }
          actionLabel={hasActiveFilters ? 'Clear Filters' : 'Create First Lead'}
          onAction={hasActiveFilters ? clearFilters : () => setFormOpen(true)}
        />
      ) : (
        <div className="glass-card rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900/60 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  <th className="py-3.5 px-4">Company & Contact</th>
                  <th className="py-3.5 px-4">Project & Budget</th>
                  <th className="py-3.5 px-4">Source</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4">Priority</th>
                  <th className="py-3.5 px-4">Follow-up</th>
                  <th className="py-3.5 px-4">Assigned</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-xs">
                {leads.map((lead) => (
                  <tr
                    key={lead.id}
                    className="hover:bg-slate-800/40 transition-colors group cursor-pointer"
                    onClick={(e) => {
                      if (e.target.closest('select') || e.target.closest('button')) return;
                      onSelectLead(lead.id);
                    }}
                  >
                    <td className="py-3.5 px-4 min-w-[180px]">
                      <div className="font-bold text-white group-hover:text-blue-400 transition-colors">
                        {lead.company_name}
                      </div>
                      <div className="text-slate-400 text-[11px]">
                        {lead.contact_name || lead.email || '—'}
                      </div>
                    </td>

                    <td className="py-3.5 px-4 min-w-[190px]">
                      <div className="text-slate-200 font-medium truncate max-w-xs">
                        {lead.project_title || 'Software Opportunity'}
                      </div>
                      <div className="text-emerald-400 font-bold text-[11px]">
                        {formatCurrency(lead.budget, lead.currency)}
                      </div>
                    </td>

                    <td className="py-3.5 px-4 text-slate-400">
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-[11px] font-medium border border-slate-700/80">
                        {lead.source}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 min-w-[140px]">
                      <select
                        value={lead.status}
                        onChange={(e) => handleInlineStatusChange(lead.id, e.target.value)}
                        className="bg-slate-900 border border-slate-700 text-xs text-white rounded-lg px-2 py-1 outline-none font-semibold"
                      >
                        {PIPELINE_STATUSES.map((st) => (
                          <option key={st.id} value={st.id}>
                            {st.label}
                          </option>
                        ))}
                      </select>
                    </td>

                    <td className="py-3.5 px-4">
                      <PriorityBadge priority={lead.priority} />
                    </td>

                    <td className="py-3.5 px-4 min-w-[130px]">
                      <FollowUpIndicator dateString={lead.follow_up_date} />
                    </td>

                    <td className="py-3.5 px-4 text-slate-300 min-w-[130px]">
                      {lead.assigned_user ? (
                        <div className="flex items-center gap-1.5">
                          <div className="w-5 h-5 rounded-full bg-slate-800 text-slate-300 flex items-center justify-center text-[10px] font-bold shrink-0">
                            {getInitials(lead.assigned_user.name)}
                          </div>
                          <span className="truncate">{lead.assigned_user.name}</span>
                        </div>
                      ) : (
                        <span className="text-slate-500">Unassigned</span>
                      )}
                    </td>

                    <td className="py-3.5 px-4 text-right shrink-0 space-x-1">
                      <button
                        title="Edit Lead"
                        onClick={(e) => {
                          e.stopPropagation();
                          setEditingLead(lead);
                          setFormOpen(true);
                        }}
                        className="p-1.5 text-slate-400 hover:text-blue-400 hover:bg-slate-800 rounded-lg transition-colors"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>

                      {isAdmin && (
                        <button
                          title="Delete Lead"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(lead.id);
                          }}
                          disabled={deletingId === lead.id}
                          className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}

                      <button
                        title="Open Lead Hub"
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectLead(lead.id);
                        }}
                        className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                      >
                        <ChevronRight className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <LeadFormModal
        isOpen={formOpen}
        onClose={() => {
          setFormOpen(false);
          setEditingLead(null);
        }}
        initialData={editingLead}
        users={users}
        onSuccess={() => {
          fetchLeads();
        }}
      />
    </div>
  );
}
