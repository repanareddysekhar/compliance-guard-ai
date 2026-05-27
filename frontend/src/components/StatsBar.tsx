import React from 'react';
import { Shield, AlertTriangle, CheckCircle, Search } from 'lucide-react';

interface StatsBarProps {
  services: number;
  violations: number;
  fixed: number;
  score: number;
}

const StatsBar: React.FC<StatsBarProps> = ({ services, violations, fixed, score }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <StatCard 
        label="Services Scanned" 
        value={services} 
        icon={<Search className="text-blue-500" />} 
        color="blue"
      />
      <StatCard 
        label="Total Violations" 
        value={violations} 
        icon={<AlertTriangle className="text-red-500" />} 
        color="red"
      />
      <StatCard 
        label="Auto-Fixed" 
        value={fixed} 
        icon={<CheckCircle className="text-green-500" />} 
        color="green"
      />
      <StatCard 
        label="Compliance Score" 
        value={`${score}%`} 
        icon={<Shield className="text-indigo-500" />} 
        color="indigo"
      />
    </div>
  );
};

interface StatCardProps {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
}

const StatCard: React.FC<StatCardProps> = ({ label, value, icon, color }) => {
  return (
    <div className={`bg-white p-4 rounded-lg shadow-sm border-l-4 border-${color}-500 flex items-center`}>
      <div className="p-3 rounded-full bg-gray-50 mr-4">
        {icon}
      </div>
      <div>
        <p className="text-sm text-gray-500 font-medium">{label}</p>
        <p className="text-2xl font-bold text-gray-800">{value}</p>
      </div>
    </div>
  );
};

export default StatsBar;
