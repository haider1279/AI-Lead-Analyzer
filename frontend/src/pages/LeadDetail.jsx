import React, { useState, useEffect } from 'react';
import {
  ArrowLeft,
  Building2,
  DollarSign,
  Sparkles,
  Plus,
  FileText,
  CheckCircle2,
  Edit2,
  ShieldCheck,
  ShieldAlert,
  RefreshCw,
} from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../auth/AuthContext';
import { formatCurrency, formatDate, formatDateTime } from '../utils/formatters';
import { StatusBadge } from '../components/leads/StatusBadge';
import { PriorityBadge } from '../components/leads/PriorityBadge';
import { FollowUpIndicator } from '../components/leads/FollowUpIndicator';
import { AILeadAnalyzer } from '../components/ai/AILeadAnalyzer';

import { ActivityTimeline } from '../components/activities/ActivityTimeline';
import { AddActivityModal } from '../components/activities/AddActivityModal';
import { ProposalDraftModal } from '../components/proposals/ProposalDraftModal';
import { ProposalList } from '../components/proposals/ProposalList';
import { TaskModal } from '../components/tasks/TaskModal';
import { LeadFormModal } from '../components/leads/LeadFormModal';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { Button } from '../components/common/Button';
import { PIPELINE_STATUSES } from '../utils/constants';

export function LeadDetail({ leadId, onBack }) {
  const { user, isAdmin } = useAuth();

  const [lead, setLead] = useState(null);
  const [activities, setActivities] = useState([]);
  const [statusHistory, setStatusHistory] = useState([]);
  const [proposals, setProposals] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [users, setUsers] = useState([]);

  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [toastMessage, setToastMessage] = useState(null);

  const [editOpen, setEditOpen] = useState(false);
  const [addActivityOpen, setAddActivityOpen] = useState(false);
  const [proposalModalOpen, setProposalModalOpen] = useState(false);
  const [taskModalOpen, setTaskModalOpen] = useState(false);

  const fetchLeadDetails = async () => {
    setLoading(true);
    setError(null);
    try {
      const [leadData, actsData, histData, propsData, tasksData, usersData] = await Promise.all([
        api.leads.get(leadId),
        api.activities.listForLead(leadId).catch(() => []),
        api.leads.getHistory(leadId).catch(() => []),
        api.proposals.listForLead(leadId).catch(() => []),
        api.tasks.list({ lead_id: leadId }).catch(() => []),
        api.auth.getUsers().catch(() => []),
      ]);

      setLead(leadData);
      setActivities(actsData);
      setStatusHistory(histData);
      setProposals(propsData);
      setTasks(tasksData);
      setUsers(usersData);
    } catch (err) {
      setError(err.message || 'Failed to load lead information.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (leadId) fetchLeadDetails();
  }, [leadId]);

  const handleStatusChange = async (newStatus) => {
    try {
      const updated = await api.leads.update(lead.id, { status: newStatus });
      setLead(updated);
      const [acts, hist] = await Promise.all([
        api.activities.listForLead(lead.id),
        api.leads.getHistory(lead.id),
      ]);
      setActivities(acts);
      setStatusHistory(hist);
    } catch (err) {
      alert(err.message || 'Failed to update pipeline status.');
    }
  };

  const handleTaskToggle = async (task) => {
    const newStatus = task.status === 'COMPLETED' ? 'PENDING' : 'COMPLETED';
    try {
      await api.tasks.update(task.id, { status: newStatus });
      setTasks((prev) =>
        prev.map((t) => (t.id === task.id ? { ...t, status: newStatus } : t))
      );
    } catch (err) {
      alert(err.message || 'Failed to update task.');
    }
  };

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  if (loading) {
    return <LoadingSpinner text="Loading opportunity profile & AI intelligence..." size="lg" />;
  }

  if (error || !lead) {
    return (
      <div className="p-8 glass-card rounded-2xl border border-rose-500/30 text-center my-6 space-y-4">
        <p className="text-rose-400 text-sm font-semibold">{error || 'Lead not found.'}</p>
        <Button variant="outline" size="sm" onClick={onBack} icon={ArrowLeft}>
          Back to Directory
        </Button>
      </div>
    );
  }

  const tabs = [
    { id: 'overview', label: 'Overview & Information' },
    { id: 'ai', label: 'AI Intelligence Engine', badge: lead.ai_analysis ? 'Ready' : null },
    { id: 'timeline', label: `Activity Timeline (${activities.length})` },
    { id: 'proposals', label: `Proposals (${proposals.length})` },
    { id: 'tasks', label: `Tasks (${tasks.length})` },
    { id: 'journey', label: 'Status Journey' },
  ];

  return (
    <div className="space-y-6">
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 p-4 rounded-xl bg-emerald-600 text-white text-xs font-semibold shadow-2xl flex items-center gap-2 animate-slideUp">
          <CheckCircle2 className="w-4 h-4" />
          <span>{toastMessage}</span>
        </div>
      )}

      <div className="flex flex-wrap items-center justify-between gap-4 glass-card p-4 rounded-2xl border border-slate-800">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-2 text-slate-400 hover:text-white bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-xl transition-all"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>

          <div>
            <div className="flex flex-wrap items-center gap-2 mb-1">
              <h2 className="text-lg font-extrabold text-white font-heading tracking-tight">
                {lead.company_name}
              </h2>
              <StatusBadge status={lead.status} />
              <PriorityBadge priority={lead.priority} />
            </div>
            <p className="text-xs text-slate-400">
              {lead.project_title || 'Software Opportunity'} • Source: <b>{lead.source}</b>
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Stage:</span>
            <select
              value={lead.status}
              onChange={(e) => handleStatusChange(e.target.value)}
              className="bg-transparent text-xs text-white font-semibold outline-none cursor-pointer"
            >
              {PIPELINE_STATUSES.map((st) => (
                <option key={st.id} value={st.id} className="bg-slate-900">
                  {st.label}
                </option>
              ))}
            </select>
          </div>

          <Button
            variant="secondary"
            size="sm"
            onClick={() => setAddActivityOpen(true)}
            icon={Plus}
          >
            Log Activity
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setEditOpen(true)}
            icon={Edit2}
          >
            Edit Lead
          </Button>
        </div>
      </div>

      <div className="flex items-center gap-1 overflow-x-auto border-b border-slate-800 pb-2 scrollbar-none">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-2 ${
              activeTab === tab.id
                ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            <span>{tab.label}</span>
            {tab.badge && (
              <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                {tab.badge}
              </span>
            )}
          </button>
        ))}
      </div>

      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="glass-card p-5 rounded-2xl border border-slate-800 space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                <FileText className="w-4 h-4 text-purple-400" />
                <span>Project & Scope Description</span>
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-line bg-slate-900/60 p-4 rounded-xl border border-slate-800">
                {lead.project_description || 'No detailed project description recorded.'}
              </p>
            </div>

            <div className="glass-card p-5 rounded-2xl border border-slate-800 space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                <Building2 className="w-4 h-4 text-blue-400" />
                <span>Client & Company Details</span>
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                  <span className="text-slate-500 font-medium block mb-0.5">Primary Contact Person</span>
                  <span className="text-white font-semibold">{lead.contact_name || '—'}</span>
                </div>

                <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                  <span className="text-slate-500 font-medium block mb-0.5">Job Title / Role</span>
                  <span className="text-white font-semibold">{lead.job_title || 'Not specified'}</span>
                </div>

                <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                  <span className="text-slate-500 font-medium block mb-0.5">Contact Email</span>
                  {lead.email ? (
                    <a href={`mailto:${lead.email}`} className="text-blue-400 hover:underline font-semibold">
                      {lead.email}
                    </a>
                  ) : (
                    <span className="text-slate-500">—</span>
                  )}
                </div>

                <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                  <span className="text-slate-500 font-medium block mb-0.5">Phone / WhatsApp</span>
                  <span className="text-white font-semibold">{lead.phone || '—'}</span>
                </div>

                <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                  <span className="text-slate-500 font-medium block mb-0.5">Website</span>
                  {lead.website ? (
                    <a
                      href={lead.website.startsWith('http') ? lead.website : `https://${lead.website}`}
                      target="_blank"
                      rel="noreferrer"
                      className="text-blue-400 hover:underline font-semibold truncate block"
                    >
                      {lead.website}
                    </a>
                  ) : (
                    <span className="text-slate-500">—</span>
                  )}
                </div>

                <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                  <span className="text-slate-500 font-medium block mb-0.5">Industry</span>
                  <span className="text-white font-semibold">{lead.industry || 'Technology'}</span>
                </div>

                <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                  <span className="text-slate-500 font-medium block mb-0.5">Country / Region</span>
                  <span className="text-white font-semibold">{lead.country || 'International'}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            {/* Lead Verification Audit Card */}
            <div className="glass-card p-5 rounded-2xl border border-slate-800 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span>Lead Verification Audit</span>
                </h3>
                <span className={`text-[11px] font-extrabold px-2.5 py-0.5 rounded-full border ${
                  (lead.verification_status === 'VERIFIED')
                    ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                    : (lead.verification_status === 'REJECTED')
                    ? 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                    : 'bg-slate-800 text-slate-400 border-slate-700'
                }`}>
                  {lead.verification_status || 'UNVERIFIED'} • {lead.verification_score ?? 0}%
                </span>
              </div>

              {/* Checks Checklist */}
              <div className="space-y-2 text-xs bg-slate-900/60 p-3.5 rounded-xl border border-slate-800/80">
                <div className="flex items-start justify-between gap-2">
                  <span className="text-slate-400">Company & Name Check:</span>
                  <span className={`font-semibold ${lead.verification_details?.checks?.company_name?.passed ? 'text-emerald-400' : 'text-slate-500'}`}>
                    {lead.verification_details?.checks?.company_name?.passed ? '✓ Valid Company' : '—'}
                  </span>
                </div>

                <div className="flex items-start justify-between gap-2">
                  <span className="text-slate-400">Email Syntax & DNS MX:</span>
                  <span className={`font-semibold ${lead.verification_details?.checks?.email_mx_dns?.passed ? 'text-emerald-400' : 'text-slate-500'}`}>
                    {lead.verification_details?.checks?.email_mx_dns?.passed ? '✓ MX Active' : (lead.email ? 'MX Unresolved' : 'No Email')}
                  </span>
                </div>

                <div className="flex items-start justify-between gap-2">
                  <span className="text-slate-400">Website & Domain DNS:</span>
                  <span className={`font-semibold ${lead.verification_details?.checks?.website_reachability?.passed ? 'text-emerald-400' : 'text-slate-500'}`}>
                    {lead.verification_details?.checks?.website_reachability?.passed ? '✓ Reachable' : (lead.website ? 'Unreachable' : 'No Website')}
                  </span>
                </div>

                <div className="flex items-start justify-between gap-2">
                  <span className="text-slate-400">Contact & Role Identified:</span>
                  <span className={`font-semibold ${lead.verification_details?.checks?.contact_name?.passed ? 'text-emerald-400' : 'text-slate-500'}`}>
                    {lead.contact_name ? `✓ ${lead.contact_name}` : 'Unspecified'}
                  </span>
                </div>
              </div>

              <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1">
                <span>
                  Last verified: {lead.last_verified_at ? formatDate(lead.last_verified_at) : 'Not verified yet'}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={async () => {
                    try {
                      const updated = await api.leads.verify(lead.id);
                      setLead((prev) => ({ ...prev, ...updated }));
                      showToast('Lead re-verified successfully!');
                    } catch (e) {
                      alert(e.message || 'Verification failed');
                    }
                  }}
                  className="text-[10px] py-1 px-2 h-7"
                >
                  <RefreshCw className="w-3 h-3 mr-1" />
                  Re-Verify
                </Button>
              </div>
            </div>

            <div className="glass-card p-5 rounded-2xl border border-slate-800 space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                <DollarSign className="w-4 h-4 text-emerald-400" />
                <span>Commercial Terms</span>
              </h3>

              <div className="space-y-3">
                <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
                  <span className="text-xs text-slate-400">Estimated Budget</span>
                  <span className="text-base font-extrabold text-emerald-400 font-heading">
                    {formatCurrency(lead.budget, lead.currency)}
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between text-xs">
                  <span className="text-slate-400">Target Deadline</span>
                  <span className="text-white font-semibold">{formatDate(lead.expected_deadline)}</span>
                </div>

                <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between text-xs">
                  <span className="text-slate-400">Follow-Up Radar</span>
                  <FollowUpIndicator dateString={lead.follow_up_date} />
                </div>

                <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between text-xs">
                  <span className="text-slate-400">Assigned Employee</span>
                  <span className="text-white font-semibold">
                    {lead.assigned_user?.name || 'Unassigned'}
                  </span>
                </div>
              </div>
            </div>


          </div>
        </div>
      )}


      {activeTab === 'ai' && (
        <AILeadAnalyzer
          lead={lead}
          onUpdate={(updates) => {
            setLead((prev) => ({ ...prev, ...updates }));
            showToast('AI Analysis saved to Lead profile.');
          }}
          onActionCreated={(msg) => {
            showToast(msg);
            api.tasks.list({ lead_id: lead.id }).then(setTasks);
          }}
        />
      )}

      {activeTab === 'timeline' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white tracking-tight">Chronological Activity History</h3>
            <Button
              variant="primary"
              size="sm"
              onClick={() => setAddActivityOpen(true)}
              icon={Plus}
            >
              Log Touchpoint
            </Button>
          </div>

          <ActivityTimeline activities={activities} />
        </div>
      )}

      {activeTab === 'proposals' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white tracking-tight">Commercial Proposals</h3>
              <p className="text-xs text-slate-400">Generate, edit, and download PDF proposals</p>
            </div>
            <Button
              variant="ai"
              size="sm"
              onClick={() => setProposalModalOpen(true)}
              icon={Sparkles}
            >
              Draft Proposal with AI
            </Button>
          </div>

          <ProposalList proposals={proposals} leadCompanyName={lead.company_name} />
        </div>
      )}

      {activeTab === 'tasks' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white tracking-tight">Action Items & Tasks</h3>
              <p className="text-xs text-slate-400">Manage deliverables for this opportunity</p>
            </div>
            <Button
              variant="primary"
              size="sm"
              onClick={() => setTaskModalOpen(true)}
              icon={Plus}
            >
              Add Task
            </Button>
          </div>

          {tasks.length === 0 ? (
            <div className="text-center py-10 text-slate-500 text-xs">
              No tasks linked to this lead. Click 'Add Task' or convert an AI recommendation into an action item.
            </div>
          ) : (
            <div className="space-y-2.5">
              {tasks.map((t) => (
                <div
                  key={t.id}
                  className={`p-3.5 rounded-xl border flex items-center justify-between gap-3 transition-all ${
                    t.status === 'COMPLETED'
                      ? 'bg-slate-900/40 border-slate-800/60 opacity-60'
                      : 'bg-slate-900/80 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <button
                      onClick={() => handleTaskToggle(t)}
                      className={`w-5 h-5 rounded-lg border flex items-center justify-center transition-colors shrink-0 ${
                        t.status === 'COMPLETED'
                          ? 'bg-emerald-600 border-emerald-500 text-white'
                          : 'border-slate-700 hover:border-slate-500 text-transparent'
                      }`}
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                    </button>
                    <div className="min-w-0">
                      <p
                        className={`text-xs font-semibold ${
                          t.status === 'COMPLETED' ? 'line-through text-slate-400' : 'text-white'
                        }`}
                      >
                        {t.title}
                      </p>
                      {t.description && (
                        <p className="text-[11px] text-slate-400 truncate">{t.description}</p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <PriorityBadge priority={t.priority} />
                    {t.due_date && (
                      <span className="text-[11px] text-slate-400">Due {formatDate(t.due_date)}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'journey' && (
        <div className="space-y-4">
          <h3 className="text-sm font-bold text-white tracking-tight">Audit Trail & Pipeline Transitions</h3>

          <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4">
            {statusHistory.length === 0 ? (
              <p className="text-xs text-slate-500 text-center py-6">No status transitions recorded yet.</p>
            ) : (
              <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
                {statusHistory.map((h) => (
                  <div key={h.id} className="relative flex items-center justify-between text-xs">
                    <div className="absolute -left-6 w-4 h-4 rounded-full bg-slate-900 border-2 border-blue-500 flex items-center justify-center" />
                    <div>
                      <span className="text-slate-400 font-medium">Transitioned to </span>
                      <StatusBadge status={h.new_status} />
                      {h.old_status && (
                        <span className="text-slate-500 text-[11px] ml-2">(from {h.old_status})</span>
                      )}
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        By {h.changed_by_user?.name || 'Employee'}
                      </p>
                    </div>
                    <span className="text-slate-500 text-[11px]">{formatDateTime(h.changed_at)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      <LeadFormModal
        isOpen={editOpen}
        onClose={() => setEditOpen(false)}
        initialData={lead}
        users={users}
        onSuccess={(saved) => {
          setLead(saved);
          showToast('Lead updated successfully!');
        }}
      />

      <AddActivityModal
        isOpen={addActivityOpen}
        onClose={() => setAddActivityOpen(false)}
        leadId={lead.id}
        onSuccess={(newAct) => {
          setActivities((prev) => [newAct, ...prev]);
          if (newAct.follow_up_date) {
            setLead((prev) => ({ ...prev, follow_up_date: newAct.follow_up_date }));
          }
          showToast('Activity logged to timeline!');
        }}
      />

      <ProposalDraftModal
        isOpen={proposalModalOpen}
        onClose={() => setProposalModalOpen(false)}
        lead={lead}
        onSaved={(savedProp) => {
          setProposals((prev) => [savedProp, ...prev]);
          showToast('Proposal saved! You can now download the PDF.');
        }}
      />

      <TaskModal
        isOpen={taskModalOpen}
        onClose={() => setTaskModalOpen(false)}
        leadId={lead.id}
        users={users}
        onSuccess={(savedTask) => {
          setTasks((prev) => [savedTask, ...prev]);
          showToast('Task added to Lead!');
        }}
      />
    </div>
  );
}
