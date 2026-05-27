import React, { useState } from 'react';
import StatsBar from './components/StatsBar';
import ScanTrigger from './components/ScanTrigger';
import ScanStatus from './components/ScanStatus';
import ViolationLog from './components/ViolationLog';
import { useScanWebSocket } from './hooks/useScanWebSocket';
import { useViolations } from './hooks/useViolations';
import { Shield } from 'lucide-react';

const App: React.FC = () => {
  const [currentScanId, setCurrentScanId] = useState<string | null>(null);
  const { events, status } = useScanWebSocket(currentScanId);
  const { violations } = useViolations(currentScanId || undefined);

  // Mock stats for demo purposes
  const stats = {
    services: 1,
    violations: violations.length,
    fixed: 0,
    score: currentScanId ? 85 : 100
  };

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 font-sans">
      <header className="bg-white border-b border-gray-200 px-8 py-4 flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <div className="bg-indigo-600 p-2 rounded-lg">
            <Shield className="text-white h-6 w-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight">ComplianceGuard AI</h1>
            <p className="text-xs text-gray-500 font-medium uppercase tracking-widest">Autonomous Policy Enforcement</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-sm font-bold">The Stacktracers</p>
            <p className="text-[10px] text-gray-400 font-mono">team-B1A342C54DB3</p>
          </div>
          <div className="h-10 w-10 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-white font-bold">
            TS
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-8 py-8">
        <StatsBar 
          services={stats.services} 
          violations={stats.violations} 
          fixed={stats.fixed} 
          score={stats.score} 
        />
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-1">
            <ScanTrigger onScanTriggered={setCurrentScanId} />
            <ScanStatus events={events} status={status} />
          </div>
          
          <div className="lg:col-span-2">
            <ViolationLog violations={violations} />
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;
