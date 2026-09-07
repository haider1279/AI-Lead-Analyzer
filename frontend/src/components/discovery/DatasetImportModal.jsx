import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  FileSpreadsheet,
  CheckCircle2,
  XCircle,
  AlertCircle,
  ArrowRight,
  RefreshCw,
  SlidersHorizontal,
  Layers,
  Sparkles,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  X,
  BadgeCheck,
  ShieldAlert,
} from 'lucide-react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { api } from '../../services/api';

const TARGET_FIELDS = [
  { id: 'company_name', label: 'Company Name', required: true },
  { id: 'contact_name', label: 'Contact Name', required: false },
  { id: 'job_title', label: 'Job Title / Role', required: false },
  { id: 'email', label: 'Email Address', required: false },
  { id: 'phone', label: 'Phone Number', required: false },
  { id: 'website', label: 'Website / Domain', required: false },
  { id: 'country', label: 'Country', required: false },
  { id: 'industry', label: 'Industry / Vertical', required: false },
  { id: 'budget', label: 'Est. Budget', required: false },
  { id: 'project_description', label: 'Description / Notes', required: false },
];

function formatErrorMessage(err, fallback = 'Operation failed.') {
  if (!err) return fallback;
  if (typeof err === 'string') return err;
  if (typeof err.message === 'string') return err.message;
  if (typeof err.detail === 'string') return err.detail;
  if (Array.isArray(err.detail)) {
    return err.detail.map((d) => (typeof d === 'string' ? d : d?.msg || JSON.stringify(d))).join(', ');
  }
  return fallback;
}

export function DatasetImportModal({ isOpen, onClose, onSuccess }) {
  const [step, setStep] = useState(1); // 1: Upload, 2: Mapping, 3: Executing, 4: Results
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Preview data
  const [detectedHeaders, setDetectedHeaders] = useState([]);
  const [previewRows, setPreviewRows] = useState([]);
  const [totalPreviewRows, setTotalPreviewRows] = useState(0);
  const [mappings, setMappings] = useState({});

  // Options
  const [autoVerify, setAutoVerify] = useState(true);
  const [sourceName, setSourceName] = useState('CSV Import');

  // Import Results
  const [importStats, setImportStats] = useState(null);

  // Rejection detail panel
  const [showRejections, setShowRejections] = useState(false);

  const fileInputRef = useRef(null);

  const resetModal = () => {
    setStep(1);
    setFile(null);
    setLoading(false);
    setError(null);
    setDetectedHeaders([]);
    setPreviewRows([]);
    setMappings({});
    setImportStats(null);
    setShowRejections(false);
  };

  const handleClose = () => {
    resetModal();
    onClose();
  };

  const handleFileSelect = async (selectedFile) => {
    if (!selectedFile) return;

    const fn = selectedFile.name.toLowerCase();
    if (!fn.endsWith('.csv') && !fn.endsWith('.xlsx') && !fn.endsWith('.xls')) {
      setError('Please upload a valid CSV or XLSX spreadsheet file.');
      return;
    }

    setFile(selectedFile);
    setError(null);
    setLoading(true);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const res = await api.leads.previewImport(formData);
      setDetectedHeaders(res.detected_headers || []);
      setPreviewRows(res.preview_rows || []);
      setTotalPreviewRows(res.total_preview_rows || 0);
      setMappings(res.suggested_mappings || {});
      setSourceName(selectedFile.name.replace(/\.[^/.]+$/, ''));
      setStep(2);
    } catch (err) {
      setError(formatErrorMessage(err, 'Failed to read spreadsheet preview.'));
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleMappingChange = (fileCol, targetField) => {
    setMappings((prev) => ({
      ...prev,
      [fileCol]: targetField,
    }));
  };

  const handleStartImport = async () => {
    // Validate that company_name or contact+email is mapped
    const hasCompany = Object.values(mappings).includes('company_name');
    const hasContact = Object.values(mappings).includes('contact_name');
    const hasEmail = Object.values(mappings).includes('email');

    if (!hasCompany && !(hasContact && hasEmail)) {
      setError('Please map at least the "Company Name" or "Contact Name & Email" column to proceed.');
      return;
    }

    setLoading(true);
    setError(null);
    setStep(3);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('column_mapping', JSON.stringify(mappings));
    formData.append('auto_verify', autoVerify);
    formData.append('source_name', sourceName || 'Dataset Import');

    try {
      const res = await api.leads.executeImport(formData);
      setImportStats(res);
      setStep(4);
      if (onSuccess) {
        onSuccess(res);
      }
    } catch (err) {
      setError(formatErrorMessage(err, 'Import execution failed.'));
      setStep(2);
    } finally {
      setLoading(false);
    }
  };

  const acceptanceRate = importStats
    ? Math.round(((importStats.accepted_rows ?? importStats.verified_rows) / Math.max(importStats.valid_rows, 1)) * 100)
    : 0;

  const threshold = importStats?.rejection_threshold ?? 70;

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={
        step === 1
          ? '📥 Import Lead Discovery Dataset'
          : step === 2
          ? '🔍 Preview & Column Mapping'
          : step === 3
          ? '⚙️ Verifying & Applying 70% Gate...'
          : '🎉 Import & Verification Report'
      }
      maxWidth="max-w-4xl"
    >
      <div className="space-y-6">
        {/* Step Indicator */}
        <div className="flex items-center justify-between px-2">
          {[
            { num: 1, label: 'Upload' },
            { num: 2, label: 'Mapping & Options' },
            { num: 3, label: 'Verifying' },
            { num: 4, label: 'Results' },
          ].map((s, idx) => (
            <div key={s.num} className="flex items-center gap-2">
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                  step === s.num
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/25 ring-2 ring-blue-500/30'
                    : step > s.num
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : 'bg-slate-800 text-slate-500'
                }`}
              >
                {step > s.num ? '✓' : s.num}
              </div>
              <span
                className={`text-xs font-semibold ${
                  step === s.num ? 'text-white' : 'text-slate-500'
                }`}
              >
                {s.label}
              </span>
              {idx < 3 && <div className="w-8 h-px bg-slate-800 mx-2" />}
            </div>
          ))}
        </div>

        {error && (
          <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-start gap-3 text-xs text-rose-300 animate-fadeIn">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-400 mt-0.5" />
            <div className="flex-1">{typeof error === 'string' ? error : (error?.message || 'An error occurred during import.')}</div>
            <button onClick={() => setError(null)} className="text-rose-400 hover:text-white">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* STEP 1: UPLOAD */}
        {step === 1 && (
          <div className="space-y-4">
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-slate-700 hover:border-blue-500/60 rounded-2xl p-10 text-center cursor-pointer transition-all bg-slate-900/40 hover:bg-slate-900/80 group"
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv, .xlsx, .xls"
                className="hidden"
                onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
              />
              <div className="w-14 h-14 rounded-2xl bg-blue-600/10 border border-blue-500/20 flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
                <UploadCloud className="w-7 h-7 text-blue-400" />
              </div>
              <h4 className="text-sm font-bold text-white font-heading">
                Upload CSV or Excel Dataset
              </h4>
              <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                Drag and drop your spreadsheet file here, or click to browse. Supports{' '}
                <span className="text-blue-400 font-semibold">.csv</span> and{' '}
                <span className="text-blue-400 font-semibold">.xlsx</span> up to 10MB.
              </p>
            </div>

            {/* 70% Gate info card */}
            <div className="p-3.5 rounded-xl bg-amber-500/8 border border-amber-500/25 flex items-start gap-3">
              <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <p className="text-xs font-bold text-amber-300">70% Verification Gate Active</p>
                <p className="text-[10px] text-amber-200/70 mt-0.5">
                  Only leads that score ≥ 70% across email, website, company, contact, and phone
                  signals will be stored in the database. Leads scoring below 70% are rejected
                  server-side and never inserted.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3 pt-1">
              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-left">
                <ShieldCheck className="w-4 h-4 text-emerald-400 mb-1.5" />
                <p className="text-[11px] font-bold text-white">Multi-Signal Verification</p>
                <p className="text-[10px] text-slate-400">
                  Email, website, DNS/MX, phone, company & completeness scoring.
                </p>
              </div>
              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-left">
                <Layers className="w-4 h-4 text-blue-400 mb-1.5" />
                <p className="text-[11px] font-bold text-white">Duplicate Detection</p>
                <p className="text-[10px] text-slate-400">
                  Flags existing email and company records automatically.
                </p>
              </div>
              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-left">
                <Sparkles className="w-4 h-4 text-purple-400 mb-1.5" />
                <p className="text-[11px] font-bold text-white">AI Analysis Ready</p>
                <p className="text-[10px] text-slate-400">
                  Accepted leads can be analyzed with 1-click Gemini intelligence.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* STEP 2: PREVIEW & COLUMN MAPPING */}
        {step === 2 && (
          <div className="space-y-5">
            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <div className="flex items-center gap-3">
                <FileSpreadsheet className="w-5 h-5 text-blue-400" />
                <div>
                  <p className="text-xs font-bold text-white">{file?.name}</p>
                  <span className="text-[10px] text-slate-400">
                    {totalPreviewRows} detected rows • {detectedHeaders.length} columns found
                  </span>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setStep(1);
                  setFile(null);
                }}
              >
                Change File
              </Button>
            </div>

            {/* Mapping Grid */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                  Map Spreadsheet Columns
                </label>
                <span className="text-[11px] text-slate-400">
                  * Company Name is required
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2.5 max-h-56 overflow-y-auto pr-1">
                {detectedHeaders.map((header) => (
                  <div
                    key={header}
                    className="p-2.5 rounded-xl bg-slate-900/50 border border-slate-800/80 flex items-center justify-between gap-3"
                  >
                    <div className="min-w-0">
                      <p className="text-xs font-semibold text-white truncate">{header}</p>
                      <span className="text-[10px] text-slate-500 truncate block">
                        e.g. "{previewRows[0]?.[header] || '...'}"
                      </span>
                    </div>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-600 shrink-0" />
                    <select
                      value={mappings[header] || ''}
                      onChange={(e) => handleMappingChange(header, e.target.value)}
                      className="text-xs bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-blue-500 shrink-0 w-44"
                    >
                      <option value="">-- Ignore Column --</option>
                      {TARGET_FIELDS.map((tf) => (
                        <option key={tf.id} value={tf.id}>
                          {tf.label} {tf.required ? '*' : ''}
                        </option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>
            </div>

            {/* Options */}
            <div className="p-3.5 rounded-xl bg-slate-900/40 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <div>
                    <p className="text-xs font-bold text-white">Auto-Verify & Apply 70% Gate</p>
                    <p className="text-[10px] text-slate-400">
                      Performs live DNS/MX, HTTP, phone & email checks. Only leads scoring ≥ 70% are stored.
                    </p>
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={autoVerify}
                  onChange={(e) => setAutoVerify(e.target.checked)}
                  className="w-4 h-4 rounded text-blue-600 bg-slate-950 border-slate-700 focus:ring-blue-500"
                />
              </div>

              <div className="flex items-center justify-between gap-3 pt-2 border-t border-slate-800/60">
                <label className="text-xs font-medium text-slate-300 shrink-0">
                  Dataset Source Tag:
                </label>
                <input
                  type="text"
                  value={sourceName}
                  onChange={(e) => setSourceName(e.target.value)}
                  placeholder="e.g. Q3 Tech Leads CSV"
                  className="text-xs bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-slate-200 w-64 focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-end gap-3 pt-2">
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button variant="primary" onClick={handleStartImport} loading={loading}>
                Execute Import & 70% Gate Verification
              </Button>
            </div>
          </div>
        )}

        {/* STEP 3: PROCESSING */}
        {step === 3 && (
          <div className="py-8 px-4 space-y-6 text-center animate-fadeIn">
            <div className="relative w-16 h-16 mx-auto">
              <div className="absolute inset-0 rounded-full border-4 border-blue-500/20 animate-ping" />
              <div className="w-16 h-16 rounded-full bg-blue-600/10 border-2 border-blue-500 flex items-center justify-center">
                <RefreshCw className="w-8 h-8 text-blue-400 animate-spin" />
              </div>
            </div>

            <div>
              <h4 className="text-base font-bold text-white font-heading">
                Verifying Records & Applying 70% Gate...
              </h4>
              <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
                Processing <span className="text-blue-400 font-semibold">{totalPreviewRows || 'dataset'}</span> rows.
                Leads scoring below 70% will be rejected server-side.
              </p>
            </div>

            {/* Stage Breakdown Checklist */}
            <div className="max-w-md mx-auto p-4 rounded-xl bg-slate-900/70 border border-slate-800 space-y-3 text-left">
              <div className="flex items-center gap-2.5 text-xs text-slate-300">
                <div className="w-4 h-4 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-[10px] font-bold">✓</div>
                <span>CSV / XLSX Parsing & Field Normalization</span>
              </div>
              <div className="flex items-center gap-2.5 text-xs text-slate-200">
                <div className="w-4 h-4 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-[10px] font-bold animate-pulse">●</div>
                <span>Multi-Signal Verification: Email · Website · DNS · Phone · Company (Max concurrency: 20)</span>
              </div>
              <div className="flex items-center gap-2.5 text-xs text-slate-400">
                <div className="w-4 h-4 rounded-full bg-amber-500/20 text-amber-400 flex items-center justify-center text-[10px]">⚡</div>
                <span>Applying 70% Acceptance Gate — Rejecting low-quality leads</span>
              </div>
              <div className="flex items-center gap-2.5 text-xs text-slate-400">
                <div className="w-4 h-4 rounded-full bg-slate-800 text-slate-500 flex items-center justify-center text-[10px]">○</div>
                <span>Batched Supabase Insertion (accepted leads only)</span>
              </div>
            </div>

            <div className="w-full bg-slate-800/80 rounded-full h-1.5 overflow-hidden max-w-md mx-auto">
              <div className="bg-gradient-to-r from-blue-500 via-emerald-400 to-blue-500 h-full w-full animate-pulse" />
            </div>
          </div>
        )}

        {/* STEP 4: RESULTS REPORT */}
        {step === 4 && importStats && (
          <div className="space-y-5 animate-fadeIn">
            {/* Summary Banner */}
            {(importStats.rejected_rows ?? 0) === 0 ? (
              <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center gap-3">
                <CheckCircle2 className="w-6 h-6 text-emerald-400 shrink-0" />
                <div>
                  <h4 className="text-sm font-bold text-white font-heading">
                    All {importStats.accepted_rows ?? importStats.verified_rows} leads passed the {threshold}% verification threshold
                  </h4>
                  <p className="text-xs text-emerald-300">
                    All valid records met the quality bar and have been stored in your database.
                  </p>
                </div>
              </div>
            ) : (
              <div className="p-4 rounded-2xl bg-blue-500/10 border border-blue-500/30 flex items-center gap-3">
                <BadgeCheck className="w-6 h-6 text-blue-400 shrink-0" />
                <div>
                  <h4 className="text-sm font-bold text-white font-heading">
                    {importStats.accepted_rows ?? importStats.verified_rows} leads passed the {threshold}% threshold
                    {' '}— {importStats.rejected_rows} rejected
                  </h4>
                  <p className="text-xs text-blue-300">
                    Rejected leads were not inserted into the database.
                    Acceptance rate: <span className="font-bold text-white">{acceptanceRate}%</span>
                  </p>
                </div>
              </div>
            )}

            {/* Threshold badge */}
            <div className="flex items-center gap-2 px-1">
              <div className="h-px flex-1 bg-slate-800" />
              <span className="text-[10px] text-amber-400 font-bold border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 rounded-full">
                ACCEPTANCE THRESHOLD: {threshold}%
              </span>
              <div className="h-px flex-1 bg-slate-800" />
            </div>

            {/* Real Statistics Grid */}
            <div className="grid grid-cols-3 gap-3">
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-center">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                  Total Rows
                </span>
                <span className="text-2xl font-extrabold text-white mt-1 block">
                  {importStats.total_rows}
                </span>
              </div>

              <div className="p-4 rounded-xl bg-emerald-900/30 border border-emerald-700/40 text-center">
                <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider block">
                  ✓ Accepted (≥{threshold}%)
                </span>
                <span className="text-2xl font-extrabold text-emerald-400 mt-1 block">
                  {importStats.accepted_rows ?? importStats.verified_rows}
                </span>
                <span className="text-[10px] text-emerald-600">Inserted into database</span>
              </div>

              <div className="p-4 rounded-xl bg-rose-900/20 border border-rose-700/30 text-center">
                <span className="text-[11px] font-semibold text-rose-400 uppercase tracking-wider block">
                  ✗ Rejected (&lt;{threshold}%)
                </span>
                <span className="text-2xl font-extrabold text-rose-400 mt-1 block">
                  {importStats.rejected_rows ?? 0}
                </span>
                <span className="text-[10px] text-rose-600">Not inserted</span>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-center">
                <span className="text-[11px] font-semibold text-amber-400 uppercase tracking-wider block">
                  Duplicates
                </span>
                <span className="text-2xl font-extrabold text-amber-400 mt-1 block">
                  {importStats.duplicate_rows}
                </span>
                <span className="text-[10px] text-amber-700">Skipped</span>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-center">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                  Invalid Rows
                </span>
                <span className="text-2xl font-extrabold text-slate-300 mt-1 block">
                  {importStats.invalid_rows}
                </span>
                <span className="text-[10px] text-slate-600">Missing required fields</span>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-center">
                <span className="text-[11px] font-semibold text-blue-400 uppercase tracking-wider block">
                  Acceptance Rate
                </span>
                <span className="text-2xl font-extrabold text-blue-400 mt-1 block">
                  {acceptanceRate}%
                </span>
                <span className="text-[10px] text-blue-700">of valid leads</span>
              </div>
            </div>

            {/* Rejection Details panel */}
            {importStats.rejection_details && importStats.rejection_details.length > 0 && (
              <div className="rounded-xl border border-rose-500/25 overflow-hidden">
                <button
                  onClick={() => setShowRejections((v) => !v)}
                  className="w-full flex items-center justify-between px-4 py-3 bg-rose-500/10 hover:bg-rose-500/15 transition-colors text-left"
                >
                  <div className="flex items-center gap-2">
                    <XCircle className="w-4 h-4 text-rose-400" />
                    <span className="text-xs font-bold text-rose-300">
                      {importStats.rejection_details.length} Rejected Lead{importStats.rejection_details.length !== 1 ? 's' : ''} — Details
                    </span>
                  </div>
                  {showRejections ? (
                    <ChevronUp className="w-4 h-4 text-rose-400" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-rose-400" />
                  )}
                </button>

                {showRejections && (
                  <div className="max-h-64 overflow-y-auto bg-slate-950/60 divide-y divide-slate-800">
                    {importStats.rejection_details.slice(0, 100).map((rd, idx) => (
                      <div key={idx} className="px-4 py-3">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-bold text-slate-200">
                            Row #{rd.row_number} — {rd.company_name}
                          </span>
                          <span className="text-[11px] font-bold text-rose-400 border border-rose-500/30 bg-rose-500/10 px-2 py-0.5 rounded-full">
                            {rd.score}% score
                          </span>
                        </div>
                        <ul className="space-y-0.5">
                          {Array.isArray(rd.reasons) && rd.reasons.slice(0, 5).map((reason, ri) => (
                            <li key={ri} className="text-[10px] text-slate-400 flex items-start gap-1.5">
                              <span className="text-rose-500 mt-0.5 shrink-0">•</span>
                              <span>{typeof reason === 'string' ? reason : (reason?.detail || reason?.msg || JSON.stringify(reason))}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    ))}
                    {importStats.rejection_details.length > 100 && (
                      <div className="px-4 py-2 text-center text-[10px] text-slate-500">
                        Showing first 100 of {importStats.rejection_details.length} rejections
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            <div className="flex items-center justify-end gap-3 pt-2">
              <Button variant="primary" onClick={handleClose}>
                Done & View Accepted Leads
              </Button>
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
}
