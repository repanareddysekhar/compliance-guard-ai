import React, { useState, useEffect } from 'react';
import StatsBar from './components/StatsBar';
import ScanTrigger from './components/ScanTrigger';
import ScanStatus from './components/ScanStatus';
import ViolationLog from './components/ViolationLog';
import { useScanWebSocket } from './hooks/useScanWebSocket';
import { useViolations } from './hooks/useViolations';
import { Shield, Activity, Search, Book, History, ExternalLink, Code } from 'lucide-react';
import client from './api/client';
import { AuditEvent } from './types';

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
  const { events, status } = useScanWebSocket(currentScanId);
  const { violations } = useViolations(currentScanId || undefined);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [policies, setPolicies] = useState<Policy[]>([]);

  // Mock stats for demo purposes
  const stats = {
    services: 1,
    violations: violations.length,
    fixed: 0,
    score: currentScanId ? 85 : 100
  };

  useEffect(() => {
    if (activeView === 'audit' && currentScanId) {
      client.get(`/api/audit/${currentScanId}`).then((res: { data: AuditEvent[] }) => setAuditEvents(res.data));
    }
    if (activeView === 'policies') {
      client.get('/api/policies').then((res: { data: Policy[] }) => setPolicies(res.data));
    }
  }, [activeView, currentScanId]);

  return (
    <div className="flex h-screen bg-slate-50 text-slate-900 overflow-hidden font-sans">
      {/* Sidebar - Simple Navigation */}
      <aside className="w-20 lg:w-64 bg-white border-r border-slate-200 flex flex-col items-center lg:items-stretch py-6 px-4 shrink-0">
        <div className="flex items-center gap-3 px-2 mb-10">
          <div className="bg-indigo-600 p-2 rounded-xl shadow-lg shadow-indigo-200 cursor-pointer" onClick={() => setActiveView('dashboard')}>
            <Shield className="text-white h-6 w-6" />
          </div>
          <div className="hidden lg:block overflow-hidden">
            <h1 className="text-sm font-black tracking-tight whitespace-nowrap">COMPLIANCEGUARD</h1>
            <p className="text-[10px] text-slate-400 font-bold uppercase tracking-tighter leading-none">v2.0 Autonomous</p>
          </div>
        </div>

        <nav className="flex-1 space-y-2">
          <div 
            onClick={() => setActiveView('dashboard')}
            className={`p-3 rounded-xl flex items-center gap-3 cursor-pointer group transition-all ${
              activeView === 'dashboard' ? 'bg-indigo-50 text-indigo-700 shadow-sm' : 'text-slate-400 hover:bg-slate-50 hover:text-slate-600'
            }`}
          >
            <Activity size={20} className="shrink-0" />
            <span className={`hidden lg:block text-sm font-bold ${activeView === 'dashboard' ? '' : 'opacity-70 group-hover:opacity-100'}`}>Active Scans</span>
          </div>
          <div 
            onClick={() => setActiveView('policies')}
            className={`p-3 rounded-xl flex items-center gap-3 cursor-pointer group transition-all ${
              activeView === 'policies' ? 'bg-indigo-50 text-indigo-700 shadow-sm' : 'text-slate-400 hover:bg-slate-50 hover:text-slate-600'
            }`}
          >
            <Book size={20} className="shrink-0" />
            <span className={`hidden lg:block text-sm font-bold ${activeView === 'policies' ? '' : 'opacity-70 group-hover:opacity-100'}`}>Policy Library</span>
          </div>
          <div 
            onClick={() => setActiveView('audit')}
            className={`p-3 rounded-xl flex items-center gap-3 cursor-pointer group transition-all ${
              activeView === 'audit' ? 'bg-indigo-50 text-indigo-700 shadow-sm' : 'text-slate-400 hover:bg-slate-50 hover:text-slate-600'
            }`}
          >
            <History size={20} className="shrink-0" />
            <span className={`hidden lg:block text-sm font-bold ${activeView === 'audit' ? '' : 'opacity-70 group-hover:opacity-100'}`}>Audit Logs</span>
          </div>
        </nav>

        <div className="mt-auto pt-6 border-t border-slate-100">
          <div className="flex items-center gap-3 px-2 py-3 rounded-xl bg-slate-50 border border-slate-100">
            <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-white text-xs font-black shadow-sm shrink-0">
              TS
            </div>
            <div className="hidden lg:block overflow-hidden">
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
                {activeView === 'dashboard' ? 'Scan Control' : activeView === 'policies' ? 'Policy Management' : 'Autonomous Audit'}
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
              
              <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 items-start pb-10">
                <div className="xl:col-span-4 space-y-8">
                  <ScanTrigger onScanTriggered={setCurrentScanId} />
                  <ScanStatus events={events} status={status} />
                </div>
                
                <div className="xl:col-span-8 h-full">
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
            <div className="space-y-6">
              <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="p-8 border-b border-slate-100">
                  <h2 className="text-2xl font-black text-slate-800 tracking-tight">Audit Trail</h2>
                  <p className="text-slate-500 font-medium">Cryptographically signed execution logs verified by ArmorIQ.</p>
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
          )}
        </div>
      </main>
    </div>
  );
};

export default App;
