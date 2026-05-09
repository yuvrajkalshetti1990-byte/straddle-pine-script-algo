'use client';

import React, { useEffect, useRef, useState } from 'react';

interface StrategySettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultTab?: 'inputs' | 'style' | 'visibility' | 'trading';
}

interface TradeExecutionPopupProps {
  isOpen: boolean;
  onClose: () => void;
  tradeType: 'BUY' | 'SELL' | null;
  selectedStrike?: string;
}

const TradeExecutionPopup = ({ isOpen, onClose, tradeType, selectedStrike }: TradeExecutionPopupProps) => {
  const [orderType, setOrderType] = useState<'MARKET' | 'LIMIT' | 'SL' | 'SL-M'>('MARKET');
  const [quantity, setQuantity] = useState('1');
  const [price, setPrice] = useState('');
  const [stopLoss, setStopLoss] = useState('');
  const [target, setTarget] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const executeTradeOrder = async () => {
    setIsLoading(true);
    
    // Simulate trade execution
    setTimeout(() => {
      const orderDetails = {
        type: tradeType,
        strike: selectedStrike || '25850',
        orderType,
        quantity: parseInt(quantity),
        price: orderType === 'MARKET' ? 'Market Price' : price,
        stopLoss,
        target,
        timestamp: new Date().toLocaleTimeString()
      };
      
      // Show success message
      alert(`✅ ${tradeType} Order Placed Successfully!\n\nStrike: ${selectedStrike}\nQuantity: ${quantity} lots\nOrder Type: ${orderType}\nTime: ${orderDetails.timestamp}`);
      
      setIsLoading(false);
      onClose();
    }, 2000);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-[60] p-4">
      <div className="bg-[#1e293b] rounded-lg border border-gray-700 w-full max-w-md shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            {tradeType === 'BUY' ? '🟢 BUY' : '🔴 SELL'} Order
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors text-xl"
          >
            ✕
          </button>
        </div>

        {/* Order Details */}
        <div className="p-4 space-y-4">
          <div className="bg-gray-800 rounded-lg p-3">
            <div className="text-sm text-gray-400">Strike Price</div>
            <div className="text-lg font-bold text-white">{selectedStrike || '25850'} CE</div>
            <div className="text-sm text-gray-400">LTP: ₹210.60</div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">
                Order Type
              </label>
              <select
                value={orderType}
                onChange={(e) => setOrderType(e.target.value as any)}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm focus:outline-none focus:border-blue-500"
              >
                <option value="MARKET">MARKET</option>
                <option value="LIMIT">LIMIT</option>
                <option value="SL">SL</option>
                <option value="SL-M">SL-M</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">
                Quantity (Lots)
              </label>
              <input
                type="number"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                min="1"
                max="10"
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          {orderType === 'LIMIT' && (
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">
                Limit Price
              </label>
              <input
                type="number"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder="Enter price"
                step="0.05"
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">
                Stop Loss
              </label>
              <input
                type="number"
                value={stopLoss}
                onChange={(e) => setStopLoss(e.target.value)}
                placeholder="Optional"
                step="0.05"
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm focus:outline-none focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">
                Target
              </label>
              <input
                type="number"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                placeholder="Optional"
                step="0.05"
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          {/* Order Summary */}
          <div className="bg-gray-900 rounded-lg p-3 text-sm">
            <div className="flex justify-between mb-1">
              <span className="text-gray-400">Order Value:</span>
              <span className="text-white">₹{(210.60 * parseInt(quantity) * 50).toLocaleString()}</span>
            </div>
            <div className="flex justify-between mb-1">
              <span className="text-gray-400">Margin Required:</span>
              <span className="text-white">₹{(75000 * parseInt(quantity)).toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Brokerage:</span>
              <span className="text-white">₹40</span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-2">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors text-sm"
            >
              Cancel
            </button>
            <button
              onClick={executeTradeOrder}
              disabled={isLoading}
              className={`flex-1 px-4 py-2 rounded-md text-white text-sm transition-colors ${
                tradeType === 'BUY' 
                  ? 'bg-green-600 hover:bg-green-700' 
                  : 'bg-red-600 hover:bg-red-700'
              } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              {isLoading ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Placing...
                </div>
              ) : (
                `${tradeType} Order`
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default function StrategySettingsModal({
  isOpen,
  onClose,
  defaultTab = 'inputs',
}: StrategySettingsModalProps) {
  /* ================= TAB ================= */
  const [activeTab, setActiveTab] = useState<'inputs' | 'style' | 'visibility' | 'trading'>(
    defaultTab
  );

  // Trading Popup State
  const [tradePopup, setTradePopup] = useState<{
    isOpen: boolean;
    type: 'BUY' | 'SELL' | null;
    strike?: string;
  }>({ isOpen: false, type: null });

  // Reset tab when modal opens
  useEffect(() => {
    if (isOpen) {
      setActiveTab(defaultTab);
      fetchConfig();
    }
  }, [isOpen, defaultTab]);

  const fetchConfig = async () => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/v1/strategy/config?index=${indexSelection}`);
      const result = await response.json();
      if (result.status === 'success' && result.data) {
        const config = result.data;
        
        // Setup
        if (config.index) setIndexSelection(config.index);
        setExpiryDate({ 
          dd: String(config.expiry_dd).padStart(2, '0'), 
          mm: String(config.expiry_mm).padStart(2, '0'), 
          yy: String(config.expiry_yy).padStart(2, '0') 
        });
        setStartDate({ 
          dd: String(config.start_dd).padStart(2, '0'), 
          mm: String(config.start_mm).padStart(2, '0'), 
          yy: String(config.start_yy) 
        });
        setEndDate({ 
          dd: String(config.end_dd).padStart(2, '0'), 
          mm: String(config.end_mm).padStart(2, '0'), 
          yy: String(config.end_yy) 
        });

        // Strikes
        if (config.strikes) {
          setStrikes(config.strikes.map((s: any, idx: number) => ({
            id: idx + 1,
            enabled: s.enabled,
            chart: s.chart,
            index: s.show_index,
            price: String(s.price),
            atm: idx === 2
          })));
        }

        // Logic
        if (config.logic) {
          setCalcMode(config.logic.calc_mode || 'Auto');
          setFilterChop(config.logic.filter_chop ?? true);
          setChopValue(String(config.logic.chop_threshold || '61.8'));
          setBreakdownWindow(String(config.logic.breakdown_window || '0'));
          setUseMomentum(config.logic.use_momentum ?? true);
          setUseTrend(config.logic.use_trend ?? false);
          setUseVwapRev(config.logic.use_vwap_rev ?? false);
          setMinRevSize(String(config.logic.min_reversal_size || '5'));
          setRestrictVwapScope(config.logic.restrict_vwap_scope ?? false);
          if (config.logic.vwap_scope) setVwapScope(config.logic.vwap_scope);
        }

        // Short
        if (config.short) {
          setEnableShort(config.short.enabled ?? true);
          setShortLots(String(config.short.lots || '2'));
          setMaxShortTrades(String(config.short.max_trades || '0'));
          setShortStartTime(config.short.start_time || '09:15');
          setIgnoreLogicShort(config.short.ignore_logic ?? false);
          setRestrictShortScope(config.short.restrict_scope ?? true);
          if (config.short.scope) setShortScope(config.short.scope);
          setShortFixedSl(String(config.short.fixed_sl || '0'));
          setShortFixedTgt(String(config.short.fixed_target || '0'));
          setSmartSlDisable(config.short.smart_sl_disable ?? true);
          setSmartSlPoints(String(config.short.smart_sl_points || '10'));
          if (config.short.trailing_sl) {
            setShortTrailingSl(config.short.trailing_sl.enabled ?? false);
            setShortTrailingAct(String(config.short.trailing_sl.activation || '20'));
            setShortTrailingDist(String(config.short.trailing_sl.distance || '10'));
          }
          if (config.short.time_exit) {
            setShortTimeExit(config.short.time_exit.enabled ?? true);
            setShortExitTime({ 
              h: String(config.short.time_exit.hour).padStart(2, '0'), 
              m: String(config.short.time_exit.minute).padStart(2, '0') 
            });
          }
        }

        // Long
        if (config.long) {
          setEnableLong(config.long.enabled ?? true);
          setLongLots(String(config.long.lots || '6'));
          setMaxLongTrades(String(config.long.max_trades || '1'));
          setLongStartTime(config.long.start_time || '09:30');
          setIgnoreLogicLong(config.long.ignore_logic ?? true);
          setLongAdx(String(config.long.adx_threshold || '20'));
          setRestrictLongScope(config.long.restrict_scope ?? true);
          if (config.long.scope) setLongScope(config.long.scope);
          setLongFixedSl(String(config.long.fixed_sl || '0'));
          setLongFixedTgt(String(config.long.fixed_target || '0'));
          if (config.long.trailing_sl) {
            setLongTrailingSl(config.long.trailing_sl.enabled ?? false);
            setLongTrailingAct(String(config.long.trailing_sl.activation || '15'));
            setLongTrailingDist(String(config.long.trailing_sl.distance || '10'));
          }
          if (config.long.time_exit) {
            setLongTimeExit(config.long.time_exit.enabled ?? true);
            setLongExitTime({ 
              h: String(config.long.time_exit.hour).padStart(2, '0'), 
              m: String(config.long.time_exit.minute).padStart(2, '0') 
            });
          }
        }
      }
    } catch (err) {
      console.error('Error fetching config:', err);
    }
  };

  /* ================= FORM STATE ================= */
  // Setup: Index & Time
  const [indexSelection, setIndexSelection] = useState('NIFTY');
  const [expiryDate, setExpiryDate] = useState({ dd: '13', mm: '01', yy: '26' });
  const [startDate, setStartDate] = useState({ dd: '30', mm: '12', yy: '2025' });
  const [endDate, setEndDate] = useState({ dd: '31', mm: '12', yy: '2099' });

  // Strike Selection
  const [strikes, setStrikes] = useState([
    { id: 1, enabled: false, chart: false, index: true, price: '25700' },
    { id: 2, enabled: true, chart: false, index: true, price: '25800' },
    { id: 3, enabled: true, chart: false, index: true, price: '25850', atm: true },
    { id: 4, enabled: true, chart: true, index: true, price: '25900' },
    { id: 5, enabled: false, chart: false, index: true, price: '26100' },
  ]);

  // Logic Settings
  const [calcMode, setCalcMode] = useState('Auto');
  const [filterChop, setFilterChop] = useState(true);
  const [chopValue, setChopValue] = useState('61.8');
  const [breakdownWindow, setBreakdownWindow] = useState('0');
  const [useMomentum, setUseMomentum] = useState(true);
  const [useTrend, setUseTrend] = useState(false);
  const [useVwapRev, setUseVwapRev] = useState(false);
  const [minRevSize, setMinRevSize] = useState('5');
  const [restrictVwapScope, setRestrictVwapScope] = useState(false);
  const [vwapScope, setVwapScope] = useState({
    s1: false, s2: false, s3: false, s4: false, s5: false
  });

  // Short Strategy
  const [enableShort, setEnableShort] = useState(true);
  const [shortLots, setShortLots] = useState('2');
  const [shortDays, setShortDays] = useState({
    mon: true, tue: true, wed: true, thu: true, fri: true
  });
  const [maxShortTrades, setMaxShortTrades] = useState('0');
  const [shortStartTime, setShortStartTime] = useState('14:00');
  const [ignoreLogicShort, setIgnoreLogicShort] = useState(false);
  const [restrictShortScope, setRestrictShortScope] = useState(true);
  const [shortScope, setShortScope] = useState({
    s1: false, s2: true, s3: true, s4: true, s5: false
  });
  const [shortTimeExit, setShortTimeExit] = useState(true);
  const [shortExitTime, setShortExitTime] = useState({ h: '14', m: '30' });
  const [shortFixedSl, setShortFixedSl] = useState('0');
  const [shortFixedTgt, setShortFixedTgt] = useState('0');
  const [smartSlDisable, setSmartSlDisable] = useState(true);
  const [smartSlPoints, setSmartSlPoints] = useState('10');
  const [shortTrailingSl, setShortTrailingSl] = useState(false);
  const [shortTrailingAct, setShortTrailingAct] = useState('20');
  const [shortTrailingDist, setShortTrailingDist] = useState('10');

  // Long Strategy
  const [enableLong, setEnableLong] = useState(true);
  const [longLots, setLongLots] = useState('6');
  const [longDays, setLongDays] = useState({
    mon: true, tue: true, wed: true, thu: true, fri: true
  });
  const [maxLongTrades, setMaxLongTrades] = useState('1');
  const [longStartTime, setLongStartTime] = useState('09:15');
  const [ignoreLogicLong, setIgnoreLogicLong] = useState(true);
  const [longAdx, setLongAdx] = useState('20');
  const [longTimeExit, setLongTimeExit] = useState(true);
  const [longExitTime, setLongExitTime] = useState({ h: '15', m: '10' });
  const [restrictLongScope, setRestrictLongScope] = useState(true);
  const [longScope, setLongScope] = useState({
    s1: false, s2: true, s3: false, s4: true, s5: false
  });
  const [longFixedSl, setLongFixedSl] = useState('0');
  const [longFixedTgt, setLongFixedTgt] = useState('0');
  const [longTrailingSl, setLongTrailingSl] = useState(false);
  const [longTrailingAct, setLongTrailingAct] = useState('15');
  const [longTrailingDist, setLongTrailingDist] = useState('10');

  // Visuals
  const [mainTable, setMainTable] = useState('Hide');
  const [pnlTable, setPnlTable] = useState('Bottom m');
  const [showRegime, setShowRegime] = useState(true);
  const [showIndReg, setShowIndReg] = useState(true);
  const [showTMode, setShowTMode] = useState(true);
  const [showTType, setShowTType] = useState(true);
  const [showSuperTrend, setShowSuperTrend] = useState(false);
  const [superTrendFactor, setSuperTrendFactor] = useState('3');
  const [superTrendPeriod, setSuperTrendPeriod] = useState('10');
  const [showEma20, setShowEma20] = useState(true);
  const [showVwap, setShowVwap] = useState(true);
  const [showVwma, setShowVwma] = useState(true);
  const [vwmaLength, setVwmaLength] = useState('35');
  const [showMomLabels, setShowMomLabels] = useState(false);
  const [showDirLabels, setShowDirLabels] = useState(false);

  // Strategy Tag
  const [strategyTag, setStrategyTag] = useState('Yuvi-N-Short/Long');
  const [strategyTagColor, setStrategyTagColor] = useState('#3b82f6');

  // Strategy Lag
  const [strategyLagValue, setStrategyLagValue] = useState('0');
  const [lagMode, setLagMode] = useState('Auto');

  // Capital
  const [initialCapital, setInitialCapital] = useState('100000');
  const [maxCapitalPerTrade, setMaxCapitalPerTrade] = useState('10000');
  const [riskPercentage, setRiskPercentage] = useState('2');

  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    const config = {
      index: indexSelection,
      expiry_dd: parseInt(expiryDate.dd),
      expiry_mm: parseInt(expiryDate.mm),
      expiry_yy: parseInt(expiryDate.yy),
      start_dd: parseInt(startDate.dd),
      start_mm: parseInt(startDate.mm),
      start_yy: parseInt(startDate.yy),
      end_dd: parseInt(endDate.dd),
      end_mm: parseInt(endDate.mm),
      end_yy: parseInt(endDate.yy),
      strikes: strikes.map(s => ({
        label: `S${s.id}`,
        enabled: s.enabled,
        chart: s.chart,
        show_index: s.index,
        price: parseFloat(s.price) || 0
      })),
      logic: {
        calcMode: calcMode,
        filterChop: filterChop,
        chopThreshold: parseFloat(chopValue) || 0,
        breakdownWindow: parseInt(breakdownWindow) || 0,
        useMomentum: useMomentum,
        useTrend: useTrend,
        useVwapRev: useVwapRev,
        minReversalSize: parseFloat(minRevSize) || 0,
        restrictVwapScope: restrictVwapScope,
        vwapScope: vwapScope
      },
      short: {
        enabled: enableShort,
        lots: parseInt(shortLots) || 0,
        maxTrades: parseInt(maxShortTrades) || 0,
        startTime: shortStartTime,
        ignoreLogic: ignoreLogicShort,
        restrictScope: restrictShortScope,
        scope: shortScope,
        fixedSL: parseFloat(shortFixedSl) || 0,
        fixedTarget: parseFloat(shortFixedTgt) || 0,
        smartSlDisable: smartSlDisable,
        smartSlPoints: parseFloat(smartSlPoints) || 0,
        trailingSL: {
          enabled: shortTrailingSl,
          activation: parseFloat(shortTrailingAct) || 0,
          distance: parseFloat(shortTrailingDist) || 0
        },
        timeExit: {
          enabled: shortTimeExit,
          hour: parseInt(shortExitTime.h) || 0,
          minute: parseInt(shortExitTime.m) || 0
        }
      },
      long: {
        enabled: enableLong,
        lots: parseInt(longLots) || 0,
        maxTrades: parseInt(maxLongTrades) || 0,
        startTime: longStartTime,
        ignoreLogic: ignoreLogicLong,
        adxThreshold: parseFloat(longAdx) || 0,
        strictEntry: true,
        restrictScope: restrictLongScope,
        scope: longScope,
        fixedSL: parseFloat(longFixedSl) || 0,
        fixedTarget: parseFloat(longFixedTgt) || 0,
        trailingSL: {
          enabled: longTrailingSl,
          activation: parseFloat(longTrailingAct) || 0,
          distance: parseFloat(longTrailingDist) || 0
        },
        timeExit: {
          enabled: longTimeExit,
          hour: parseInt(longExitTime.h) || 0,
          minute: parseInt(longExitTime.m) || 0
        }
      },
      strategyTag: strategyTag,
      tradingMode: 'paper',
      initialCapital: parseFloat(initialCapital) || 100000,
      maxCapitalPerTrade: parseFloat(maxCapitalPerTrade) || 10000,
      riskPercentage: parseFloat(riskPercentage) || 2
    };

    try {
      const response = await fetch('/api/v1/strategy/config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config })
      });
      
      if (response.ok) {
        alert('✅ Strategy settings saved and applied!');
        onClose();
      } else {
        const error = await response.json();
        alert(`❌ Failed to save settings: ${error.detail || 'Unknown error'}`);
      }
    } catch (err) {
      alert(`❌ Error connecting to backend: ${err}`);
    } finally {
      setIsSaving(false);
    }
  };

  /* ================= WINDOW STATE ================= */
  const [pos, setPos] = useState({ x: 0, y: 0 });
  const [size, setSize] = useState({ width: 900, height: 700 });

  const [dragging, setDragging] = useState(false);
  const [resizing, setResizing] = useState<
    'left' | 'right' | 'top' | 'bottom' | null
  >(null);

  const startMouse = useRef({ x: 0, y: 0 });
  const startPos = useRef({ x: 0, y: 0 });
  const startSize = useRef({ width: 0, height: 0 });

  const MIN_W = 600;
  const MIN_H = 400;

  /* ================= CENTER ================= */
  useEffect(() => {
    if (!isOpen) return;
    setPos({
      x: (window.innerWidth - size.width) / 2,
      y: (window.innerHeight - size.height) / 2,
    });
  }, [isOpen]);

  /* ================= ESC ================= */
  useEffect(() => {
    if (!isOpen) return;
    const esc = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', esc);
    return () => window.removeEventListener('keydown', esc);
  }, [isOpen, onClose]);

  /* ================= DRAG ================= */
  const startDrag = (e: React.MouseEvent) => {
    setDragging(true);
    startMouse.current = { x: e.clientX, y: e.clientY };
    startPos.current = pos;
  };

  /* ================= RESIZE ================= */
  const startResize = (
    dir: 'left' | 'right' | 'top' | 'bottom',
    e: React.MouseEvent
  ) => {
    e.stopPropagation();
    setResizing(dir);
    startMouse.current = { x: e.clientX, y: e.clientY };
    startPos.current = pos;
    startSize.current = size;
  };

  /* ================= MOVE / RESIZE ================= */
  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      const dx = e.clientX - startMouse.current.x;
      const dy = e.clientY - startMouse.current.y;

      if (dragging) {
        setPos({
          x: startPos.current.x + dx,
          y: startPos.current.y + dy,
        });
      }

      if (resizing === 'right') {
        const w = startSize.current.width + dx;
        if (w >= MIN_W) setSize((s) => ({ ...s, width: w }));
      }

      if (resizing === 'left') {
        const w = startSize.current.width - dx;
        if (w >= MIN_W) {
          setSize((s) => ({ ...s, width: w }));
          setPos((p) => ({ ...p, x: startPos.current.x + dx }));
        }
      }

      if (resizing === 'bottom') {
        const h = startSize.current.height + dy;
        if (h >= MIN_H) setSize((s) => ({ ...s, height: h }));
      }

      if (resizing === 'top') {
        const h = startSize.current.height - dy;
        if (h >= MIN_H) {
          setSize((s) => ({ ...s, height: h }));
          setPos((p) => ({ ...p, y: startPos.current.y + dy }));
        }
      }
    };

    const stop = () => {
      setDragging(false);
      setResizing(null);
    };

    if (dragging || resizing) {
      window.addEventListener('mousemove', onMove);
      window.addEventListener('mouseup', stop);
    }

    return () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', stop);
    };
  }, [dragging, resizing]);

  if (!isOpen) return null;

  /* ================= RENDER ================= */
  return (
    <>
      {/* OVERLAY */}
      <div
        className="fixed inset-0 bg-black/60 z-40"
        onClick={onClose}
      />

      {/* MODAL */}
      <div
        className="fixed z-50 bg-[#1e222d] border border-[#2a2e39] rounded-lg shadow-xl flex flex-col text-[#d1d4dc] text-sm"
        style={{
          left: pos.x,
          top: pos.y,
          width: size.width,
          height: size.height,
        }}
      >
        {/* HEADER */}
        <div
          onMouseDown={startDrag}
          className="flex-shrink-0 flex items-center justify-between p-4 border-b border-[#2a2e39] cursor-move select-none"
        >
          <h2 className="text-lg font-medium text-white">
            Yuvi-N-Short/Long (MasterV6)-Final
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            ✕
          </button>
        </div>

        {/* TABS */}
        <div className="flex-shrink-0 flex gap-6 px-4 py-2 border-b border-[#2a2e39]">
          {['inputs', 'style', 'visibility', 'trading'].map((t) => (
            <button
              key={t}
              onClick={() => setActiveTab(t as any)}
              className={`pb-2 ${
                activeTab === t
                  ? 'text-white border-b-2 border-white'
                  : 'text-[#787b86] hover:text-white'
              }`}
            >
              {t === 'trading' ? '⚡ Trading' : t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>

        {/* LEFT / RIGHT / TOP / BOTTOM RESIZE */}
        <div
          className="absolute left-0 top-0 h-full w-2 cursor-ew-resize"
          onMouseDown={(e) => startResize('left', e)}
        />
        <div
          className="absolute right-0 top-0 h-full w-2 cursor-ew-resize"
          onMouseDown={(e) => startResize('right', e)}
        />
        <div
          className="absolute top-0 left-0 w-full h-2 cursor-ns-resize"
          onMouseDown={(e) => startResize('top', e)}
        />
        <div
          className="absolute bottom-0 left-0 w-full h-2 cursor-ns-resize"
          onMouseDown={(e) => startResize('bottom', e)}
        />

        {/* ✅ SCROLLABLE CONTENT */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-6">
          {activeTab === 'inputs' && (
            <>
              {/* ========== 1. SETUP: INDEX & TIME ========== */}
              <div>
                <div className="text-xs text-[#787b86] font-semibold uppercase mb-4">
                  ========== 1. SETUP: INDEX & TIME ==========
                </div>
                
                <div className="space-y-4">
                  {/* Index Selection */}
                  <div className="flex items-center gap-3">
                    <label className="text-[#d1d4dc] min-w-[120px]">Index Selection</label>
                    <select 
                      value={indexSelection} 
                      onChange={(e) => setIndexSelection(e.target.value)}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] min-w-[80px]"
                    >
                      <option>NIFTY</option>
                      <option>BANKNIFTY</option>
                    </select>
                  </div>

                  {/* Expiry Date */}
                  <div className="flex items-center gap-3">
                    <label className="text-[#d1d4dc] min-w-[120px]">Ex.Date (DD</label>
                    <input 
                      type="text" 
                      value={expiryDate.dd}
                      onChange={(e) => setExpiryDate({...expiryDate, dd: e.target.value})}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-12"
                    />
                    <span className="text-[#d1d4dc]">- MM</span>
                    <input 
                      type="text" 
                      value={expiryDate.mm}
                      onChange={(e) => setExpiryDate({...expiryDate, mm: e.target.value})}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-12"
                    />
                    <span className="text-[#d1d4dc]">- YY)</span>
                    <input 
                      type="text" 
                      value={expiryDate.yy}
                      onChange={(e) => setExpiryDate({...expiryDate, yy: e.target.value})}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-12"
                    />
                  </div>

                  {/* Start Date */}
                  <div className="flex items-center gap-3">
                    <label className="text-[#d1d4dc] min-w-[120px]">Start Date (DD</label>
                    <input 
                      type="text" 
                      value={startDate.dd}
                      onChange={(e) => setStartDate({...startDate, dd: e.target.value})}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-12"
                    />
                    <span className="text-[#d1d4dc]">- MM</span>
                    <input 
                      type="text" 
                      value={startDate.mm}
                      onChange={(e) => setStartDate({...startDate, mm: e.target.value})}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-12"
                    />
                    <span className="text-[#d1d4dc]">- YY</span>
                    <input 
                      type="text" 
                      value={startDate.yy}
                      onChange={(e) => setStartDate({...startDate, yy: e.target.value})}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-12"
                    />
                  </div>

                  {/* End Date */}
                  <div className="flex items-center gap-3">
                    <label className="text-[#d1d4dc] min-w-[120px]">End Date (DD</label>
                    <input 
                      type="text" 
                      value={endDate.dd}
                      onChange={(e) => setEndDate({...endDate, dd: e.target.value})}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-12"
                    />
                    <span className="text-[#d1d4dc]">- MM</span>
                    <input 
                      type="text" 
                      value={endDate.mm}
                      onChange={(e) => setEndDate({...endDate, mm: e.target.value})}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-12"
                    />
                    <span className="text-[#d1d4dc]">- YY)</span>
                    <input 
                      type="text" 
                      value={endDate.yy}
                      onChange={(e) => setEndDate({...endDate, yy: e.target.value})}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-12"
                    />
                  </div>
                </div>
              </div>

              {/* ========== 2. STRIKE SELECTION (MASTER) ========== */}
              <div>
                <div className="text-xs text-[#787b86] font-semibold uppercase mb-4">
                  ========== 2. STRIKE SELECTION (MASTER) ==========
                </div>
                
                <div className="space-y-2">
                  {strikes.map((strike, idx) => (
                    <div key={strike.id} className="flex items-center gap-3">
                      <input 
                        type="checkbox" 
                        checked={strike.enabled}
                        onChange={(e) => {
                          const newStrikes = [...strikes];
                          newStrikes[idx].enabled = e.target.checked;
                          setStrikes(newStrikes);
                        }}
                        className="w-4 h-4"
                      />
                      <label className="text-[#d1d4dc] min-w-[20px]">En</label>
                      
                      <input 
                        type="checkbox" 
                        checked={strike.chart}
                        onChange={(e) => {
                          const newStrikes = [...strikes];
                          newStrikes[idx].chart = e.target.checked;
                          setStrikes(newStrikes);
                        }}
                        className="w-4 h-4"
                      />
                      <label className="text-[#d1d4dc] min-w-[35px]">Chart</label>
                      
                      <input 
                        type="checkbox" 
                        checked={strike.index}
                        onChange={(e) => {
                          const newStrikes = [...strikes];
                          newStrikes[idx].index = e.target.checked;
                          setStrikes(newStrikes);
                        }}
                        className="w-4 h-4"
                      />
                      <label className="text-[#d1d4dc] min-w-[30px]">Ind</label>
                      
                      <label className="text-[#d1d4dc] min-w-[50px]">
                        Strike {strike.id} {strike.atm ? '(ATM)' : ''}
                      </label>
                      
                      <input 
                        type="text" 
                        value={strike.price}
                        onChange={(e) => {
                          const newStrikes = [...strikes];
                          newStrikes[idx].price = e.target.value;
                          setStrikes(newStrikes);
                        }}
                        className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-16"
                      />
                    </div>
                  ))}
                </div>
              </div>

              {/* ========== 3. LOGIC SETTINGS ========== */}
              <div>
                <div className="text-xs text-[#787b86] font-semibold uppercase mb-4">
                  ========== 3. LOGIC SETTINGS ==========
                </div>
                
                <div className="space-y-4">
                  {/* Calc Mode */}
                  <div className="flex items-center gap-3">
                    <label className="text-[#d1d4dc] min-w-[120px]">Calc Mode</label>
                    <select 
                      value={calcMode} 
                      onChange={(e) => setCalcMode(e.target.value)}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc]"
                    >
                      <option>Auto</option>
                      <option>Manual</option>
                    </select>
                    
                    <input 
                      type="checkbox" 
                      checked={filterChop}
                      onChange={(e) => setFilterChop(e.target.checked)}
                      className="w-4 h-4 ml-6"
                    />
                    <label className="text-[#d1d4dc]">Filter Chop &gt;</label>
                    <input 
                      type="text" 
                      value={chopValue}
                      onChange={(e) => setChopValue(e.target.value)}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-16"
                    />
                  </div>

                  {/* Breakdown Window */}
                  <div className="flex items-center gap-3">
                    <label className="text-[#d1d4dc] min-w-[120px]">Breakdown Window</label>
                    <input 
                      type="text" 
                      value={breakdownWindow}
                      onChange={(e) => setBreakdownWindow(e.target.value)}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-16"
                    />
                  </div>

                  {/* Toggles */}
                  <div className="flex items-center gap-6">
                    <div className="flex items-center gap-2">
                      <input 
                        type="checkbox" 
                        checked={useMomentum}
                        onChange={(e) => setUseMomentum(e.target.checked)}
                        className="w-4 h-4"
                      />
                      <label className="text-[#d1d4dc]">Use Momentum</label>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <input 
                        type="checkbox" 
                        checked={useTrend}
                        onChange={(e) => setUseTrend(e.target.checked)}
                        className="w-4 h-4"
                      />
                      <label className="text-[#d1d4dc]">Use Trend</label>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <input 
                        type="checkbox" 
                        checked={useVwapRev}
                        onChange={(e) => setUseVwapRev(e.target.checked)}
                        className="w-4 h-4"
                      />
                      <label className="text-[#d1d4dc]">Use VWAP Rev</label>
                    </div>
                  </div>

                  {/* Min Reversal Size */}
                  <div className="flex items-center gap-3">
                    <label className="text-[#d1d4dc] min-w-[120px]">Min Rev Size</label>
                    <input 
                      type="text" 
                      value={minRevSize}
                      onChange={(e) => setMinRevSize(e.target.value)}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-16"
                    />
                  </div>

                  {/* VWAP Scope */}
                  <div className="flex items-center gap-3">
                    <input 
                      type="checkbox" 
                      checked={restrictVwapScope}
                      onChange={(e) => setRestrictVwapScope(e.target.checked)}
                      className="w-4 h-4"
                    />
                    <label className="text-[#d1d4dc] min-w-[120px]">Restrict VWAP Scope?</label>
                    
                    {['s1', 's2', 's3', 's4', 's5'].map((scope) => (
                      <div key={scope} className="flex items-center gap-1">
                        <input 
                          type="checkbox" 
                          checked={vwapScope[scope as keyof typeof vwapScope]}
                          onChange={(e) => setVwapScope({...vwapScope, [scope]: e.target.checked})}
                          className="w-4 h-4"
                        />
                        <label className="text-[#d1d4dc] text-xs">{scope.toUpperCase()}</label>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* ========== 4. SHORT STRATEGY ========== */}
              <div>
                <div className="text-xs text-[#787b86] font-semibold uppercase mb-4">
                  ========== 4. SHORT STRATEGY ==========
                </div>
                
                <div className="space-y-4">
                  {/* Enable Short */}
                  <div className="flex items-center gap-3">
                    <input 
                      type="checkbox" 
                      checked={enableShort}
                      onChange={(e) => setEnableShort(e.target.checked)}
                      className="w-4 h-4"
                    />
                    <label className="text-[#d1d4dc] min-w-[100px]">Enable Short</label>
                    <label className="text-[#d1d4dc] min-w-[40px]">Lots</label>
                    <input 
                      type="text" 
                      value={shortLots}
                      onChange={(e) => setShortLots(e.target.value)}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-16"
                    />
                  </div>

                  {/* Short Days Selection */}
                  <div className="flex items-center gap-3">
                    <label className="text-[#d1d4dc] min-w-[100px]">Trade Days</label>
                    {(['mon', 'tue', 'wed', 'thu', 'fri'] as const).map((day) => (
                      <label key={day} className="flex items-center gap-1 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={shortDays[day]}
                          onChange={(e) => setShortDays({ ...shortDays, [day]: e.target.checked })}
                          className="w-4 h-4"
                        />
                        <span className="text-[#d1d4dc] text-sm capitalize">{day}</span>
                      </label>
                    ))}
                  </div>

                  {/* Max Trades */}
                  <div className="flex items-center gap-3">
                    <label className="text-[#d1d4dc] min-w-[140px]">Max Short Trades (0=Unl.)</label>
                    <input 
                      type="text" 
                      value={maxShortTrades}
                      onChange={(e) => setMaxShortTrades(e.target.value)}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-16"
                    />
                  </div>

                  {/* Start Time Box & Ignore Logic */}
                  <div className="flex items-center gap-3">
                    <label className="text-[#d1d4dc] min-w-[100px]">Short Start Time</label>
                    <input 
                      type="text" 
                      value={shortStartTime}
                      onChange={(e) => setShortStartTime(e.target.value)}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-20"
                      placeholder="HH:MM"
                    />
                    <input 
                      type="checkbox" 
                      checked={ignoreLogicShort}
                      onChange={(e) => setIgnoreLogicShort(e.target.checked)}
                      className="w-4 h-4 ml-4"
                    />
                    <label className="text-[#d1d4dc]">Ignore logic - Consider start time</label>
                  </div>

                  {/* Restrict Scope */}
                  <div className="flex items-center gap-3">
                    <input 
                      type="checkbox" 
                      checked={restrictShortScope}
                      onChange={(e) => setRestrictShortScope(e.target.checked)}
                      className="w-4 h-4"
                    />
                    <label className="text-[#d1d4dc] min-w-[100px]">Restrict Scope?</label>
                    
                    {['s1', 's2', 's3', 's4', 's5'].map((scope) => (
                      <div key={scope} className="flex items-center gap-1">
                        <input 
                          type="checkbox" 
                          checked={shortScope[scope as keyof typeof shortScope]}
                          onChange={(e) => setShortScope({...shortScope, [scope]: e.target.checked})}
                          className="w-4 h-4"
                        />
                        <label className="text-[#d1d4dc] text-xs">{scope.toUpperCase()}</label>
                      </div>
                    ))}
                  </div>

                  {/* Time Exit */}
                  <div className="flex items-center gap-3">
                    <input 
                      type="checkbox" 
                      checked={shortTimeExit}
                      onChange={(e) => setShortTimeExit(e.target.checked)}
                      className="w-4 h-4"
                    />
                    <label className="text-[#d1d4dc] min-w-[80px]">Time Exit? H</label>
                    <input 
                      type="text" 
                      value={shortExitTime.h}
                      onChange={(e) => setShortExitTime({...shortExitTime, h: e.target.value})}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-12"
                    />
                    <label className="text-[#d1d4dc]">M</label>
                    <input 
                      type="text" 
                      value={shortExitTime.m}
                      onChange={(e) => setShortExitTime({...shortExitTime, m: e.target.value})}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-12"
                    />
                  </div>

                  {/* Fixed SL/TGT */}
                  <div className="flex items-center gap-3">
                    <label className="text-[#d1d4dc] min-w-[60px]">Fixed SL</label>
                    <input 
                      type="text" 
                      value={shortFixedSl}
                      onChange={(e) => setShortFixedSl(e.target.value)}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-16"
                    />
                    <label className="text-[#d1d4dc] min-w-[70px] ml-4">Fixed TGT</label>
                    <input 
                      type="text" 
                      value={shortFixedTgt}
                      onChange={(e) => setShortFixedTgt(e.target.value)}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-16"
                    />
                  </div>

                  {/* Smart SL */}
                  <div className="flex items-center gap-3">
                    <input 
                      type="checkbox" 
                      checked={smartSlDisable}
                      onChange={(e) => setSmartSlDisable(e.target.checked)}
                      className="w-4 h-4"
                    />
                    <label className="text-[#d1d4dc] min-w-[120px]">Smart SL Disable &gt;</label>
                    <label className="text-[#d1d4dc] min-w-[30px]">Pts</label>
                    <input 
                      type="text" 
                      value={smartSlPoints}
                      onChange={(e) => setSmartSlPoints(e.target.value)}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-16"
                    />
                  </div>

                  {/* Trailing SL */}
                  <div className="flex items-center gap-3">
                    <input 
                      type="checkbox" 
                      checked={shortTrailingSl}
                      onChange={(e) => setShortTrailingSl(e.target.checked)}
                      className="w-4 h-4"
                    />
                    <label className="text-[#d1d4dc] min-w-[100px]">Trailing SL | Act:</label>
                    <input 
                      type="text" 
                      value={shortTrailingAct}
                      onChange={(e) => setShortTrailingAct(e.target.value)}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-16"
                    />
                    <label className="text-[#d1d4dc] min-w-[50px]">| Dist:</label>
                    <input 
                      type="text" 
                      value={shortTrailingDist}
                      onChange={(e) => setShortTrailingDist(e.target.value)}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-16"
                    />
                  </div>
                </div>
              </div>

              {/* ========== 5. LONG STRATEGY ========== */}
              <div>
                <div className="text-xs text-[#787b86] font-semibold uppercase mb-4">
                  ========== 5. LONG STRATEGY ==========
                </div>
                
                <div className="space-y-4">
                  {/* Enable Long */}
                  <div className="flex items-center gap-3">
                    <input 
                      type="checkbox" 
                      checked={enableLong}
                      onChange={(e) => setEnableLong(e.target.checked)}
                      className="w-4 h-4"
                    />
                    <label className="text-[#d1d4dc] min-w-[100px]">Enable Long</label>
                    <label className="text-[#d1d4dc] min-w-[40px]">Lots</label>
                    <input 
                      type="text" 
                      value={longLots}
                      onChange={(e) => setLongLots(e.target.value)}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-16"
                    />
                  </div>

                  {/* Long Days Selection */}
                  <div className="flex items-center gap-3">
                    <label className="text-[#d1d4dc] min-w-[100px]">Trade Days</label>
                    {(['mon', 'tue', 'wed', 'thu', 'fri'] as const).map((day) => (
                      <label key={day} className="flex items-center gap-1 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={longDays[day]}
                          onChange={(e) => setLongDays({ ...longDays, [day]: e.target.checked })}
                          className="w-4 h-4"
                        />
                        <span className="text-[#d1d4dc] text-sm capitalize">{day}</span>
                      </label>
                    ))}
                  </div>

                  {/* Max Trades */}
                  <div className="flex items-center gap-3">
                    <label className="text-[#d1d4dc] min-w-[140px]">Max Long Trades (0=Unl.)</label>
                    <input 
                      type="text" 
                      value={maxLongTrades}
                      onChange={(e) => setMaxLongTrades(e.target.value)}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-16"
                    />
                  </div>

                  {/* Long Start Time & Ignore Logic */}
                  <div className="flex items-center gap-3">
                    <label className="text-[#d1d4dc] min-w-[100px]">Long Start Time</label>
                    <input 
                      type="text" 
                      value={longStartTime}
                      onChange={(e) => setLongStartTime(e.target.value)}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-20"
                      placeholder="HH:MM"
                    />
                    <input 
                      type="checkbox" 
                      checked={ignoreLogicLong}
                      onChange={(e) => setIgnoreLogicLong(e.target.checked)}
                      className="w-4 h-4 ml-4"
                    />
                    <label className="text-[#d1d4dc]">Ignore logic - Consider start time</label>
                  </div>

                  {/* ADX */}
                  <div className="flex items-center gap-3">
                    <label className="text-[#d1d4dc] min-w-[100px]">ADX</label>
                    <input 
                      type="text" 
                      value={longAdx}
                      onChange={(e) => setLongAdx(e.target.value)}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-16"
                    />
                  </div>

                  {/* Time Exit */}
                  <div className="flex items-center gap-3">
                    <input 
                      type="checkbox" 
                      checked={longTimeExit}
                      onChange={(e) => setLongTimeExit(e.target.checked)}
                      className="w-4 h-4"
                    />
                    <label className="text-[#d1d4dc] min-w-[80px]">Time Exit? H</label>
                    <input 
                      type="text" 
                      value={longExitTime.h}
                      onChange={(e) => setLongExitTime({...longExitTime, h: e.target.value})}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-12"
                    />
                    <label className="text-[#d1d4dc]">M</label>
                    <input 
                      type="text" 
                      value={longExitTime.m}
                      onChange={(e) => setLongExitTime({...longExitTime, m: e.target.value})}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-12"
                    />
                  </div>

                  {/* Restrict Scope */}
                  <div className="flex items-center gap-3">
                    <input 
                      type="checkbox" 
                      checked={restrictLongScope}
                      onChange={(e) => setRestrictLongScope(e.target.checked)}
                      className="w-4 h-4"
                    />
                    <label className="text-[#d1d4dc] min-w-[100px]">Restrict Scope?</label>
                    
                    {['s1', 's2', 's3', 's4', 's5'].map((scope) => (
                      <div key={scope} className="flex items-center gap-1">
                        <input 
                          type="checkbox" 
                          checked={longScope[scope as keyof typeof longScope]}
                          onChange={(e) => setLongScope({...longScope, [scope]: e.target.checked})}
                          className="w-4 h-4"
                        />
                        <label className="text-[#d1d4dc] text-xs">{scope.toUpperCase()}</label>
                      </div>
                    ))}
                  </div>

                  {/* Fixed SL/TGT */}
                  <div className="flex items-center gap-3">
                    <label className="text-[#d1d4dc] min-w-[60px]">Fixed SL</label>
                    <input 
                      type="text" 
                      value={longFixedSl}
                      onChange={(e) => setLongFixedSl(e.target.value)}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-16"
                    />
                    <label className="text-[#d1d4dc] min-w-[70px] ml-4">Fixed TGT</label>
                    <input 
                      type="text" 
                      value={longFixedTgt}
                      onChange={(e) => setLongFixedTgt(e.target.value)}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-16"
                    />
                  </div>

                  {/* Trailing SL */}
                  <div className="flex items-center gap-3">
                    <input 
                      type="checkbox" 
                      checked={longTrailingSl}
                      onChange={(e) => setLongTrailingSl(e.target.checked)}
                      className="w-4 h-4"
                    />
                    <label className="text-[#d1d4dc] min-w-[100px]">Trailing SL | Act:</label>
                    <input 
                      type="text" 
                      value={longTrailingAct}
                      onChange={(e) => setLongTrailingAct(e.target.value)}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-16"
                    />
                    <label className="text-[#d1d4dc] min-w-[50px]">| Dist:</label>
                    <input 
                      type="text" 
                      value={longTrailingDist}
                      onChange={(e) => setLongTrailingDist(e.target.value)}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-16"
                    />
                  </div>
                </div>
              </div>

              {/* ========== 6. VISUALS ========== */}
              <div>
                <div className="text-xs text-[#787b86] font-semibold uppercase mb-4">
                  ========== 6. VISUALS ==========
                </div>
                
                <div className="space-y-4">
                  {/* Main Table */}
                  <div className="flex items-center gap-3">
                    <label className="text-[#d1d4dc] min-w-[80px]">Main Table</label>
                    <select 
                      value={mainTable} 
                      onChange={(e) => setMainTable(e.target.value)}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc]"
                    >
                      <option>Hide</option>
                      <option>Show</option>
                    </select>
                    
                    <label className="text-[#d1d4dc] min-w-[80px] ml-6">P&L Table</label>
                    <select 
                      value={pnlTable} 
                      onChange={(e) => setPnlTable(e.target.value)}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc]"
                    >
                      <option>Bottom m</option>
                      <option>Top</option>
                      <option>Hide</option>
                    </select>
                  </div>

                  {/* Regime & Indicators Checkboxes */}
                  <div className="flex items-center gap-6">
                    <div className="flex items-center gap-2">
                      <input 
                        type="checkbox" 
                        checked={showRegime}
                        onChange={(e) => setShowRegime(e.target.checked)}
                        className="w-4 h-4"
                      />
                      <label className="text-[#d1d4dc]">Regime</label>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <input 
                        type="checkbox" 
                        checked={showIndReg}
                        onChange={(e) => setShowIndReg(e.target.checked)}
                        className="w-4 h-4"
                      />
                      <label className="text-[#d1d4dc]">Ind Reg</label>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <input 
                        type="checkbox" 
                        checked={showTMode}
                        onChange={(e) => setShowTMode(e.target.checked)}
                        className="w-4 h-4"
                      />
                      <label className="text-[#d1d4dc]">T mode</label>
                    </div>

                    <div className="flex items-center gap-2">
                      <input 
                        type="checkbox" 
                        checked={showTType}
                        onChange={(e) => setShowTType(e.target.checked)}
                        className="w-4 h-4"
                      />
                      <label className="text-[#d1d4dc]">T type</label>
                    </div>
                  </div>

                  {/* SuperTrend */}
                  <div className="flex items-center gap-3">
                    <input 
                      type="checkbox" 
                      checked={showSuperTrend}
                      onChange={(e) => setShowSuperTrend(e.target.checked)}
                      className="w-4 h-4"
                    />
                    <label className="text-[#d1d4dc] min-w-[80px]">SuperTrend</label>
                    <label className="text-[#d1d4dc] min-w-[30px]">Fac</label>
                    <input 
                      type="text" 
                      value={superTrendFactor}
                      onChange={(e) => setSuperTrendFactor(e.target.value)}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-16"
                    />
                    <label className="text-[#d1d4dc] min-w-[30px]">Per</label>
                    <input 
                      type="text" 
                      value={superTrendPeriod}
                      onChange={(e) => setSuperTrendPeriod(e.target.value)}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-16"
                    />
                  </div>

                  {/* Indicators */}
                  <div className="flex items-center gap-6">
                    <div className="flex items-center gap-2">
                      <input 
                        type="checkbox" 
                        checked={showEma20}
                        onChange={(e) => setShowEma20(e.target.checked)}
                        className="w-4 h-4"
                      />
                      <label className="text-[#d1d4dc]">EMA(20)</label>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <input 
                        type="checkbox" 
                        checked={showVwap}
                        onChange={(e) => setShowVwap(e.target.checked)}
                        className="w-4 h-4"
                      />
                      <label className="text-[#d1d4dc]">VWAP</label>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <input 
                        type="checkbox" 
                        checked={showVwma}
                        onChange={(e) => setShowVwma(e.target.checked)}
                        className="w-4 h-4"
                      />
                      <label className="text-[#d1d4dc]">VWMA</label>
                      <label className="text-[#d1d4dc]">Len</label>
                      <input 
                        type="text" 
                        value={vwmaLength}
                        onChange={(e) => setVwmaLength(e.target.value)}
                        className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-12"
                      />
                    </div>
                  </div>

                  {/* Labels */}
                  <div className="flex items-center gap-6">
                    <div className="flex items-center gap-2">
                      <input 
                        type="checkbox" 
                        checked={showMomLabels}
                        onChange={(e) => setShowMomLabels(e.target.checked)}
                        className="w-4 h-4"
                      />
                      <label className="text-[#d1d4dc]">Show Mom. Labels</label>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <input 
                        type="checkbox" 
                        checked={showDirLabels}
                        onChange={(e) => setShowDirLabels(e.target.checked)}
                        className="w-4 h-4"
                      />
                      <label className="text-[#d1d4dc]">Show Dir. Labels</label>
                    </div>
                  </div>
                </div>
              </div>

              {/* ========== 7. STRATEGY TAG ========== */}
              <div>
                <div className="text-xs text-[#787b86] font-semibold uppercase mb-4">
                  ========== 7. STRATEGY TAG ==========
                </div>
                
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <label className="text-[#d1d4dc] min-w-[100px]">Strategy Tag</label>
                    <input 
                      type="text" 
                      value={strategyTag}
                      onChange={(e) => setStrategyTag(e.target.value)}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-64"
                      placeholder="Enter strategy tag name"
                    />
                  </div>

                  <div className="flex items-center gap-3">
                    <label className="text-[#d1d4dc] min-w-[100px]">Tag Color</label>
                    <input 
                      type="color" 
                      value={strategyTagColor}
                      onChange={(e) => setStrategyTagColor(e.target.value)}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded w-10 h-8 cursor-pointer"
                    />
                    <div 
                      className="px-3 py-1 rounded text-white text-xs font-medium"
                      style={{ backgroundColor: strategyTagColor }}
                    >
                      {strategyTag || 'Preview'}
                    </div>
                  </div>
                </div>
              </div>

              {/* ========== 8. STRATEGY LAG ========== */}
              <div>
                <div className="text-xs text-[#787b86] font-semibold uppercase mb-4">
                  ========== 8. STRATEGY LAG ==========
                </div>
                
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <label className="text-[#d1d4dc] min-w-[100px]">Lag Value</label>
                    <input 
                      type="text" 
                      value={strategyLagValue}
                      onChange={(e) => setStrategyLagValue(e.target.value)}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-20"
                    />
                  </div>

                  <div className="flex items-center gap-3">
                    <label className="text-[#d1d4dc] min-w-[100px]">Lag Mode</label>
                    <select 
                      value={lagMode} 
                      onChange={(e) => setLagMode(e.target.value)}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc]"
                    >
                      <option>Auto</option>
                      <option>Manual</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* ========== 9. CAPITAL ========== */}
              <div>
                <div className="text-xs text-[#787b86] font-semibold uppercase mb-4">
                  ========== 9. CAPITAL ==========
                </div>
                
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <label className="text-[#d1d4dc] min-w-[150px]">Initial Capital (₹)</label>
                    <input 
                      type="text" 
                      value={initialCapital}
                      onChange={(e) => setInitialCapital(e.target.value)}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-32"
                    />
                  </div>

                  <div className="flex items-center gap-3">
                    <label className="text-[#d1d4dc] min-w-[150px]">Max Capital Per Trade (₹)</label>
                    <input 
                      type="text" 
                      value={maxCapitalPerTrade}
                      onChange={(e) => setMaxCapitalPerTrade(e.target.value)}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-32"
                    />
                  </div>

                  <div className="flex items-center gap-3">
                    <label className="text-[#d1d4dc] min-w-[150px]">Risk per Trade (%)</label>
                    <input 
                      type="text" 
                      value={riskPercentage}
                      onChange={(e) => setRiskPercentage(e.target.value)}
                      className="bg-[#2a2e39] border border-[#3a3e49] rounded px-3 py-1 text-[#d1d4dc] w-20"
                    />
                  </div>
                </div>
              </div>
            </>
          )}

          {activeTab === 'style' && (
            <div className="text-gray-400">Style settings coming soon…</div>
          )}

          {activeTab === 'visibility' && (
            <div className="text-gray-400">
              Visibility settings coming soon…
            </div>
          )}

          {activeTab === 'trading' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-white font-semibold">⚡ Quick Trading Panel</h3>
                <div className="text-xs text-gray-400">Live Market</div>
              </div>

              {/* Strike Prices with Trading Actions */}
              <div className="space-y-2">
                <h4 className="text-sm text-gray-400 mb-3">Available Strikes</h4>
                
                {strikes.filter(strike => strike.enabled).map((strike) => (
                  <div key={strike.id} className="bg-[#2a2e39] rounded-lg p-3 flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="text-white font-medium">
                        {strike.price} {strike.atm ? '(ATM)' : ''}
                      </div>
                      <div className="text-green-400 text-sm">CE: ₹210.60</div>
                      <div className="text-red-400 text-sm">PE: ₹89.45</div>
                    </div>
                    
                    <div className="flex gap-2">
                      <button
                        onClick={() => setTradePopup({ isOpen: true, type: 'BUY', strike: strike.price })}
                        className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-xs rounded transition-colors"
                      >
                        🟢 BUY
                      </button>
                      <button
                        onClick={() => setTradePopup({ isOpen: true, type: 'SELL', strike: strike.price })}
                        className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-xs rounded transition-colors"
                      >
                        🔴 SELL
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Quick Action Buttons */}
              <div className="grid grid-cols-2 gap-3 mt-6">
                <button
                  onClick={() => setTradePopup({ isOpen: true, type: 'BUY', strike: '25850' })}
                  className="px-4 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  <span>🤖</span>
                  <span>Auto Buy ATM</span>
                </button>
                <button
                  onClick={() => setTradePopup({ isOpen: true, type: 'SELL', strike: '25850' })}
                  className="px-4 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  <span>🤖</span>
                  <span>Auto Sell ATM</span>
                </button>
              </div>

              {/* Market Status */}
              <div className="bg-[#2a2e39] rounded-lg p-3 mt-4">
                <h4 className="text-sm text-gray-400 mb-2">Market Status</h4>
                <div className="grid grid-cols-2 gap-4 text-xs">
                  <div className="flex justify-between">
                    <span className="text-gray-400">NIFTY:</span>
                    <span className="text-green-400 font-semibold">25,850 (+0.8%)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">VIX:</span>
                    <span className="text-orange-400 font-semibold">14.2</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Time:</span>
                    <span className="text-blue-400 font-semibold">{new Date().toLocaleTimeString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Status:</span>
                    <span className="text-green-400 font-semibold">● OPEN</span>
                  </div>
                </div>
              </div>

              {/* Recent Orders */}
              <div className="bg-[#2a2e39] rounded-lg p-3">
                <h4 className="text-sm text-gray-400 mb-2">Recent Orders</h4>
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between items-center">
                    <span className="text-white">25850 CE BUY × 2</span>
                    <span className="text-green-400">COMPLETED</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-white">25800 PE SELL × 1</span>
                    <span className="text-green-400">COMPLETED</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-white">25900 CE BUY × 3</span>
                    <span className="text-yellow-400">PENDING</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* FOOTER */}
        <div className="flex-shrink-0 flex items-center justify-between p-4 border-t border-[#2a2e39] bg-[#1e222d] rounded-b-lg">
          <div className="flex gap-4">
            <button className="text-[#787b86] hover:text-white text-xs">Defaults</button>
          </div>
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-[#2a2e39] hover:bg-[#363a45] text-white rounded transition-colors text-sm"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving}
              className={`px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded transition-colors text-sm flex items-center gap-2 ${isSaving ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              {isSaving ? (
                <>
                  <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></div>
                  Saving...
                </>
              ) : (
                <>💾 Save Settings</>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Trade Execution Popup */}
      <TradeExecutionPopup
        isOpen={tradePopup.isOpen}
        onClose={() => setTradePopup({ isOpen: false, type: null })}
        tradeType={tradePopup.type}
        selectedStrike={tradePopup.strike}
      />
    </>
  );
}
