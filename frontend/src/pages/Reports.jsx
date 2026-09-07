import React, { useState, useEffect } from 'react';
import {
  Download,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import { api } from '../services/api';
import { formatCurrency } from '../utils/formatters';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { Button } from '../components/common/Button';

export function Reports() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  const fetchSummary = async () => {
    setLoading(true);
    try {
      const data = await api.reports.getSummary();
      setSummary(data);
    } catch (err) {
      alert(err.message || 'Failed to load report analytics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  const handleExportCsv = async () => {
    setExporting(true);
    try {
      await api.reports.exportCsv();
    } catch (err) {
      alert(err.message || 'Failed to export CSV.');
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return <LoadingSpinner text="Aggregating sales intelligence reports..." size="lg" />;
  }

  if (!summary) {
    return null;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 glass-card p-4 rounded-2xl border border-slate-800">
        <div>
          <h2 className="text-base font-bold text-white tracking-tight">Executive Sales Reports & Analytics</h2>
          <p className="text-xs text-slate-400">
            Channel conversion metrics, pipeline velocity, and full data export
          </p>
        </div>

        <Button
          variant="primary"
          size="sm"
          onClick={handleExportCsv}
          loading={exporting}
          icon={Download}
        >
          Download Full CSV Export
        </Button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-card p-5 rounded-2xl border border-slate-800">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Active Pipeline
          </span>
          <div className="text-2xl font-extrabold text-blue-400 font-heading mb-1">
            {formatCurrency(summary.total_pipeline_value)}
          </div>
          <p className="text-xs text-slate-500">{summary.active_leads_count} ongoing deals</p>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-slate-800">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Closed Won Revenue
          </span>
          <div className="text-2xl font-extrabold text-emerald-400 font-heading mb-1">
            {formatCurrency(summary.won_pipeline_value)}
          </div>
          <p className="text-xs text-slate-500">{summary.won_leads_count} signed contracts</p>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-slate-800">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Overall Win Rate
          </span>
          <div className="text-2xl font-extrabold text-white font-heading mb-1">
            {summary.conversion_rate}%
          </div>
          <p className="text-xs text-slate-500">Won / (Won + Lost)</p>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-slate-800">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Lost Value
          </span>
          <div className="text-2xl font-extrabold text-rose-400 font-heading mb-1">
            {formatCurrency(summary.lost_pipeline_value)}
          </div>
          <p className="text-xs text-slate-500">{summary.lost_leads_count} lost opportunities</p>
        </div>
      </div>

      <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-white tracking-tight">Channel Conversion Efficiency</h3>
            <p className="text-xs text-slate-400">Performance comparison across marketing & lead channels</p>
          </div>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={summary.source_efficiency || []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
              <XAxis dataKey="source" stroke="#64748b" fontSize={11} tickLine={false} />
              <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    return (
                      <div className="p-3 rounded-xl bg-slate-900 border border-slate-700 shadow-xl text-xs space-y-1">
                        <p className="font-bold text-white">{data.source}</p>
                        <p className="text-blue-400">Total Leads: {data.total_leads}</p>
                        <p className="text-emerald-400">Won Deals: {data.won_leads} ({data.conversion_rate}%)</p>
                        <p className="text-slate-300">Won Value: {formatCurrency(data.won_value)}</p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Bar dataKey="total_leads" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Total Leads" />
              <Bar dataKey="won_leads" fill="#10b981" radius={[4, 4, 0, 0]} name="Won Deals" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="overflow-x-auto rounded-xl border border-slate-800/80">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900/80 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                <th className="py-3 px-4">Channel Source</th>
                <th className="py-3 px-4">Total Volume</th>
                <th className="py-3 px-4">Won Deals</th>
                <th className="py-3 px-4">Conversion Rate</th>
                <th className="py-3 px-4">Pipeline Value</th>
                <th className="py-3 px-4 text-right">Realized Revenue</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {summary.source_efficiency?.map((s, idx) => (
                <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3 px-4 font-bold text-white">{s.source}</td>
                  <td className="py-3 px-4 text-slate-300">{s.total_leads}</td>
                  <td className="py-3 px-4 text-emerald-400 font-semibold">{s.won_leads}</td>
                  <td className="py-3 px-4 font-semibold text-blue-400">{s.conversion_rate}%</td>
                  <td className="py-3 px-4 text-slate-300">{formatCurrency(s.total_value)}</td>
                  <td className="py-3 px-4 text-right font-bold text-emerald-400">{formatCurrency(s.won_value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
