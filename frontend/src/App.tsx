import React, { useState, useEffect } from 'react';
import StatsBar from './components/StatsBar';
import ScanTrigger from './components/ScanTrigger';
import ScanStatus from './components/ScanStatus';
import ViolationLog from './components/ViolationLog';
import AuditTrail from './components/AuditTrail';
import { useScanWebSocket } from './hooks/useScanWebSocket';
import { useViolations } from './hooks/useViolations';
import { useAuditEvents } from './hooks/useAuditEvents';
import { Shield, Activity, Book, History, Code, PanelLeftClose, PanelLeftOpen, ChevronRight, ChevronDown, Wrench } from 'lucide-react';
import client from './api/client';
import { AuditEvent, ScanLog, ScanRun, Violation } from './types';

type View = 'dashboard' | 'policies' | 'audit';

interface Policy {
  id: number;
  name: string;
  path: string;
  status: string;
  rules: number;
  description?: string;
  category?: string;
  severity?: string;
  standards?: string[];
  rules_list?: string[];
  remediation?: string;
}

const App: React.FC = () => {
  const [activeView, setActiveView] = useState<View>('dashboard');
  const [currentScanId, setCurrentScanId] = useState<string | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const { events, status } = useScanWebSocket(currentScanId);
  const { violations } = useViolations(currentScanId || undefined);
  const { auditEvents: liveAuditEvents } = useAuditEvents(currentScanId || undefined);
  const [historyAuditEvents, setHistoryAuditEvents] = useState<AuditEvent[]>([]);
  const [scanRuns, setScanRuns] = useState<ScanRun[]>([]);
  const [scanLogs, setScanLogs] = useState<ScanLog[]>([]);
  const [historyViolations, setHistoryViolations] = useState<Violation[]>([]);
  const [historyViolationsCollapsed, setHistoryViolationsCollapsed] = useState(false);
  const [historyAuditCollapsed, setHistoryAuditCollapsed] = useState(false);
  const [selectedHistoryScanId, setSelectedHistoryScanId] = useState<string | null>(null);
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [selectedPolicyId, setSelectedPolicyId] = useState<number | null>(null);

  // Mock stats for demo purposes
  const stats = {
    services: 1,
    violations: violations.length,
    fixed: 0,
    score: currentScanId ? 85 : 100
  };
  const selectedHistoryScan = scanRuns.find((scan) => scan.id === selectedHistoryScanId);

  useEffect(() => {
    if (activeView === 'audit') {
      client.get('/api/scans').then((res: { data: ScanRun[] }) => {
        setScanRuns(res.data);
        setSelectedHistoryScanId((selected) => selected || res.data[0]?.id || null);
      });
    }
    if (activeView === 'policies') {
      client.get('/api/policies').then((res: { data: Policy[] }) => setPolicies(res.data));
    }
  }, [activeView]);

  useEffect(() => {
    if (activeView !== 'audit' || !selectedHistoryScanId) {
      setHistoryAuditEvents([]);
      setScanLogs([]);
      setHistoryViolations([]);
      return;
    }

    client.get(`/api/audit/${selectedHistoryScanId}`).then((res: { data: AuditEvent[] }) => setHistoryAuditEvents(res.data));
    client.get(`/api/scan/${selectedHistoryScanId}/logs`).then((res: { data: ScanLog[] }) => setScanLogs(res.data));
    client.get('/api/violations', { params: { scan_id: selectedHistoryScanId } }).then((res: { data: Violation[] }) => setHistoryViolations(res.data));
  }, [activeView, selectedHistoryScanId]);

  return (
    <div className="flex h-screen bg-[#080d16] text-slate-100 overflow-hidden font-sans">
      {/* Sidebar - Translucent Modern Navigation */}
      <aside className={`bg-[#0b1322]/40 backdrop-blur-md border-r border-slate-800/80 flex flex-col py-6 px-4 shrink-0 transition-all duration-300 ${sidebarCollapsed ? 'w-20 items-center' : 'w-20 lg:w-64 items-center lg:items-stretch'}`}>
        <div className={`flex items-center gap-3 px-2 mb-10 w-full ${sidebarCollapsed ? 'justify-center' : 'justify-between'}`}>
          <div 
            className="bg-indigo-600 p-2.5 rounded-xl shadow-lg shadow-indigo-500/20 cursor-pointer hover:scale-105 transition-transform duration-300" 
            onClick={() => setActiveView('dashboard')}
          >
            <Shield className="text-white h-5 w-5" />
          </div>
          <div className={`${sidebarCollapsed ? 'hidden' : 'hidden lg:block'} overflow-hidden`}>
            <h1 className="text-xs font-black tracking-widest bg-gradient-to-r from-slate-100 to-slate-300 bg-clip-text text-transparent uppercase whitespace-nowrap leading-none mb-1">ComplianceGuard</h1>
            <p className="text-[9px] text-indigo-400 font-bold uppercase tracking-widest leading-none">v2.0 Autonomous</p>
          </div>
          <button
            type="button"
            onClick={() => setSidebarCollapsed((collapsed) => !collapsed)}
            className={`${sidebarCollapsed ? 'hidden' : 'hidden lg:flex'} h-8 w-8 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-800 hover:text-slate-200 transition-colors cursor-pointer`}
            aria-label="Collapse sidebar"
          >
            <PanelLeftClose size={15} />
          </button>
        </div>

        <nav className="flex-1 space-y-2 w-full">
          <div 
            onClick={() => setActiveView('dashboard')}
            className={`p-3.5 rounded-xl flex items-center gap-3.5 cursor-pointer group transition-all duration-300 ${
              activeView === 'dashboard' ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 shadow-md' : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-200 border border-transparent'
            }`}
          >
            <Activity size={18} className="shrink-0" />
            <span className={`${sidebarCollapsed ? 'hidden' : 'hidden lg:block'} text-xs font-bold ${activeView === 'dashboard' ? '' : 'opacity-70 group-hover:opacity-100'}`}>Active Scans</span>
          </div>
          <div 
            onClick={() => setActiveView('policies')}
            className={`p-3.5 rounded-xl flex items-center gap-3.5 cursor-pointer group transition-all duration-300 ${
              activeView === 'policies' ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 shadow-md' : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-200 border border-transparent'
            }`}
          >
            <Book size={18} className="shrink-0" />
            <span className={`${sidebarCollapsed ? 'hidden' : 'hidden lg:block'} text-xs font-bold ${activeView === 'policies' ? '' : 'opacity-70 group-hover:opacity-100'}`}>Policy Library</span>
          </div>
          <div 
            onClick={() => setActiveView('audit')}
            className={`p-3.5 rounded-xl flex items-center gap-3.5 cursor-pointer group transition-all duration-300 ${
              activeView === 'audit' ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 shadow-md' : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-200 border border-transparent'
            }`}
          >
            <History size={18} className="shrink-0" />
            <span className={`${sidebarCollapsed ? 'hidden' : 'hidden lg:block'} text-xs font-bold ${activeView === 'audit' ? '' : 'opacity-70 group-hover:opacity-100'}`}>Scan History</span>
          </div>
        </nav>

        <div className="mt-auto pt-6 border-t border-slate-800/80 w-full flex flex-col items-center">
          {sidebarCollapsed && (
            <button
              type="button"
              onClick={() => setSidebarCollapsed(false)}
              className="mb-4 hidden h-8 w-8 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-800 hover:text-slate-200 lg:flex cursor-pointer"
              aria-label="Expand sidebar"
            >
              <PanelLeftOpen size={16} />
            </button>
          )}
          <div className={`flex items-center gap-3 px-3 py-3 rounded-xl bg-slate-900/30 border border-slate-800/80 w-full ${sidebarCollapsed ? 'justify-center' : ''}`}>
            <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-white text-xs font-black shadow-sm shrink-0">
              TS
            </div>
            <div className={`${sidebarCollapsed ? 'hidden' : 'hidden lg:block'} overflow-hidden`}>
              <p className="text-[11px] font-bold truncate leading-none mb-1 text-slate-300">Stacktracers</p>
              <p className="text-[8px] text-slate-500 font-mono font-bold leading-none uppercase">ID: B1A342C5</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 bg-[#080d16]/70 backdrop-blur-md border-b border-slate-800/80 px-8 flex items-center justify-between z-10">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Dashboard</span>
              <span className="text-slate-700">/</span>
              <span className="text-[10px] font-bold text-slate-300 uppercase tracking-widest">
                {activeView === 'dashboard' ? 'Scan Control' : activeView === 'policies' ? 'Policy Management' : 'Scan History'}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-3.5">
            <div className="h-2 w-2 rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.6)] animate-pulse"></div>
            <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest">System Operational</span>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto px-6 py-6 md:px-10 md:py-8 fade-in">
          {activeView === 'dashboard' && (
            <div className="space-y-8">
              <StatsBar 
                services={stats.services} 
                violations={stats.violations} 
                fixed={stats.fixed} 
                score={stats.score} 
              />
              
              <div className="grid grid-cols-1 2xl:grid-cols-12 gap-8 items-start pb-10">
                <div className="2xl:col-span-4 space-y-8">
                  <ScanTrigger onScanTriggered={setCurrentScanId} />
                  <ScanStatus events={events} auditEvents={liveAuditEvents} status={status} scanId={currentScanId} />
                </div>
                
                <div className="2xl:col-span-8 h-full">
                  <ViolationLog violations={violations} />
                </div>
              </div>
            </div>
          )}

          {activeView === 'policies' && (
            <div className="space-y-6 max-w-6xl">
              <div className="bg-slate-900/30 backdrop-blur-md rounded-2xl p-8 border border-slate-800/80 shadow-lg">
                <h2 className="text-xl font-bold text-slate-200 mb-1.5 tracking-tight">Policy Governance</h2>
                <p className="text-xs text-slate-500 font-medium leading-relaxed">Manage and review active OPA policies enforced by ArmorIQ.</p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mt-8">
                  {policies.map(p => {
                    const isExpanded = selectedPolicyId === p.id;
                    return (
                      <div 
                        key={p.id} 
                        onClick={() => setSelectedPolicyId(isExpanded ? null : p.id)}
                        className={`p-6 rounded-2xl border transition-all duration-300 bg-slate-950/20 hover:bg-slate-900/30 cursor-pointer flex flex-col justify-between ${
                          isExpanded 
                            ? 'border-indigo-500/50 shadow-[0_0_20px_rgba(99,102,241,0.15)] md:col-span-2' 
                            : 'border-slate-800/80 hover:border-indigo-500/30'
                        }`}
                      >
                        <div>
                          <div className="flex justify-between items-start mb-4">
                            <div className="p-2.5 bg-indigo-500/10 rounded-xl text-indigo-400">
                              <Code size={18} />
                            </div>
                            <div className="flex items-center gap-2">
                              {p.severity && (
                                <span className={`text-[8px] font-black px-2 py-0.5 rounded border ${
                                  p.severity === 'HIGH' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                                }`}>
                                  {p.severity}
                                </span>
                              )}
                              <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[9px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider">{p.status}</span>
                            </div>
                          </div>
                          <h3 className="font-bold text-sm text-slate-200 tracking-tight">{p.name}</h3>
                          <p className="text-[10px] text-slate-500 font-mono mt-1">{p.path}.rego</p>
                          {p.description && (
                            <p className="text-xs text-slate-400 font-medium mt-3 leading-relaxed">{p.description}</p>
                          )}
                        </div>

                        {isExpanded && (
                          <div className="mt-6 border-t border-slate-800/80 pt-6 space-y-5 fade-in" onClick={(e) => e.stopPropagation()}>
                            {/* Standards mapped */}
                            {p.standards && p.standards.length > 0 && (
                              <div>
                                <h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">Compliance Frameworks</h4>
                                <div className="flex flex-wrap gap-2">
                                  {p.standards.map((std, i) => (
                                    <span key={i} className="text-[9px] font-bold bg-slate-900 border border-slate-800 text-indigo-400 px-2.5 py-1 rounded-md">
                                      {std}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Logic check list */}
                            {p.rules_list && p.rules_list.length > 0 && (
                              <div>
                                <h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">Evaluated Checkpoints ({p.rules})</h4>
                                <ul className="space-y-2">
                                  {p.rules_list.map((rule, idx) => (
                                    <li key={idx} className="text-xs text-slate-300 flex items-start gap-2.5">
                                      <span className="h-1.5 w-1.5 rounded-full bg-indigo-500 mt-1.5 shrink-0"></span>
                                      <span>{rule}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {/* Remediation block */}
                            {p.remediation && (
                              <div className="rounded-xl border border-emerald-500/10 bg-emerald-500/5 px-4 py-3 flex gap-3">
                                <div className="p-1.5 bg-emerald-500/10 rounded-lg text-emerald-400 h-fit">
                                  <Wrench size={13} />
                                </div>
                                <div>
                                  <h5 className="text-[9px] font-bold uppercase tracking-wider text-emerald-400 mb-0.5">Governance Guide</h5>
                                  <p className="text-xs leading-relaxed text-emerald-300/90 font-medium">{p.remediation}</p>
                                </div>
                              </div>
                            )}
                          </div>
                        )}

                        <div className="mt-6 flex items-center justify-between border-t border-slate-800/45 pt-4">
                          <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">{p.rules} Logic Rules</span>
                          <div className="text-slate-500 hover:text-indigo-400 transition-colors flex items-center gap-1">
                            <span className="text-[9px] font-bold uppercase tracking-widest">{isExpanded ? 'Hide Details' : 'Show Details'}</span>
                            {isExpanded ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {activeView === 'audit' && (
            <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
              {/* Left Panel: Scan History List */}
              <div className="xl:col-span-4 bg-slate-900/30 backdrop-blur-md rounded-2xl border border-slate-800/80 overflow-hidden shadow-lg">
                <div className="p-6 border-b border-slate-800/80 bg-slate-900/40">
                  <h2 className="text-base font-bold text-slate-200 tracking-tight">Scan History</h2>
                  <p className="text-[11px] text-slate-500 font-medium mt-0.5">Pick a scan run to review audit data.</p>
                </div>
                <div className="max-h-[620px] overflow-y-auto divide-y divide-slate-800/40 scrollbar-thin">
                  {scanRuns.length === 0 ? (
                    <div className="p-8 text-xs font-bold text-slate-500 italic text-center">No scans persisted yet.</div>
                  ) : (
                    scanRuns.map((scan) => (
                      <button
                        key={scan.id}
                        type="button"
                        onClick={() => setSelectedHistoryScanId(scan.id)}
                        className={`w-full text-left p-5 transition-colors cursor-pointer flex flex-col ${selectedHistoryScanId === scan.id ? 'bg-indigo-500/5' : 'hover:bg-slate-900/20'}`}
                      >
                        <div className="flex items-center justify-between gap-3 w-full">
                          <span className="text-xs font-bold text-slate-200 group-hover:text-slate-100">{scan.service_name}</span>
                          <span className={`rounded-full px-2 py-0.2 text-[8px] font-black border ${
                            scan.status === 'COMPLETED' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                            scan.status === 'FAILED' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' :
                            scan.status === 'RUNNING' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' : 'bg-slate-800 text-slate-500 border-slate-700'
                          }`}>
                            {scan.status}
                          </span>
                        </div>
                        <p className="mt-2 break-all text-[9px] font-mono text-slate-500">ID: {scan.id}</p>
                        <div className="mt-3 flex flex-wrap gap-2 text-[9px] font-bold text-slate-500 border-t border-slate-800/20 pt-2 w-full">
                          <span>{new Date(scan.started_at).toLocaleDateString()}</span>
                          <span>•</span>
                          <span className="text-indigo-400">{scan.violations_found} violations</span>
                          <span>•</span>
                          <span>{scan.log_count ?? 0} logs</span>
                          <span>•</span>
                          <span>{scan.audit_count ?? 0} audit events</span>
                          {scan.compliance_score !== undefined && (
                            <>
                              <span>•</span>
                              <span className="text-emerald-400">{Number(scan.compliance_score).toFixed(0)} score</span>
                            </>
                          )}
                        </div>
                      </button>
                    ))
                  )}
                </div>
              </div>

              {/* Right Panel: Persistence Telemetry details */}
              <div className="xl:col-span-8 space-y-6">
                {selectedHistoryScan && (
                  <div className="rounded-2xl border border-slate-800/80 bg-slate-900/30 backdrop-blur-md shadow-lg overflow-hidden">
                    <div className="border-b border-slate-800/80 bg-slate-900/40 px-6 py-5">
                      <div className="flex flex-wrap items-start justify-between gap-4">
                        <div className="min-w-0">
                          <p className="text-[9px] font-bold uppercase tracking-widest text-indigo-400">Selected Evidence Package</p>
                          <h2 className="mt-1 text-lg font-bold tracking-tight text-slate-200">{selectedHistoryScan.service_name}</h2>
                          <p className="mt-1 break-all text-[10px] font-mono text-slate-500">{selectedHistoryScan.id}</p>
                        </div>
                        <span className={`rounded-full px-3 py-0.5 text-[9px] font-bold border ${
                          selectedHistoryScan.status === 'COMPLETED' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                          selectedHistoryScan.status === 'FAILED' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' :
                          selectedHistoryScan.status === 'RUNNING' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' : 'bg-slate-800 text-slate-500 border-slate-700/60'
                        }`}>
                          {selectedHistoryScan.status}
                        </span>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-px bg-slate-800/40 md:grid-cols-4">
                      <div className="bg-slate-950/20 px-5 py-4">
                        <p className="text-[9px] font-bold uppercase tracking-widest text-slate-500">Violations</p>
                        <p className="mt-1 text-xl font-bold text-rose-400 glow-rose">{selectedHistoryScan.violations_found}</p>
                      </div>
                      <div className="bg-slate-950/20 px-5 py-4">
                        <p className="text-[9px] font-bold uppercase tracking-widest text-slate-500">Execution Logs</p>
                        <p className="mt-1 text-xl font-bold text-slate-200">{selectedHistoryScan.log_count ?? scanLogs.length}</p>
                      </div>
                      <div className="bg-slate-950/20 px-5 py-4">
                        <p className="text-[9px] font-bold uppercase tracking-widest text-slate-500">Audit Events</p>
                        <p className="mt-1 text-xl font-bold text-slate-200">{selectedHistoryScan.audit_count ?? historyAuditEvents.length}</p>
                      </div>
                      <div className="bg-slate-950/20 px-5 py-4">
                        <p className="text-[9px] font-bold uppercase tracking-widest text-slate-500">Compliance Score</p>
                        <p className="mt-1 text-xl font-bold text-emerald-400 glow-emerald">
                          {selectedHistoryScan.compliance_score !== undefined ? `${Number(selectedHistoryScan.compliance_score).toFixed(0)}%` : '--'}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Persisted Logs */}
                <div className="bg-slate-900/30 backdrop-blur-md rounded-2xl border border-slate-800/80 overflow-hidden shadow-lg">
                  <div className="px-6 py-4.5 border-b border-slate-800/80 bg-slate-900/40 flex flex-wrap items-center justify-between gap-4">
                    <div>
                      <h2 className="text-sm font-bold text-slate-200 tracking-tight">Persisted Execution Logs</h2>
                      <p className="text-[10px] font-mono text-slate-500 mt-0.5">
                        {selectedHistoryScanId ? `Scan ID: ${selectedHistoryScanId}` : 'Select a scan'}
                      </p>
                    </div>
                    <span className="rounded-full bg-slate-800 border border-slate-700/50 px-2.5 py-0.5 text-[9px] font-bold text-slate-400">
                      {scanLogs.length} events
                    </span>
                  </div>
                  <div className="h-80 overflow-y-auto bg-[#070b12] p-5 font-mono text-[10px] leading-relaxed scrollbar-thin">
                    {scanLogs.length === 0 ? (
                      <div className="text-slate-600 italic">No logs persisted for this scan run.</div>
                    ) : (
                      <div className="space-y-1.5">
                        {scanLogs.map((log) => (
                          <div key={log.id} className="grid grid-cols-[80px_110px_1fr] gap-3 border-l border-slate-800 pl-3">
                            <span className="text-slate-500">{new Date(log.timestamp).toLocaleTimeString([], { hour12: false })}</span>
                            <span className="font-bold text-indigo-400 uppercase tracking-tighter">{log.event_type}</span>
                            <span className="text-slate-300">{log.message}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                <ViolationLog
                  violations={historyViolations}
                  compact
                  collapsible
                  collapsed={historyViolationsCollapsed}
                  onCollapsedChange={setHistoryViolationsCollapsed}
                />

                <AuditTrail
                  events={historyAuditEvents}
                  compact
                  collapsible
                  collapsed={historyAuditCollapsed}
                  onCollapsedChange={setHistoryAuditCollapsed}
                  emptyMessage="No signed audit rows found for this scan. If this is an older scan, run a new scan after restarting the backend."
                />
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default App;
