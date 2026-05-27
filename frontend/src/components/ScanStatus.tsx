import React from 'react';
import { WsEvent } from '../types';
import { Terminal, CheckCircle2, XCircle, Activity } from 'lucide-react';

interface ScanStatusProps {
  events: WsEvent[];
  status: string;
}

const ScanStatus: React.FC<ScanStatusProps> = ({ events, status }) => {
  return (
    <div className="bg-gray-900 rounded-lg shadow-sm border border-gray-800 mb-6 overflow-hidden">
      <div className="px-4 py-2 bg-gray-800 border-b border-gray-700 flex justify-between items-center">
        <div className="flex items-center gap-2 text-gray-300">
          <Terminal size={16} />
          <span className="text-xs font-mono font-bold uppercase tracking-wider">Scan Live Feed</span>
        </div>
        <div className="flex items-center gap-2">
          {status === 'RUNNING' && <Activity size={14} className="text-blue-400 animate-pulse" />}
          {status === 'COMPLETED' && <CheckCircle2 size={14} className="text-green-400" />}
          {status === 'FAILED' && <XCircle size={14} className="text-red-400" />}
          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
            status === 'RUNNING' ? 'bg-blue-900 text-blue-200' :
            status === 'COMPLETED' ? 'bg-green-900 text-green-200' :
            status === 'FAILED' ? 'bg-red-900 text-red-200' : 'bg-gray-700 text-gray-400'
          }`}>
            {status}
          </span>
        </div>
      </div>
      <div className="p-4 h-48 overflow-y-auto font-mono text-xs flex flex-col-reverse gap-1">
        {events.length === 0 ? (
          <div className="text-gray-600">Waiting for scan to start...</div>
        ) : (
          events.slice().reverse().map((event, idx) => (
            <div key={idx} className="flex gap-2">
              <span className="text-gray-500">[{new Date().toLocaleTimeString()}]</span>
              {event.type === 'SCAN_STARTED' && (
                <span className="text-blue-400">Scan started for service: {event.service}</span>
              )}
              {event.type === 'TOOL_CALLED' && (
                <span className="text-gray-300 italic">
                  Calling {event.tool}: <span className="text-gray-500">{event.intent}</span> → 
                  <span className={event.decision === 'ALLOW' ? 'text-green-400' : 'text-red-400'}> {event.decision}</span>
                </span>
              )}
              {event.type === 'VIOLATION_FOUND' && (
                <span className="text-amber-400">
                  ⚠️ Found {event.violation?.severity} violation: {event.violation?.description}
                </span>
              )}
              {event.type === 'SCAN_COMPLETED' && (
                <span className="text-green-400 font-bold underline">Scan completed successfully.</span>
              )}
              {event.type === 'SCAN_FAILED' && (
                <span className="text-red-400 font-bold underline">Scan failed: {event.error}</span>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default ScanStatus;
