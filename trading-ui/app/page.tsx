'use client'

import { useState, useRef, useEffect } from "react";
import MainLayout from "@/components/layout/MainLayout";
import StrikePricesTable from "@/components/StrikePricesTable";
import OngoingTradesTable from "@/components/OngoingTradesTable";
import AccountSummary from "@/components/AccountSummary";
import MobileTradingDashboard from "@/components/MobileTradingDashboard";
import TradingChart from "@/components/TradingChart";

export default function Home() {
  const [leftWidth, setLeftWidth] = useState(50);
  const [tableHeight, setTableHeight] = useState(500);
  const [isResizable, setIsResizable] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [activeView, setActiveView] = useState<'tables' | 'chart'>('tables');
  const [engineRunning, setEngineRunning] = useState(false);
  const [showQTPPopup, setShowQTPPopup] = useState(false);
  const [qtpIndex, setQTPIndex] = useState('NIFTY');
  const [strategyStatus, setStrategyStatus] = useState<any>(null);
  const [timeframe, setTimeframe] = useState('3');
  
  // Strike prices per index (10 strikes each, in S1-S5 groups)
  const strikesByIndex: Record<string, { group: string; strikes: string[] }[]> = {
    NIFTY: [
      { group: 'S1', strikes: ['25600', '25650'] },
      { group: 'S2', strikes: ['25700', '25750'] },
      { group: 'S3', strikes: ['25800', '25850'] },
      { group: 'S4', strikes: ['25900', '25950'] },
      { group: 'S5', strikes: ['26000', '26050'] },
    ],
    BANKNIFTY: [
      { group: 'S1', strikes: ['53000', '53100'] },
      { group: 'S2', strikes: ['53200', '53300'] },
      { group: 'S3', strikes: ['53400', '53500'] },
      { group: 'S4', strikes: ['53600', '53700'] },
      { group: 'S5', strikes: ['53800', '53900'] },
    ],
    FINNIFTY: [
      { group: 'S1', strikes: ['24800', '24850'] },
      { group: 'S2', strikes: ['24900', '24950'] },
      { group: 'S3', strikes: ['25000', '25050'] },
      { group: 'S4', strikes: ['25100', '25150'] },
      { group: 'S5', strikes: ['25200', '25250'] },
    ],
  };
  
  const [qtpSelectedStrikes, setQtpSelectedStrikes] = useState<Record<string, boolean>>({});
  const [qtpQty, setQtpQty] = useState('1');
  const [qtpPrice, setQtpPrice] = useState('');
  const [qtpMarketPrice, setQtpMarketPrice] = useState(true);
  const [qtpMarketProtection, setQtpMarketProtection] = useState(false);
  const [qtpTriggerEnabled, setQtpTriggerEnabled] = useState(false);
  const [qtpTriggerPrice, setQtpTriggerPrice] = useState('');
  const [qtpPosition, setQtpPosition] = useState({ x: 0, y: 0 });
  const [qtpDragging, setQtpDragging] = useState(false);
  const [qtpDragOffset, setQtpDragOffset] = useState({ x: 0, y: 0 });
  const qtpRef = useRef<HTMLDivElement>(null);
  const [mounted, setMounted] = useState(false);
  
  useEffect(() => {
    setMounted(true);
  }, []);
  
  const containerRef = useRef<HTMLDivElement>(null);
  const [killSwitchActive, setKillSwitchActive] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState('NIFTY');
  
  // MTM Trailing for all indices
  const [mtmTarget, setMtmTarget] = useState('');
  const [mtmSL, setMtmSL] = useState('');

  // Live NIFTY price
  const [niftyPrice, setNiftyPrice] = useState<number | null>(null);
  const [niftyChange, setNiftyChange] = useState<number | null>(null);
  const [niftyChangePercent, setNiftyChangePercent] = useState<number | null>(null);
  const [connected, setConnected] = useState<boolean>(() => typeof window !== 'undefined' && localStorage.getItem('hdfc_connected') === 'true');
  const [lastUpdated, setLastUpdated] = useState('');

  // Handle HDFC Sky OAuth callback: ?requestToken=xxx lands on this page
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const requestToken = params.get('requestToken') || params.get('request_token');
    if (!requestToken) return;

    // Clean the URL immediately so it doesn't re-trigger on refresh
    window.history.replaceState({}, '', window.location.pathname);

    // Use relative URL so it goes through nginx → backend (works in both dev and prod)
    fetch(`/auth/exchange?token=${encodeURIComponent(requestToken)}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.status === 'success') {
          console.log('HDFC Sky connected successfully');
          setConnected(true);
          // Store connection flag in localStorage so navbar stays green across refreshes
          localStorage.setItem('hdfc_connected', 'true');
        } else {
          console.error('Token exchange failed:', data.message);
        }
      })
      .catch((err) => console.error('Token exchange error:', err));
  }, []);

  // Check broker auth connection directly
  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        const res = await fetch('/auth/status');
        const result = await res.json();
        const isConn = result.connected ?? false;
        setConnected(isConn);
        if (isConn) {
          localStorage.setItem('hdfc_connected', 'true');
        } else {
          localStorage.removeItem('hdfc_connected');
        }
      } catch (error) {
        console.error('Error checking auth status:', error);
        setConnected(false);
        localStorage.removeItem('hdfc_connected');
      }
    };
    checkAuthStatus();
  }, []);

  // Fetch live NIFTY price
  useEffect(() => {
    const fetchNifty = async () => {
      try {
        const res = await fetch('/api/market/nifty-price');
        const result = await res.json();
        if (result.status === 'success' && result.data?.price) {
          setNiftyPrice(result.data.price);
          setNiftyChange(result.data.change ?? null);
          setNiftyChangePercent(result.data.changePercent ?? null);
          setLastUpdated(new Date().toLocaleTimeString('en-IN', { hour12: false }));
        }
      } catch (error) {
        console.error('Error fetching NIFTY price:', error);
      }
    };
    fetchNifty();
    const interval = setInterval(fetchNifty, 5000);
    return () => clearInterval(interval);
  }, []);

  // Fetch Strategy Status
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch(`/api/v1/strategy/status?index=${selectedIndex}`);
        const result = await res.json();
        if (result.status === 'success') {
          setStrategyStatus(result.data);
          setEngineRunning(result.data.engineRunning);
          if (result.data.config?.timeframe_minutes) {
            setTimeframe(result.data.config.timeframe_minutes.toString());
          }
        }
      } catch (error) {
        console.error('Error fetching strategy status:', error);
      }
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, [selectedIndex]);

  // QTP Draggable handlers
  const handleQtpMouseDown = (e: React.MouseEvent) => {
    if (qtpRef.current) {
      const rect = qtpRef.current.getBoundingClientRect();
      setQtpDragOffset({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      });
      setQtpDragging(true);
    }
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (qtpDragging) {
        setQtpPosition({
          x: e.clientX - qtpDragOffset.x,
          y: e.clientY - qtpDragOffset.y
        });
      }
    };

    const handleMouseUp = () => {
      setQtpDragging(false);
    };

    if (qtpDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [qtpDragging, qtpDragOffset]);

  // Reset QTP position when popup opens
  const handleMouseDown = (e: React.MouseEvent) => {
    if (!isResizable) return;
    setIsDragging(true);
    e.preventDefault();
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging || !isResizable || !containerRef.current) return;
    
    const rect = containerRef.current.getBoundingClientRect();
    const newLeftWidth = ((e.clientX - rect.left) / rect.width) * 100;
    
    if (newLeftWidth >= 20 && newLeftWidth <= 80) {
      setLeftWidth(Math.round(newLeftWidth));
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleEngineToggle = async () => {
    const action = engineRunning ? 'stop' : 'start';
    try {
      const res = await fetch(`/api/v1/strategy/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ index: selectedIndex })
      });
      const result = await res.json();
      if (result.status === 'success') {
        setEngineRunning(!engineRunning);
      } else {
        alert(`Failed to ${action} engine: ${result.message}`);
      }
    } catch (error) {
      alert(`Error ${action}ing engine: ${error}`);
    }
  };

  const handleTimeframeChange = async (newTf: string) => {
    if (strategyStatus?.activeTrades > 0) {
      alert("❌ Cannot change timeframe while trades are active. Please square off first.");
      return;
    }

    const confirmRestart = confirm(`Changing timeframe to ${newTf}m will restart the engine for ${selectedIndex}. Continue?`);
    if (!confirmRestart) return;

    try {
      // Start with new config (backend handles stop if already running)
      const res = await fetch('/api/v1/strategy/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          index: selectedIndex,
          config: { timeframe_minutes: parseInt(newTf) }
        })
      });
      const result = await res.json();
      if (result.status === 'success') {
        setTimeframe(newTf);
        alert(`✅ Engine restarting with ${newTf}m timeframe...`);
      } else {
        alert(`Failed to change timeframe: ${result.message}`);
      }
    } catch (error) {
      alert(`Error changing timeframe: ${error}`);
    }
  };

  const handleSquareOffAll = () => {
    console.log('Square off all positions');
  };

  const handleQTPAction = (action: 'LE' | 'LX' | 'SE' | 'SX') => {
    const actionNames: {[key: string]: string} = {
      'LE': 'Long Entry',
      'LX': 'Long Exit',
      'SE': 'Short Entry',
      'SX': 'Short Exit'
    };
    
    const selectedStrikes = Object.entries(qtpSelectedStrikes)
      .filter(([_, selected]) => selected)
      .map(([strike, _]) => strike);
    
    const message = `${actionNames[action]} initiated for ${qtpIndex}\nStrike(s): ${selectedStrikes.join(', ') || 'None'}`;
    console.log(message);
    alert(`✅ ${message}`);
  };

  if (!mounted) {
    return null; // Prevent hydration mismatch
  }

  return (
    <MainLayout>
      <div 
        className="bg-[#0b1220] min-h-screen text-white p-1 select-none"
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        
        {/* Header Controls */}
        <div className="mb-2 flex flex-wrap gap-3 items-center justify-between">
          <div className="flex items-center gap-4">
            {/* Status Bar - moved from bottom */}
            <div className="flex items-center gap-4 text-xs text-gray-400">
              <span>📅 {mounted ? new Date().toLocaleDateString('en-GB') : '--'}</span>
              <span>🕐 Last Updated: {lastUpdated || '--:--:--'}</span>
              <div className="flex items-center gap-1">
                <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className={connected ? 'text-green-400' : 'text-red-400'}>
                  {connected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>
            <div className="hidden lg:flex items-center gap-4 text-xs">
              <span className="text-white">NIFTY:{' '}
                {niftyPrice ? (
                  <span className={niftyChangePercent !== null && niftyChangePercent >= 0 ? 'text-green-400' : 'text-red-400'}>
                    {niftyPrice.toLocaleString('en-IN')} ({niftyChangePercent !== null && niftyChangePercent >= 0 ? '+' : ''}{niftyChangePercent ?? 0}%)
                  </span>
                ) : (
                  <span className="text-gray-500">--</span>
                )}
              </span>

              {/* Status Badge */}
              <div className="flex items-center gap-2">
                {strategyStatus?.engineRunning ? (
                  strategyStatus.isWarmingUp ? (
                    <span className="flex items-center gap-1 bg-orange-600/20 text-orange-400 px-2 py-0.5 rounded border border-orange-600/30 font-bold animate-pulse">
                      ⏳ WARMING UP
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 bg-green-600/20 text-green-400 px-2 py-0.5 rounded border border-green-600/30 font-bold">
                      ● LIVE
                    </span>
                  )
                ) : (
                  <span className="flex items-center gap-1 bg-red-600/20 text-red-400 px-2 py-0.5 rounded border border-red-600/30 font-bold">
                    ● HALTED
                  </span>
                )}
              </div>

              {/* Timeframe Selector */}
              <div className="flex items-center gap-1 bg-blue-600/20 text-blue-400 px-2 py-0.5 rounded border border-blue-600/30 font-bold">
                <span className="text-[10px] opacity-70">TF:</span>
                <select 
                  value={timeframe}
                  onChange={(e) => handleTimeframeChange(e.target.value)}
                  className="bg-transparent border-none focus:outline-none text-xs cursor-pointer"
                >
                  <option value="1" className="bg-[#1e293b]">1m</option>
                  <option value="3" className="bg-[#1e293b]">3m</option>
                  <option value="5" className="bg-[#1e293b]">5m</option>
                  <option value="15" className="bg-[#1e293b]">15m</option>
                </select>
              </div>

              <span className="text-white">BANK NIFTY: <span className="text-gray-500">--</span></span>
              <span className="text-white">VIX: <span className="text-gray-500">--</span></span>
            </div>
            
            {/* View Switcher */}
            <div className="hidden lg:flex gap-1 bg-gray-800 rounded-lg p-1">
              <button
                onClick={() => setActiveView('tables')}
                className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                  activeView === 'tables'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:text-white hover:bg-gray-700'
                }`}
              >
                📋 Tables
              </button>
              <button
                onClick={() => setActiveView('chart')}
                className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                  activeView === 'chart'
                    ? 'bg-green-600 text-white'
                    : 'text-gray-300 hover:text-white hover:bg-gray-700'
                }`}
              >
                📈 Charts
              </button>
            </div>
          </div>
        </div>

        {/* Auto Action Buttons - Desktop (below header) */}
        <div className="hidden lg:flex flex-wrap gap-2 mb-2 items-center">
          {/* Index Selector */}
          <div className="flex gap-1 bg-gray-800 rounded-lg p-1">
            {['NIFTY', 'SENSEX', 'BANKNIFTY'].map((index) => (
              <button
                key={index}
                onClick={() => setSelectedIndex(index)}
                className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                  selectedIndex === index
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:text-white hover:bg-gray-700'
                }`}
              >
                {index}
              </button>
            ))}
          </div>


          {/* Square Off All */}
          <button 
            onClick={handleSquareOffAll}
            className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded text-sm transition-colors flex items-center gap-2"
          >
            ⚡ Square Off All
          </button>

          {/* T.MTM Trailing for all indices */}
          <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-700 rounded text-sm">
            <span className="text-gray-300 font-medium">T.MTM:</span>
            <div className="flex items-center gap-1">
              <span className="text-green-400 text-xs">Trgt</span>
              <input
                type="text"
                value={mtmTarget}
                onChange={(e) => setMtmTarget(e.target.value)}
                placeholder="0"
                className="w-14 px-2 py-1 bg-gray-800 border border-gray-600 rounded text-white text-xs focus:outline-none focus:border-green-400"
              />
            </div>
            <div className="flex items-center gap-1">
              <span className="text-red-400 text-xs">SL</span>
              <input
                type="text"
                value={mtmSL}
                onChange={(e) => setMtmSL(e.target.value)}
                placeholder="0"
                className="w-14 px-2 py-1 bg-gray-800 border border-gray-600 rounded text-white text-xs focus:outline-none focus:border-red-400"
              />
            </div>
          </div>

          {/* QTP Button */}
          <button 
            onClick={() => {
              setQtpPosition({ x: window.innerWidth / 2 - 350, y: window.innerHeight / 2 - 250 });
              setShowQTPPopup(true);
            }}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded text-sm transition-colors flex items-center gap-2"
          >
            🎯 QTP
          </button>

          <button className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded text-sm transition-colors flex items-center gap-2">
            🔄 Refresh Data
          </button>
        </div>

        {/* Mobile Dashboard Component */}
        <MobileTradingDashboard />

        {/* Desktop Layout */}
        <div className="hidden lg:block">
          {activeView === 'tables' ? (
            <>
              {/* Trading Tables Section */}
              <div>
                {/* Strike Prices Table and Account Summary - Side by Side */}
                <div className="flex gap-2 mb-2">
                  {/* Strike Prices Table - Left (60%) */}
                  <div ref={containerRef} className="w-[60%]">
                    <StrikePricesTable />
                  </div>

                  {/* Account Summary - Right (40%) */}
                  <div className="w-[40%]">
                    <AccountSummary />
                  </div>
                </div>

                {/* Ongoing Trades Table */}
                <OngoingTradesTable 
                  trades={strategyStatus?.trades || []} 
                  engineRunning={strategyStatus?.engineRunning || false}
                  index={selectedIndex}
                />
              </div>
            </>
          ) : (
            /* Chart View */
            <div className="space-y-4">
              <div style={{ height: `${tableHeight + 100}px` }}>
                <TradingChart className="h-full" />
              </div>
              
              {/* Chart-specific controls */}
              <div className="bg-[#111827] border border-gray-700 rounded-lg p-4">
                  <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                    📊 Market Analysis
                  </h3>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Trend:</span>
                      <span className="text-green-400 font-semibold">BULLISH</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Support:</span>
                      <span className="text-blue-400 font-semibold">25,750</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Resistance:</span>
                      <span className="text-red-400 font-semibold">26,100</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Volatility:</span>
                      <span className="text-orange-400 font-semibold">MEDIUM</span>
                    </div>
                  </div>
                </div>
            </div>
          )}
        </div>

        {/* QTP Popup - Only closes on X button, Draggable */}
        {showQTPPopup && (
          <div 
            ref={qtpRef}
            className="fixed bg-gray-800 border border-gray-600 rounded-lg w-full max-w-3xl max-h-[90vh] overflow-y-auto z-50 shadow-2xl"
            style={{ 
              left: qtpPosition.x, 
              top: qtpPosition.y,
              cursor: qtpDragging ? 'grabbing' : 'default'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Draggable Header */}
            <div 
                className="flex justify-between items-center p-4 border-b border-gray-600 cursor-grab active:cursor-grabbing bg-gray-700 rounded-t-lg"
                onMouseDown={handleQtpMouseDown}
              >
                <h3 className="text-white font-bold text-lg">🎯 Quick Trade Panel (QTP)</h3>
                <button 
                  onClick={() => setShowQTPPopup(false)}
                  className="text-gray-400 hover:text-white text-2xl font-bold px-2 py-1 hover:bg-gray-600 rounded"
                >
                  ✕
                </button>
              </div>
              
              <div className="p-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Left Column: Strategy Configuration */}
                <div className="space-y-4">
                  {/* Action Buttons - LE/LX/SE/SX */}
                  <div>
                    <label className="block text-sm text-gray-300 mb-2 font-bold">Select Entry/Exit Action</label>
                    <div className="grid grid-cols-2 gap-2">
                      <button
                        onClick={() => handleQTPAction('LE')}
                        className="bg-green-600 hover:bg-green-700 text-white py-3 rounded font-bold text-sm transition-colors"
                      >
                        🟢 LE (Long Entry)
                      </button>
                      <button
                        onClick={() => handleQTPAction('LX')}
                        className="bg-green-700 hover:bg-green-800 text-white py-3 rounded font-bold text-sm transition-colors"
                      >
                        🟢 LX (Long Exit)
                      </button>
                      <button
                        onClick={() => handleQTPAction('SE')}
                        className="bg-red-600 hover:bg-red-700 text-white py-3 rounded font-bold text-sm transition-colors"
                      >
                        🔴 SE (Short Entry)
                      </button>
                      <button
                        onClick={() => handleQTPAction('SX')}
                        className="bg-red-700 hover:bg-red-800 text-white py-3 rounded font-bold text-sm transition-colors"
                      >
                        🔴 SX (Short Exit)
                      </button>
                    </div>
                  </div>

                  {/* Index Selection */}
                  <div>
                    <label className="block text-sm text-gray-300 mb-2 font-bold">Select Index</label>
                    <select 
                      value={qtpIndex} 
                      onChange={(e) => {
                        setQTPIndex(e.target.value);
                        setQtpSelectedStrikes({});
                      }}
                      className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-400"
                    >
                      <option value="NIFTY">NIFTY</option>
                      <option value="BANKNIFTY">BANKNIFTY</option>
                      <option value="FINNIFTY">FINNIFTY</option>
                    </select>
                  </div>

                  {/* Qty and Price Fields */}
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-sm text-gray-300 mb-2 font-bold">Qty</label>
                      <input
                        type="number"
                        value={qtpQty}
                        onChange={(e) => setQtpQty(e.target.value)}
                        min="1"
                        className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-400"
                        placeholder="Quantity"
                      />
                    </div>
                    <div>
                      <label className="block text-sm text-gray-300 mb-2 font-bold">Price</label>
                      <input
                        type="number"
                        value={qtpPrice}
                        onChange={(e) => setQtpPrice(e.target.value)}
                        disabled={qtpMarketPrice}
                        className={`w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-400 ${qtpMarketPrice ? 'opacity-50 cursor-not-allowed' : ''}`}
                        placeholder="Enter price"
                      />
                    </div>
                  </div>

                  {/* Market Price & Market Protection Checkboxes */}
                  <div className="flex flex-col gap-2">
                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={qtpMarketPrice}
                        onChange={(e) => setQtpMarketPrice(e.target.checked)}
                        className="w-4 h-4 accent-blue-500"
                      />
                      <span className="text-sm text-gray-300">Market Price</span>
                    </label>
                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={qtpMarketProtection}
                        onChange={(e) => setQtpMarketProtection(e.target.checked)}
                        className="w-4 h-4 accent-blue-500"
                      />
                      <span className="text-sm text-gray-300">Market Protection</span>
                    </label>
                  </div>

                  {/* Trigger Price Checkbox and Input */}
                  <div>
                    <label className="flex items-center space-x-2 cursor-pointer mb-2">
                      <input
                        type="checkbox"
                        checked={qtpTriggerEnabled}
                        onChange={(e) => setQtpTriggerEnabled(e.target.checked)}
                        className="w-4 h-4 accent-blue-500"
                      />
                      <span className="text-sm text-gray-300 font-bold">Trigger Price</span>
                    </label>
                    {qtpTriggerEnabled && (
                      <input
                        type="number"
                        value={qtpTriggerPrice}
                        onChange={(e) => setQtpTriggerPrice(e.target.value)}
                        className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-400"
                        placeholder="Enter trigger price"
                      />
                    )}
                  </div>
                </div>

                {/* Right Column: Strike Selection (10 strikes in S1-S5 groups) */}
                <div>
                  <label className="block text-sm text-gray-300 mb-2 font-bold">Select Strike Prices ({qtpIndex}) - S1 to S5</label>
                  <div className="bg-gray-700 p-3 rounded max-h-64 overflow-y-auto space-y-3">
                    {strikesByIndex[qtpIndex]?.map((group) => (
                      <div key={group.group} className="border-b border-gray-600 pb-2 last:border-b-0">
                        <div className="text-xs text-blue-400 font-bold mb-1">{group.group}</div>
                        <div className="grid grid-cols-2 gap-2">
                          {group.strikes.map((strike) => (
                            <label 
                              key={strike} 
                              className={`flex items-center space-x-2 p-2 rounded cursor-pointer transition-colors ${
                                qtpSelectedStrikes[strike] ? 'bg-blue-600' : 'bg-gray-600 hover:bg-gray-500'
                              }`}
                            >
                              <input 
                                type="checkbox" 
                                checked={qtpSelectedStrikes[strike] || false}
                                onChange={(e) => setQtpSelectedStrikes(prev => ({ ...prev, [strike]: e.target.checked }))}
                                className="w-4 h-4 accent-blue-500" 
                              />
                              <span className="text-sm text-white font-mono">{strike}</span>
                            </label>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="text-xs text-gray-400 mt-2">
                    Selected: {Object.values(qtpSelectedStrikes).filter(v => v).length} / 10 strikes
                  </div>
                </div>
              </div>
              </div>
            </div>
        )}
      </div>
    </MainLayout>
  );
}
