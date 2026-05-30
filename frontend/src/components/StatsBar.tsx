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
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
      <StatCard 
        label="Services Scanned" 
        value={services} 
        icon={<Search size={20} />} 
        iconColor="text-blue-400"
        glowClass="shadow-blue-500/5 hover:shadow-blue-500/10 hover:border-blue-500/30"
        bgIcon="bg-blue-500/10"
      />
      <StatCard 
        label="Active Violations" 
        value={violations} 
        icon={<AlertTriangle size={20} />} 
        iconColor="text-rose-400"
        glowClass="shadow-rose-500/5 hover:shadow-rose-500/10 hover:border-rose-500/30"
        bgIcon="bg-rose-500/10"
        valueClass={violations > 0 ? "text-rose-400 glow-rose" : "text-slate-100"}
      />
      <StatCard 
        label="Auto-Remediated" 
        value={fixed} 
        icon={<CheckCircle size={20} />} 
        iconColor="text-emerald-400"
        glowClass="shadow-emerald-500/5 hover:shadow-emerald-500/10 hover:border-emerald-500/30"
        bgIcon="bg-emerald-500/10"
        valueClass={fixed > 0 ? "text-emerald-400 glow-emerald" : "text-slate-100"}
      />
      <StatCard 
        label="Compliance Score" 
        value={`${score}%`} 
        icon={<Shield size={20} />} 
        iconColor="text-indigo-400"
        glowClass="shadow-indigo-500/5 hover:shadow-indigo-500/10 hover:border-indigo-500/30"
        bgIcon="bg-indigo-500/10"
        valueClass="bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent font-black"
      />
    </div>
  );
};

interface StatCardProps {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  iconColor: string;
  glowClass: string;
  bgIcon: string;
  valueClass?: string;
}

const StatCard: React.FC<StatCardProps> = ({ label, value, icon, iconColor, glowClass, bgIcon, valueClass = "text-slate-100" }) => {
  return (
    <div className={`bg-slate-900/30 backdrop-blur-md border border-slate-800/80 p-5 rounded-2xl flex items-center gap-5 transition-all duration-300 ${glowClass} group cursor-default`}>
      <div className={`p-3.5 rounded-xl ${bgIcon} ${iconColor} group-hover:scale-105 transition-transform duration-300 flex items-center justify-center`}>
        {icon}
      </div>
      <div>
        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest leading-none mb-1.5">{label}</p>
        <p className={`text-2xl font-black tracking-tight leading-none ${valueClass}`}>{value}</p>
      </div>
    </div>
  );
};

export default StatsBar;
