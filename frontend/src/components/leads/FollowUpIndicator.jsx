import React from 'react';
import { Clock } from 'lucide-react';
import { getFollowUpState } from '../../utils/formatters';

export function FollowUpIndicator({ dateString, showDate = true }) {
  if (!dateString) {
    return <span className="text-slate-500 text-xs italic">No follow-up</span>;
  }

  const info = getFollowUpState(dateString);
  if (!info) return null;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${info.badgeClass}`}
    >
      <Clock className="w-3 h-3 shrink-0" />
      <span>{showDate ? info.label : info.label.split('(')[0]}</span>
    </span>
  );
}
