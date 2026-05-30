import React from 'react';
import { AuditEvent, WsEvent } from '../types';
import { Terminal, Activity } from 'lucide-react';

interface ScanStatusProps {
  events: WsEvent[];
  auditEvents?: AuditEvent[];
  status: string;
  scanId?: string | null;
}

const ScanStatus: React.FC<ScanStatusProps> = ({ events, auditEvents = [], status, scanId }) => {
  const pendingTrace = scanId ? [
    { label: 'QUEUED', message: `Scan accepted: ${scanId}` },
    { label: 'CONNECT', message: 'Opening live WebSocket trace...' },
    { label: 'WAIT', message: 'Waiting for scanner events from backend.' },
  ] : [
    { label: 'IDLE', message: 'Start a scan to stream agent activity here.' },
    { label: 'TIP', message: 'Use a container path like /scan-repos/repana/my-repo.' },
  ];
  const hasTrace = events.length > 0 || auditEvents.length > 0;

  return (
    <div className="bg-[#0c121e]/90 rounded-2xl border border-slate-800/80 overflow-hidden shadow-lg shadow-black/30">
      {/* Console Header */}
      <div className="px-5 py-3.5 bg-slate-900/60 border-b border-slate-800/80 flex justify-between items-center">
        <div className="flex items-center gap-2.5 text-slate-300">
          <Terminal size={14} className="text-indigo-400" />
          <span className="text-[10px] font-bold uppercase tracking-widest text-slate-300">Live Execution Trace</span>
        </div>
        <div className="flex items-center gap-2">
          {status === 'RUNNING' && <Activity size={12} className="text-indigo-400 animate-pulse" />}
          <span className={`text-[9px] font-black px-2 py-0.5 rounded-full uppercase tracking-wider ${
            status === 'RUNNING' ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20' :
            status === 'COMPLETED' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
            status === 'FAILED' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : 'bg-slate-800 text-slate-500 border border-slate-700/50'
          }`}>
            {status}
          </span>
        </div>
      </div>

      {/* Terminal Viewport */}
      <div className="p-5 h-80 overflow-y-auto font-mono text-[11px] leading-relaxed space-y-2.5 bg-[#090d16]/80 scrollbar-thin">
        {!hasTrace ? (
          pendingTrace.map((item) => (
            <div key={item.label} className="flex gap-4 border-l border-slate-800/60 pl-3 pb-1 relative">
              <div className="absolute -left-[2px] top-1.5 w-1 h-1 rounded-full bg-slate-700 shadow-[0_0_8px_rgba(100,116,139,0.5)]"></div>
              <span className="w-16 shrink-0 text-slate-500 font-bold tracking-tighter uppercase">{item.label}</span>
              <span className="text-slate-400">{item.message}</span>
            </div>
          ))
        ) : (
          <>
            {events.map((event, idx) => (
              <div key={`event-${idx}`} className="flex gap-4 border-l border-slate-800/60 pl-3 pb-1 relative">
                <div className="absolute -left-[2px] top-1.5 w-1 h-1 rounded-full bg-slate-700"></div>
                <span className="text-slate-600 shrink-0 font-bold">
                  {new Date().toLocaleTimeString([], { hour12: false })}
                </span>
                <div className="flex-1">
                  {event.type === 'SCAN_STARTED' && (
                    <span className="text-indigo-400 font-bold">▶ START SCAN: {event.service}</span>
                  )}
                  {event.type === 'TOOL_CALLED' && (
                    <div className="flex flex-col gap-0.5">
                      <span className="text-slate-300">
                        <span className="text-emerald-400 font-bold">⚒ CALL TOOL:</span> {event.tool}
                      </span>
                      <span className="text-slate-500 italic text-[10px] pl-3">↳ {event.intent}</span>
                    </div>
                  )}
                  {event.type === 'VIOLATION_FOUND' && (
                    <span className="text-rose-400 font-bold bg-rose-500/5 border border-rose-500/10 px-1.5 py-0.5 rounded">
                      ⚠ DISCOVERED: {event.violation?.description}
                    </span>
                  )}
                  {event.type === 'SCAN_COMPLETED' && (
                    <span className="text-emerald-400 font-bold">✔ SUCCESS: Compliance scan completed.</span>
                  )}
                  {event.type === 'SCAN_FAILED' && (
                    <span className="text-rose-500 font-bold">✘ FAILURE: {event.error}</span>
                  )}
                </div>
              </div>
            ))}
            {auditEvents.map((event) => (
              <div key={`audit-${event.event_id}`} className="flex gap-4 border-l border-indigo-500/20 pl-3 pb-1 relative">
                <div className="absolute -left-[2px] top-1.5 w-1 h-1 rounded-full bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.5)]"></div>
                <span className="text-slate-600 shrink-0 font-bold">
                  {new Date(event.timestamp).toLocaleTimeString([], { hour12: false })}
                </span>
                <div className="flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-indigo-400 font-bold tracking-tighter">🔒 AUDIT LOG</span>
                    <span className="text-slate-300 font-bold">{event.tool_called}</span>
                    <span className={`rounded-full px-2 py-0.2 text-[9px] font-bold ${
                      event.policy_decision === 'ALLOW' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                    }`}>
                      {event.policy_decision}
                    </span>
                    <span className="rounded bg-slate-800/80 px-2 py-0.2 text-[9px] font-bold text-indigo-300 font-mono">
                      sig:{event.signature.substring(0, 10)}
                    </span>
                  </div>
                  <span className="text-slate-500 italic text-[10px] pl-3">↳ {event.intent}</span>
                </div>
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
};

export default ScanStatus;
