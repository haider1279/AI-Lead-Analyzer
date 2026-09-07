import React, { useState } from 'react';
import { Sparkles, TrendingUp, RefreshCw } from 'lucide-react';
import { api } from '../../services/api';
import { Button } from '../common/Button';

export function AIScoreCard({ lead, onUpdate }) {
  const [loading, setLoading] = useState(false);
  const [scoreData, setScoreData] = useState(null);

  const currentScore = scoreData?.score ?? lead?.lead_score;
  const currentLabel = scoreData?.label ?? lead?.lead_score_label;

  const handleComputeScore = async () => {
    setLoading(true);
    try {
      const res = await api.ai.score(lead.id);
      setScoreData(res);
      if (onUpdate) onUpdate(res);
    } catch (err) {
      alert(err.message || 'Failed to calculate AI score.');
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (sc) => {
    if (!sc && sc !== 0) return 'text-slate-500 border-slate-700';
    if (sc >= 80) return 'text-emerald-400 border-emerald-500/40 bg-emerald-500/10';
    if (sc >= 60) return 'text-blue-400 border-blue-500/40 bg-blue-500/10';
    if (sc >= 40) return 'text-amber-400 border-amber-500/40 bg-amber-500/10';
    return 'text-rose-400 border-rose-500/40 bg-rose-500/10';
  };

  return (
    <div className="glass-card p-5 rounded-2xl border border-slate-800 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">AI Win Probability</h4>
            <p className="text-[11px] text-slate-500">Gemini predictive score (0–100)</p>
          </div>
        </div>

        <Button
          variant="ai"
          size="xs"
          loading={loading}
          onClick={handleComputeScore}
          icon={RefreshCw}
        >
          {currentScore !== undefined && currentScore !== null ? 'Re-Score' : 'Calculate'}
        </Button>
      </div>

      <div className="flex items-center gap-4">
        <div
          className={`w-16 h-16 rounded-2xl border flex flex-col items-center justify-center shrink-0 ${getScoreColor(
            currentScore
          )}`}
        >
          <span className="text-2xl font-extrabold font-heading">
            {currentScore !== undefined && currentScore !== null ? currentScore : '—'}
          </span>
          <span className="text-[9px] font-bold uppercase tracking-wider opacity-80">/100</span>
        </div>

        <div className="space-y-1 text-xs">
          <div className="font-bold text-white flex items-center gap-1.5">
            <span>Score Quality:</span>
            <span
              className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                currentScore >= 75
                  ? 'bg-emerald-500/20 text-emerald-300'
                  : currentScore >= 50
                  ? 'bg-amber-500/20 text-amber-300'
                  : 'bg-rose-500/20 text-rose-300'
              }`}
            >
              {currentLabel || (currentScore ? `${currentScore}% Match` : 'Uncalculated')}
            </span>
          </div>

          <p className="text-[11px] text-slate-400 leading-relaxed">
            {scoreData?.explanation ||
              'Click Calculate to let Gemini analyze project scope, budget, and contact details to determine conversion likelihood.'}
          </p>
        </div>
      </div>
    </div>
  );
}
