import React, { useState } from 'react';
import client from '../api/client';
import { Play, Loader2, ShieldCheck } from 'lucide-react';

interface ScanTriggerProps {
  onScanTriggered: (scanId: string) => void;
}

const ScanTrigger: React.FC<ScanTriggerProps> = ({ onScanTriggered }) => {
  const [serviceName, setServiceName] = useState('ComplianceGuard-AI');
  const [repoPath, setRepoPath] = useState('/app');
  const [loading, setLoading] = useState(false);

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!serviceName || !repoPath) return;

    setLoading(true);
    try {
      const res = await client.post("/api/scan", { 
        service_name: serviceName, 
        repo_path: repoPath 
      });
      onScanTriggered(res.data.scan_id);
    } catch (err) {
      console.error("Failed to trigger scan", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900/30 backdrop-blur-md p-6 rounded-2xl border border-slate-800/80 shadow-lg shadow-indigo-950/5">
      <div className="flex items-center gap-2.5 mb-5">
        <div className="p-1.5 bg-indigo-500/10 rounded-lg text-indigo-400">
          <Play size={14} className="fill-indigo-400/20" />
        </div>
        <h3 className="text-xs font-bold text-slate-300 uppercase tracking-widest">Trigger Engine</h3>
      </div>
      <form onSubmit={handleScan} className="space-y-4">
        <div>
          <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1.5">Service Name</label>
          <input
            type="text"
            value={serviceName}
            onChange={(e) => setServiceName(e.target.value)}
            placeholder="e.g. AuthService"
            className="w-full px-4 py-2.5 bg-slate-950/40 border border-slate-800/80 rounded-xl text-sm font-semibold text-slate-200 placeholder-slate-600 focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500/50 transition-all outline-none"
            required
          />
        </div>
        <div>
          <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1.5">Repository Path</label>
          <input
            type="text"
            value={repoPath}
            onChange={(e) => setRepoPath(e.target.value)}
            placeholder="e.g. /app"
            className="w-full px-4 py-2.5 bg-slate-950/40 border border-slate-800/80 rounded-xl text-sm font-semibold text-slate-200 placeholder-slate-600 focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500/50 transition-all outline-none"
            required
          />
        </div>
        <button
          type="submit"
          disabled={loading || !serviceName || !repoPath}
          className="w-full relative overflow-hidden group bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 disabled:from-indigo-800/50 disabled:to-violet-800/50 text-white font-bold text-xs uppercase tracking-widest py-3.5 rounded-xl transition-all duration-300 shadow-md shadow-indigo-500/10 hover:shadow-[0_0_20px_rgba(99,102,241,0.3)] active:scale-[0.98] flex items-center justify-center gap-2 cursor-pointer disabled:cursor-not-allowed"
        >
          {loading ? (
            <Loader2 className="animate-spin h-4 w-4 text-indigo-200" />
          ) : (
            <ShieldCheck className="h-4 w-4 transition-transform group-hover:scale-110" />
          )}
          <span>{loading ? 'Executing Scan...' : 'Initiate Scan'}</span>
        </button>
      </form>
    </div>
  );
};

export default ScanTrigger;
