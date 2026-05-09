'use client'

import React, { useState, useEffect } from "react";
import StrikePricesTable from './StrikePricesTable';
import AccountSummary from './AccountSummary';
import TradingChart from './TradingChart';

const MobileTradingDashboard = () => {
  const [activeTab, setActiveTab] = useState<'strikes' | 'account' | 'chart'>('strikes');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return null;
  }

  return (
    <div className="lg:hidden">
      {/* Mobile Tab Navigation */}
      <div className="flex mb-3 bg-gray-800 rounded-lg p-1">
        <button
          onClick={() => setActiveTab('strikes')}
          className={`flex-1 px-2 py-2 text-sm font-medium rounded-md transition-colors ${
            activeTab === 'strikes'
              ? 'bg-blue-600 text-white'
              : 'text-gray-300 hover:text-white hover:bg-gray-700'
          }`}
        >
          📊 Strikes
        </button>
        <button
          onClick={() => setActiveTab('account')}
          className={`flex-1 px-2 py-2 text-sm font-medium rounded-md transition-colors ${
            activeTab === 'account'
              ? 'bg-green-600 text-white'
              : 'text-gray-300 hover:text-white hover:bg-gray-700'
          }`}
        >
          💼 Account
        </button>
        <button
          onClick={() => setActiveTab('chart')}
          className={`flex-1 px-2 py-2 text-sm font-medium rounded-md transition-colors ${
            activeTab === 'chart'
              ? 'bg-purple-600 text-white'
              : 'text-gray-300 hover:text-white hover:bg-gray-700'
          }`}
        >
          📈 Chart
        </button>
      </div>

      {/* Mobile Controls */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex gap-2">
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="px-3 py-1 bg-gray-600 hover:bg-gray-700 text-white text-xs rounded transition-colors"
          >
            {isFullscreen ? '🗗 Normal' : '🗖 Expand'}
          </button>
          <button className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition-colors">
            🔄 Refresh
          </button>
        </div>
        
        <div className="text-xs text-gray-400">
          {activeTab === 'strikes' ? '5 Strikes' : activeTab === 'account' ? '2 Positions' : 'NIFTY Chart'}
        </div>
      </div>

      {/* Tab Content */}
      <div 
        className={`transition-all duration-300 ${
          isFullscreen 
            ? 'fixed inset-0 z-50 bg-[#0b1220] p-4 pt-12' 
            : 'relative'
        }`}
        style={{ height: isFullscreen ? '100vh' : '70vh' }}
      >
        {/* Fullscreen Close Button */}
        {isFullscreen && (
          <button
            onClick={() => setIsFullscreen(false)}
            className="absolute top-2 right-2 w-8 h-8 bg-red-600 hover:bg-red-700 text-white rounded-full text-sm z-10 flex items-center justify-center"
          >
            ✕
          </button>
        )}

        {activeTab === 'strikes' ? (
          <StrikePricesTable className="h-full" />
        ) : activeTab === 'account' ? (
          <AccountSummary className="h-full" />
        ) : (
          <TradingChart className="h-full" />
        )}
      </div>

      {/* Mobile Quick Actions */}
      <div className="mt-3 grid grid-cols-2 gap-2">
        <button className="px-3 py-2 bg-green-600 hover:bg-green-700 text-white text-sm rounded transition-colors flex items-center justify-center gap-1">
          🤖 Auto Buy
        </button>
        <button className="px-3 py-2 bg-red-600 hover:bg-red-700 text-white text-sm rounded transition-colors flex items-center justify-center gap-1">
          🤖 Auto Sell
        </button>
      </div>

      {/* Mobile Trading Stats */}
      <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
        <div className="bg-gray-800 rounded p-2">
          <div className="text-gray-400">Today's Trades</div>
          <div className="text-white font-bold">12 trades</div>
        </div>
        <div className="bg-gray-800 rounded p-2">
          <div className="text-gray-400">Success Rate</div>
          <div className="text-green-400 font-bold">75%</div>
        </div>
      </div>

      {/* Mobile Status */}
      <div className="mt-3 text-xs text-gray-400 text-center">
        Last Update: {mounted ? new Date().toLocaleTimeString() : '--:--:--'} • 🟢 Live
      </div>
    </div>
  );
};

export default MobileTradingDashboard;