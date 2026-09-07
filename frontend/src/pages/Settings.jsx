import React, { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon,
  User,
  Tags,
  Server,
  Plus,
  Trash2,
  CheckCircle,
} from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../auth/AuthContext';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { Button } from '../components/common/Button';

export function Settings() {
  const { user, isAdmin } = useAuth();

  const [profileName, setProfileName] = useState(user?.name || '');
  const [profileEmail, setProfileEmail] = useState(user?.email || '');
  const [sources, setSources] = useState([]);
  const [newSourceName, setNewSourceName] = useState('');
  const [systemConfig, setSystemConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [savingProfile, setSavingProfile] = useState(false);
  const [addingSource, setAddingSource] = useState(false);
  const [toast, setToast] = useState(null);

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const [sourcesData, sysData] = await Promise.all([
        api.settings.getSources().catch(() => []),
        api.settings.getSystem().catch(() => null),
      ]);
      setSources(sourcesData);
      setSystemConfig(sysData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    setSavingProfile(true);
    try {
      await api.auth.updateMe({ name: profileName });
      setToast('Profile name updated successfully!');
      setTimeout(() => setToast(null), 3000);
    } catch (err) {
      alert(err.message || 'Failed to update profile.');
    } finally {
      setSavingProfile(false);
    }
  };

  const handleAddSource = async (e) => {
    e.preventDefault();
    if (!newSourceName.trim()) return;

    setAddingSource(true);
    try {
      const created = await api.settings.createSource(newSourceName.trim());
      setSources((prev) => [...prev, created]);
      setNewSourceName('');
      setToast(`Added custom source '${created.name}'!`);
      setTimeout(() => setToast(null), 3000);
    } catch (err) {
      alert(err.message || 'Failed to add source.');
    } finally {
      setAddingSource(false);
    }
  };

  const handleDeleteSource = async (id) => {
    try {
      await api.settings.deleteSource(id);
      setSources((prev) => prev.filter((s) => s.id !== id));
    } catch (err) {
      alert(err.message || 'Failed to delete lead source.');
    }
  };

  if (loading) {
    return <LoadingSpinner text="Loading system preferences..." size="md" />;
  }

  return (
    <div className="space-y-6 max-w-4xl">
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 p-4 rounded-xl bg-emerald-600 text-white text-xs font-semibold shadow-2xl flex items-center gap-2 animate-slideUp">
          <CheckCircle className="w-4 h-4" />
          <span>{toast}</span>
        </div>
      )}

      <div className="glass-card p-4 rounded-2xl border border-slate-800">
        <div className="flex items-center gap-2 mb-1">
          <SettingsIcon className="w-4 h-4 text-blue-400" />
          <h2 className="text-base font-bold text-white tracking-tight">System & Profile Settings</h2>
        </div>
        <p className="text-xs text-slate-400">
          Configure your personal preferences, lead sources, and view active environment diagnostics
        </p>
      </div>

      <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4">
        <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
          <User className="w-4 h-4 text-purple-400" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">Your Profile</h3>
        </div>

        <form onSubmit={handleSaveProfile} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Full Name</label>
            <input
              type="text"
              value={profileName}
              onChange={(e) => setProfileName(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 focus:border-blue-500 rounded-xl px-3.5 py-2 text-xs text-white outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Email Address</label>
            <input
              type="email"
              disabled
              value={profileEmail}
              className="w-full bg-slate-900/50 border border-slate-800/80 rounded-xl px-3.5 py-2 text-xs text-slate-500 cursor-not-allowed"
            />
          </div>

          <div className="sm:col-span-2 flex items-center justify-between pt-2">
            <span className="text-xs text-slate-500">
              Role: <b className="text-slate-300 capitalize">{user?.role}</b> (Managed by Admin)
            </span>
            <Button type="submit" variant="primary" size="sm" loading={savingProfile}>
              Save Profile
            </Button>
          </div>
        </form>
      </div>

      {isAdmin && (
        <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
            <Tags className="w-4 h-4 text-emerald-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
              Custom Lead Sources (Admin)
            </h3>
          </div>

          <p className="text-xs text-slate-400">
            Configure active inbound marketing channels available in the Add Lead form dropdown.
          </p>

          <form onSubmit={handleAddSource} className="flex items-center gap-2">
            <input
              type="text"
              placeholder="e.g. Clutch.co, TechCrunch, Cold Call"
              value={newSourceName}
              onChange={(e) => setNewSourceName(e.target.value)}
              className="flex-1 bg-slate-900 border border-slate-800 focus:border-blue-500 rounded-xl px-3.5 py-2 text-xs text-white outline-none"
            />
            <Button type="submit" variant="secondary" size="sm" loading={addingSource} icon={Plus}>
              Add Source
            </Button>
          </form>

          <div className="flex flex-wrap gap-2 pt-2">
            {sources.map((src) => (
              <div
                key={src.id}
                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/90 border border-slate-800 text-xs text-slate-200"
              >
                <span>{src.name}</span>
                <button
                  onClick={() => handleDeleteSource(src.id)}
                  title="Delete source"
                  className="text-slate-500 hover:text-rose-400 transition-colors"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {systemConfig && (
        <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
            <Server className="w-4 h-4 text-cyan-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
              System Architecture Diagnostics
            </h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-slate-500 block mb-0.5">Backend Service</span>
              <span className="text-white font-semibold">{systemConfig.project_name} v{systemConfig.version}</span>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-slate-500 block mb-0.5">AI Engine Model</span>
              <span className="text-indigo-400 font-semibold">{systemConfig.ai_model || 'gemini-2.5-flash'}</span>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-slate-500 block mb-0.5">Database Layer</span>
              <span className="text-emerald-400 font-semibold">{systemConfig.database_mode}</span>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-slate-500 block mb-0.5">Environment</span>
              <span className="text-white font-semibold capitalize">{systemConfig.environment}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
