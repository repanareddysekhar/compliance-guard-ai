import React, { useState, useEffect } from 'react';
import StatsBar from './components/StatsBar';
import ScanTrigger from './components/ScanTrigger';
import ScanStatus from './components/ScanStatus';
import ViolationLog from './components/ViolationLog';
import { useScanWebSocket } from './hooks/useScanWebSocket';
import { useViolations } from './hooks/useViolations';
import { Shield, Activity, Book, History, ExternalLink, Code, PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import client from './api/client';
import { AuditEvent, ScanLog, ScanRun } from './types';

type View = 'dashboard' | 'policies' | 'audit';

interface Policy {
  id: number;
  name: string;
  path: string;
  status: string;
  rules: number;
}

const App: React.FC = () => {
  const [activeView, setActiveView] = useState<View>('dashboard');
  const [currentScanId, setCurrentScanId] = useState<string | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const { events, status } = useScanWebSocket(currentScanId);
  const { violations } = useViolations(currentScanId || undefined);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [scanRuns, setScanRuns] = useState<ScanRun[]>([]);
  const [scanLogs, setScanLogs] = useState<ScanLog[]>([]);
  const [selectedHistoryScanId, setSelectedHistoryScanId] = useState<string | null>(null);
  const [policies, setPolicies] = useState<Policy[]>([]);

  // Mock stats for demo purposes
  const stats = {
    services: 1,
    violations: violations.length,
    fixed: 0,
    score: currentScanId ? 85 : 100
  };

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
      setAuditEvents([]);
      setScanLogs([]);
      return;
    }

    client.get(`/api/audit/${selectedHistoryScanId}`).then((res: { data: AuditEvent[] }) => setAuditEvents(res.data));
    client.get(`/api/scan/${selectedHistoryScanId}/logs`).then((res: { data: ScanLog[] }) => setScanLogs(res.data));
  }, [activeView, selectedHistoryScanId]);

  return (
    <div className="flex h-screen bg-slate-50 text-slate-900 overflow-hidden font-sans">
      {/* Sidebar - Simple Navigation */}
      <aside className={`bg-white border-r border-slate-200 flex flex-col py-6 px-4 shrink-0 transition-all duration-300 ${sidebarCollapsed ? 'w-20 items-center' : 'w-20 lg:w-64 items-center lg:items-stretch'}`}>
        <div className={`flex items-center gap-3 px-2 mb-10 ${sidebarCollapsed ? 'justify-center' : 'justify-between'}`}>
          <div className="bg-indigo-600 p-2 rounded-xl shadow-lg shadow-indigo-200 cursor-pointer" onClick={() => setActiveView('dashboard')}>
            <Shield className="text-white h-6 w-6" />
          </div>
          <div className={`${sidebarCollapsed ? 'hidden' : 'hidden lg:block'} overflow-hidden`}>
            <h1 className="text-sm font-black tracking-tight whitespace-nowrap">COMPLIANCEGUARD</h1>
            <p className="text-[10px] text-slate-400 font-bold uppercase tracking-tighter leading-none">v2.0 Autonomous</p>
          </div>
          <button
            type="button"
            onClick={() => setSidebarCollapsed((collapsed) => !collapsed)}
            className={`${sidebarCollapsed ? 'hidden' : 'hidden lg:flex'} h-8 w-8 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors`}
            aria-label="Collapse sidebar"
          >
            <PanelLeftClose size={16} />
          </button>
        </div>

        <nav className="flex-1 space-y-2">
          <div 
            onClick={() => setActiveView('dashboard')}
            className={`p-3 rounded-xl flex items-center gap-3 cursor-pointer group transition-all ${
              activeView === 'dashboard' ? 'bg-indigo-50 text-indigo-700 shadow-sm' : 'text-slate-400 hover:bg-slate-50 hover:text-slate-600'
            }`}
          >
            <Activity size={20} className="shrink-0" />
            <span className={`${sidebarCollapsed ? 'hidden' : 'hidden lg:block'} text-sm font-bold ${activeView === 'dashboard' ? '' : 'opacity-70 group-hover:opacity-100'}`}>Active Scans</span>
          </div>
          <div 
            onClick={() => setActiveView('policies')}
            className={`p-3 rounded-xl flex items-center gap-3 cursor-pointer group transition-all ${
              activeView === 'policies' ? 'bg-indigo-50 text-indigo-700 shadow-sm' : 'text-slate-400 hover:bg-slate-50 hover:text-slate-600'
            }`}
          >
            <Book size={20} className="shrink-0" />
            <span className={`${sidebarCollapsed ? 'hidden' : 'hidden lg:block'} text-sm font-bold ${activeView === 'policies' ? '' : 'opacity-70 group-hover:opacity-100'}`}>Policy Library</span>
          </div>
          <div 
            onClick={() => setActiveView('audit')}
            className={`p-3 rounded-xl flex items-center gap-3 cursor-pointer group transition-all ${
              activeView === 'audit' ? 'bg-indigo-50 text-indigo-700 shadow-sm' : 'text-slate-400 hover:bg-slate-50 hover:text-slate-600'
            }`}
          >
            <History size={20} className="shrink-0" />
            <span className={`${sidebarCollapsed ? 'hidden' : 'hidden lg:block'} text-sm font-bold ${activeView === 'audit' ? '' : 'opacity-70 group-hover:opacity-100'}`}>Scan History</span>
          </div>
        </nav>

        <div className="mt-auto pt-6 border-t border-slate-100">
          {sidebarCollapsed && (
            <button
              type="button"
              onClick={() => setSidebarCollapsed(false)}
              className="mb-4 hidden h-9 w-9 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700 lg:flex"
              aria-label="Expand sidebar"
            >
              <PanelLeftOpen size={17} />
            </button>
          )}
          <div className={`flex items-center gap-3 px-2 py-3 rounded-xl bg-slate-50 border border-slate-100 ${sidebarCollapsed ? 'justify-center' : ''}`}>
            <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-white text-xs font-black shadow-sm shrink-0">
              TS
            </div>
            <div className={`${sidebarCollapsed ? 'hidden' : 'hidden lg:block'} overflow-hidden`}>
              <p className="text-xs font-black truncate leading-none mb-1">Stacktracers</p>
              <p className="text-[9px] text-slate-400 font-mono font-bold leading-none uppercase">ID: B1A342C5</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 bg-white/80 backdrop-blur-md border-b border-slate-200 px-8 flex items-center justify-between z-10">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Dashboard</span>
              <span className="text-slate-300">/</span>
              <span className="text-xs font-bold text-slate-800 uppercase tracking-widest">
                {activeView === 'dashboard' ? 'Scan Control' : activeView === 'policies' ? 'Policy Management' : 'Scan History'}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></div>
            <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">System Operational</span>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto px-6 py-6 md:px-10 md:py-8">
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
                  <ScanStatus events={events} status={status} />
                </div>
                
                <div className="2xl:col-span-8 h-full">
                  <ViolationLog violations={violations} />
                </div>
              </div>
            </div>
          )}

          {activeView === 'policies' && (
            <div className="space-y-6 max-w-6xl">
              <div className="bg-white rounded-2xl p-8 border border-slate-200 shadow-sm">
                <h2 className="text-2xl font-black text-slate-800 mb-2 tracking-tight">Policy Governance</h2>
                <p className="text-slate-500 font-medium">Manage and review active OPA policies enforced by ArmorIQ.</p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8">
                  {policies.map(p => (
                    <div key={p.id} className="p-6 rounded-xl border border-slate-100 bg-slate-50/50 hover:border-indigo-100 hover:bg-white transition-all group cursor-pointer">
                      <div className="flex justify-between items-start mb-4">
                        <div className="p-2 bg-white rounded-lg shadow-sm group-hover:text-indigo-600 transition-colors">
                          <Code size={20} />
                        </div>
                        <span className="bg-emerald-100 text-emerald-700 text-[10px] font-black px-2 py-0.5 rounded uppercase">{p.status}</span>
                      </div>
                      <h3 className="font-bold text-slate-800">{p.name}</h3>
                      <p className="text-xs text-slate-400 font-mono mt-1">{p.path}.rego</p>
                      <div className="mt-6 flex items-center justify-between">
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{p.rules} Logic Rules</span>
                        <ExternalLink size={14} className="text-slate-300 group-hover:text-indigo-500" />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeView === 'audit' && (
            <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
              <div className="xl:col-span-4 bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="p-8 border-b border-slate-100">
                  <h2 className="text-2xl font-black text-slate-800 tracking-tight">Scan History</h2>
                  <p className="text-slate-500 font-medium">Pick a scan to replay persisted logs.</p>
                </div>
                <div className="max-h-[680px] overflow-y-auto divide-y divide-slate-100">
                  {scanRuns.length === 0 ? (
                    <div className="p-8 text-sm font-medium text-slate-400">No scans persisted yet.</div>
                  ) : (
                    scanRuns.map((scan) => (
                      <button
                        key={scan.id}
                        type="button"
                        onClick={() => setSelectedHistoryScanId(scan.id)}
                        className={`w-full text-left p-5 transition-colors ${selectedHistoryScanId === scan.id ? 'bg-indigo-50' : 'hover:bg-slate-50'}`}
                      >
                        <div className="flex items-center justify-between gap-3">
                          <span className="text-sm font-black text-slate-800">{scan.service_name}</span>
                          <span className={`rounded px-2 py-0.5 text-[10px] font-black ${
                            scan.status === 'COMPLETED' ? 'bg-emerald-100 text-emerald-700' :
                            scan.status === 'FAILED' ? 'bg-rose-100 text-rose-700' :
                            scan.status === 'RUNNING' ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-600'
                          }`}>
                            {scan.status}
                          </span>
                        </div>
                        <p className="mt-2 break-all text-[11px] font-mono text-slate-500">Scan ID: {scan.id}</p>
                        <div className="mt-3 flex flex-wrap gap-2 text-[10px] font-bold text-slate-500">
                          <span>{new Date(scan.started_at).toLocaleString()}</span>
                          <span>•</span>
                          <span>{scan.violations_found} violations</span>
                          {scan.compliance_score !== undefined && (
                            <>
                              <span>•</span>
                              <span>{Number(scan.compliance_score).toFixed(0)} score</span>
                            </>
                          )}
                        </div>
                      </button>
                    ))
                  )}
                </div>
              </div>

              <div className="xl:col-span-8 space-y-6">
                <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
                  <div className="p-6 border-b border-slate-100 flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <h2 className="text-xl font-black text-slate-800 tracking-tight">Persisted Execution Logs</h2>
                      <p className="text-xs font-mono text-slate-500 mt-1">
                        {selectedHistoryScanId ? `Scan ID: ${selectedHistoryScanId}` : 'Select a scan'}
                      </p>
                    </div>
                    <span className="rounded-lg bg-slate-100 px-2.5 py-1 text-[10px] font-black text-slate-600">
                      {scanLogs.length} events
                    </span>
                  </div>
                  <div className="h-80 overflow-y-auto bg-slate-950 p-4 font-mono text-[11px] leading-relaxed">
                    {scanLogs.length === 0 ? (
                      <div className="text-slate-600 italic">No persisted logs for this scan.</div>
                    ) : (
                      <div className="space-y-2">
                        {scanLogs.map((log) => (
                          <div key={log.id} className="grid grid-cols-[88px_120px_1fr] gap-3 border-l border-slate-800 pl-3">
                            <span className="text-slate-600">{new Date(log.timestamp).toLocaleTimeString([], { hour12: false })}</span>
                            <span className="font-black text-indigo-300">{log.event_type}</span>
                            <span className="text-slate-300">{log.message}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
                  <div className="p-6 border-b border-slate-100">
                    <h2 className="text-xl font-black text-slate-800 tracking-tight">Cryptographic Audit Trail</h2>
                    <p className="text-slate-500 font-medium">Signed agent actions persisted in PostgreSQL.</p>
                  </div>
                  <div className="overflow-x-auto">
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
                      {auditEvents.length === 0 ? (
                        <tr>
                          <td colSpan={5} className="px-8 py-20 text-center text-slate-400 font-medium italic">
                            No audit events recorded for the current scan session.
                          </td>
                        </tr>
                      ) : (
                        auditEvents.map(event => (
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
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default App;
