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
    <div className="bg-slate-900 rounded-xl shadow-lg border border-slate-800 overflow-hidden">
      <div className="px-4 py-3 bg-slate-800/50 border-b border-slate-800 flex justify-between items-center">
        <div className="flex items-center gap-2 text-slate-300">
          <Terminal size={14} className="text-emerald-400" />
          <span className="text-[10px] font-black uppercase tracking-widest">Live Execution Trace</span>
        </div>
        <div className="flex items-center gap-2">
          {status === 'RUNNING' && <Activity size={12} className="text-blue-400 animate-pulse" />}
          <span className={`text-[9px] font-black px-2 py-0.5 rounded uppercase ${
            status === 'RUNNING' ? 'bg-blue-500/20 text-blue-400' :
            status === 'COMPLETED' ? 'bg-emerald-500/20 text-emerald-400' :
            status === 'FAILED' ? 'bg-rose-500/20 text-rose-400' : 'bg-slate-700 text-slate-400'
          }`}>
            {status}
          </span>
        </div>
      </div>
      <div className="p-4 h-80 overflow-y-auto font-mono text-[11px] leading-relaxed space-y-1 bg-slate-950/50">
        {!hasTrace ? (
          pendingTrace.map((item) => (
            <div key={item.label} className="flex gap-3 border-l border-slate-800 pl-3 pb-1 relative">
              <div className="absolute -left-[1px] top-1.5 w-[3px] h-[3px] rounded-full bg-slate-700"></div>
              <span className="w-16 shrink-0 text-slate-600 font-bold">{item.label}</span>
              <span className="text-slate-400">{item.message}</span>
            </div>
          ))
        ) : (
          <>
            {events.map((event, idx) => (
              <div key={`event-${idx}`} className="flex gap-3 border-l border-slate-800 pl-3 pb-1 relative">
                <div className="absolute -left-[1px] top-1.5 w-[3px] h-[3px] rounded-full bg-slate-700"></div>
                <span className="text-slate-600 shrink-0 font-bold">{new Date().toLocaleTimeString([], { hour12: false })}</span>
                <div className="flex-1">
                  {event.type === 'SCAN_STARTED' && (
                    <span className="text-blue-400 font-bold">START: {event.service}</span>
                  )}
                  {event.type === 'TOOL_CALLED' && (
                    <div className="flex flex-col">
                      <span className="text-slate-300">
                        <span className="text-emerald-400 font-bold">CALL</span> {event.tool}
                      </span>
                      <span className="text-slate-500 italic text-[10px]">{event.intent}</span>
                    </div>
                  )}
                  {event.type === 'VIOLATION_FOUND' && (
                    <span className="text-rose-400 font-bold">
                      FOUND: {event.violation?.description}
                    </span>
                  )}
                  {event.type === 'SCAN_COMPLETED' && (
                    <span className="text-emerald-400 font-bold">SUCCESS: Scan finalized.</span>
                  )}
                  {event.type === 'SCAN_FAILED' && (
                    <span className="text-rose-500 font-bold">FAILURE: {event.error}</span>
                  )}
                </div>
              </div>
            ))}
            {auditEvents.map((event) => (
              <div key={`audit-${event.event_id}`} className="flex gap-3 border-l border-indigo-900/80 pl-3 pb-1 relative">
                <div className="absolute -left-[1px] top-1.5 w-[3px] h-[3px] rounded-full bg-indigo-400"></div>
                <span className="text-slate-600 shrink-0 font-bold">
                  {new Date(event.timestamp).toLocaleTimeString([], { hour12: false })}
                </span>
                <div className="flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-indigo-300 font-black">AUDIT</span>
                    <span className="text-slate-300">{event.tool_called}</span>
                    <span className={`rounded px-1.5 py-0.5 text-[9px] font-black ${
                      event.policy_decision === 'ALLOW' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'
                    }`}>
                      {event.policy_decision}
                    </span>
                    <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[9px] font-bold text-indigo-200">
                      sig {event.signature.substring(0, 12)}...
                    </span>
                  </div>
                  <span className="text-slate-500 italic text-[10px]">{event.intent}</span>
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
