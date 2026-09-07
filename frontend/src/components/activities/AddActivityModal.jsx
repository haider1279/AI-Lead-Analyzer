import React, { useState } from 'react';
import { api } from '../../services/api';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { ACTIVITY_TYPES } from '../../utils/constants';

export function AddActivityModal({ isOpen, onClose, leadId, onSuccess }) {
  // Default matches backend ActivityType.NOTE enum value exactly: "Note"
  const [type, setType] = useState(ACTIVITY_TYPES.find((t) => t.id === 'Note')?.id || ACTIVITY_TYPES[0].id);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [activityDate, setActivityDate] = useState(new Date().toISOString().slice(0, 16));
  const [followUpDate, setFollowUpDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Pre-submit validation
    if (!leadId) {
      setError('No lead selected. Please close and reopen from a lead page.');
      return;
    }
    if (!type) {
      setError('Please select an activity type.');
      return;
    }
    if (!title.trim()) {
      setError('Summary title is required.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Build ISO datetime strings — never send undefined or Invalid Date
      let parsedActivityDate;
      try {
        parsedActivityDate = activityDate
          ? new Date(activityDate).toISOString()
          : new Date().toISOString();
      } catch {
        parsedActivityDate = new Date().toISOString();
      }

      let parsedFollowUpDate = null;
      if (followUpDate) {
        try {
          const d = new Date(followUpDate);
          if (!isNaN(d.getTime())) {
            parsedFollowUpDate = d.toISOString();
          }
        } catch {
          parsedFollowUpDate = null;
        }
      }

      // Payload matches ActivityCreate schema exactly:
      // lead_id, type (ActivityType enum value), title, description,
      // activity_date (datetime), follow_up_date (datetime | null)
      const payload = {
        lead_id: leadId,
        type,                   // e.g. "Note", "Email", "Follow-up" — exact backend enum value
        title: title.trim(),
        description: description.trim() || null,
        activity_date: parsedActivityDate,
        follow_up_date: parsedFollowUpDate,
      };

      const result = await api.activities.create(payload);
      if (onSuccess) onSuccess(result);
      onClose();
    } catch (err) {
      // Log full backend validation detail to console for debugging
      console.error('[AddActivityModal] Create activity failed:', err);
      console.error('[AddActivityModal] Status:', err.status);
      console.error('[AddActivityModal] Response detail:', err.original?.response?.data);

      // Show a user-friendly message (err.message is already parsed from Pydantic detail by api.js interceptor)
      setError(err.message || 'Unable to log this activity. Please check all required fields and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Log Client Touchpoint / Activity"
      maxWidth="max-w-lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 rounded-xl bg-rose-500/10 text-rose-400 text-xs border border-rose-500/20">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Activity Type</label>
            <select
              value={type}
              onChange={(e) => setType(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 focus:border-blue-500 rounded-xl px-3 py-2 text-xs text-white outline-none"
            >
              {ACTIVITY_TYPES.map((activityType) => (
                <option key={activityType.id} value={activityType.id}>
                  {activityType.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Date &amp; Time</label>
            <input
              type="datetime-local"
              value={activityDate}
              onChange={(e) => setActivityDate(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 focus:border-blue-500 rounded-xl px-3 py-1.5 text-xs text-white outline-none"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5">Summary Title</label>
          <input
            type="text"
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Scope alignment call on Google Meet"
            className="w-full bg-slate-900 border border-slate-800 focus:border-blue-500 rounded-xl px-3.5 py-2 text-xs text-white outline-none"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5">Detailed Notes</label>
          <textarea
            rows={4}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Record client responses, key questions raised, architecture preferences discussed..."
            className="w-full bg-slate-900 border border-slate-800 focus:border-blue-500 rounded-xl p-3 text-xs text-white outline-none"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5">
            Schedule Next Follow-Up (Optional)
          </label>
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
            Save Touchpoint
          </Button>
        </div>
      </form>
    </Modal>
  );
}
