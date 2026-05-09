'use client'

import React, { useState, useEffect } from 'react';

interface Trade {
  tradeId: string;
  strikeLabel: string;
  strikePrice: number;
  direction: string;
  optionType: string;
  entryPrice: number;
  currentPrice: number;
  lots: number;
  floatingPnl: number;
  entryTime: string;
  status: string;
  source: string;
  isReplay: boolean;
}

const OngoingTradesTable = ({ 
  className = "", 
  trades = [], 
  engineRunning = false,
  index = "NIFTY"
}: { 
  className?: string;
  trades?: Trade[];
  engineRunning?: boolean;
  index?: string;
}) => {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return <div className="h-40 bg-gray-900 animate-pulse rounded-md" />;

  const totalMTM = trades.reduce((sum, trade) => sum + trade.floatingPnl, 0);

  return (
    <div className={`border border-gray-700 bg-[#020617] rounded-md overflow-hidden ${className}`}>
      {/* Header with Control Buttons */}
      <div className="bg-[#1f2937] p-3 border-b border-gray-700">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            📊 Active Trades ({index})
          </h3>
          <div className="text-sm text-gray-300">
            Total MTM: <span className={totalMTM >= 0 ? 'text-green-400 font-bold' : 'text-red-400 font-bold'}>
              ₹{totalMTM.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </span>
          </div>
        </div>

        {/* Control Buttons */}
        <div className="flex items-center gap-3 flex-wrap">
          <span className={`text-xs px-2 py-1 rounded font-bold ${
            engineRunning ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'
          }`}>
            {engineRunning ? '🟢 RUNNING' : '🔴 STOPPED'}
          </span>
        </div>
      </div>

      {/* Trades Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-[11px] border-collapse min-w-[1000px]">
          <thead className="bg-[#1d4ed8]">
            <tr>
              {["TYPE", "SYMBOL", "SOURCE", "QTY", "ENTRY", "CURRENT", "MTM", "ENTRY TIME", "STATUS", "BOOK"].map(h => (
                <th key={h} className="px-2 py-1 text-left font-bold text-white border-r border-blue-900 whitespace-nowrap">
                  {h}
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {trades.length === 0 ? (
              <tr>
                <td colSpan={10} className="px-4 py-8 text-center text-gray-500 italic">
                  No active trades for {index}
                </td>
              </tr>
            ) : (
              trades.map((trade) => (
                <tr key={trade.tradeId} className="border-t border-gray-800 hover:bg-gray-800/50 transition-colors">
                  <td className={`px-2 py-1 font-bold text-xs ${
                    trade.direction === 'LONG' ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {trade.direction === 'LONG' ? 'BUY' : 'SELL'}
                  </td>
                  <td className="px-2 py-1 text-white font-mono font-semibold">
                    {trade.strikeLabel} {trade.optionType}
                  </td>
                  <td className="px-2 py-1">
                    <div className="flex items-center gap-1">
                      <span className={`px-1.5 py-0.5 rounded-[2px] text-[9px] font-bold ${
                        trade.source === 'LIVE' ? 'bg-blue-600/20 text-blue-400' : 'bg-purple-600/20 text-purple-400'
                      }`}>
                        {trade.source}
                      </span>
                      {trade.isReplay && (
                        <span className="bg-yellow-600/20 text-yellow-400 px-1 py-0.5 rounded-[2px] text-[9px] font-bold">
                          REPLAY
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-2 py-1 text-gray-300 font-semibold">{trade.lots}</td>
                  <td className="px-2 py-1 text-blue-300">₹{trade.entryPrice.toFixed(2)}</td>
                  <td className="px-2 py-1 text-yellow-300 font-semibold">₹{trade.currentPrice.toFixed(2)}</td>
                  <td className={`px-2 py-1 font-bold ${
                    trade.floatingPnl >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {trade.floatingPnl >= 0 ? '+' : ''}{trade.floatingPnl.toFixed(2)}
                  </td>
                  <td className="px-2 py-1 text-gray-400 text-[10px]">
                    {new Date(trade.entryTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </td>
                  <td className="px-2 py-1">
                    <span className="px-2 py-0.5 bg-green-900 text-green-300 rounded text-[10px] font-bold">
                      ACTIVE
                    </span>
                  </td>
                  <td className="px-2 py-1 text-center">
                    <button className="px-2 py-0.5 bg-gray-700 hover:bg-gray-600 text-white text-[10px] font-bold rounded transition-colors opacity-50 cursor-not-allowed">
                      BOOK
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Footer Info */}
      <div className="border-t border-gray-700 bg-[#020617] text-[11px] px-3 py-2">
        <div className="flex flex-wrap gap-4 items-center">
          <span className="text-white font-bold">Active Trades: {trades.length}</span>
          <span className={`font-bold ${totalMTM >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            Session MTM: ₹{totalMTM.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </span>
        </div>
      </div>
    </div>
  );
};

export default OngoingTradesTable;
