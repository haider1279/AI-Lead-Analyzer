import React from 'react';
import { Plus } from 'lucide-react';
import { Button } from '../common/Button';

export function Header({ title, onOpenAddLead, stats }) {
  return (
    <header className="h-16 border-b border-slate-800/80 bg-[#080c16]/80 backdrop-blur-md px-8 flex items-center justify-between sticky top-0 z-30">
      <div>
        <h2 className="text-base font-extrabold text-white font-heading tracking-tight">{title}</h2>
      </div>

      <div className="flex items-center gap-3">
        <Button variant="primary" size="sm" onClick={onOpenAddLead} icon={Plus}>
          New Lead
        </Button>
      </div>
    </header>
  );
}

