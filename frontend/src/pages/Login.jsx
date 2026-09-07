import React, { useState } from 'react';
import { Mail, Lock } from 'lucide-react';
import { useAuth } from '../auth/AuthContext';
import { Button } from '../components/common/Button';

export function Login({ onNavigateSignUp, onLoginSuccess }) {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim()) {
      setError('Email address is required.');
      return;
    }
    if (!password || !password.trim()) {
      setError('Password is required.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await login(email.trim(), password);
      onLoginSuccess();
    } catch (err) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#080c16] px-4 py-12 relative overflow-hidden">
      <div className="absolute -top-40 -left-40 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-md relative z-10 space-y-6">
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-cyan-500 flex items-center justify-center shadow-xl shadow-blue-500/25 text-white font-extrabold text-2xl font-heading mx-auto">
            E
          </div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight font-heading">
            Euroshub Sales Hub
          </h1>
          <p className="text-xs text-slate-400">Internal CRM &amp; AI Lead Intelligence Platform</p>
        </div>

        <div className="glass-panel p-8 rounded-2xl border border-slate-800 space-y-6 shadow-2xl bg-[#0f172a]/80">
          {error && (
            <div className="p-3 rounded-xl bg-rose-500/10 text-rose-400 text-xs border border-rose-500/20 text-center font-medium">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@euroshub.com"
                  className="w-full bg-slate-900 border border-slate-800 focus:border-blue-500 rounded-xl pl-10 pr-4 py-2 text-xs text-white placeholder-slate-500 outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-slate-900 border border-slate-800 focus:border-blue-500 rounded-xl pl-10 pr-4 py-2 text-xs text-white placeholder-slate-500 outline-none"
                />
              </div>
            </div>

            <Button type="submit" variant="primary" size="md" loading={loading} className="w-full">
              Sign In to Euroshub
            </Button>
          </form>

          <div className="text-center text-xs text-slate-500 pt-2">
            Need a new account?{' '}
            <button
              onClick={onNavigateSignUp}
              className="text-blue-400 hover:underline font-semibold"
            >
              Sign Up
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

