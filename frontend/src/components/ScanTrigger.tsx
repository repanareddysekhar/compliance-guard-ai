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
    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
      <div className="flex items-center gap-2 mb-4">
        <Play size={16} className="text-indigo-600" />
        <h3 className="text-sm font-black text-slate-800 uppercase tracking-widest">Trigger Engine</h3>
      </div>
      <form onSubmit={handleScan} className="space-y-4">
        <div>
          <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Service Name</label>
          <input
            type="text"
            value={serviceName}
            onChange={(e) => setServiceName(e.target.value)}
            placeholder="e.g. AuthService"
            className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm font-semibold focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all outline-none"
            required
          />
        </div>
        <div>
          <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Repository Path</label>
          <input
            type="text"
            value={repoPath}
            onChange={(e) => setRepoPath(e.target.value)}
            placeholder="e.g. /app"
            className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm font-semibold focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all outline-none"
            required
          />
        </div>
        <button
          type="submit"
          disabled={loading || !serviceName || !repoPath}
          className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white font-black text-xs uppercase tracking-widest py-3 rounded-lg transition-all shadow-lg shadow-indigo-100 flex items-center justify-center gap-2 active:scale-95"
        >
          {loading ? <Loader2 className="animate-spin h-4 w-4" /> : <ShieldCheck className="h-4 w-4" />}
          {loading ? 'Executing...' : 'Initiate Scan'}
        </button>
      </form>
    </div>
  );
};

export default ScanTrigger;
