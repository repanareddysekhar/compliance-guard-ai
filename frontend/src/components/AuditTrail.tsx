import React from 'react';
import { ChevronDown, ChevronRight, ShieldCheck } from 'lucide-react';
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

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
      <div className="p-6 border-b border-slate-100 bg-white">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              {collapsible && (
                <button
                  type="button"
                  onClick={() => onCollapsedChange?.(!collapsed)}
                  aria-controls={contentId}
                  aria-expanded={!collapsed}
                  className="h-7 w-7 shrink-0 rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors flex items-center justify-center"
                >
                  {collapsed ? <ChevronRight size={16} /> : <ChevronDown size={16} />}
                </button>
              )}
              <ShieldCheck size={18} className="text-indigo-500 shrink-0" />
              <h2 className="text-xl font-black text-slate-800 tracking-tight">{title}</h2>
            </div>
            <p className="text-slate-500 font-medium mt-1">{description}</p>
          </div>
          <span className="rounded-lg bg-indigo-50 px-2.5 py-1 text-[10px] font-black text-indigo-700">
            {events.length} signed events
          </span>
        </div>
      </div>
      {!collapsed && <div id={contentId} className={`${compact ? 'max-h-[460px]' : ''} overflow-x-auto overflow-y-auto`}>
        <table className="w-full text-left">
          <thead className="bg-slate-50 border-b border-slate-100">
            <tr>
              <th className="px-8 py-4 text-[10px] font-black text-slate-400 uppercase tracking-widest">Timestamp</th>
              <th className="px-8 py-4 text-[10px] font-black text-slate-400 uppercase tracking-widest">Agent Action</th>
              <th className="px-8 py-4 text-[10px] font-black text-slate-400 uppercase tracking-widest">Intent Verification</th>
              <th className="px-8 py-4 text-[10px] font-black text-slate-400 uppercase tracking-widest">Policy Decision</th>
              <th className="px-8 py-4 text-[10px] font-black text-slate-400 uppercase tracking-widest text-right">Signature</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {events.length === 0 ? (
              <tr>
                <td colSpan={5} className={`${compact ? 'px-8 py-12' : 'px-8 py-20'} text-center text-slate-400 font-medium italic`}>
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              events.map((event) => (
                <tr key={event.event_id} className="hover:bg-slate-50/50 transition-colors">
                  <td className="px-8 py-4 text-xs font-bold text-slate-500">{new Date(event.timestamp).toLocaleString()}</td>
                  <td className="px-8 py-4">
                    <span className="text-xs font-black bg-indigo-50 text-indigo-700 px-2 py-1 rounded uppercase tracking-tighter border border-indigo-100">
                      {event.tool_called}
                    </span>
                  </td>
                  <td className="px-8 py-4 text-xs font-medium text-slate-600 max-w-xs truncate">{event.intent}</td>
                  <td className="px-8 py-4">
                    <span className={`text-[10px] font-black px-2 py-0.5 rounded uppercase ${
                      event.policy_decision === 'ALLOW' ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'
                    }`}>
                      {event.policy_decision}
                    </span>
                  </td>
                  <td className="px-8 py-4 text-right">
                    <span className="text-[10px] font-mono font-bold text-indigo-400 bg-slate-50 px-2 py-1 rounded border border-slate-100">
                      {event.signature.substring(0, 12)}...
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>}
    </div>
  );
};

export default AuditTrail;
