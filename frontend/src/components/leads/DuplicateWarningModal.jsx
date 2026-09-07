import React from 'react';
import { AlertTriangle, ArrowRight, X } from 'lucide-react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';

export function DuplicateWarningModal({
  isOpen,
  onClose,
  duplicates = [],
  onProceedAnyway,
}) {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Duplicate Lead Detected"
      maxWidth="max-w-xl"
    >
      <div className="space-y-4">
        <div className="flex items-start gap-3 p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300">
          <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
          <div className="text-xs space-y-1">
            <p className="font-bold">A potential existing lead was found in the database.</p>
            <p className="text-amber-300/80">
              Euroshub prevents duplicate entries to maintain data hygiene. Review the matched leads below before continuing.
            </p>
          </div>
        </div>

        <div className="space-y-2">
          {duplicates.map((lead) => (
            <div
              key={lead.id}
              className="p-3 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between text-xs"
            >
              <div>
                <div className="font-bold text-white">{lead.company_name}</div>
                <div className="text-slate-400 text-[11px]">
                  Contact: {lead.contact_name || lead.email || '—'} • Status: {lead.status}
                </div>
              </div>
              <span className="text-[11px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                {lead.match_reason || 'Match Found'}
              </span>
            </div>
          ))}
        </div>

        <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
          <Button variant="outline" size="sm" onClick={onClose}>
            Cancel & Edit
          </Button>
          <Button variant="danger" size="sm" onClick={onProceedAnyway}>
            Proceed & Save Anyway
          </Button>
        </div>
      </div>
    </Modal>
  );
}
