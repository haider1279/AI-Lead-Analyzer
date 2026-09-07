import React, { useState } from 'react';
import {
  Sparkles,
  CheckCircle,
  AlertTriangle,
  Flame,
  ArrowRight,
  RefreshCw,
  PlusCircle,
  FileCheck,
  MessageSquare,
} from 'lucide-react';
import { api } from '../../services/api';
import { Button } from '../common/Button';
import { ConversationAnalyzerModal } from './ConversationAnalyzerModal';

export function AILeadAnalyzer({ lead, onUpdate, onActionCreated }) {
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState(lead?.ai_analysis || null);
  const [chatModalOpen, setChatModalOpen] = useState(false);
  const [addingAction, setAddingAction] = useState(false);

  const handleRunFullAnalysis = async () => {
    setLoading(true);
    try {
      const res = await api.ai.analyze(lead.id);
      setAnalysis(res);
      if (onUpdate) {
        onUpdate({
          ai_analysis: res,
          ai_summary: res.summary,
          lead_score: res.lead_score,
          lead_score_label: res.lead_score_label,
        });
      }
    } catch (err) {
      alert(err.message || 'Failed to run AI analysis.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateActionItem = async () => {
    if (!analysis?.recommended_action) return;
    setAddingAction(true);
    try {
      const res = await api.ai.createActionItem(
        lead.id,
        analysis.recommended_action,
        'HIGH'
      );
      if (onActionCreated) onActionCreated(res.message);
    } catch (err) {
      alert(err.message || 'Failed to convert to task.');
    } finally {
      setAddingAction(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="glass-card p-5 rounded-2xl border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-bold text-white tracking-tight">
              Gemini AI Opportunity Intelligence Hub
            </h3>
          </div>
          <p className="text-xs text-slate-400">
            Extract requirements, detect risks, generate executive summaries, and analyze client transcripts
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setChatModalOpen(true)}
            icon={MessageSquare}
          >
            Analyze Chat Transcript
          </Button>

          <Button
            variant="ai"
            size="sm"
            loading={loading}
            onClick={handleRunFullAnalysis}
            icon={RefreshCw}
          >
            {analysis ? 'Re-Analyze Opportunity' : 'Run Full AI Analysis'}
          </Button>
        </div>
      </div>

      {!analysis ? (
        <div className="glass-card p-10 rounded-2xl border border-slate-800 text-center space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 mx-auto">
            <Sparkles className="w-6 h-6" />
          </div>
          <h4 className="text-sm font-bold text-white">No AI Analysis Generated Yet</h4>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Click 'Run Full AI Analysis' to extract requirements, evaluate technical complexity, surface potential risks, and calculate win probability.
          </p>
          <Button variant="ai" size="sm" onClick={handleRunFullAnalysis} loading={loading}>
            Start AI Analysis
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                <FileCheck className="w-4 h-4 text-blue-400" />
                <span>Executive Summary</span>
              </h4>
              <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-line bg-slate-900/60 p-4 rounded-xl border border-slate-800">
                {analysis.summary || 'No summary generated.'}
              </p>
            </div>

            <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-400" />
                <span>Extracted Requirements ({analysis.extracted_requirements?.length || 0})</span>
              </h4>
              {analysis.extracted_requirements?.length > 0 ? (
                <ul className="space-y-2">
                  {analysis.extracted_requirements.map((req, idx) => (
                    <li
                      key={idx}
                      className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-200 flex items-start gap-2.5"
                    >
                      <span className="w-5 h-5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
                        {idx + 1}
                      </span>
                      <span className="leading-relaxed">{req}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-slate-500">No specific requirements detected.</p>
              )}
            </div>

            {analysis.risks_identified?.length > 0 && (
              <div className="glass-card p-6 rounded-2xl border border-amber-500/30 space-y-3 bg-amber-950/10">
                <h4 className="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" />
                  <span>Identified Risks & Red Flags</span>
                </h4>
                <ul className="space-y-2">
                  {analysis.risks_identified.map((risk, idx) => (
                    <li
                      key={idx}
                      className="p-3 rounded-xl bg-slate-900/80 border border-amber-500/20 text-xs text-amber-200/90 flex items-start gap-2"
                    >
                      <span className="text-amber-400 font-bold">•</span>
                      <span>{risk}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <div className="space-y-6">
            <div className="glass-card p-6 rounded-2xl border border-indigo-500/30 bg-indigo-950/15 space-y-4">
              <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-2">
                <Flame className="w-4 h-4" />
                <span>Recommended Next Action</span>
              </h4>

              <div className="p-4 rounded-xl bg-slate-900/90 border border-indigo-500/20 text-xs text-slate-200 leading-relaxed">
                {analysis.recommended_action || 'No action recommendation available.'}
              </div>

              <Button
                variant="ai"
                size="sm"
                className="w-full"
                loading={addingAction}
                onClick={handleCreateActionItem}
                icon={PlusCircle}
              >
                1-Click Convert to Task
              </Button>
            </div>

            <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                Complexity Assessment
              </h4>
              <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
                <span className="text-xs text-slate-400">Estimated Effort</span>
                <span className="text-xs font-bold text-white px-2.5 py-1 rounded bg-slate-800 border border-slate-700">
                  {analysis.complexity_estimate || 'Moderate'}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      <ConversationAnalyzerModal
        isOpen={chatModalOpen}
        onClose={() => setChatModalOpen(false)}
        leadId={lead.id}
        onAnalyzed={(res) => {
          setAnalysis((prev) => ({
            ...prev,
            summary: res.summary || prev?.summary,
            extracted_requirements: [
              ...(prev?.extracted_requirements || []),
              ...(res.extracted_requirements || []),
            ],
            recommended_action: res.recommended_action || prev?.recommended_action,
          }));
        }}
      />
    </div>
  );
}
