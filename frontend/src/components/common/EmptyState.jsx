import React from 'react';
import { Inbox } from 'lucide-react';
import { Button } from './Button';

export function EmptyState({
  title = 'No items found',
  description = 'There are no records matching this criteria.',
  icon: Icon = Inbox,
  actionLabel,
  actionText,
  onAction,
  action,
}) {
  const label = actionLabel || actionText;

  return (
    <div className="p-12 text-center glass-card rounded-2xl border border-slate-800/80 my-4 space-y-3">
      <div className="w-12 h-12 rounded-2xl bg-slate-800/50 border border-slate-700 flex items-center justify-center text-slate-400 mx-auto">
        {React.isValidElement(Icon) ? (
          Icon
        ) : Icon ? (
          <Icon className="w-6 h-6" />
        ) : (
          <Inbox className="w-6 h-6" />
        )}
      </div>
      <h3 className="text-sm font-bold text-white">{title}</h3>
      <p className="text-xs text-slate-400 max-w-sm mx-auto leading-relaxed">{description}</p>
      {action ? (
        <div className="pt-2">{action}</div>
      ) : label && onAction ? (
        <div className="pt-2">
          <Button variant="primary" size="sm" onClick={onAction}>
            {label}
          </Button>
        </div>
      ) : null}
    </div>
  );
}
