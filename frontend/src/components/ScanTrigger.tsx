import React, { useState } from 'react';
import client from '../api/client';
import { Play, Loader2 } from 'lucide-react';

interface ScanTriggerProps {
  onScanTriggered: (scanId: string) => void;
}

const ScanTrigger: React.FC<ScanTriggerProps> = ({ onScanTriggered }) => {
  const [serviceName, setServiceName] = useState('');
  const [repoPath, setRepoPath] = useState('');
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
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mb-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">Start New Compliance Scan</h3>
      <form onSubmit={handleScan} className="flex flex-col md:flex-row gap-4">
        <div className="flex-1">
          <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Service Name</label>
          <input
            type="text"
            value={serviceName}
            onChange={(e) => setServiceName(e.target.value)}
            placeholder="e.g. AuthService"
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            required
          />
        </div>
        <div className="flex-[2]">
          <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Repository Path</label>
          <input
            type="text"
            value={repoPath}
            onChange={(e) => setRepoPath(e.target.value)}
            placeholder="e.g. /Users/rreddy/Documents/projects/auth-service"
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            required
          />
        </div>
        <div className="flex items-end">
          <button
            type="submit"
            disabled={loading || !serviceName || !repoPath}
            className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white font-bold py-2 px-6 rounded-md transition-colors flex items-center gap-2"
          >
            {loading ? <Loader2 className="animate-spin h-5 w-5" /> : <Play className="h-5 w-5" />}
            {loading ? 'Queuing...' : 'Trigger Scan'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ScanTrigger;
