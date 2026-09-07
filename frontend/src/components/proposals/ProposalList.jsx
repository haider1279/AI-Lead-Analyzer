import React, { useState } from 'react';
import { FileText, Download, Clock, DollarSign, Edit2 } from 'lucide-react';
import { api } from '../../services/api';
import { formatCurrency, formatDate } from '../../utils/formatters';
import { Button } from '../common/Button';

export function ProposalList({ proposals, leadCompanyName }) {
  const [downloadingId, setDownloadingId] = useState(null);

  const handleDownload = async (prop) => {
    setDownloadingId(prop.id);
    try {
      const cleanName = `${leadCompanyName.replace(/\s+/g, '_')}_Proposal_v${prop.version}.pdf`;
      await api.proposals.downloadPdf(prop.id, cleanName);
    } catch (err) {
      alert(err.message || 'Failed to download proposal PDF.');
    } finally {
      setDownloadingId(null);
    }
  };

  if (!proposals || proposals.length === 0) {
    return (
      <div className="text-center py-10 glass-card rounded-2xl border border-slate-800 text-xs text-slate-500">
        No proposals generated for this lead yet. Click 'Draft Proposal with AI' to generate a commercial proposal.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {proposals.map((prop) => (
        <div
          key={prop.id}
          className="glass-card p-4 rounded-2xl border border-slate-800 hover:border-slate-700 flex flex-wrap items-center justify-between gap-4 transition-all"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-purple-600/10 border border-purple-500/20 text-purple-400 flex items-center justify-center font-bold text-xs shrink-0">
              v{prop.version}
            </div>

            <div>
              <h4 className="text-xs font-bold text-white">{prop.title}</h4>
              <p className="text-[11px] text-slate-400 flex items-center gap-2 mt-0.5">
                <span>Created {formatDate(prop.created_at)}</span>
                <span>•</span>
                <span className="font-semibold text-emerald-400">
                  {formatCurrency(prop.price, prop.currency)}
                </span>
                <span>•</span>
                <span className="capitalize text-slate-300">{prop.status.toLowerCase()}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="primary"
              size="sm"
              loading={downloadingId === prop.id}
              onClick={() => handleDownload(prop)}
              icon={Download}
            >
              Download PDF
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
}
