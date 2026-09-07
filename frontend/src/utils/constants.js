export const PIPELINE_STATUSES = [
  { id: 'NEW', label: 'New Lead', color: 'bg-blue-500/10 text-blue-400 border-blue-500/20' },
  { id: 'CONTACTED', label: 'Contacted', color: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' },
  { id: 'QUALIFIED', label: 'Qualified', color: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20' },
  { id: 'PROPOSAL_SENT', label: 'Proposal Sent', color: 'bg-purple-500/10 text-purple-400 border-purple-500/20' },
  { id: 'NEGOTIATION', label: 'Negotiation', color: 'bg-amber-500/10 text-amber-400 border-amber-500/20' },
  { id: 'WON', label: 'Won', color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' },
  { id: 'LOST', label: 'Lost', color: 'bg-rose-500/10 text-rose-400 border-rose-500/20' },
];

export const LEAD_SOURCES = [
  'Upwork',
  'LinkedIn',
  'WhatsApp',
  'Email',
  'Website',
  'Referral',
  'Phone',
  'Other',
];

export const PRIORITIES = [
  { id: 'LOW', label: 'Low', color: 'bg-slate-500/10 text-slate-400 border-slate-500/20' },
  { id: 'MEDIUM', label: 'Medium', color: 'bg-blue-500/10 text-blue-400 border-blue-500/20' },
  { id: 'HIGH', label: 'High', color: 'bg-amber-500/10 text-amber-400 border-amber-500/20' },
  { id: 'URGENT', label: 'Urgent', color: 'bg-rose-500/10 text-rose-400 border-rose-500/20' },
];

// Values MUST match backend ActivityType enum exactly (enums.py)
export const ACTIVITY_TYPES = [
  { id: 'Upwork Conversation', label: '💬 Upwork Conversation' },
  { id: 'WhatsApp Conversation', label: '📱 WhatsApp Conversation' },
  { id: 'Email', label: '📧 Email' },
  { id: 'Phone Call', label: '📞 Phone Call' },
  { id: 'Meeting', label: '🤝 Meeting' },
  { id: 'Proposal Sent', label: '📄 Proposal Sent' },
  { id: 'Follow-up', label: '🔄 Follow-up' },
  { id: 'Note', label: '📝 Note' },
  { id: 'Status Change', label: '🔀 Status Change' },
  { id: 'Other', label: '📌 Other' },
];

export const TASK_STATUSES = [
  { id: 'PENDING', label: 'Pending', color: 'bg-slate-500/10 text-slate-400 border-slate-500/20' },
  { id: 'IN_PROGRESS', label: 'In Progress', color: 'bg-blue-500/10 text-blue-400 border-blue-500/20' },
  { id: 'COMPLETED', label: 'Completed', color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' },
];

