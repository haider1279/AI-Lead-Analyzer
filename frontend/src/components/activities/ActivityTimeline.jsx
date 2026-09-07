import React from 'react';
import {
  MessageSquare,
  Phone,
  Mail,
  Calendar,
  FileText,
  Clock,
  GitCommit,
  UserCheck,
} from 'lucide-react';
import { formatDateTime, getInitials } from '../../utils/formatters';

const TYPE_ICONS = {
  CALL: Phone,
  EMAIL: Mail,
  WHATSAPP: MessageSquare,
  UPWORK: MessageSquare,
  LINKEDIN: MessageSquare,
  MEETING: Calendar,
  NOTE: FileText,
  STATUS_CHANGE: GitCommit,
};

const TYPE_COLORS = {
  CALL: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
  EMAIL: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
  WHATSAPP: 'bg-green-500/10 text-green-400 border-green-500/30',
  UPWORK: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
  LINKEDIN: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
  MEETING: 'bg-purple-500/10 text-purple-400 border-purple-500/30',
  NOTE: 'bg-slate-800 text-slate-300 border-slate-700',
  STATUS_CHANGE: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
};

export function ActivityTimeline({ activities = [] }) {
  if (!activities || activities.length === 0) {
    return (
      <div className="p-8 text-center glass-card rounded-2xl border border-slate-800 text-xs text-slate-500">
        No activities or touchpoints recorded yet. Click 'Log Touchpoint' to add client interactions.
      </div>
    );
  }

  return (
    <div className="relative pl-6 space-y-4 before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
      {activities.map((act) => {
        const Icon = TYPE_ICONS[act.type] || FileText;
        const colorClass = TYPE_COLORS[act.type] || TYPE_COLORS.NOTE;

        return (
          <div key={act.id} className="relative group">
            <div
              className={`absolute -left-6 w-6 h-6 rounded-full border flex items-center justify-center bg-slate-900 ${colorClass}`}
            >
              <Icon className="w-3 h-3" />
            </div>

            <div className="glass-card p-4 rounded-xl border border-slate-800/90 hover:border-slate-700 transition-all space-y-1.5">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-white">{act.title}</span>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.2 rounded-full border ${colorClass}`}
                  >
                    {act.type}
                  </span>
                </div>

                <span className="text-[11px] text-slate-500">
                  {formatDateTime(act.activity_date)}
                </span>
              </div>

              {act.description && (
                <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-line">
                  {act.description}
                </p>
              )}

              <div className="flex items-center justify-between pt-1 border-t border-slate-800/60 text-[11px] text-slate-500">
                <span>By {act.user?.name || 'Euroshub Employee'}</span>
                {act.follow_up_date && (
                  <span className="text-amber-400 font-medium flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    <span>Follow-up: {formatDateTime(act.follow_up_date)}</span>
                  </span>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
