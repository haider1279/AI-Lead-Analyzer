import React from 'react';
import { PIPELINE_STATUSES } from '../../utils/constants';

export function StatusBadge({ status = 'NEW' }) {
  const st = PIPELINE_STATUSES.find((s) => s.id === status) || {
    label: status,
    color: 'bg-slate-800 text-slate-300 border-slate-700',
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border shadow-sm ${st.color}`}
    >
      {st.label}
    </span>
  );
}
