'use client'

import React, { useState, useEffect, useRef } from 'react';
import { Shield } from 'lucide-react';

interface Account {
  id: string;
  name: string;
  broker: string;
  capital: string;
  dayPnl: string;
  totalPnl: string;
  margin: string;
  isActive: boolean;
}

const AccountSummary = ({ className = "" }: { className?: string }) => {
  const [mounted, setMounted] = useState(false);
  const [mtmTrailing1, setMtmTrailing1] = useState('50');
  const [mtmTrailing2, setMtmTrailing2] = useState('100');
  const [showAddAccount, setShowAddAccount] = useState(false);
  const [newAccountName, setNewAccountName] = useState('');
  const [newAccountBroker, setNewAccountBroker] = useState('HDFC Sky');
  const [accounts, setAccounts] = useState<Account[]>([
    {
      id: '1',
      name: 'Fy',
      broker: 'Fyers',
      capital: '0',
      dayPnl: '0',
      totalPnl: '0',
      margin: '0',
      isActive: true
    },
    {
      id: '2',
      name: 'Primary Account',
      broker: 'HDFC Sky',
      capital: '100000',
      dayPnl: '0',
      totalPnl: '0',
      margin: '100000',
      isActive: false
    }
  ]);
  const [activeAccountId, setActiveAccountId] = useState('1');
  
  // Trigger popup state
  const [triggerPopup, setTriggerPopup] = useState<{
    show: boolean;
    index: number;
    trigger: string;
    strike: string;
    price: string;
    ceStrike: string;
    peStrike: string;
    cePrice: string;
    pePrice: string;
    position: { x: number; y: number };
  } | null>(null);
  const [triggerCallPut, setTriggerCallPut] = useState({ call: true, put: false });
  
  // Draggable popup state
  const [popupPosition, setPopupPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const popupRef = useRef<HTMLDivElement>(null);
  
  // Handle dragging
  const handleMouseDown = (e: React.MouseEvent) => {
    if (popupRef.current) {
      const rect = popupRef.current.getBoundingClientRect();
      setDragOffset({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      });
      setIsDragging(true);
    }
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (isDragging) {
        setPopupPosition({
          x: e.clientX - dragOffset.x,
          y: e.clientY - dragOffset.y
        });
      }
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, dragOffset]);

  // Set initial popup position when it opens
  useEffect(() => {
    if (triggerPopup?.show) {
      setPopupPosition(triggerPopup.position);
    }
  }, [triggerPopup?.show]);
  
  useEffect(() => {
    setMounted(true);
  }, []);

  const [tradeData, setTradeData] = useState<any[]>([]);
  const [stats, setStats] = useState({
    capital: '0',
    dayPnl: '0',
    totalPnl: '0',
    margin: '0',
    hist: [] as string[]
  });
  const [engineRunning, setEngineRunning] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const fetchLiveTrades = async () => {
    try {
      // 1. Fetch trades
      const tradesRes = await fetch(`/api/v1/strategy/trades?index=NIFTY`);
      const tradesData = await tradesRes.json();
      if (tradesData.status === 'success') {
        const mapped = (tradesData.data.trades || []).map((t: any) => {
          const pnl = t.active ? (t.floatingPnl || 0) : (t.realizedPnl || 0);
          return {
            strike: `${t.strikeLabel || t.strikePrice || '-'} ${t.direction || ''}`.trim(),
            entry: t.entryTime ? t.entryTime.split('T')[1]?.substring(0, 5) : '-',
            exit: t.exitTime ? t.exitTime.split('T')[1]?.substring(0, 5) : (t.active ? 'OPEN' : '-'),
            lots: String(t.lots || 1),
            price: t.entryPrice != null ? Number(t.entryPrice).toFixed(2) : '0.00',
            pts: pnl > 0 ? `+${pnl.toFixed(1)}` : pnl.toFixed(1),
            pnl: pnl > 0 ? `+${Math.round(pnl)}` : String(Math.round(pnl)),
            trigger: t.exitReason || (t.active ? 'LIVE' : '-'),
            s: t.direction === 'SHORT' ? '1' : '0',
            b: t.direction === 'LONG' ? '1' : '0',
            slTrgt: `${t.slSafe ? 'SL✓' : '-'}/${t.trailingSLLevel > 0 ? Number(t.trailingSLLevel).toFixed(0) : '-'}`,
            isPositive: pnl >= 0,
            ceStrike: t.optionType === 'CE' ? String(t.strikePrice) : '-',
            peStrike: t.optionType === 'PE' ? String(t.strikePrice) : '-',
            cePrice: t.optionType === 'CE' ? Number(t.entryPrice).toFixed(2) : '-',
            pePrice: t.optionType === 'PE' ? Number(t.entryPrice).toFixed(2) : '-',
          };
        });
        setTradeData(mapped);
      }

      // 2. Fetch overall status for capital/summary
      const statusRes = await fetch(`/api/v1/strategy/status?index=NIFTY`);
      const statusData = await statusRes.json();
      if (statusData.status === 'success' && statusData.data) {
        const engine = statusData.data;
        const acc = engine.account || {};
        const daily = engine.daily || {};
        setStats({
          capital: String(acc.initialCapital || '0'),
          dayPnl: String(((daily.realizedPnl || 0) + (daily.floatingPnl || 0)).toFixed(0)),
          totalPnl: String((acc.totalPnl || 0).toFixed(0)),
          margin: String(acc.currentCapital || acc.initialCapital || '0'),
          hist: acc.historicalPnl || []
        });
        setEngineRunning(engine.engineRunning || false);
      }
    } catch (err) {
      console.error('Error fetching trade data:', err);
    }
  };

  useEffect(() => {
    fetchLiveTrades();
    const interval = setInterval(fetchLiveTrades, 5000);
    return () => clearInterval(interval);
  }, []);

  if (!mounted) {
    return (
      <div className={`bg-gray-800 text-white p-4 rounded-lg shadow-lg ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-700 rounded mb-4"></div>
          <div className="space-y-2">
            <div className="h-4 bg-gray-700 rounded"></div>
            <div className="h-4 bg-gray-700 rounded w-3/4"></div>
          </div>
        </div>
      </div>
    );
  }

  const handleBookTrade = (index: number, event: React.MouseEvent, trade: typeof tradeData[0]) => {
    event.stopPropagation();
    const rect = (event.target as HTMLElement).getBoundingClientRect();
    
    // Toggle popup - if same trigger clicked, close it
    if (triggerPopup?.index === index) {
      setTriggerPopup(null);
      return;
    }
    
    setTriggerPopup({
      show: true,
      index,
      trigger: trade.trigger,
      strike: trade.strike,
      price: trade.price,
      ceStrike: trade.ceStrike,
      peStrike: trade.peStrike,
      cePrice: trade.cePrice,
      pePrice: trade.pePrice,
      position: { x: rect.left, y: rect.bottom + 5 }
    });
  };
  
  const executeTriggerAction = (action: 'LE' | 'LX' | 'SX' | 'SE') => {
    const actionNames: Record<string, string> = {
      'LE': 'Long Entry',
      'LX': 'Long Exit',
      'SX': 'Short Exit',
      'SE': 'Short Entry'
    };
    const types = [];
    if (triggerCallPut.call) types.push('CALL');
    if (triggerCallPut.put) types.push('PUT');
    
    alert(`✅ ${actionNames[action]} executed!\nStrike: ${triggerPopup?.strike}\nType(s): ${types.join(', ')}\nPrice: ${triggerPopup?.price}`);
  };

  const toggleStrategy = async () => {
    setIsProcessing(true);
    try {
      const endpoint = engineRunning ? '/api/v1/strategy/stop' : '/api/v1/strategy/start';
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ index: 'NIFTY' })
      });
      const data = await res.json();
      if (data.status === 'success') {
        setEngineRunning(!engineRunning);
        fetchLiveTrades(); // Refresh immediately
      } else {
        alert(`Error: ${data.data?.message || 'Unknown error'}`);
      }
    } catch (err) {
      console.error('Error toggling strategy:', err);
    } finally {
      setIsProcessing(false);
    }
  };

  const addAccount = () => {
    if (!newAccountName.trim()) return;
    
    const newAccount: Account = {
      id: Date.now().toString(),
      name: newAccountName,
      broker: newAccountBroker,
      capital: '100000',
      dayPnl: '0',
      totalPnl: '0',
      margin: '100000',
      isActive: true
    };
    
    setAccounts([...accounts, newAccount]);
    setNewAccountName('');
    setShowAddAccount(false);
  };

  const removeAccount = (id: string) => {
    if (accounts.length <= 1) {
      alert('Cannot remove the last account');
      return;
    }
    setAccounts(accounts.filter(acc => acc.id !== id));
    if (activeAccountId === id) {
      setActiveAccountId(accounts.find(acc => acc.id !== id)?.id || '1');
    }
  };

  const activeAccount = accounts.find(acc => acc.id === activeAccountId) || accounts[0];

  return (
    <div className={`border border-gray-700 bg-[#111827] rounded-md overflow-hidden ${className}`}>
      {/* Account Selector Section */}
      <div className="bg-[#1f2937] border-b border-gray-700 px-3 py-2">
        <div className="flex items-center justify-between gap-2 flex-wrap mb-2">
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-400">Account:</span>
            <select
              value={activeAccountId}
              onChange={(e) => setActiveAccountId(e.target.value)}
              className="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-xs text-white focus:outline-none focus:border-blue-400"
            >
              {accounts.map(acc => (
                <option key={acc.id} value={acc.id}>
                  {acc.name} ({acc.broker})
                </option>
              ))}
            </select>
          </div>
          
          <div className="flex gap-2">
            <button
              disabled={true}
              className="px-3 py-1.5 rounded-md text-xs font-bold bg-gray-700/50 text-gray-500 border border-gray-600/30 cursor-not-allowed flex items-center gap-2"
              title="Real broker order execution is not yet implemented in the current shadow-validation phase."
            >
              <Shield size={12} />
              Live Execution Pending
            </button>
            <button 
              onClick={() => setShowAddAccount(true)}
              className="bg-green-600 hover:bg-green-700 text-white px-3 py-1.5 rounded-md text-xs font-bold transition-all flex items-center gap-1 shadow-md"
            >
              <span className="text-lg">+</span> Add Account
            </button>
            <button 
              onClick={() => removeAccount(activeAccountId)}
              className="bg-red-600 hover:bg-red-700 text-white px-3 py-1.5 rounded-md text-xs font-bold transition-all shadow-md"
            >
              Remove
            </button>
          </div>
          </div>
        </div>

        {/* Add Account Form */}
        {showAddAccount && (
          <div className="mt-3 p-3 bg-gray-800 rounded border border-gray-600">
            <div className="text-xs text-gray-300 font-bold mb-2">Add New Account</div>
            <div className="flex flex-wrap gap-2 items-end">
              <div>
                <label className="block text-[10px] text-gray-400 mb-1">Account Name</label>
                <input
                  type="text"
                  value={newAccountName}
                  onChange={(e) => setNewAccountName(e.target.value)}
                  placeholder="e.g., Account 2"
                  className="w-32 bg-gray-700 border border-gray-600 rounded px-2 py-1 text-xs text-white focus:outline-none focus:border-blue-400"
                />
              </div>
              <div>
                <label className="block text-[10px] text-gray-400 mb-1">Broker</label>
                <select
                  value={newAccountBroker}
                  onChange={(e) => setNewAccountBroker(e.target.value)}
                  className="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-xs text-white focus:outline-none focus:border-blue-400"
                >
                  <option value="HDFC Sky">HDFC Sky</option>
                  <option value="Fyers">Fyers</option>
                  <option value="Zerodha">Zerodha</option>
                  <option value="Angel One">Angel One</option>
                  <option value="Upstox">Upstox</option>
                  <option value="Groww">Groww</option>
                  <option value="ICICI Direct">ICICI Direct</option>
                  <option value="5Paisa">5Paisa</option>
                  <option value="Kotak">Kotak</option>
                </select>
              </div>
              <button
                onClick={addAccount}
                className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition-colors"
              >
                Add
              </button>
              <button
                onClick={() => setShowAddAccount(false)}
                className="px-3 py-1 bg-gray-600 hover:bg-gray-700 text-white text-xs rounded transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Account List (when multiple) */}
        {accounts.length > 1 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {accounts.map(acc => (
              <div
                key={acc.id}
                onClick={() => setActiveAccountId(acc.id)}
                className={`px-2 py-1 rounded text-[10px] cursor-pointer transition-colors ${
                  acc.id === activeAccountId
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {acc.name}
                <span className={`ml-1 ${parseFloat(acc.dayPnl) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  ₹{parseFloat(acc.dayPnl).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        )}

      <div className="overflow-x-auto">
        <table className="w-full text-[10px] border-collapse">
          <thead className="bg-[#1f2937]">
            <tr>
              {["STRIKE", "ENTRY", "EXIT", "LOTS", "PRICE", "PTS", "P&L", "SL/TRGT", "TRIG", "S", "B"].map(h => (
                <th key={h} className="px-1 py-1 text-left font-bold text-gray-300 border-r border-gray-700 whitespace-nowrap">
                  {h}
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {tradeData.map((trade, i) => (
              <tr key={i} className={`${i === 0 ? 'bg-[#020617]' : 'border-t border-gray-800'} hover:bg-gray-800/30 transition-colors`}>
                <td className="px-1 py-1 font-bold text-yellow-400">{trade.strike}</td>
                <td className="px-1 py-1 text-gray-300">{trade.entry}</td>
                <td className="px-1 py-1 text-gray-300">{trade.exit}</td>
                <td className="px-1 py-1 text-gray-300">{trade.lots}</td>
                <td className="px-1 py-1 font-semibold text-white">{trade.price}</td>
                <td className={`px-1 py-1 font-semibold ${trade.pts.startsWith('+') ? 'text-green-400' : 'text-red-400'}`}>
                  {trade.pts}
                </td>
                <td className={`px-1 py-1 font-bold ${trade.isPositive ? 'text-green-400' : 'text-red-400'}`}>
                  {trade.pnl}
                </td>
                <td className="px-1 py-1 text-gray-300 font-mono text-[9px]">
                  <input
                    type="text"
                    value={trade.slTrgt}
                    className="w-14 bg-gray-600 border border-gray-500 rounded px-1 py-0.5 text-gray-100 text-[9px]"
                    readOnly
                  />
                </td>
                <td className="px-1 py-1 relative">
                  <div className={`font-bold text-black text-center rounded-sm cursor-pointer ${
                    trade.trigger === 'OLD' ? 'bg-yellow-500' : 'bg-blue-500 text-white'
                  }`}>
                    <button
                      onClick={(e) => handleBookTrade(i, e, trade)}
                      className="w-full px-1 py-0.5 hover:opacity-80"
                      title="Click to open trade panel"
                    >
                      {trade.trigger}
                    </button>
                  </div>
                </td>
                <td className="px-1 py-1 text-center text-gray-300">{trade.s}</td>
                <td className="px-1 py-1 text-center text-gray-300">{trade.b}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* MTM Trailing Controls */}
        <div className="border-t border-gray-700 bg-[#020617] px-3 py-2">
          <div className="flex items-center space-x-4 text-[11px]">
            <span className="text-gray-400">MTM Trailing:</span>
            <div className="flex items-center space-x-2">
              <span className="text-gray-300">Target:</span>
              <input
                type="text"
                value={mtmTrailing1}
                onChange={(e) => setMtmTrailing1(e.target.value)}
                className="w-12 bg-gray-700 border border-gray-600 rounded px-1 py-0.5 text-gray-100"
              />
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-gray-300">SL:</span>
              <input
                type="text"
                value={mtmTrailing2}
                onChange={(e) => setMtmTrailing2(e.target.value)}
                className="w-12 bg-gray-700 border border-gray-600 rounded px-1 py-0.5 text-gray-100"
              />
            </div>
          </div>
        </div>

        {/* Account Summary Footer */}
        <div className="border-t border-gray-700 bg-[#020617] text-[11px]">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 px-3 py-2">
            <div className="flex flex-col">
              <span className="text-gray-400 text-[10px]">CAPITAL</span>
              <span className="text-green-400 font-bold">₹{parseFloat(stats.capital).toLocaleString()}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-gray-400 text-[10px]">DAY P&L</span>
              <span className={`font-bold ${parseFloat(stats.dayPnl) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                ₹{parseFloat(stats.dayPnl).toLocaleString()}
              </span>
            </div>
            <div className="flex flex-col">
              <span className="text-gray-400 text-[10px]">TOTAL P&L</span>
              <span className={`font-bold ${parseFloat(stats.totalPnl) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                ₹{parseFloat(stats.totalPnl).toLocaleString()}
              </span>
            </div>
            <div className="flex flex-col">
              <span className="text-gray-400 text-[10px]">AVAILABLE MARGIN</span>
              <span className="text-blue-400 font-bold">₹{parseFloat(stats.margin).toLocaleString()}</span>
            </div>
          </div>

          <div className="px-3 py-2 text-gray-500 border-t border-gray-800">
            <span className="text-[10px]">HIST:</span>
            <span className="ml-1">{stats.hist.length > 0 ? stats.hist.map(v => `₹${v}`).join(' | ') : 'No history'}</span>
          </div>
        </div>
      </div>

      {/* Trigger Popup (no background overlay) */}
      {triggerPopup?.show && (
        <div 
          ref={popupRef}
          className="fixed z-50 bg-[#c0c8d4] border-2 border-blue-600 rounded shadow-xl"
          style={{ 
            left: popupPosition.x,
            top: popupPosition.y,
            cursor: isDragging ? 'grabbing' : 'default'
          }}
        >
          {/* Header with Trade button - Draggable */}
          <div 
            className="flex items-center justify-between px-3 py-2 border-b border-gray-400 cursor-grab active:cursor-grabbing"
            onMouseDown={handleMouseDown}
          >
            <button
              onClick={() => alert('Trade executed!')}
              className="px-4 py-1 bg-green-600 hover:bg-green-700 text-white text-sm font-bold rounded transition-colors"
            >
              {triggerPopup?.strike}
            </button>
            <button
              onClick={() => setTriggerPopup(null)}
              className="text-gray-600 hover:text-black text-lg font-bold leading-none ml-2"
            >
              ×
            </button>
          </div>

          {/* Action Buttons */}
          <div className="p-3 space-y-2">
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => executeTriggerAction('LE')}
                className="px-4 py-2 bg-white hover:bg-blue-50 text-blue-700 font-bold text-sm border border-gray-300 rounded transition-colors"
              >
                LE
              </button>
              <button
                onClick={() => executeTriggerAction('LX')}
                className="px-4 py-2 bg-white hover:bg-blue-50 text-blue-700 font-bold text-sm border border-gray-300 rounded transition-colors"
              >
                LX
              </button>
              <button
                onClick={() => executeTriggerAction('SX')}
                className="px-4 py-2 bg-white hover:bg-red-50 text-red-700 font-bold text-sm border border-gray-300 rounded transition-colors"
              >
                SX
              </button>
              <button
                onClick={() => executeTriggerAction('SE')}
                className="px-4 py-2 bg-white hover:bg-red-50 text-red-700 font-bold text-sm border border-gray-300 rounded transition-colors"
              >
                SE
              </button>
            </div>

            {/* Price Info */}
            <div className="bg-white rounded p-2 mt-2 space-y-1 text-xs border border-gray-300">
              <div className="flex justify-between">
                <span className="text-gray-600">Price</span>
                <span className="text-black font-semibold">25213.45</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Strike(CE)</span>
                <span className="text-black font-semibold">{triggerPopup?.ceStrike}</span>
              </div>
              <div className="flex justify-between pl-4">
                <span className="text-gray-500 text-[10px]">CE Price</span>
                <span className="text-blue-600 font-semibold">₹{triggerPopup?.cePrice}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Strike(PE)</span>
                <span className="text-black font-semibold">{triggerPopup?.peStrike}</span>
              </div>
              <div className="flex justify-between pl-4">
                <span className="text-gray-500 text-[10px]">PE Price</span>
                <span className="text-red-600 font-semibold">₹{triggerPopup?.pePrice}</span>
              </div>
            </div>

            {/* Exit All Button */}
            <button
              onClick={() => alert('Trade list opened')}
              className="w-full px-3 py-2 bg-[#4a6fa5] hover:bg-[#3d5d8a] text-white text-sm font-bold rounded transition-colors mt-2"
            >
              Exit All
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AccountSummary;
