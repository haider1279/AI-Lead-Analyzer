import React from 'react';
import { PRIORITIES } from '../../utils/constants';

export function PriorityBadge({ priority = 'MEDIUM' }) {
  const p = PRIORITIES.find((item) => item.id === priority) || {
    label: priority,
    color: 'bg-slate-800 text-slate-300 border-slate-700',
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-semibold border ${p.color}`}
    >
      {p.label}
    </span>
  );
}
