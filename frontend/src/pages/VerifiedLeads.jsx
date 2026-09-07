import React, { useState, useEffect, useCallback } from 'react';
import {
  ShieldCheck,
  CheckCircle2,
  Sparkles,
  Search,
  Globe,
  Building2,
  ArrowRight,
  ExternalLink,
  KanbanSquare,
  FileText,
  UserCheck,
  ChevronLeft,
  ChevronRight,
  SlidersHorizontal,
} from 'lucide-react';
import { api } from '../services/api';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { EmptyState } from '../components/common/EmptyState';

export function VerifiedLeads({ onSelectLead, onNavigate }) {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [query, setQuery] = useState('');
  const [country, setCountry] = useState('');
  const [industry, setIndustry] = useState('');
  const [minScore, setMinScore] = useState(70);

  // Pagination
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalLeads, setTotalLeads] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  const fetchVerifiedLeads = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        page,
        page_size: pageSize,
        min_verification_score: minScore,
      };
      if (query.trim()) params.query = query.trim();
      if (country.trim()) params.country = country.trim();
      if (industry.trim()) params.industry = industry.trim();

      const res = await api.leads.getVerified(params);
      setLeads(res.leads || []);
      setTotalLeads(res.total || 0);
      setTotalPages(res.total_pages || 1);
    } catch (err) {
      setError(err.message || 'Failed to fetch verified leads');
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, query, country, industry, minScore]);

  useEffect(() => {
    fetchVerifiedLeads();
  }, [fetchVerifiedLeads]);

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      {/* Top Banner */}
      <div className="p-6 rounded-2xl glass-panel border border-emerald-500/20 bg-emerald-950/20 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-2xl bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center shrink-0">
            <ShieldCheck className="w-6 h-6 text-emerald-400" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h2 className="text-xl font-extrabold text-white font-heading tracking-tight">
                Verified Leads Intelligence Directory
              </h2>
              <Badge variant="emerald" className="font-bold">
                {totalLeads} Verified & High-Confidence
              </Badge>
            </div>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl">
              These records have passed deterministic data integrity checks (DNS MX resolution, website reachability, and corporate domain matching). Ready for high-conversion outreach and AI scoping.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button variant="outline" onClick={() => onNavigate && onNavigate('find-leads')}>
            <Search className="w-4 h-4 mr-2" />
            Find More Candidates
          </Button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="p-4 rounded-2xl glass-panel border border-slate-800/80 bg-slate-900/40 grid grid-cols-1 md:grid-cols-4 gap-3">
        <div className="relative md:col-span-2">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setPage(1);
            }}
            placeholder="Search verified company, person, or industry..."
            className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        <div>
          <input
            type="text"
            value={country}
            onChange={(e) => {
              setCountry(e.target.value);
              setPage(1);
            }}
            placeholder="Filter Country (e.g. Germany)"
            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        <div>
          <select
            value={minScore}
            onChange={(e) => {
              setMinScore(Number(e.target.value));
              setPage(1);
            }}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
          >
            <option value="70">Min Score: 70%+ (Verified)</option>
            <option value="80">Min Score: 80%+ (High Quality)</option>
            <option value="90">Min Score: 90%+ (Gold Standard)</option>
          </select>
        </div>
      </div>

      {/* Cards List */}
      {loading ? (
        <div className="p-16 text-center">
          <LoadingSpinner size="lg" />
          <p className="text-xs text-slate-400 mt-3">Loading verified opportunities...</p>
        </div>
      ) : error ? (
        <div className="p-6 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
          {error}
        </div>
      ) : leads.length === 0 ? (
        <EmptyState
          title="No verified leads found"
          description="Try lowering the minimum verification score filter or run verification checks on discovered candidate leads."
          actionText="Discover Leads"
          onAction={() => onNavigate && onNavigate('find-leads')}
        />
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {leads.map((lead) => {
              const score = lead.verification_score ?? 0;
              const checks = lead.verification_details?.checks || {};

              return (
                <div
                  key={lead.id}
                  onClick={() => onSelectLead && onSelectLead(lead.id)}
                  className="p-5 rounded-2xl glass-panel border border-slate-800 bg-slate-900/50 hover:border-emerald-500/40 hover:bg-slate-900/90 transition-all cursor-pointer space-y-4 group"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <Building2 className="w-4 h-4 text-emerald-400 shrink-0" />
                        <h3 className="text-sm font-bold text-white group-hover:text-emerald-300 transition-colors truncate">
                          {lead.company_name}
                        </h3>
                      </div>
                      <p className="text-xs text-slate-300 mt-1">
                        {lead.contact_name ? (
                          <span className="font-semibold">{lead.contact_name}</span>
                        ) : (
                          <span className="text-slate-500">Contact not specified</span>
                        )}
                        {lead.job_title && (
                          <span className="text-slate-400 font-normal"> • {lead.job_title}</span>
                        )}
                      </p>
                    </div>

                    <div className="text-right shrink-0">
                      <Badge
                        variant={score >= 75 ? 'emerald' : 'amber'}
                        className="font-extrabold text-xs"
                      >
                        <CheckCircle2 className="w-3 h-3 mr-1" />
                        {score}% Integrity
                      </Badge>

                    </div>
                  </div>

                  {/* Verification Check Badges */}
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {checks.email_mx_dns?.passed && (
                      <span className="text-[10px] px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 font-medium">
                        ✓ MX Active
                      </span>
                    )}
                    {checks.website_reachability?.passed && (
                      <span className="text-[10px] px-2 py-0.5 rounded-md bg-blue-500/10 text-blue-300 border border-blue-500/20 font-medium">
                        ✓ Web Reachable
                      </span>
                    )}
                    {checks.email_domain_match?.passed && (
                      <span className="text-[10px] px-2 py-0.5 rounded-md bg-purple-500/10 text-purple-300 border border-purple-500/20 font-medium">
                        ✓ Corporate Match
                      </span>
                    )}
                    {lead.country && (
                      <span className="text-[10px] px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700 font-medium flex items-center gap-1">
                        <Globe className="w-2.5 h-2.5" />
                        {lead.country}
                      </span>
                    )}
                  </div>

                  {/* Footer metadata & Action */}
                  <div className="flex items-center justify-between pt-3 border-t border-slate-800/80 text-[11px] text-slate-400">
                    <span className="font-mono text-[10px] text-slate-300 truncate max-w-[200px]">
                      {lead.email || lead.website || 'Verified Record'}
                    </span>

                    <span className="text-emerald-400 font-semibold flex items-center gap-1 group-hover:translate-x-0.5 transition-transform">
                      View Intelligence & AI Analysis
                      <ArrowRight className="w-3 h-3" />
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between px-2 pt-2">
            <span className="text-xs text-slate-400">
              Showing {(page - 1) * pageSize + 1} to{' '}
              {Math.min(page * pageSize, totalLeads)} of {totalLeads} verified leads
            </span>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <span className="text-xs font-semibold text-white px-2">
                Page {page} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
