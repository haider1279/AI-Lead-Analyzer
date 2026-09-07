import React, { useState, useEffect, useCallback } from 'react';
import {
  Search,
  Globe,
  Building2,
  Mail,
  Phone,
  Briefcase,
  ShieldCheck,
  ShieldAlert,
  ShieldOff,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  SlidersHorizontal,
  UploadCloud,
  Sparkles,
  CheckCircle2,
  MapPin,
  ExternalLink,
  Loader2,
} from 'lucide-react';
import { api } from '../services/api';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { EmptyState } from '../components/common/EmptyState';
import { DatasetImportModal } from '../components/discovery/DatasetImportModal';

// ─── Verification Status Helpers ─────────────────────────────────────────────

function VerificationBadge({ status, score }) {
  if (status === 'VERIFIED' || score >= 70) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
        <ShieldCheck className="w-3 h-3" />
        VERIFIED {score != null ? `${score}%` : ''}
      </span>
    );
  }
  if (status === 'REJECTED' || (score != null && score < 70 && score > 0)) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-500/15 text-rose-300 border border-rose-500/30">
        <ShieldAlert className="w-3 h-3" />
        LOW QUALITY {score != null ? `${score}%` : ''}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-500/20 text-slate-400 border border-slate-700">
      <ShieldOff className="w-3 h-3" />
      UNVERIFIED
    </span>
  );
}

// ─── Lead Discovery Card ──────────────────────────────────────────────────────

function DiscoveryLeadCard({ lead, onVerify, verifyingId }) {
  const isVerifying = verifyingId === lead.id;
  const score = lead.verification_score ?? 0;
  const verified = lead.verification_status === 'VERIFIED' || score >= 70;

  return (
    <div className="glass-card rounded-2xl border border-slate-800 hover:border-indigo-500/30 p-5 transition-all group flex flex-col gap-3">
      {/* Header row */}
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-bold text-white group-hover:text-blue-300 transition-colors truncate max-w-xs">
              {lead.company_name || '—'}
            </span>
            <VerificationBadge status={lead.verification_status} score={score} />
          </div>
          {lead.contact_name && (
            <p className="text-xs text-slate-400 mt-0.5 truncate">
              {lead.contact_name}
              {lead.job_title ? ` · ${lead.job_title}` : ''}
            </p>
          )}
        </div>
        <div className="shrink-0 flex items-center gap-1.5">
          {!verified && (
            <Button
              variant="outline"
              size="xs"
              onClick={() => onVerify(lead.id)}
              loading={isVerifying}
              icon={isVerifying ? undefined : Sparkles}
              title="Run verification engine"
            >
              Verify
            </Button>
          )}
        </div>
      </div>

      {/* Meta info */}
      <div className="grid grid-cols-2 gap-x-3 gap-y-1.5 text-[11px] text-slate-400">
        {lead.email && (
          <div className="flex items-center gap-1.5 truncate">
            <Mail className="w-3 h-3 shrink-0 text-blue-400" />
            <span className="truncate">{lead.email}</span>
          </div>
        )}
        {lead.phone && (
          <div className="flex items-center gap-1.5 truncate">
            <Phone className="w-3 h-3 shrink-0 text-purple-400" />
            <span className="truncate">{lead.phone}</span>
          </div>
        )}
        {(lead.industry || lead.country) && (
          <div className="flex items-center gap-1.5 truncate">
            <Briefcase className="w-3 h-3 shrink-0 text-amber-400" />
            <span className="truncate">
              {[lead.industry, lead.country].filter(Boolean).join(' · ')}
            </span>
          </div>
        )}
        {lead.website && (
          <a
            href={lead.website.startsWith('http') ? lead.website : `https://${lead.website}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-cyan-400 hover:text-cyan-300 truncate transition-colors"
          >
            <ExternalLink className="w-3 h-3 shrink-0" />
            <span className="truncate">{lead.website}</span>
          </a>
        )}
        {lead.source && (
          <div className="flex items-center gap-1.5 truncate col-span-2">
            <Globe className="w-3 h-3 shrink-0 text-slate-500" />
            <span className="truncate">Source: {lead.source}</span>
          </div>
        )}
      </div>

      {/* Verification details */}
      {lead.verification_details && typeof lead.verification_details === 'object' && (
        <div className="mt-1 pt-3 border-t border-slate-800/80 grid grid-cols-2 gap-1">
          {Object.entries(lead.verification_details)
            .filter(([, v]) => v !== null && v !== undefined)
            .slice(0, 4)
            .map(([k, v]) => (
              <div key={k} className="flex items-center gap-1 text-[10px]">
                {v === true || v === 'pass' ? (
                  <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />
                ) : (
                  <AlertCircle className="w-3 h-3 text-amber-400 shrink-0" />
                )}
                <span className="text-slate-400 capitalize">{k.replace(/_/g, ' ')}</span>
              </div>
            ))}
        </div>
      )}
    </div>
  );
}

// ─── Main FindLeads Page ──────────────────────────────────────────────────────

export function FindLeads({ onNavigate }) {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [verifyingId, setVerifyingId] = useState(null);
  const [batchVerifying, setBatchVerifying] = useState(false);
  const [showImport, setShowImport] = useState(false);

  // Filters
  const [query, setQuery] = useState('');
  const [country, setCountry] = useState('');
  const [industry, setIndustry] = useState('');
  const [verificationFilter, setVerificationFilter] = useState('');
  const [minScore, setMinScore] = useState(0);
  const [isCandidate, setIsCandidate] = useState('');

  // Pagination
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  const fetchLeads = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = { page, page_size: pageSize };
      if (query.trim()) params.query = query.trim();
      if (country.trim()) params.country = country.trim();
      if (industry.trim()) params.industry = industry.trim();
      if (verificationFilter) params.verification_status = verificationFilter;
      if (minScore > 0) params.min_verification_score = minScore;
      if (isCandidate !== '') params.is_candidate = isCandidate === 'true';

      const res = await api.leads.discover(params);
      setLeads(res.leads || []);
      setTotal(res.total || 0);
      setTotalPages(res.total_pages || 1);
    } catch (err) {
      setError(err.message || 'Failed to load leads.');
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, query, country, industry, verificationFilter, minScore, isCandidate]);

  useEffect(() => {
    fetchLeads();
  }, [fetchLeads]);

  const handleVerify = async (leadId) => {
    setVerifyingId(leadId);
    try {
      const updated = await api.leads.verify(leadId);
      setLeads((prev) => prev.map((l) => (l.id === leadId ? { ...l, ...updated } : l)));
    } catch (err) {
      alert(err.message || 'Verification failed.');
    } finally {
      setVerifyingId(null);
    }
  };

  const handleBatchVerify = async () => {
    const unverifiedIds = leads
      .filter((l) => !l.verification_status || l.verification_status === 'UNVERIFIED')
      .map((l) => l.id)
      .slice(0, 25);

    if (unverifiedIds.length === 0) {
      alert('No unverified leads on this page.');
      return;
    }

    setBatchVerifying(true);
    try {
      const result = await api.leads.verifyBatch(unverifiedIds);
      if (result.results?.length > 0) {
        const updatedMap = {};
        for (const r of result.results) {
          if (r.id) updatedMap[r.id] = r;
        }
        setLeads((prev) => prev.map((l) => (updatedMap[l.id] ? { ...l, ...updatedMap[l.id] } : l)));
      }
      alert(
        `Batch verification complete!\n✅ Verified: ${result.verified_count}\n❌ Rejected: ${result.rejected_count}\n⚠️ Unverified: ${result.unverified_count}`
      );
    } catch (err) {
      alert(err.message || 'Batch verification failed.');
    } finally {
      setBatchVerifying(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    fetchLeads();
  };

  const handleImportSuccess = () => {
    setShowImport(false);
    setPage(1);
    fetchLeads();
  };

  const verifiedCount = leads.filter((l) => (l.verification_score ?? 0) >= 70).length;
  const unverifiedCount = leads.filter(
    (l) => !l.verification_status || l.verification_status === 'UNVERIFIED'
  ).length;

  return (
    <div className="space-y-6">
      {/* ── Page Header ── */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white font-heading tracking-tight">
            Find Leads — Radar
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Discover, verify, and enrich lead data from imported datasets.
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <Button
            variant="outline"
            size="sm"
            icon={Sparkles}
            onClick={handleBatchVerify}
            loading={batchVerifying}
            disabled={leads.length === 0}
            title="Verify all unverified leads on this page (max 25)"
          >
            Verify Page
          </Button>
          <Button
            variant="primary"
            size="sm"
            icon={UploadCloud}
            onClick={() => setShowImport(true)}
          >
            Import Dataset
          </Button>
        </div>
      </div>

      {/* ── Stats Strip ── */}
      {!loading && leads.length > 0 && (
        <div className="flex items-center gap-4 text-xs text-slate-400">
          <span>
            <span className="text-emerald-400 font-bold">{verifiedCount}</span> verified on this page
          </span>
          <span className="text-slate-700">|</span>
          <span>
            <span className="text-amber-400 font-bold">{unverifiedCount}</span> awaiting verification
          </span>
          <span className="text-slate-700">|</span>
          <span>
            <span className="text-slate-200 font-bold">{total}</span> total leads
          </span>
        </div>
      )}

      {/* ── Filters ── */}
      <div className="glass-card rounded-2xl border border-slate-800 p-4">
        <form onSubmit={handleSearch} className="flex flex-wrap gap-3 items-end">
          <div className="flex-1 min-w-48">
            <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
              Search
            </label>
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Company, contact, email..."
                className="w-full bg-slate-900/80 border border-slate-800 focus:border-blue-500 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 outline-none transition-colors"
              />
            </div>
          </div>

          <div className="w-36">
            <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
              Country
            </label>
            <div className="relative">
              <MapPin className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
              <input
                type="text"
                value={country}
                onChange={(e) => setCountry(e.target.value)}
                placeholder="e.g. UK"
                className="w-full bg-slate-900/80 border border-slate-800 focus:border-blue-500 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 outline-none transition-colors"
              />
            </div>
          </div>

          <div className="w-36">
            <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
              Industry
            </label>
            <div className="relative">
              <Building2 className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
              <input
                type="text"
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                placeholder="e.g. FinTech"
                className="w-full bg-slate-900/80 border border-slate-800 focus:border-blue-500 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 outline-none transition-colors"
              />
            </div>
          </div>

          <div className="w-40">
            <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
              Verification
            </label>
            <select
              value={verificationFilter}
              onChange={(e) => setVerificationFilter(e.target.value)}
              className="w-full bg-slate-900/80 border border-slate-800 focus:border-blue-500 rounded-xl px-3 py-2 text-xs text-white outline-none appearance-none"
            >
              <option value="">All Statuses</option>
              <option value="VERIFIED">Verified ✅</option>
              <option value="UNVERIFIED">Unverified</option>
              <option value="REJECTED">Rejected ❌</option>
            </select>
          </div>

          <div className="w-36">
            <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
              Type
            </label>
            <select
              value={isCandidate}
              onChange={(e) => setIsCandidate(e.target.value)}
              className="w-full bg-slate-900/80 border border-slate-800 focus:border-blue-500 rounded-xl px-3 py-2 text-xs text-white outline-none appearance-none"
            >
              <option value="">All Types</option>
              <option value="true">Candidates only</option>
              <option value="false">CRM Leads only</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <Button type="submit" variant="primary" size="sm" icon={Search}>
              Search
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              icon={RefreshCw}
              onClick={() => {
                setQuery('');
                setCountry('');
                setIndustry('');
                setVerificationFilter('');
                setMinScore(0);
                setIsCandidate('');
                setPage(1);
              }}
              title="Reset filters"
            />
          </div>
        </form>
      </div>

      {/* ── Content ── */}
      {loading ? (
        <LoadingSpinner text="Scanning radar for leads..." size="lg" />
      ) : error ? (
        <div className="glass-card rounded-2xl border border-rose-500/30 p-6 text-center">
          <AlertCircle className="w-8 h-8 text-rose-400 mx-auto mb-2" />
          <p className="text-sm font-bold text-white mb-1">Failed to load leads</p>
          <p className="text-xs text-slate-400 mb-4">{error}</p>
          <Button variant="primary" size="sm" onClick={fetchLeads}>
            Retry
          </Button>
        </div>
      ) : leads.length === 0 ? (
        <EmptyState
          icon={Globe}
          title="No leads found"
          description="Import a dataset to discover and verify leads, or adjust your filters."
          action={
            <Button variant="primary" size="md" icon={UploadCloud} onClick={() => setShowImport(true)}>
              Import Dataset
            </Button>
          }
        />
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {leads.map((lead) => (
              <DiscoveryLeadCard
                key={lead.id}
                lead={lead}
                onVerify={handleVerify}
                verifyingId={verifyingId}
              />
            ))}
          </div>

          {/* ── Pagination ── */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-4 border-t border-slate-800/80">
              <p className="text-xs text-slate-400">
                Page {page} of {totalPages} · {total} total leads
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  icon={ChevronLeft}
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                >
                  Next
                  <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}

      {/* ── Dataset Import Modal ── */}
      <DatasetImportModal
        isOpen={showImport}
        onClose={() => setShowImport(false)}
        onSuccess={handleImportSuccess}
      />
    </div>
  );
}
