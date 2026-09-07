import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { DuplicateWarningModal } from './DuplicateWarningModal';
import { PIPELINE_STATUSES, PRIORITIES, LEAD_SOURCES } from '../../utils/constants';

export function LeadFormModal({
  isOpen,
  onClose,
  initialData = null,
  users = [],
  onSuccess,
}) {
  const [companyName, setCompanyName] = useState('');
  const [contactName, setContactName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [website, setWebsite] = useState('');
  const [projectTitle, setProjectTitle] = useState('');
  const [projectDescription, setProjectDescription] = useState('');
  const [budget, setBudget] = useState('');
  const [currency, setCurrency] = useState('USD');
  const [expectedDeadline, setExpectedDeadline] = useState('');
  const [source, setSource] = useState('Upwork');
  const [priority, setPriority] = useState('MEDIUM');
  const [status, setStatus] = useState('NEW');
  const [assignedTo, setAssignedTo] = useState('');
  const [followUpDate, setFollowUpDate] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [duplicateWarningOpen, setDuplicateWarningOpen] = useState(false);
  const [matchedDuplicates, setMatchedDuplicates] = useState([]);

  useEffect(() => {
    if (initialData) {
      setCompanyName(initialData.company_name || '');
      setContactName(initialData.contact_name || '');
      setEmail(initialData.email || '');
      setPhone(initialData.phone || '');
      setWebsite(initialData.website || '');
      setProjectTitle(initialData.project_title || '');
      setProjectDescription(initialData.project_description || '');
      setBudget(initialData.budget !== undefined && initialData.budget !== null ? String(initialData.budget) : '');
      setCurrency(initialData.currency || 'USD');
      setExpectedDeadline(initialData.expected_deadline ? initialData.expected_deadline.slice(0, 10) : '');
      setSource(initialData.source || 'Upwork');
      setPriority(initialData.priority || 'MEDIUM');
      setStatus(initialData.status || 'NEW');
      setAssignedTo(initialData.assigned_to || '');
      setFollowUpDate(initialData.follow_up_date ? initialData.follow_up_date.slice(0, 10) : '');
    } else {
      setCompanyName('');
      setContactName('');
      setEmail('');
      setPhone('');
      setWebsite('');
      setProjectTitle('');
      setProjectDescription('');
      setBudget('');
      setCurrency('USD');
      setExpectedDeadline('');
      setSource('Upwork');
      setPriority('MEDIUM');
      setStatus('NEW');
      setAssignedTo('');
      setFollowUpDate('');
    }
    setError(null);
  }, [initialData, isOpen]);

  const submitForm = async (force = false) => {
    setLoading(true);
    setError(null);
    try {
      const payload = {
        company_name: companyName.trim(),
        contact_name: contactName.trim() || null,
        email: email.trim() || null,
        phone: phone.trim() || null,
        website: website.trim() || null,
        project_title: projectTitle.trim() || null,
        project_description: projectDescription.trim() || null,
        budget: budget ? parseFloat(budget) : null,
        currency,
        expected_deadline: expectedDeadline || null,
        source,
        priority,
        status,
        assigned_to: assignedTo || null,
        follow_up_date: followUpDate || null,
      };

      let result;
      if (initialData?.id) {
        result = await api.leads.update(initialData.id, payload);
      } else {
        result = await api.leads.create(payload, force);
      }

      if (onSuccess) onSuccess(result);
      onClose();
    } catch (err) {
      if (err.status === 409 && err.original?.response?.data?.duplicates) {
        setMatchedDuplicates(err.original.response.data.duplicates);
        setDuplicateWarningOpen(true);
      } else {
        setError(err.message || 'Failed to save lead information.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!companyName.trim()) {
      setError('Company Name is required.');
      return;
    }
    submitForm(false);
  };

  return (
    <>
      <Modal
        isOpen={isOpen}
        onClose={onClose}
        title={initialData ? 'Edit Lead Details' : 'Create New Sales Opportunity'}
        maxWidth="max-w-2xl"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3 rounded-xl bg-rose-500/10 text-rose-400 text-xs border border-rose-500/20">
              {error}
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Company Name <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                required
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="e.g. Apex Financial Corp"
                className="w-full bg-slate-900 border border-slate-800 focus:border-blue-500 rounded-xl px-3.5 py-2 text-xs text-white outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Contact Person</label>
              <input
                type="text"
                value={contactName}
                onChange={(e) => setContactName(e.target.value)}
                placeholder="e.g. Marcus Vance"
                className="w-full bg-slate-900 border border-slate-800 focus:border-blue-500 rounded-xl px-3.5 py-2 text-xs text-white outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Email Address</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="marcus@apex.com"
                className="w-full bg-slate-900 border border-slate-800 focus:border-blue-500 rounded-xl px-3.5 py-2 text-xs text-white outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Phone / WhatsApp</label>
              <input
                type="text"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+1 555 019 2834"
                className="w-full bg-slate-900 border border-slate-800 focus:border-blue-500 rounded-xl px-3.5 py-2 text-xs text-white outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Website</label>
              <input
                type="text"
                value={website}
                onChange={(e) => setWebsite(e.target.value)}
                placeholder="apexfinancial.io"
                className="w-full bg-slate-900 border border-slate-800 focus:border-blue-500 rounded-xl px-3.5 py-2 text-xs text-white outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Inbound Source</label>
              <select
                value={source}
                onChange={(e) => setSource(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 focus:border-blue-500 rounded-xl px-3 py-2 text-xs text-white outline-none"
              >
                {LEAD_SOURCES.map((src) => (
                  <option key={src} value={src}>
                    {src}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Project Title</label>
            <input
              type="text"
              value={projectTitle}
              onChange={(e) => setProjectTitle(e.target.value)}
              placeholder="e.g. Next-gen Banking Platform & iOS App"
              className="w-full bg-slate-900 border border-slate-800 focus:border-blue-500 rounded-xl px-3.5 py-2 text-xs text-white outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Project Description & Client Scope
            </label>
            <textarea
              rows={3}
              value={projectDescription}
              onChange={(e) => setProjectDescription(e.target.value)}
              placeholder="Detail client requirements, features requested, tech stack preferences..."
              className="w-full bg-slate-900 border border-slate-800 focus:border-blue-500 rounded-xl p-3 text-xs text-white outline-none"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Estimated Budget</label>
              <input
                type="number"
                value={budget}
                onChange={(e) => setBudget(e.target.value)}
                placeholder="45000"
                className="w-full bg-slate-900 border border-slate-800 focus:border-blue-500 rounded-xl px-3.5 py-2 text-xs text-white outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Currency</label>
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 focus:border-blue-500 rounded-xl px-3 py-2 text-xs text-white outline-none"
              >
                <option value="USD">USD ($)</option>
                <option value="EUR">EUR (€)</option>
                <option value="GBP">GBP (£)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Target Deadline</label>
              <input
                type="date"
                value={expectedDeadline}
                onChange={(e) => setExpectedDeadline(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 focus:border-blue-500 rounded-xl px-3 py-2 text-xs text-white outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Pipeline Stage</label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 focus:border-blue-500 rounded-xl px-3 py-2 text-xs text-white outline-none"
              >
                {PIPELINE_STATUSES.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Priority</label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 focus:border-blue-500 rounded-xl px-3 py-2 text-xs text-white outline-none"
              >
                {PRIORITIES.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Assigned Employee</label>
              <select
                value={assignedTo}
                onChange={(e) => setAssignedTo(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 focus:border-blue-500 rounded-xl px-3 py-2 text-xs text-white outline-none"
              >
                <option value="">Unassigned</option>
                {users.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Follow-up Date</label>
            <input
              type="date"
              value={followUpDate}
              onChange={(e) => setFollowUpDate(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 focus:border-blue-500 rounded-xl px-3.5 py-2 text-xs text-white outline-none"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
            <Button variant="outline" size="sm" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm" loading={loading}>
              {initialData ? 'Save Changes' : 'Create Opportunity'}
            </Button>
          </div>
        </form>
      </Modal>

      <DuplicateWarningModal
        isOpen={duplicateWarningOpen}
        onClose={() => setDuplicateWarningOpen(false)}
        duplicates={matchedDuplicates}
        onProceedAnyway={() => {
          setDuplicateWarningOpen(false);
          submitForm(true);
        }}
      />
    </>
  );
}
