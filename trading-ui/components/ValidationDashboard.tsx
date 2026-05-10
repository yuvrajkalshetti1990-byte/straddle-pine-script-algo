'use client';

import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  ShieldCheck, 
  AlertTriangle, 
  Zap, 
  BarChart3, 
  Clock, 
  RefreshCcw, 
  Layers,
  Loader2,
  AlertCircle
} from 'lucide-react';

interface ValidationData {
  summary: {
    net_pnl: number;
    win_rate: number;
    profit_factor: number;
    total_trades: number;
    max_drawdown: number;
  };
  integrity: {
    duplicates: number;
    restarts: number;
    drift_alerts: number;
    stale_data: number;
  };
  regime: {
    by_type: Record<string, { pnl: number; trades: number; win_rate: number }>;
    by_session: Record<string, { pnl: number; trades: number }>;
  };
  badges: {
    pine_match: boolean;
    restart_safe: boolean;
    duplicate_free: boolean;
    data_healthy: boolean;
  };
}

const ValidationDashboard = ({ indexName = 'NIFTY' }) => {
  const [data, setData] = useState<ValidationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMetrics = async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout

      const res = await fetch(`/api/v1/strategy/validation-summary?index=${indexName}`, {
        signal: controller.signal
      });
      clearTimeout(timeoutId);
      
      const result = await res.json();
      if (result.status === 'success') {
        setData(result.data);
        setError(null);
      } else {
        setError(result.message || 'Failed to load telemetry');
      }
    } catch (err: any) {
      if (err.name === 'AbortError') {
        setError('Request timed out');
      } else {
        console.error('Failed to fetch validation metrics:', err);
        setError('Connection failed');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000); // Polling every 30s
    return () => clearInterval(interval);
  }, [indexName]);

  if (loading && !data) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-400 space-y-4">
        <Loader2 className="animate-spin text-blue-500" size={32} />
        <span className="text-sm font-medium animate-pulse">Loading Validation Telemetry...</span>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-400 border border-gray-800 border-dashed rounded-2xl bg-gray-900/20">
        <AlertCircle className="text-red-500/50 mb-2" size={32} />
        <span className="text-sm font-medium">{error}</span>
        <button 
          onClick={() => { setLoading(true); fetchMetrics(); }}
          className="mt-4 text-xs text-blue-400 hover:text-blue-300 underline"
        >
          Try Again
        </button>
      </div>
    );
  }

  const Badge = ({ active, label, icon: Icon }: { active: boolean, label: string, icon: any }) => (
    <div className={`flex items-center space-x-2 px-3 py-1.5 rounded-full border ${
      active ? 'bg-green-500/10 border-green-500/50 text-green-400' : 'bg-red-500/10 border-red-500/50 text-red-400'
    }`}>
      <Icon size={14} />
      <span className="text-xs font-bold uppercase tracking-wider">{label}</span>
    </div>
  );

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Status Badges */}
      <div className="flex flex-wrap gap-3">
        <Badge active={!!data?.badges?.pine_match} label="Pine Match" icon={ShieldCheck} />
        <Badge active={!!data?.badges?.restart_safe} label="Restart Safe" icon={RefreshCcw} />
        <Badge active={!!data?.badges?.duplicate_free} label="Duplicate Free" icon={Layers} />
        <Badge active={!!data?.badges?.data_healthy} label="Data Healthy" icon={Activity} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Daily Summary */}
        <div className="lg:col-span-2 bg-gray-900/50 backdrop-blur-md border border-gray-800 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <BarChart3 className="text-blue-400" size={20} />
              Daily Validation Summary
            </h3>
            <span className="text-xs text-gray-500 uppercase tracking-widest">Paper Trade: Day 1 of 30</span>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 bg-gray-800/50 rounded-xl border border-gray-700">
              <div className="text-gray-400 text-xs mb-1 uppercase tracking-wider">Net P&L</div>
              <div className={`text-xl font-bold ${(data?.summary?.net_pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                ₹{(data?.summary?.net_pnl || 0).toLocaleString('en-IN')}
              </div>
            </div>
            <div className="p-4 bg-gray-800/50 rounded-xl border border-gray-700">
              <div className="text-gray-400 text-xs mb-1 uppercase tracking-wider">Win Rate</div>
              <div className="text-xl font-bold text-white">{data?.summary?.win_rate || 0}%</div>
            </div>
            <div className="p-4 bg-gray-800/50 rounded-xl border border-gray-700">
              <div className="text-gray-400 text-xs mb-1 uppercase tracking-wider">Profit Factor</div>
              <div className="text-xl font-bold text-blue-400">{data?.summary?.profit_factor || 0}</div>
            </div>
            <div className="p-4 bg-gray-800/50 rounded-xl border border-gray-700">
              <div className="text-gray-400 text-xs mb-1 uppercase tracking-wider">Total Trades</div>
              <div className="text-xl font-bold text-purple-400">{data?.summary?.total_trades || 0}</div>
            </div>
          </div>
        </div>

        {/* Engine Integrity */}
        <div className="bg-gray-900/50 backdrop-blur-md border border-gray-800 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
            <ShieldCheck className="text-green-400" size={20} />
            Engine Integrity
          </h3>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-gray-800/30 rounded-lg">
              <div className="flex items-center gap-3">
                <Layers className="text-gray-500" size={18} />
                <span className="text-sm text-gray-300">Duplicate Entries</span>
              </div>
              <span className={`font-mono font-bold ${(data?.integrity?.duplicates || 0) > 0 ? 'text-red-400' : 'text-green-400'}`}>
                {data?.integrity?.duplicates || 0}
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-800/30 rounded-lg">
              <div className="flex items-center gap-3">
                <RefreshCcw className="text-gray-500" size={18} />
                <span className="text-sm text-gray-300">Restart Recovery</span>
              </div>
              <span className="font-mono font-bold text-blue-400">{data?.integrity?.restarts || 0}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-800/30 rounded-lg">
              <div className="flex items-center gap-3">
                <AlertTriangle className="text-gray-500" size={18} />
                <span className="text-sm text-gray-300">Drift Alerts</span>
              </div>
              <span className={`font-mono font-bold ${(data?.integrity?.drift_alerts || 0) > 0 ? 'text-orange-400' : 'text-green-400'}`}>
                {data?.integrity?.drift_alerts || 0}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Regime Breakdown */}
        <div className="bg-gray-900/50 backdrop-blur-md border border-gray-800 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
            <Zap className="text-orange-400" size={20} />
            Market Regime Performance
          </h3>
          <div className="grid grid-cols-2 gap-4">
            {Object.entries(data?.regime?.by_type || {}).map(([regime, stats]) => (
              <div key={regime} className="p-4 bg-gray-800/50 rounded-xl border border-gray-700">
                <div className="text-gray-400 text-xs mb-2 uppercase tracking-wider">{regime}</div>
                <div className={`text-lg font-bold ${(stats?.pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  ₹{(stats?.pnl || 0).toLocaleString('en-IN')}
                </div>
                <div className="text-[10px] text-gray-500 mt-1 uppercase">
                  {stats?.trades || 0} Trades | {stats?.win_rate || 0}% Win
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Session Analysis */}
        <div className="bg-gray-900/50 backdrop-blur-md border border-gray-800 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
            <Clock className="text-purple-400" size={20} />
            Session Analysis
          </h3>
          <div className="space-y-4">
            {Object.entries(data?.regime?.by_session || {}).map(([session, stats]) => (
              <div key={session} className="flex items-center justify-between p-4 bg-gray-800/50 rounded-xl border border-gray-700">
                <span className="text-sm font-medium text-gray-300">{session} Session</span>
                <div className="text-right">
                  <div className={`text-base font-bold ${(stats?.pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    ₹{(stats?.pnl || 0).toLocaleString('en-IN')}
                  </div>
                  <div className="text-[10px] text-gray-500 uppercase">{stats?.trades || 0} Trades</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ValidationDashboard;
