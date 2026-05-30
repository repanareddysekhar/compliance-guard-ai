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
  HIGH: "bg-rose-500/10 text-rose-400 border-rose-500/20 shadow-[0_0_12px_rgba(244,63,94,0.1)]",
  MED:  "bg-amber-500/10 text-amber-400 border-amber-500/20 shadow-[0_0_12px_rgba(245,158,11,0.1)]",
  LOW:  "bg-blue-500/10 text-blue-400 border-blue-500/20 shadow-[0_0_12px_rgba(59,130,246,0.1)]",
};

const STATUS_COLORS: Record<string, string> = {
  BLOCKED:    "bg-rose-500/20 text-rose-300 border border-rose-500/30",
  FLAGGED:    "bg-amber-500/20 text-amber-300 border border-amber-500/30",
  REPORTED:   "bg-slate-800 text-slate-400 border border-slate-700/50",
  AUTO_FIXED: "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30",
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
    <div className={`bg-slate-900/30 backdrop-blur-md rounded-2xl border border-slate-800/80 overflow-hidden flex flex-col ${compact ? 'min-h-0' : 'h-full min-h-[560px]'}`}>
      <div className="px-6 py-4 border-b border-slate-800/80 bg-slate-900/40 flex justify-between items-center">
        <div className="min-w-0">
          <h3 className="text-base font-bold text-slate-200 flex items-center gap-2">
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
            Violation Log
          </h3>
          <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mt-0.5">Evidence, location, and suggested fixes</p>
        </div>
        <div className="flex items-center gap-2.5">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Total Detected:</span>
          <span className="bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2.5 py-0.5 rounded-lg text-xs font-bold">{violations.length}</span>
        </div>
      </div>
      {!collapsed && (
        <div id={contentId} className={`${compact ? 'max-h-[460px]' : 'flex-1'} overflow-y-auto p-5 bg-[#090d16]/30 space-y-4`}>
          {violations.length === 0 ? (
            <div className={`${compact ? 'min-h-32' : 'h-full min-h-[320px]'} flex flex-col items-center justify-center gap-3 text-slate-500`}>
              <CheckCircle2 size={compact ? 34 : 40} className="text-emerald-500/30 glow-emerald" />
              <p className="text-xs font-bold tracking-tight text-slate-400">No violations detected in the current scope.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {violations.map((v) => (
                <article key={v.id} className="rounded-xl border border-slate-800/60 bg-[#0c121e]/50 p-5 shadow-sm hover:border-slate-700/80 transition-colors">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2 mb-2.5">
                        <span className={`px-2 py-0.5 rounded-md text-[9px] font-black tracking-wider border ${SEVERITY_COLORS[v.severity]}`}>
                          {v.severity}
                        </span>
                        <span className={`px-2 py-0.5 rounded-md text-[9px] font-bold ${STATUS_COLORS[v.status]}`}>
                          {v.status}
                        </span>
                        <span className="px-2 py-0.5 rounded-md bg-slate-800 text-[9px] font-bold text-slate-400 border border-slate-700/40 uppercase tracking-wider">
                          {v.category}
                        </span>
                      </div>
                      <h4 className="text-sm font-bold text-slate-200 leading-tight">{v.description}</h4>
                      <p className="mt-1.5 break-all text-[10px] text-slate-500 font-mono">
                        {v.file_path || 'Unknown file'}{v.line_number ? `:${v.line_number}` : ''}
                      </p>
                    </div>
                    <span className="shrink-0 rounded-lg bg-indigo-500/10 border border-indigo-500/20 px-2.5 py-1 text-[10px] font-bold text-indigo-400">
                      {v.service}
                    </span>
                  </div>

                  {v.code_snippet && (
                    <div className="mt-4 rounded-xl overflow-hidden border border-slate-800/80 bg-[#070b12] shadow-inner shadow-black/20">
                      <div className="px-4 py-2 bg-slate-900/60 border-b border-slate-800/60 flex items-center gap-2 text-[9px] font-bold text-slate-400 uppercase tracking-wider">
                        <FileCode2 size={12} className="text-indigo-400" />
                        Code Evidence
                      </div>
                      <div className="py-2.5 text-[11px] leading-5 overflow-x-auto scrollbar-thin">
                        {formatSnippet(v).map(({ lineNumber, code, isFinding }) => (
                          <div key={lineNumber} className={`px-4 flex gap-4 ${isFinding ? 'bg-rose-500/10 text-rose-200' : 'text-slate-400'}`}>
                            <span className={`select-none min-w-8 text-right font-mono ${isFinding ? 'text-rose-400 font-bold' : 'text-slate-600'}`}>
                              {lineNumber}
                            </span>
                            <code className="font-mono whitespace-pre">{code || ' '}</code>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {v.remediation && (
                    <div className="mt-4 rounded-xl border border-emerald-500/10 bg-emerald-500/5 px-4 py-3 flex gap-3">
                      <div className="p-1.5 bg-emerald-500/10 rounded-lg text-emerald-400 h-fit">
                        <Wrench size={13} />
                      </div>
                      <div>
                        <div className="mb-0.5 text-[9px] font-bold uppercase tracking-wider text-emerald-400">
                          Suggested Remediation
                        </div>
                        <p className="text-xs leading-relaxed text-emerald-300/90 font-medium">{v.remediation}</p>
                      </div>
                    </div>
                  )}
                </article>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ViolationLog;
