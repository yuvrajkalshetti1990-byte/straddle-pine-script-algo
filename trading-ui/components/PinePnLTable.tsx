'use client'

import React, { useState, useEffect } from 'react';

interface StrikeState {
  label: string;
  strikePrice: number;
  lSig: number;
  lSigLong: number;
  ep: number | null;
  epLong: number | null;
  entryTime: string | null;
  exitTime: string | null;
  banked: number;
  pnlPoints: number;
  slSafe: boolean;
  isLong: boolean;
  trig: string;
  cntShort: number;
  cntLong: number;
  close: number;
  dayOpen: number;
}

interface StrategyStatusData {
  currentTime: string;
  engineRunning: boolean;
  activeTrades: number;
  closedTrades: number;
  strikes: Record<string, StrikeState>;
  account: {
    initialCapital: number;
    currentCapital: number;
    realizedPnl: number;
    floatingPnl: number;
    totalPnl: number;
  };
}

const PINE_LABEL_MAP: Record<string, string> = {
  S1: "ITM2",
  S2: "ITM1",
  S3: "ATM",
  S4: "OTM1",
  S5: "OTM2",
};

// Pine renders rows in this specific order
const STRIKE_ORDER = ["S1", "S2", "S3", "S4", "S5"];

export const PinePnLTable = ({ className = "" }: { className?: string }) => {
  const [statusData, setStatusData] = useState<StrategyStatusData | null>(null);
  const [configData, setConfigData] = useState<any>(null);
  const [mounted, setMounted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;

    const fetchState = async () => {
      try {
        const [statusRes, configRes] = await Promise.all([
          fetch('/api/v1/strategy/status?index=NIFTY'),
          fetch('/api/v1/strategy/config?index=NIFTY')
        ]);

        const statusResult = await statusRes.json();
        const configResult = await configRes.json();

        if (statusResult.status === 'success') {
          setStatusData(statusResult.data);
          setError(null);
        } else {
          setError(statusResult.message || 'Failed to fetch status');
        }

        if (configResult.status === 'success') {
          setConfigData(configResult.data);
        }
      } catch (err: any) {
        setError(err.message || 'Connection error');
      }
    };

    fetchState();
    const interval = setInterval(fetchState, 3000);
    return () => clearInterval(interval);
  }, [mounted]);

  if (!mounted) return <div className={`h-40 bg-gray-900 animate-pulse rounded-md ${className}`} />;

  if (!statusData || !configData) {
    return (
      <div className={`bg-[#020617] border border-gray-700 p-4 text-white text-center text-sm ${className}`}>
        {error ? <span className="text-red-400">Error: {error}</span> : "Loading Pine Script P&L..."}
      </div>
    );
  }

  const { strikes, account } = statusData;
  const userLotSize = configData.lotSize || 25; // Default NIFTY lot size
  const lotsShort = configData.short?.lots || 1;
  const lotsLong = configData.long?.lots || 1;

  const formatTime = (isoString: string | null) => {
    if (!isoString) return '—';
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return '—';
    return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: false });
  };

  const formatMoney = (val: number) => {
    const sign = val >= 0 ? '+₹' : '₹';
    return `${sign}${Math.floor(val)}`;
  };

  const formatPts = (val: number) => {
    const sign = val > 0 ? '+' : '';
    return `${sign}${val.toFixed(2)}`;
  };

  let tableTotalPnL = 0;
  let floatingSum = 0;

  return (
    <div className={`bg-black font-mono border border-gray-800 rounded-md overflow-hidden ${className}`}>
      {/* Pine Script Style Header */}
      <div className="bg-[#111] p-2 border-b border-gray-800 flex justify-between items-center">
        <h3 className="text-[11px] font-bold text-gray-300">PINE SCRIPT T2 TABLE</h3>
        <span className="text-[10px] text-gray-500">{statusData.engineRunning ? '🟢 LIVE' : '🔴 STOPPED'}</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-[11px] border-collapse bg-black text-white">
          <thead className="bg-[#1a1a1a]">
            <tr>
              {["STRIKE", "ENTRY", "EXIT", "LOTS", "PRICE", "PTS", "P&L", "TRIG", "S", "B"].map(h => (
                <th key={h} className="px-2 py-1 text-center font-normal text-gray-400 border border-gray-800 whitespace-nowrap">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {STRIKE_ORDER.map((label) => {
              const strike = strikes[label];
              if (!strike) return null;
              
              // Only render if there has been at least one trade or signal
              if (!strike.entryTime && strike.cntShort === 0 && strike.cntLong === 0 && strike.banked === 0) {
                 return null;
              }

              const pineLabel = PINE_LABEL_MAP[label] || label;
              const isShortActive = strike.lSig === -1;
              const isLongActive = strike.lSigLong === 2;
              
              const currentLots = (isLongActive || strike.isLong) ? lotsLong : lotsShort;
              const pnlVal = strike.pnlPoints * userLotSize * currentLots;
              
              tableTotalPnL += pnlVal;
              if (isShortActive || isLongActive) {
                floatingSum += pnlVal;
              }

              const pnlColorClass = strike.pnlPoints >= 0 ? "text-green-500" : "text-red-500";
              const entryPrice = strike.isLong ? strike.epLong : strike.ep;

              return (
                <tr key={label} className="border-b border-gray-800 hover:bg-[#111]">
                  <td className="px-2 py-1 text-center border-r border-gray-800">{pineLabel}</td>
                  <td className="px-2 py-1 text-center border-r border-gray-800">{formatTime(strike.entryTime)}</td>
                  <td className="px-2 py-1 text-center border-r border-gray-800">{formatTime(strike.exitTime)}</td>
                  <td className="px-2 py-1 text-center border-r border-gray-800">{currentLots}</td>
                  <td className="px-2 py-1 text-center border-r border-gray-800">{entryPrice !== null ? entryPrice.toFixed(2) : '—'}</td>
                  <td className={`px-2 py-1 text-center border-r border-gray-800 ${pnlColorClass}`}>{formatPts(strike.pnlPoints)}</td>
                  <td className={`px-2 py-1 text-center border-r border-gray-800 ${pnlColorClass}`}>{formatMoney(pnlVal)}</td>
                  <td className="px-2 py-1 text-center border-r border-gray-800 text-yellow-500">{strike.trig}</td>
                  <td className="px-2 py-1 text-center border-r border-gray-800">{strike.cntShort}</td>
                  <td className="px-2 py-1 text-center">{strike.cntLong}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Account Summary section matching Pine Script */}
      <div className="bg-[#1a1a1a] p-2 flex items-center justify-between border-t border-gray-800">
        <div className="flex space-x-6">
          <div className="text-[10px]">
            <span className="text-gray-500 mr-2">CAPITAL:</span>
            <span className="text-white">₹{account.initialCapital.toLocaleString('en-IN')}</span>
          </div>
          <div className="text-[10px]">
            <span className="text-gray-500 mr-2">DAY P&L:</span>
            <span className={tableTotalPnL >= 0 ? "text-green-500" : "text-red-500"}>
              {formatMoney(tableTotalPnL)}
            </span>
          </div>
          <div className="text-[10px]">
            <span className="text-gray-500 mr-2">FLOATING:</span>
            <span className={floatingSum >= 0 ? "text-green-500" : "text-red-500"}>
              {formatMoney(floatingSum)}
            </span>
          </div>
          <div className="text-[10px]">
            <span className="text-gray-500 mr-2">HIST:</span>
            <span className={account.realizedPnl >= 0 ? "text-green-500" : "text-red-500"}>
              {formatMoney(account.realizedPnl)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PinePnLTable;
