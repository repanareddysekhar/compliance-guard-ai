import React from 'react';
import { Violation, Severity } from '../types';
import { AlertCircle, AlertTriangle, Info, CheckCircle2 } from 'lucide-react';

interface ViolationLogProps {
  violations: Violation[];
}

const SEVERITY_COLORS: Record<Severity, string> = {
  HIGH: "bg-red-100 text-red-700 border-red-200",
  MED:  "bg-amber-100 text-amber-700 border-amber-200",
  LOW:  "bg-blue-100 text-blue-700 border-blue-200",
};

const STATUS_COLORS: Record<string, string> = {
  BLOCKED:    "bg-red-600 text-white",
  FLAGGED:    "bg-amber-500 text-white",
  REPORTED:   "bg-gray-500 text-white",
  AUTO_FIXED: "bg-green-600 text-white",
};

const ViolationLog: React.FC<ViolationLogProps> = ({ violations }) => {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex flex-col h-full min-h-[600px]">
      <div className="px-6 py-4 border-b border-slate-200 bg-white flex justify-between items-center">
        <div>
          <h3 className="text-lg font-bold text-slate-800">Violation Log</h3>
          <p className="text-xs text-slate-500 font-medium uppercase tracking-wider">Detected policy breaches</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-slate-400 uppercase">Total:</span>
          <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded-md text-sm font-bold">{violations.length}</span>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50 sticky top-0 z-10">
            <tr>
              <th className="px-6 py-3 text-left text-[10px] font-bold text-slate-500 uppercase tracking-widest">Severity</th>
              <th className="px-6 py-3 text-left text-[10px] font-bold text-slate-500 uppercase tracking-widest">Description</th>
              <th className="px-6 py-3 text-left text-[10px] font-bold text-slate-500 uppercase tracking-widest">Category</th>
              <th className="px-6 py-3 text-left text-[10px] font-bold text-slate-500 uppercase tracking-widest">Status</th>
              <th className="px-6 py-3 text-left text-[10px] font-bold text-slate-500 uppercase tracking-widest text-right">Service</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-slate-100">
            {violations.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-20 text-center">
                  <div className="flex flex-col items-center gap-2 text-slate-300">
                    <CheckCircle2 size={48} className="opacity-20" />
                    <p className="text-sm font-medium">No violations detected in the current scope.</p>
                  </div>
                </td>
              </tr>
            ) : (
              violations.map((v) => (
                <tr key={v.id} className="hover:bg-slate-50/50 transition-colors group">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 rounded text-[10px] font-black tracking-tighter border ${SEVERITY_COLORS[v.severity]}`}>
                      {v.severity}
                    </span>
                  </td>
                  <td className="px-6 py-4 max-w-md">
                    <div className="text-sm text-slate-900 font-semibold group-hover:text-indigo-600 transition-colors">{v.description}</div>
                    <div className="text-[11px] text-slate-400 font-mono mt-0.5 flex items-center gap-1">
                      <span className="opacity-50">PATH:</span> {v.file_path}:{v.line_number}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-[11px] font-bold text-slate-500">
                    {v.category}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${STATUS_COLORS[v.status]}`}>
                      {v.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-800 font-bold text-right">
                    {v.service}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ViolationLog;
