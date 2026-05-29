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
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard 
        label="Services" 
        value={services} 
        icon={<Search size={18} className="text-blue-600" />} 
        bgColor="bg-blue-50"
        borderColor="border-blue-200"
      />
      <StatCard 
        label="Violations" 
        value={violations} 
        icon={<AlertTriangle size={18} className="text-rose-600" />} 
        bgColor="bg-rose-50"
        borderColor="border-rose-200"
      />
      <StatCard 
        label="Auto-Fixed" 
        value={fixed} 
        icon={<CheckCircle size={18} className="text-emerald-600" />} 
        bgColor="bg-emerald-50"
        borderColor="border-emerald-200"
      />
      <StatCard 
        label="Health Score" 
        value={`${score}%`} 
        icon={<Shield size={18} className="text-indigo-600" />} 
        bgColor="bg-indigo-50"
        borderColor="border-indigo-200"
      />
    </div>
  );
};

interface StatCardProps {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  bgColor: string;
  borderColor: string;
}

const StatCard: React.FC<StatCardProps> = ({ label, value, icon, bgColor, borderColor }) => {
  return (
    <div className={`bg-white p-5 rounded-xl shadow-sm border ${borderColor} flex items-center gap-4 hover:shadow-md transition-shadow cursor-default group`}>
      <div className={`p-3 rounded-lg ${bgColor} group-hover:scale-110 transition-transform`}>
        {icon}
      </div>
      <div>
        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none mb-1">{label}</p>
        <p className="text-2xl font-black text-slate-800 tracking-tighter">{value}</p>
      </div>
    </div>
  );
};

export default StatsBar;
