import React, { useState } from 'react';
import { Sparkles, MessageSquare, CheckCircle, Flame } from 'lucide-react';
import { api } from '../../services/api';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';

export function ConversationAnalyzerModal({ isOpen, onClose, leadId, onAnalyzed }) {
  const [transcript, setTranscript] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!transcript.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const res = await api.ai.analyzeConversation(leadId, transcript);
      setResult(res);
      if (onAnalyzed) onAnalyzed(res);
    } catch (err) {
      setError(err.message || 'Failed to analyze conversation.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Analyze External Chat Transcript"
      maxWidth="max-w-2xl"
    >
      <div className="space-y-4">
        <p className="text-xs text-slate-400">
          Paste conversation messages or meeting notes from WhatsApp, Upwork, LinkedIn, or Email. Gemini will extract requirements, client sentiment, and next action items.
        </p>

        {error && (
          <div className="p-3 rounded-xl bg-rose-500/10 text-rose-400 text-xs border border-rose-500/20">
            {error}
          </div>
        )}

        <form onSubmit={handleAnalyze} className="space-y-4">
          <div>
            <textarea
              rows={6}
              required
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
              placeholder="Client: Hi, we need a React + FastAPI platform with Stripe integration...&#10;Euroshub: We can deliver this within 6 weeks..."
              className="w-full bg-slate-900 border border-slate-800 focus:border-blue-500 rounded-xl p-3.5 text-xs text-white placeholder-slate-500 outline-none font-mono"
            />
          </div>

          <div className="flex items-center justify-end gap-3">
            <Button variant="outline" size="sm" onClick={onClose}>
              Close
            </Button>
            <Button type="submit" variant="ai" size="sm" loading={loading} icon={Sparkles}>
              Extract Requirements & Sentiment
            </Button>
          </div>
        </form>

        {result && (
          <div className="mt-6 p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-white uppercase tracking-wider">Analysis Results</h4>
              <span className="text-xs font-bold px-2 py-0.5 rounded bg-blue-500/20 text-blue-300">
                Sentiment: {result.sentiment || 'Positive'}
              </span>
            </div>

            <p className="text-xs text-slate-300 bg-slate-950/50 p-3 rounded-lg border border-slate-800">
              {result.summary}
            </p>

            {result.extracted_requirements?.length > 0 && (
              <div className="space-y-1.5">
                <span className="text-[11px] font-bold text-slate-400">Extracted Scope Items:</span>
                <ul className="text-xs space-y-1 text-slate-200 list-disc list-inside">
                  {result.extracted_requirements.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </Modal>
  );
}
