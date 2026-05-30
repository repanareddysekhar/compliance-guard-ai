import React from 'react';
import { Violation, Severity } from '../types';
import { CheckCircle2, ChevronDown, ChevronRight, FileCode2, Wrench } from 'lucide-react';

interface ViolationLogProps {
  violations: Violation[];
  compact?: boolean;
  collapsible?: boolean;
  collapsed?: boolean;
  onCollapsedChange?: (collapsed: boolean) => void;
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

const formatSnippet = (violation: Violation) => {
  if (!violation.code_snippet) return [];

  const startLine = violation.snippet_start_line ?? 1;
  return violation.code_snippet.split('\n').map((line, index) => ({
    lineNumber: startLine + index,
    code: line,
    isFinding: violation.line_number === startLine + index,
  }));
};

const ViolationLog: React.FC<ViolationLogProps> = ({
  violations,
  compact = false,
  collapsible = false,
  collapsed = false,
  onCollapsedChange,
}) => {
  const contentId = compact ? 'history-violation-log' : 'active-violation-log';

  return (
    <div className={`bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex flex-col ${compact ? 'min-h-0' : 'h-full min-h-[560px]'}`}>
      <div className="px-6 py-4 border-b border-slate-200 bg-white flex justify-between items-center">
        <div className="min-w-0">
          <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
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
            Violation Log
          </h3>
          <p className="text-xs text-slate-500 font-medium uppercase tracking-wider">Evidence, location, and suggested fixes</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-slate-400 uppercase">Total:</span>
          <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded-md text-sm font-bold">{violations.length}</span>
        </div>
      </div>
      {!collapsed && <div id={contentId} className={`${compact ? 'max-h-[460px]' : 'flex-1'} overflow-y-auto p-4 bg-slate-50/70`}>
        {violations.length === 0 ? (
          <div className={`${compact ? 'min-h-32' : 'h-full min-h-80'} flex flex-col items-center justify-center gap-2 text-slate-300`}>
            <CheckCircle2 size={compact ? 34 : 48} className="opacity-20" />
            <p className="text-sm font-medium">No violations detected in the current scope.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {violations.map((v) => (
              <article key={v.id} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm hover:border-indigo-100 transition-colors">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-2">
                      <span className={`px-2 py-1 rounded text-[10px] font-black tracking-tighter border ${SEVERITY_COLORS[v.severity]}`}>
                        {v.severity}
                      </span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${STATUS_COLORS[v.status]}`}>
                        {v.status}
                      </span>
                      <span className="px-2 py-0.5 rounded bg-slate-100 text-[10px] font-black text-slate-500 uppercase tracking-wider">
                        {v.category}
                      </span>
                    </div>
                    <h4 className="text-sm font-black text-slate-900">{v.description}</h4>
                    <p className="mt-1 break-all text-[11px] text-slate-500 font-mono">
                      {v.file_path || 'Unknown file'}{v.line_number ? `:${v.line_number}` : ''}
                    </p>
                  </div>
                  <span className="shrink-0 rounded-lg bg-indigo-50 px-2.5 py-1 text-[10px] font-black text-indigo-700">
                    {v.service}
                  </span>
                </div>

                {v.code_snippet && (
                  <div className="mt-4 rounded-lg overflow-hidden border border-slate-200 bg-slate-950 shadow-sm">
                    <div className="px-3 py-2 bg-slate-900 border-b border-slate-800 flex items-center gap-2 text-[10px] font-bold text-slate-300 uppercase tracking-wider">
                      <FileCode2 size={13} className="text-indigo-300" />
                      Evidence
                    </div>
                    <div className="py-2 text-[11px] leading-5 overflow-x-auto">
                      {formatSnippet(v).map(({ lineNumber, code, isFinding }) => (
                        <div key={lineNumber} className={`px-3 flex gap-3 ${isFinding ? 'bg-red-500/20 text-red-100' : 'text-slate-300'}`}>
                          <span className={`select-none min-w-8 text-right ${isFinding ? 'text-red-300 font-bold' : 'text-slate-500'}`}>
                            {lineNumber}
                          </span>
                          <code className="font-mono whitespace-pre">{code || ' '}</code>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {v.remediation && (
                  <div className="mt-4 rounded-lg border border-emerald-100 bg-emerald-50 px-3 py-2">
                    <div className="mb-1 flex items-center gap-2 text-[10px] font-black uppercase tracking-wider text-emerald-700">
                      <Wrench size={13} />
                      Suggested Fix
                    </div>
                    <p className="text-xs font-medium leading-5 text-emerald-900">{v.remediation}</p>
                  </div>
                )}
              </article>
            ))}
          </div>
        )}
      </div>}
    </div>
  );
};

export default ViolationLog;
