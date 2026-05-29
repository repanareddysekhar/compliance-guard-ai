import React from 'react';
import { WsEvent } from '../types';
import { Terminal, CheckCircle2, XCircle, Activity } from 'lucide-react';

interface ScanStatusProps {
  events: WsEvent[];
  status: string;
}

const ScanStatus: React.FC<ScanStatusProps> = ({ events, status }) => {
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
      <div className="p-4 h-64 overflow-y-auto font-mono text-[11px] leading-relaxed space-y-1 bg-slate-950/50">
        {events.length === 0 ? (
          <div className="text-slate-600 italic">No active process...</div>
        ) : (
          events.map((event, idx) => (
            <div key={idx} className="flex gap-3 border-l border-slate-800 pl-3 pb-1 relative">
              <div className="absolute -left-[1px] top-1.5 w-[3px] h-[3px] rounded-full bg-slate-700"></div>
              <span className="text-slate-600 shrink-0 font-bold">{new Date().toLocaleTimeString([], { hour12: false })}</span>
              <div className="flex-1">
                {event.type === 'SCAN_STARTED' && (
                  <span className="text-blue-400 font-bold">▶ START: {event.service}</span>
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
                    ✖ FOUND: {event.violation?.description}
                  </span>
                )}
                {event.type === 'SCAN_COMPLETED' && (
                  <span className="text-emerald-400 font-bold">✔ SUCCESS: Scan finalized.</span>
                )}
                {event.type === 'SCAN_FAILED' && (
                  <span className="text-rose-500 font-bold">✖ FAILURE: {event.error}</span>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default ScanStatus;
