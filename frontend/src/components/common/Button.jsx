import React from 'react';
import { Loader2 } from 'lucide-react';

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  icon: Icon,
  className = '',
  ...props
}) {
  const baseStyles =
    'inline-flex items-center justify-center transition-all select-none disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none';

  const variants = {
    primary:
      'bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white font-semibold shadow-lg shadow-blue-500/20 hover:shadow-blue-500/35 hover:-translate-y-0.5',
    secondary:
      'bg-slate-800 hover:bg-slate-700 text-slate-100 font-semibold border border-slate-700 hover:border-slate-600',
    outline:
      'bg-transparent hover:bg-slate-800 text-slate-300 hover:text-white font-medium border border-slate-700 hover:border-slate-600',
    ghost:
      'bg-transparent hover:bg-slate-800/60 text-slate-400 hover:text-slate-200 font-medium',
    danger:
      'bg-rose-600 hover:bg-rose-500 active:bg-rose-700 text-white font-semibold shadow-lg shadow-rose-500/20',
    emerald:
      'bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 text-white font-semibold shadow-lg shadow-emerald-500/20',
    ai:
      'bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:via-indigo-500 hover:to-purple-500 text-white font-semibold shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/40 hover:-translate-y-0.5',
  };

  const sizes = {
    xs: 'text-xs px-2.5 py-1 rounded-lg gap-1.5',
    sm: 'text-xs px-3 py-1.5 rounded-xl gap-1.5',
    md: 'text-xs px-4 py-2 rounded-xl gap-2 font-semibold',
    lg: 'text-sm px-5 py-2.5 rounded-xl gap-2.5 font-semibold',
  };

  return (
    <button
      disabled={disabled || loading}
      className={`${baseStyles} ${variants[variant] || variants.primary} ${sizes[size] || sizes.md} ${className}`}
      {...props}
    >
      {loading ? (
        <Loader2 className="w-4 h-4 animate-spin shrink-0" />
      ) : Icon ? (
        <Icon className="w-4 h-4 shrink-0" />
      ) : null}
      {children}
    </button>
  );
}
