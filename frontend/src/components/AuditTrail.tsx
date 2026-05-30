import React, { useState } from 'react';
import { ChevronDown, ChevronRight, ShieldCheck, Copy, Check } from 'lucide-react';
import { AuditEvent } from '../types';

interface AuditTrailProps {
  events: AuditEvent[];
  title?: string;
  description?: string;
  emptyMessage?: string;
  compact?: boolean;
  collapsible?: boolean;
  collapsed?: boolean;
  onCollapsedChange?: (collapsed: boolean) => void;
}

const AuditTrail: React.FC<AuditTrailProps> = ({
  events,
  title = 'Cryptographic Audit Trail',
  description = 'Signed agent actions persisted in PostgreSQL.',
  emptyMessage = 'No signed audit rows found for this scan.',
  compact = false,
  collapsible = false,
  collapsed = false,
  onCollapsedChange,
}) => {
  const contentId = compact ? 'history-audit-trail' : 'audit-trail';
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleCopy = (signature: string, id: string) => {
    navigator.clipboard.writeText(signature);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="bg-slate-900/30 backdrop-blur-md rounded-2xl border border-slate-800/80 overflow-hidden shadow-lg shadow-black/10">
      {/* Panel Header */}
      <div className="p-6 border-b border-slate-800/80 bg-slate-900/40">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2.5">
              {collapsible && (
                <button
                  type="button"
                  onClick={() => onCollapsedChange?.(!collapsed)}
                  aria-controls={contentId}
                  aria-expanded={!collapsed}
                  className="h-7 w-7 shrink-0 rounded-lg text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors flex items-center justify-center"
                >
                  {collapsed ? <ChevronRight size={16} /> : <ChevronDown size={16} />}
                </button>
              )}
              <ShieldCheck size={18} className="text-indigo-400 shrink-0" />
              <h2 className="text-base font-bold text-slate-200 tracking-tight">{title}</h2>
            </div>
            <p className="text-[11px] text-slate-500 font-medium mt-1">{description}</p>
          </div>
          <span className="rounded-lg bg-indigo-500/10 border border-indigo-500/20 px-2.5 py-1 text-[10px] font-bold text-indigo-400">
            {events.length} signed events
          </span>
        </div>
      </div>

      {/* Table Body */}
      {!collapsed && (
        <div id={contentId} className={`${compact ? 'max-h-[460px]' : ''} overflow-x-auto overflow-y-auto`}>
          <table className="w-full text-left border-collapse">
            <thead className="bg-[#0c121e]/80 border-b border-slate-800/80">
              <tr>
                <th className="px-6 py-3.5 text-[9px] font-bold text-slate-500 uppercase tracking-widest">Timestamp</th>
                <th className="px-6 py-3.5 text-[9px] font-bold text-slate-500 uppercase tracking-widest">Agent Action</th>
                <th className="px-6 py-3.5 text-[9px] font-bold text-slate-500 uppercase tracking-widest">Intent Verification</th>
                <th className="px-6 py-3.5 text-[9px] font-bold text-slate-500 uppercase tracking-widest">Policy Decision</th>
                <th className="px-6 py-3.5 text-[9px] font-bold text-slate-500 uppercase tracking-widest text-right">Signature</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/40">
              {events.length === 0 ? (
                <tr>
                  <td colSpan={5} className={`${compact ? 'px-6 py-12' : 'px-6 py-16'} text-center text-slate-500 font-medium text-xs italic`}>
                    {emptyMessage}
                  </td>
                </tr>
              ) : (
                events.map((event) => (
                  <tr key={event.event_id} className="hover:bg-slate-900/20 transition-colors">
                    <td className="px-6 py-4 text-xs font-bold text-slate-500 whitespace-nowrap">
                      {new Date(event.timestamp).toLocaleString()}
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-[10px] font-bold bg-indigo-500/10 text-indigo-400 px-2 py-0.5 rounded border border-indigo-500/20 uppercase tracking-tighter">
                        {event.tool_called}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-xs font-medium text-slate-300 max-w-xs truncate">
                      {event.intent}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full uppercase ${
                        event.policy_decision === 'ALLOW' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                      }`}>
                        {event.policy_decision}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2 group/sig">
                        <span className="text-[10px] font-mono font-bold text-indigo-400 bg-slate-900/60 border border-slate-800 px-2 py-0.5 rounded select-none">
                          {event.signature.substring(0, 12)}...
                        </span>
                        <button
                          type="button"
                          onClick={() => handleCopy(event.signature, event.event_id)}
                          className="p-1 rounded bg-slate-800/80 border border-slate-700/60 hover:border-slate-500 text-slate-400 hover:text-slate-200 opacity-0 group-hover/sig:opacity-100 transition-all cursor-pointer flex items-center justify-center"
                          title="Copy Full Signature"
                        >
                          {copiedId === event.event_id ? <Check size={10} className="text-emerald-400" /> : <Copy size={10} />}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default AuditTrail;
