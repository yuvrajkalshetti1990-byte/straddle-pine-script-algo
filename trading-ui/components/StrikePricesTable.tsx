'use client'

import React, { useState, useEffect, useRef } from 'react';

// Manual Trade Popup Component
interface ManualTradePopupProps {
  isOpen: boolean;
  onClose: () => void;
  strike: string;
  ceLTP: string;
  peLTP: string;
  spotPrice: string;
}

function getPopupStartPosition() {
  if (typeof window === 'undefined') {
    return { x: 0, y: 0 };
  }

  return {
    x: window.innerWidth / 2 - 180,
    y: window.innerHeight / 2 - 200,
  };
}

const ManualTradePopup: React.FC<ManualTradePopupProps> = ({
  isOpen,
  onClose,
  strike,
  ceLTP,
  peLTP,
  spotPrice
}) => {
  const [selectedTypes, setSelectedTypes] = useState({ call: true, put: false });
  const [quantity, setQuantity] = useState('1');
  const [price, setPrice] = useState('');
  const [marketPrice, setMarketPrice] = useState(true);
  const [marketProtection, setMarketProtection] = useState(false);
  const [triggerEnabled, setTriggerEnabled] = useState(false);
  const [triggerPrice, setTriggerPrice] = useState('');
  
  // Draggable state
  const [position, setPosition] = useState(getPopupStartPosition);
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const popupRef = useRef<HTMLDivElement>(null);

  const handleTypeToggle = (type: 'call' | 'put') => {
    setSelectedTypes(prev => ({ ...prev, [type]: !prev[type] }));
  };

  const executeAction = (action: 'LE' | 'LX' | 'SE' | 'SX') => {
    const actionNames: Record<string, string> = {
      'LE': 'Long Entry',
      'LX': 'Long Exit',
      'SE': 'Short Entry',
      'SX': 'Short Exit'
    };
    const types = [];
    if (selectedTypes.call) types.push('CE');
    if (selectedTypes.put) types.push('PE');
    
    alert(`✅ ${actionNames[action]} executed!\nStrike: ${strike}\nType(s): ${types.join(', ')}\nQuantity: ${quantity} lots`);
    onClose();
  };

  // Draggable handlers
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
        setPosition({
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

  if (!isOpen) return null;

  return (
    <div className="fixed z-50" onClick={(e) => e.stopPropagation()}>
      <div 
        ref={popupRef}
        className="bg-gray-800 border border-gray-600 rounded-lg shadow-xl w-80 text-white fixed"
        style={{ 
          left: position.x, 
          top: position.y,
          cursor: isDragging ? 'grabbing' : 'default'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header - Draggable */}
        <div 
          className="flex justify-between items-center px-4 py-3 border-b border-gray-600 cursor-grab active:cursor-grabbing bg-gray-700 rounded-t-lg"
          onMouseDown={handleMouseDown}
        >
          <h3 className="text-white font-bold text-sm">🎯 Manual Trade - {strike}</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-xl font-bold px-2 py-1 hover:bg-gray-600 rounded"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-3">
          {/* CALL/PUT Selection */}
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={selectedTypes.call}
                onChange={() => handleTypeToggle('call')}
                className="w-4 h-4 accent-blue-500"
              />
              <span className="text-sm font-semibold text-blue-300">CALL</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={selectedTypes.put}
                onChange={() => handleTypeToggle('put')}
                className="w-4 h-4 accent-red-500"
              />
              <span className="text-sm font-semibold text-red-300">PUT</span>
            </label>
          </div>

          {/* Action Buttons Grid */}
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => executeAction('LE')}
              className="px-3 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-bold rounded transition-colors"
            >
              🟢 LE (Long Entry)
            </button>
            <button
              onClick={() => executeAction('LX')}
              className="px-3 py-2 bg-green-700 hover:bg-green-800 text-white text-sm font-bold rounded transition-colors"
            >
              🟢 LX (Long Exit)
            </button>
            <button
              onClick={() => executeAction('SE')}
              className="px-3 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-bold rounded transition-colors"
            >
              🔴 SE (Short Entry)
            </button>
            <button
              onClick={() => executeAction('SX')}
              className="px-3 py-2 bg-red-700 hover:bg-red-800 text-white text-sm font-bold rounded transition-colors"
            >
              🔴 SX (Short Exit)
            </button>
          </div>

          {/* Qty and Price Fields */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-300 mb-1 font-bold">Qty</label>
              <input
                type="number"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                min="1"
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-400"
                placeholder="Quantity"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-300 mb-1 font-bold">Price</label>
              <input
                type="number"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                disabled={marketPrice}
                className={`w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-400 ${marketPrice ? 'opacity-50 cursor-not-allowed' : ''}`}
                placeholder="Enter price"
              />
            </div>
          </div>

          {/* Market Price & Market Protection Checkboxes */}
          <div className="flex flex-col gap-2">
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={marketPrice}
                onChange={(e) => setMarketPrice(e.target.checked)}
                className="w-4 h-4 accent-blue-500"
              />
              <span className="text-sm text-gray-300">Market Price</span>
            </label>
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={marketProtection}
                onChange={(e) => setMarketProtection(e.target.checked)}
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
                checked={triggerEnabled}
                onChange={(e) => setTriggerEnabled(e.target.checked)}
                className="w-4 h-4 accent-blue-500"
              />
              <span className="text-sm text-gray-300 font-bold">Trigger Price</span>
            </label>
            {triggerEnabled && (
              <input
                type="number"
                value={triggerPrice}
                onChange={(e) => setTriggerPrice(e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-400"
                placeholder="Enter trigger price"
              />
            )}
          </div>

          {/* Price Info */}
          <div className="bg-gray-700 rounded p-3 space-y-1 text-xs">
            <div className="flex justify-between">
              <span className="text-gray-400">Spot Price</span>
              <span className="text-yellow-400 font-semibold">{spotPrice}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Strike</span>
              <span className="text-white font-semibold">{strike}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">CE LTP</span>
              <span className="text-blue-300 font-semibold">₹{ceLTP}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">PE LTP</span>
              <span className="text-red-300 font-semibold">₹{peLTP}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

interface StrikeRow {
  strike: number;
  cIV: number;
  open: number;
  ltp: number;
  ce: number;
  pe: number;
  change: number;
  lead: string;
  cDelta: number;
  cVolume: string;
  ivChange?: number | null;
  netDelta?: number | null;
  deltaChange?: number | null;
  volumeSurge?: number | null;
  currentVolume?: number | null;
  avgVolume20?: number | null;
  regime: string;
  indReg: string;
  tMode: string;
  tType: string;
  isATM: boolean;
  indicators?: Indicators;
  indicatorSource?: string;
  dynamicPricing?: DynamicPricing;
}

interface Indicators {
  rsi: number | null;
  roc: number | null;
  adx: number | null;
  plusDI: number | null;
  minusDI: number | null;
  chop: number | null;
}

interface DynamicPricing {
  base_premium: number;
  ce_close: number;
  pe_close: number;
  dynamic_premium: number;
  adjustment_factor: number;
  premium_adjustment_points: number;
  premium_adjustment_percent: number;
  adjustments: {
    roc_factor: number;
    rsi_factor: number;
    di_factor: number;
    adx_factor: number;
    chop_factor: number;
  };
  indicators: Indicators;
}

interface StrikeSnapshotCache {
  strikes?: StrikeRow[];
  indicators?: Indicators;
  spotPrice?: string | number | null;
  selectedStrike?: string | number | null;
  expiry?: string | null;
  cachedAt?: string | null;
  updatedAt?: string | null;
  fallbackSource?: string | null;
  isStale?: boolean;
}

const STRIKES_CACHE_KEY = 'market.strikes.last_snapshot.v4';

const EMPTY_INDICATORS: Indicators = {
  rsi: null,
  roc: null,
  adx: null,
  plusDI: null,
  minusDI: null,
  chop: null,
};

function hasIndicatorValues(indicators?: Partial<Indicators> | null) {
  if (!indicators) {
    return false;
  }

  return Object.values(indicators).some((value) => value !== null && value !== undefined);
}

function formatIndicatorValue(value: number | null, digits = 1) {
  if (value === null || Number.isNaN(value)) {
    return '--';
  }

  return Number.isInteger(value) ? String(value) : value.toFixed(digits);
}

function formatSignedValue(value?: number | null, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '--';
  }

  const formatted = value.toFixed(digits);
  return value > 0 ? `+${formatted}` : formatted;
}

function formatMultiplier(value?: number | null) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '--';
  }

  return `${value.toFixed(1)}x`;
}

function signedValueClass(value?: number | null, positive = 'text-green-400', negative = 'text-red-400') {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return 'text-gray-400';
  }

  return value >= 0 ? positive : negative;
}

function volumeSurgeClass(value?: number | null) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return 'text-gray-400';
  }
  if (value >= 2.5) {
    return 'text-orange-300 font-bold';
  }
  if (value >= 1.5) {
    return 'text-yellow-300 font-bold';
  }
  return 'text-slate-300';
}

function parseDateOnly(value?: string | null) {
  if (!value) {
    return null;
  }

  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function isUsableCachedSnapshot(snapshot?: StrikeSnapshotCache | null) {
  if (!snapshot?.strikes?.length || snapshot.isStale) {
    return false;
  }

  // Old localStorage entries did not include expiry/spot metadata. Do not reuse
  // them because they can show expired strikes with fresh-looking timestamps.
  if (!snapshot.expiry || snapshot.spotPrice === null || snapshot.spotPrice === undefined) {
    return false;
  }

  const expiry = parseDateOnly(snapshot.expiry);
  if (!expiry) {
    return false;
  }

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  expiry.setHours(0, 0, 0, 0);
  if (expiry < today) {
    return false;
  }

  const timestamp = parseDateOnly(snapshot.cachedAt || snapshot.updatedAt);
  if (!timestamp) {
    return false;
  }

  return Date.now() - timestamp.getTime() <= 3 * 24 * 60 * 60 * 1000;
}

function centerStrikeRows(rows: StrikeRow[], centerStrike: number | null, radius = 2) {
  if (rows.length <= (radius * 2) + 1 && centerStrike === null) {
    return rows;
  }

  const centerIndex = centerStrike !== null
    ? rows.findIndex((row) => Number(row.strike) === centerStrike)
    : rows.findIndex((row) => row.isATM);

  if (centerIndex < 0) {
    return rows.slice(0, (radius * 2) + 1);
  }

  const windowSize = (radius * 2) + 1;
  let start = centerIndex - radius;
  let end = centerIndex + radius + 1;

  if (start < 0) {
    end += -start;
    start = 0;
  }
  if (end > rows.length) {
    start = Math.max(0, start - (end - rows.length));
    end = rows.length;
  }

  return rows.slice(start, end).slice(0, windowSize);
}

function clamp(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, value));
}

function projectIndicatorsFromSelectedPrice(
  indicators: Indicators,
  selectedRow?: StrikeRow
): Indicators {
  if (!selectedRow || !hasIndicatorValues(indicators) || !selectedRow.open || !selectedRow.ltp) {
    return indicators;
  }

  const botOpen = 526.5;
  const botClose = 524.5;
  const botMovePct = ((botClose - botOpen) / botOpen) * 100;
  const currentMovePct = ((selectedRow.ltp - selectedRow.open) / selectedRow.open) * 100;
  const moveDelta = currentMovePct - botMovePct;
  const trendForce = Math.abs(moveDelta);
  const bearish = moveDelta < 0;

  let plusDI = indicators.plusDI ?? 0;
  let minusDI = indicators.minusDI ?? 0;
  if (bearish) {
    minusDI += trendForce * 1.4;
    plusDI = Math.max(0, plusDI - trendForce * 0.8);
  } else {
    plusDI += trendForce * 1.4;
    minusDI = Math.max(0, minusDI - trendForce * 0.8);
  }

  return {
    roc: Number(((indicators.roc ?? 0) + moveDelta).toFixed(2)),
    rsi: Number(clamp((indicators.rsi ?? 50) + moveDelta * 2.5, 0, 100).toFixed(2)),
    minusDI: Number(clamp(minusDI, 0, 100).toFixed(2)),
    plusDI: Number(clamp(plusDI, 0, 100).toFixed(2)),
    adx: Number(clamp((indicators.adx ?? 20) + trendForce * 0.5, 0, 100).toFixed(2)),
    chop: Number(clamp((indicators.chop ?? 50) - trendForce * 0.35, 0, 100).toFixed(2)),
  };
}

const StrikePricesTable = ({ className = "" }: { className?: string }) => {
  const [mounted, setMounted] = useState(false);
  const [showManualPopup, setShowManualPopup] = useState(false);
  const [manualPopupData, setManualPopupData] = useState<{strike: string; ce: string; pe: string; spot: string} | null>(null);

  // Live data state
  const [strikeData, setStrikeData] = useState<StrikeRow[]>([]);
  const [selectedStrike, setSelectedStrike] = useState<number | null>(null);
  const [spotPrice, setSpotPrice] = useState<string | null>(null);
  const [indicators, setIndicators] = useState<Indicators>(EMPTY_INDICATORS);
  const [indicatorSource, setIndicatorSource] = useState<string | null>(null);
  const [backendConnected, setBackendConnected] = useState<boolean | null>(null);
  const [marketOpen, setMarketOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [strikeLevelIndicators, setStrikeLevelIndicators] = useState<Indicators | null>(null);
  const [strikeLevelIndicatorSource, setStrikeLevelIndicatorSource] = useState<string | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Restore last known snapshot on initial mount (useful when market is offline)
  useEffect(() => {
    try {
      const cachedRaw = localStorage.getItem(STRIKES_CACHE_KEY);
      if (!cachedRaw) {
        return;
      }

      const cached = JSON.parse(cachedRaw) as StrikeSnapshotCache;
      if (!isUsableCachedSnapshot(cached)) {
        localStorage.removeItem(STRIKES_CACHE_KEY);
        return;
      }

      if (cached?.strikes?.length) {
        setStrikeData(cached.strikes);
      }
      const cachedSelectedStrike = Number(cached?.selectedStrike ?? cached?.strikes?.find((row) => row.isATM)?.strike);
      if (Number.isFinite(cachedSelectedStrike)) {
        setSelectedStrike(cachedSelectedStrike);
      }
      if (cached?.spotPrice !== null && cached?.spotPrice !== undefined) {
        setSpotPrice(String(cached.spotPrice));
      }
      if (hasIndicatorValues(cached?.indicators)) {
        setIndicators((prev) => ({ ...prev, ...cached.indicators }));
        setIndicatorSource(cached.fallbackSource || 'local_cache');
      }
    } catch (error) {
      console.error('Error restoring strike cache:', error);
    }
  }, []);

  // Fetch strike data every 5 seconds
  useEffect(() => {
    const fetchStrikes = async () => {
      try {
        const query = selectedStrike !== null ? `?selectedStrike=${encodeURIComponent(String(selectedStrike))}` : '';
        const res = await fetch(`/api/market/strikes${query}`);
        const result = await res.json();
        setBackendConnected(result.connected ?? false);

        if (result.status === 'success' && result.data) {
          const fallbackSource = result.data.fallbackSource || 'live';
          if (result.data.isStale || fallbackSource === 'stale_snapshot') {
            setStrikeData([]);
            setIndicators(EMPTY_INDICATORS);
            setIndicatorSource('stale_snapshot');
            setMarketOpen(false);
            localStorage.removeItem(STRIKES_CACHE_KEY);
            if (result.data.spotPrice !== null && result.data.spotPrice !== undefined) {
              setSpotPrice(String(result.data.spotPrice));
            }
            return;
          }

          if (result.data.spotPrice !== null && result.data.spotPrice !== undefined) {
            setSpotPrice(String(result.data.spotPrice));
          }
          const resolvedSelectedStrike = Number(result.data.selectedStrike ?? result.data.atmStrike);
          if (Number.isFinite(resolvedSelectedStrike)) {
            setSelectedStrike(resolvedSelectedStrike);
          }
          if (result.data.strikes?.length > 0) {
            setStrikeData(result.data.strikes);
            try {
              localStorage.setItem(
                STRIKES_CACHE_KEY,
                JSON.stringify({
                  strikes: result.data.strikes,
                  indicators: result.data.indicators || {},
                  spotPrice: result.data.spotPrice ?? null,
                  selectedStrike: result.data.selectedStrike ?? result.data.atmStrike ?? selectedStrike,
                  expiry: result.data.expiry ?? null,
                  cachedAt: result.data.cachedAt ?? null,
                  fallbackSource,
                  isStale: false,
                  updatedAt: new Date().toISOString(),
                })
              );
            } catch (cacheError) {
              console.error('Error writing strike cache:', cacheError);
            }
          }
          if (hasIndicatorValues(result.data.indicators)) {
            setIndicators({ ...EMPTY_INDICATORS, ...result.data.indicators });
            setIndicatorSource(fallbackSource);
          } else {
            setIndicators(EMPTY_INDICATORS);
            setIndicatorSource(null);
          }
          setMarketOpen(result.data.marketOpen ?? false);
        }
      } catch (error) {
        console.error('Error fetching strikes:', error);
        setBackendConnected(false);
      } finally {
        setLoading(false);
      }

    };

    fetchStrikes();
    const interval = setInterval(fetchStrikes, 5000);
    return () => clearInterval(interval);
  }, [selectedStrike]);

  // Fetch strike-level indicators when strike is selected
  useEffect(() => {
    if (!selectedStrike || !strikeData.length) {
      setStrikeLevelIndicators(null);
      setStrikeLevelIndicatorSource(null);
      return;
    }

    const fetchStrikeDetail = async () => {
      try {
        const selectedRow = strikeData.find((row) => Number(row.strike) === selectedStrike);
        if (!selectedRow) {
          setStrikeLevelIndicators(null);
          setStrikeLevelIndicatorSource(null);
          return;
        }
        if (hasIndicatorValues(selectedRow.indicators)) {
          setStrikeLevelIndicators(null);
          setStrikeLevelIndicatorSource(null);
          return;
        }

        const ce = selectedRow.ce || 0;
        const pe = selectedRow.pe || 0;

        const res = await fetch(
          `/api/market/strikes/detail?strike=${selectedStrike}&ce_ltp=${ce}&pe_ltp=${pe}`
        );
        const result = await res.json();

        if (result.status === 'success' && result.data?.indicators) {
          setStrikeLevelIndicators(result.data.indicators);
          setStrikeLevelIndicatorSource(result.data.indicatorSource || null);
        } else {
          setStrikeLevelIndicators(null);
          setStrikeLevelIndicatorSource(null);
        }
      } catch (error) {
        console.error('Error fetching strike detail:', error);
        setStrikeLevelIndicators(null);
        setStrikeLevelIndicatorSource(null);
      }
    };

    fetchStrikeDetail();
  }, [selectedStrike, strikeData]);

  if (!mounted) {
    return (
      <div className={`bg-gray-800 text-white p-4 rounded-lg shadow-lg ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-700 rounded mb-4 w-1/3"></div>
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex space-x-4">
                <div className="h-4 bg-gray-700 rounded flex-1"></div>
                <div className="h-4 bg-gray-700 rounded flex-1"></div>
                <div className="h-4 bg-gray-700 rounded flex-1"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  const selectedStrikeRow = selectedStrike !== null
    ? strikeData.find((row) => Number(row.strike) === selectedStrike)
    : strikeData.find((row) => row.isATM);
  const selectedRowIndicators = selectedStrikeRow?.indicators;
  const selectedRowIndicatorSource = selectedStrikeRow?.indicatorSource || indicatorSource || 'bot_historical';
  const hasSelectedRowIndicators = hasIndicatorValues(selectedRowIndicators);
  const hasStrikeLevelIndicators = hasIndicatorValues(strikeLevelIndicators);
  const hasUsableStrikeLevelIndicators =
    hasStrikeLevelIndicators && strikeLevelIndicatorSource !== 'spot_fallback';
  
  // For a selected strike, prefer strike-specific indicators.
  // If these are unavailable, fall back to the live market-level indicators.
  const rawDisplayedIndicators: Indicators = hasSelectedRowIndicators
    ? { ...EMPTY_INDICATORS, ...selectedRowIndicators }
    : hasUsableStrikeLevelIndicators
      ? { ...EMPTY_INDICATORS, ...strikeLevelIndicators }
      : indicators;
  const displayedIndicatorSource = hasSelectedRowIndicators
    ? selectedRowIndicatorSource
    : hasUsableStrikeLevelIndicators
      ? strikeLevelIndicatorSource
      : indicatorSource;
  const isFallbackIndicatorSource = displayedIndicatorSource === 'spot_fallback';
  const isCachedIndicatorSource = ['last_snapshot', 'local_cache', 'cached_strike'].includes(displayedIndicatorSource || '');
  const isStaleIndicatorSource = displayedIndicatorSource === 'stale_snapshot';
  const isPriceProjectedSource =
    displayedIndicatorSource === 'bot_price_projected_3m' ||
    (
      Boolean(selectedStrikeRow) &&
      hasIndicatorValues(rawDisplayedIndicators) &&
      displayedIndicatorSource !== 'strike_candles' &&
      displayedIndicatorSource !== 'spot_fallback' &&
      displayedIndicatorSource !== 'stale_snapshot'
    );
  const shouldProjectSelectedPrice = isPriceProjectedSource;
  const displayedIndicators = shouldProjectSelectedPrice
    ? projectIndicatorsFromSelectedPrice(rawDisplayedIndicators, selectedStrikeRow)
    : rawDisplayedIndicators;

  const hasDisplayedIndicators = hasIndicatorValues(displayedIndicators);
  const showLiveIndicators = hasDisplayedIndicators && !isCachedIndicatorSource && !isStaleIndicatorSource;
  const showCachedIndicators = hasDisplayedIndicators && isCachedIndicatorSource;
  const indicatorLabel = isPriceProjectedSource
    ? 'BOT 3M PRICE PROJECTED'
    : showLiveIndicators
      ? selectedStrike
        ? isFallbackIndicatorSource
          ? 'MARKET INDICATORS'
          : displayedIndicatorSource === 'bot_historical'
            ? 'BOT HISTORICAL INDICATORS'
            : 'STRIKE LEVEL INDICATORS'
        : 'LIVE INDICATORS'
    : showCachedIndicators
      ? 'CACHED INDICATORS'
      : isStaleIndicatorSource
        ? 'STALE SNAPSHOT'
        : 'NO INDICATOR CANDLES';
  const indicatorHint = !hasDisplayedIndicators
    ? backendConnected === false
      ? 'HDFC Sky is disconnected. Connect broker to fetch CE/PE candles for ROC, RSI, DI, ADX and CHOP.'
      : backendConnected === null
        ? 'Checking HDFC Sky connection and option candles for ROC, RSI, DI, ADX and CHOP.'
      : displayedIndicatorSource === 'last_snapshot'
        ? 'Showing cached prices only. The cached snapshot has no option candle indicators.'
        : 'HDFC Sky is connected, but CE/PE option candles are unavailable for this strike.'
    : null;
  const visibleStrikeData = centerStrikeRows(strikeData, selectedStrike);

  return (
    <div className={`border border-gray-700 bg-[#020617] rounded-md overflow-hidden ${className}`}>
      <div className="overflow-x-auto">
        <table className="w-full text-[10px] border-collapse">
          <thead className="bg-[#1d4ed8]">
            <tr>
              {["STRIKE", "C.IV", "IV CHG", "OPEN", "LTP", "CE", "PE", "CHANGE", "LEAD", "NET DELTA", "VOL SURGE", "REGIME", "IND.REG", "T.MODE", "T.TYPE", "MANUAL"].map(h => (
                <th key={h} className="px-1 py-1 text-left font-bold text-white border-r border-blue-900 whitespace-nowrap">
                  {h}
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {visibleStrikeData.length === 0 ? (
              <tr>
                <td colSpan={16} className="px-4 py-8 text-center text-gray-500">
                  {loading ? 'Loading strike data...' : !marketOpen ? 'Market is closed - showing last close prices.' : 'No strike data available'}
                </td>
              </tr>
            ) : visibleStrikeData.map((row, i) => {
              const isSelectedCenter = selectedStrike !== null ? Number(row.strike) === selectedStrike : row.isATM;
              return (
              <tr
                key={i}
                onClick={() => setSelectedStrike(Number(row.strike))}
                className={`cursor-pointer border-t border-gray-800 transition-colors ${isSelectedCenter ? 'bg-yellow-900/40 border-yellow-600' : 'hover:bg-gray-800/50'}`}
              >
                <td className={`px-1 py-1 font-mono ${isSelectedCenter ? 'text-yellow-300 font-bold' : 'text-gray-400'}`}>{row.strike}</td>
                <td className="px-1 py-1 text-purple-400 font-semibold">{row.cIV}</td>
                <td className={`px-1 py-1 font-semibold ${signedValueClass(row.ivChange)}`}>
                  {formatSignedValue(row.ivChange, 2)}
                </td>
                <td className="px-1 py-1 text-gray-400">{row.open}</td>
                <td className="px-1 py-1 font-bold text-white">{row.ltp}</td>
                <td className="px-1 py-1 text-blue-300 font-semibold">{row.ce}</td>
                <td className="px-1 py-1 text-red-300 font-semibold">{row.pe}</td>
                <td className={`px-1 py-1 font-bold ${row.change >= 0 ? "text-green-400" : "text-red-400"}`}>
                  {row.change >= 0 ? '+' : ''}{row.change}
                </td>
                <td className="px-1 py-1 text-orange-400">
                  {row.lead}
                </td>
                <td className={`px-1 py-1 font-semibold ${signedValueClass(row.netDelta ?? row.cDelta)}`}>
                  {formatSignedValue(row.netDelta ?? row.cDelta, 2)}
                </td>
                <td className={`px-1 py-1 ${volumeSurgeClass(row.volumeSurge)}`}>
                  {formatMultiplier(row.volumeSurge)}
                </td>
                <td className={`px-1 py-1 font-bold text-center ${row.regime === 'BEARISH' ? 'text-red-400' : row.regime === 'SHORT COV' ? 'text-orange-400' : row.regime === 'BULLISH' ? 'text-green-400' : 'text-gray-400'}`}>
                  {row.regime}
                </td>
                <td className={`px-1 py-1 font-semibold ${row.indReg === 'Bullish' ? 'text-green-400' : row.indReg === 'Bearish' ? 'text-red-400' : row.indReg === 'Neutral' ? 'text-yellow-400' : 'text-gray-400'}`}>{row.indReg}</td>
                <td className="px-1 py-1 text-blue-400 font-semibold">{row.tMode}</td>
                <td className="px-1 py-1 text-green-400 font-semibold">{row.tType}</td>

                {/* MANUAL Column */}
                <td className="px-1 py-1">
                  <button
                    onClick={(event) => {
                      event.stopPropagation();
                      setManualPopupData({
                        strike: String(row.strike),
                        ce: String(row.ce),
                        pe: String(row.pe),
                        spot: spotPrice ?? '--'
                      });
                      setShowManualPopup(true);
                    }}
                    className="px-2 py-0.5 bg-green-600 hover:bg-green-700 text-white text-[10px] font-bold rounded transition-colors"
                  >
                    Trade
                  </button>
                </td>
              </tr>
              );
            })}
          </tbody>
        </table>

        {/* Manual Trade Popup */}
        {showManualPopup && (
          <ManualTradePopup
            isOpen={showManualPopup}
            onClose={() => {
              setShowManualPopup(false);
            }}
            strike={manualPopupData?.strike || '--'}
            ceLTP={manualPopupData?.ce || '--'}
            peLTP={manualPopupData?.pe || '--'}
            spotPrice={manualPopupData?.spot || '--'}
          />
        )}

        {/* Indicators Footer */}
        <div className="border-t border-gray-700 bg-[#020617] text-[11px] px-3 py-2">
          <div className="mb-2 flex flex-wrap items-center gap-2 text-[10px]">
            <span className={`rounded px-2 py-0.5 font-semibold ${showLiveIndicators ? 'bg-emerald-900/40 text-emerald-300' : showCachedIndicators ? 'bg-amber-900/40 text-amber-300' : 'bg-slate-900/60 text-slate-400'}`}>
              {indicatorLabel}
            </span>
            {selectedStrike !== null ? (
              <span className="rounded bg-blue-950/60 px-2 py-0.5 font-semibold text-blue-300">
                CENTER {selectedStrike}
              </span>
            ) : null}
            {isStaleIndicatorSource ? (
              <span className="text-slate-400">
                Live option-chain data is unavailable. Expired cached strikes were cleared.
              </span>
            ) : null}
            {indicatorHint ? (
              <span className="text-slate-400">
                {indicatorHint}
              </span>
            ) : null}
          </div>
          <div className="grid grid-cols-2 gap-2 md:grid-cols-3 xl:grid-cols-6">
            <div className="rounded border border-slate-800 bg-slate-950/60 px-2 py-1.5">
              <div className="text-[9px] font-semibold tracking-wide text-slate-500">ROC</div>
              <div className={`text-sm font-bold ${(displayedIndicators.roc ?? 0) < 0 ? 'text-red-400' : 'text-green-400'}`}>
                {formatIndicatorValue(displayedIndicators.roc)}
              </div>
            </div>
            <div className="rounded border border-slate-800 bg-slate-950/60 px-2 py-1.5">
              <div className="text-[9px] font-semibold tracking-wide text-slate-500">RSI</div>
              <div className="text-sm font-bold text-white">
                {formatIndicatorValue(displayedIndicators.rsi)}
              </div>
            </div>
            <div className="rounded border border-slate-800 bg-slate-950/60 px-2 py-1.5">
              <div className="text-[9px] font-semibold tracking-wide text-slate-500">-DI</div>
              <div className={`text-sm font-bold ${(displayedIndicators.minusDI ?? 0) > (displayedIndicators.plusDI ?? 0) ? 'text-red-400' : 'text-slate-300'}`}>
                {formatIndicatorValue(displayedIndicators.minusDI)}
              </div>
            </div>
            <div className="rounded border border-slate-800 bg-slate-950/60 px-2 py-1.5">
              <div className="text-[9px] font-semibold tracking-wide text-slate-500">+DI</div>
              <div className={`text-sm font-bold ${(displayedIndicators.plusDI ?? 0) > (displayedIndicators.minusDI ?? 0) ? 'text-green-400' : 'text-slate-300'}`}>
                {formatIndicatorValue(displayedIndicators.plusDI)}
              </div>
            </div>
            <div className="rounded border border-slate-800 bg-slate-950/60 px-2 py-1.5">
              <div className="text-[9px] font-semibold tracking-wide text-slate-500">ADX</div>
              <div className="text-sm font-bold text-cyan-400">
                {formatIndicatorValue(displayedIndicators.adx)}
              </div>
            </div>
            <div className="rounded border border-slate-800 bg-slate-950/60 px-2 py-1.5">
              <div className="text-[9px] font-semibold tracking-wide text-slate-500">CHOP</div>
              <div className={`text-sm font-bold ${(displayedIndicators.chop ?? 0) > 61.8 ? 'text-orange-400' : 'text-slate-300'}`}>
                {formatIndicatorValue(displayedIndicators.chop)}
              </div>
            </div>
          </div>
          {selectedStrikeRow ? (
            <div className="mt-2 grid grid-cols-2 gap-2 md:grid-cols-4">
              <div className="rounded border border-slate-800 bg-slate-950/60 px-2 py-1.5">
                <div className="text-[9px] font-semibold tracking-wide text-slate-500">COMB PREMIUM</div>
                <div className="text-sm font-bold text-white">
                  {Number.isFinite(selectedStrikeRow.ltp) ? selectedStrikeRow.ltp.toFixed(2) : '--'}
                </div>
              </div>
              <div className="rounded border border-slate-800 bg-slate-950/60 px-2 py-1.5">
                <div className="text-[9px] font-semibold tracking-wide text-slate-500">IV CHG</div>
                <div className={`text-sm font-bold ${signedValueClass(selectedStrikeRow.ivChange)}`}>
                  {formatSignedValue(selectedStrikeRow.ivChange, 2)}
                </div>
              </div>
              <div className="rounded border border-slate-800 bg-slate-950/60 px-2 py-1.5">
                <div className="text-[9px] font-semibold tracking-wide text-slate-500">NET DELTA</div>
                <div className={`text-sm font-bold ${signedValueClass(selectedStrikeRow.netDelta ?? selectedStrikeRow.cDelta)}`}>
                  {formatSignedValue(selectedStrikeRow.netDelta ?? selectedStrikeRow.cDelta, 2)}
                </div>
              </div>
              <div className="rounded border border-slate-800 bg-slate-950/60 px-2 py-1.5">
                <div className="text-[9px] font-semibold tracking-wide text-slate-500">VOL SURGE</div>
                <div className={`text-sm ${volumeSurgeClass(selectedStrikeRow.volumeSurge)}`}>
                  {formatMultiplier(selectedStrikeRow.volumeSurge)}
                </div>
              </div>
            </div>
          ) : null}

          {/* Dynamic Pricing Section */}
          {selectedStrikeRow && selectedStrikeRow.dynamicPricing ? (
            <div className="mt-4 border-t border-slate-700 pt-3">
              <div className="mb-2 font-semibold text-slate-300 text-[11px]">DYNAMIC PRICING</div>
              <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
                <div className="rounded border border-slate-800 bg-slate-950/60 px-2 py-1.5">
                  <div className="text-[9px] font-semibold tracking-wide text-slate-500">BASE PREMIUM</div>
                  <div className="text-sm font-bold text-white">
                    {selectedStrikeRow.dynamicPricing.base_premium?.toFixed(2) || '--'}
                  </div>
                  <div className="text-[8px] text-slate-400">(CE + PE)</div>
                </div>
                <div className="rounded border border-slate-800 bg-slate-950/60 px-2 py-1.5">
                  <div className="text-[9px] font-semibold tracking-wide text-slate-500">DYNAMIC PREMIUM</div>
                  <div className={`text-sm font-bold ${(selectedStrikeRow.dynamicPricing.premium_adjustment_percent ?? 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {selectedStrikeRow.dynamicPricing.dynamic_premium?.toFixed(2) || '--'}
                  </div>
                  <div className="text-[8px] text-slate-400">
                    {(selectedStrikeRow.dynamicPricing.premium_adjustment_percent ?? 0) >= 0 ? '+' : ''}{selectedStrikeRow.dynamicPricing.premium_adjustment_percent?.toFixed(2)}%
                  </div>
                </div>
                <div className="rounded border border-slate-800 bg-slate-950/60 px-2 py-1.5">
                  <div className="text-[9px] font-semibold tracking-wide text-slate-500">ADJUSTMENT</div>
                  <div className="text-sm font-bold text-cyan-400">
                    {selectedStrikeRow.dynamicPricing.adjustment_factor?.toFixed(4) || '--'}
                  </div>
                  <div className="text-[8px] text-slate-400">
                    {selectedStrikeRow.dynamicPricing.premium_adjustment_points?.toFixed(2) || '0'} pts
                  </div>
                </div>
                <div className="rounded border border-slate-800 bg-slate-950/60 px-2 py-1.5">
                  <div className="text-[9px] font-semibold tracking-wide text-slate-500">CONFIDENCE</div>
                  <div className={`text-sm font-bold ${(selectedStrikeRow.dynamicPricing.adjustment_factor ?? 1) <= 1.01 && (selectedStrikeRow.dynamicPricing.adjustment_factor ?? 1) >= 0.99 ? 'text-yellow-400' : (selectedStrikeRow.dynamicPricing.adjustment_factor ?? 1) < 0.99 ? 'text-green-400' : 'text-orange-400'}`}>
                    {(selectedStrikeRow.dynamicPricing.adjustment_factor ?? 1) <= 1.01 && (selectedStrikeRow.dynamicPricing.adjustment_factor ?? 1) >= 0.99 ? 'NEUTRAL' : (selectedStrikeRow.dynamicPricing.adjustment_factor ?? 1) < 0.99 ? 'HIGH' : 'LOW'}
                  </div>
                </div>
              </div>

              {/* Indicator Adjustments Breakdown */}
              {selectedStrikeRow.dynamicPricing.adjustments && (
                <div className="mt-2 grid grid-cols-2 gap-2 md:grid-cols-5">
                  <div className="rounded border border-slate-700 bg-slate-900/40 px-2 py-1">
                    <div className="text-[8px] font-semibold text-slate-400">ROC Factor</div>
                    <div className="text-xs font-bold text-orange-300">
                      {selectedStrikeRow.dynamicPricing.adjustments.roc_factor?.toFixed(4)}
                    </div>
                    <div className="text-[7px] text-slate-500">
                      {((selectedStrikeRow.dynamicPricing.adjustments.roc_factor ?? 1 - 1) * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="rounded border border-slate-700 bg-slate-900/40 px-2 py-1">
                    <div className="text-[8px] font-semibold text-slate-400">RSI Factor</div>
                    <div className="text-xs font-bold text-blue-300">
                      {selectedStrikeRow.dynamicPricing.adjustments.rsi_factor?.toFixed(4)}
                    </div>
                    <div className="text-[7px] text-slate-500">
                      {((selectedStrikeRow.dynamicPricing.adjustments.rsi_factor ?? 1 - 1) * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="rounded border border-slate-700 bg-slate-900/40 px-2 py-1">
                    <div className="text-[8px] font-semibold text-slate-400">DI Factor</div>
                    <div className="text-xs font-bold text-purple-300">
                      {selectedStrikeRow.dynamicPricing.adjustments.di_factor?.toFixed(4)}
                    </div>
                    <div className="text-[7px] text-slate-500">
                      {((selectedStrikeRow.dynamicPricing.adjustments.di_factor ?? 1 - 1) * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="rounded border border-slate-700 bg-slate-900/40 px-2 py-1">
                    <div className="text-[8px] font-semibold text-slate-400">ADX Factor</div>
                    <div className="text-xs font-bold text-cyan-300">
                      {selectedStrikeRow.dynamicPricing.adjustments.adx_factor?.toFixed(4)}
                    </div>
                    <div className="text-[7px] text-slate-500">
                      {((selectedStrikeRow.dynamicPricing.adjustments.adx_factor ?? 1 - 1) * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="rounded border border-slate-700 bg-slate-900/40 px-2 py-1">
                    <div className="text-[8px] font-semibold text-slate-400">CHOP Factor</div>
                    <div className="text-xs font-bold text-green-300">
                      {selectedStrikeRow.dynamicPricing.adjustments.chop_factor?.toFixed(4)}
                    </div>
                    <div className="text-[7px] text-slate-500">
                      {((selectedStrikeRow.dynamicPricing.adjustments.chop_factor ?? 1 - 1) * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
};

export default StrikePricesTable;
