import React, { useState } from 'react';
import { Sparkles, FileText, CheckCircle, RefreshCw } from 'lucide-react';
import { api } from '../../services/api';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';

export function ProposalDraftModal({ isOpen, onClose, lead, onSaved }) {
  const [instructions, setInstructions] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [draft, setDraft] = useState(null);
  const [error, setError] = useState(null);

  const [draftTitle, setDraftTitle] = useState('');
  const [draftPrice, setDraftPrice] = useState(lead?.budget || 15000);
  const [draftCurrency, setDraftCurrency] = useState(lead?.currency || 'USD');

  const handleGenerateDraft = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.proposals.draft(lead.id, instructions);
      setDraft(res);
      setDraftTitle(res.title || `Proposal for ${lead.company_name}`);
      setDraftPrice(res.price || lead.budget || 15000);
      setDraftCurrency(res.currency || lead.currency || 'USD');
    } catch (err) {
      setError(err.message || 'Failed to generate proposal draft with AI.');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveProposal = async () => {
    if (!draft) return;
    setSaving(true);
    setError(null);
    try {
      const payload = {
        lead_id: lead.id,
        title: draftTitle,
        executive_summary: draft.executive_summary,
        scope_of_work: draft.scope_of_work,
        deliverables: draft.deliverables,
        timeline_weeks: draft.timeline_weeks || 6,
        price: parseFloat(draftPrice) || 15000,
        currency: draftCurrency,
        terms_and_conditions: draft.terms_and_conditions,
        status: 'DRAFT',
      };

      const saved = await api.proposals.create(payload);
      if (onSaved) onSaved(saved);
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to save proposal.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Draft Commercial Proposal with AI"
      maxWidth="max-w-3xl"
    >
      <div className="space-y-4">
        {error && (
          <div className="p-3 rounded-xl bg-rose-500/10 text-rose-400 text-xs border border-rose-500/20">
            {error}
          </div>
        )}

        {!draft ? (
          <div className="space-y-4">
            <p className="text-xs text-slate-400">
              Gemini will draft a tailored proposal using the requirements from <b>{lead?.company_name}</b>, including an Executive Summary, Scope of Work, Deliverables Breakdown, Timeline, and Commercial Terms.
            </p>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Special Client Instructions / Commercial Adjustments (Optional)
              </label>
              <textarea
                rows={4}
                value={instructions}
                onChange={(e) => setInstructions(e.target.value)}
                placeholder="e.g. Include 2 weeks of post-launch QA support, emphasize high concurrency architecture, split into 3 milestones..."
                className="w-full bg-slate-900 border border-slate-800 focus:border-blue-500 rounded-xl p-3 text-xs text-white placeholder-slate-500 outline-none"
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <Button variant="outline" size="sm" onClick={onClose}>
                Cancel
              </Button>
              <Button
                variant="ai"
                size="sm"
                loading={loading}
                onClick={handleGenerateDraft}
                icon={Sparkles}
              >
                Generate Proposal Draft
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="sm:col-span-2">
                <label className="block text-xs font-medium text-slate-300 mb-1">Proposal Title</label>
                <input
                  type="text"
                  value={draftTitle}
                  onChange={(e) => setDraftTitle(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 focus:border-blue-500 rounded-xl px-3 py-1.5 text-xs text-white outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Pricing ({draftCurrency})</label>
                <input
                  type="number"
                  value={draftPrice}
                  onChange={(e) => setDraftPrice(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 focus:border-blue-500 rounded-xl px-3 py-1.5 text-xs text-white outline-none"
                />
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 max-h-72 overflow-y-auto space-y-3 text-xs text-slate-300">
              <div>
                <span className="font-bold text-white block mb-1">Executive Summary</span>
                <p className="text-slate-300 leading-relaxed whitespace-pre-line bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                  {draft.executive_summary}
                </p>
              </div>

              <div>
                <span className="font-bold text-white block mb-1">Scope of Work</span>
                <p className="text-slate-300 leading-relaxed whitespace-pre-line bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                  {draft.scope_of_work}
                </p>
              </div>

              <div>
                <span className="font-bold text-white block mb-1">Key Deliverables</span>
                <ul className="list-disc list-inside space-y-1 text-slate-200">
                  {draft.deliverables?.map((d, i) => (
                    <li key={i}>{d}</li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-800">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setDraft(null)}
                icon={RefreshCw}
              >
                Re-draft
              </Button>

              <div className="flex items-center gap-3">
                <Button variant="outline" size="sm" onClick={onClose}>
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  loading={saving}
                  onClick={handleSaveProposal}
                >
                  Save & Generate PDF
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
}
