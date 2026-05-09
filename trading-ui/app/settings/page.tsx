
'use client';
import { useState } from "react";

interface StrikeRow {
  id: number;
  enabled: boolean;
  chart: boolean;
  index: boolean;
  price: string;
  isATM: boolean;
}

export default function Settings() {
  // Setup - Index & Time
  const [indexSelection, setIndexSelection] = useState("NIFTY");
  const [expiryDD, setExpiryDD] = useState("13");
  const [expiryMM, setExpiryMM] = useState("01");
  const [expiryYY, setExpiryYY] = useState("26");
  const [startDD, setStartDD] = useState("30");
  const [startMM, setStartMM] = useState("12");
  const [startYY, setStartYY] = useState("2025");
  const [endDD, setEndDD] = useState("31");
  const [endMM, setEndMM] = useState("12");
  const [endYY, setEndYY] = useState("2099");

  // Strike Selection
  const [strikes, setStrikes] = useState<StrikeRow[]>([
    { id: 1, enabled: false, chart: false, index: true, price: "25700", isATM: false },
    { id: 2, enabled: true, chart: false, index: true, price: "25800", isATM: false },
    { id: 3, enabled: true, chart: false, index: true, price: "25850", isATM: true },
    { id: 4, enabled: true, chart: true, index: true, price: "25900", isATM: false },
    { id: 5, enabled: false, chart: false, index: true, price: "26100", isATM: false },
  ]);

  // Strategy Tag Section
  const [strategyTag, setStrategyTag] = useState("DefaultStrategy");
  
  // Capital Section  
  const [totalCapital, setTotalCapital] = useState("500000");
  const [maxRiskPercent, setMaxRiskPercent] = useState("2");
  const [dailyLossLimit, setDailyLossLimit] = useState("10000");

  // Logic Settings
  const [calcMode, setCalcMode] = useState("Auto");
  const [filterChop, setFilterChop] = useState(true);
  const [chopValue, setChopValue] = useState("61.8");
  const [breakdownWindow, setBreakdownWindow] = useState("0");
  const [useMomentum, setUseMomentum] = useState(true);
  const [useTrend, setUseTrend] = useState(false);
  const [useVWAPRev, setUseVWAPRev] = useState(false);
  const [minRevSize, setMinRevSize] = useState("5");
  const [restrictVWAPScope, setRestrictVWAPScope] = useState(false);
  const [vwapScopes, setVWAPScopes] = useState({
    S1: false, S2: false, S3: false, S4: false, S5: false
  });

  // Short Strategy
  const [enableShort, setEnableShort] = useState(true);
  const [shortLots, setShortLots] = useState("2");
  const [maxShortTrades, setMaxShortTrades] = useState("0");
  const [shortStartTime, setShortStartTime] = useState("09:15");
  const [shortIgnoreLogic, setShortIgnoreLogic] = useState(false);
  const [shortScopes, setShortScopes] = useState({
    S1: false, S2: true, S3: true, S4: true, S5: false
  });
  const [shortTimeExitH, setShortTimeExitH] = useState("14");
  const [shortTimeExitM, setShortTimeExitM] = useState("30");
  const [shortFixedSL, setShortFixedSL] = useState("0");
  const [shortFixedTGT, setShortFixedTGT] = useState("0");
  const [shortSmartSL, setShortSmartSL] = useState(true);
  const [shortSmartSLPts, setShortSmartSLPts] = useState("10");
  const [shortTrailingSL, setShortTrailingSL] = useState(false);
  const [shortTrailAct, setShortTrailAct] = useState("20");
  const [shortTrailDist, setShortTrailDist] = useState("10");

  // Long Strategy
  const [enableLong, setEnableLong] = useState(true);
  const [longLots, setLongLots] = useState("6");
  const [maxLongTrades, setMaxLongTrades] = useState("1");
  const [longStartTime, setLongStartTime] = useState("09:30");
  const [longIgnoreLogic, setLongIgnoreLogic] = useState(false);
  const [longADX, setLongADX] = useState("25");
  const [strictEntry, setStrictEntry] = useState(true);
  const [longTimeExitH, setLongTimeExitH] = useState("15");
  const [longTimeExitM, setLongTimeExitM] = useState("10");
  const [longScopes, setLongScopes] = useState({
    S1: false, S2: true, S3: false, S4: true, S5: false
  });
  const [longFixedSL, setLongFixedSL] = useState("0");
  const [longFixedTGT, setLongFixedTGT] = useState("0");
  const [longTrailingSL, setLongTrailingSL] = useState(false);
  const [longTrailAct, setLongTrailAct] = useState("15");
  const [longTrailDist, setLongTrailDist] = useState("10");

  // Visuals
  const [mainTable, setMainTable] = useState("Hide");
  const [pnlTable, setPnlTable] = useState("Bottom");
  const [showRegime, setShowRegime] = useState(true);
  const [showIndReg, setShowIndReg] = useState(true);
  const [showTMode, setShowTMode] = useState(true);
  const [showTType, setShowTType] = useState(true);
  const [showSuperTrend, setShowSuperTrend] = useState(false);
  const [superTrendFac, setSuperTrendFac] = useState("3");
  const [superTrendPer, setSuperTrendPer] = useState("10");
  const [showEMA20, setShowEMA20] = useState(true);
  const [showVWAP, setShowVWAP] = useState(true);
  const [showVWMA, setShowVWMA] = useState(true);
  const [vwmaLen, setVWMALen] = useState("35");

  const updateStrike = (id: number, field: keyof StrikeRow, value: any) => {
    setStrikes(prev => prev.map(strike => 
      strike.id === id ? { ...strike, [field]: value } : strike
    ));
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 overflow-y-auto">
      <div className="container mx-auto p-6 max-w-7xl">
        <h1 className="text-2xl font-bold mb-8 text-center">Trading Strategy Settings</h1>
        
        {/* Two-column layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Left Column */}
          <div className="space-y-6">
            
            {/* Section 1: Setup - Index & Time */}
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
              <h2 className="text-lg font-semibold mb-4 text-gray-100">Setup - Index & Time</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Index Selection</label>
                  <select 
                    value={indexSelection} 
                    onChange={(e) => setIndexSelection(e.target.value)}
                    className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="NIFTY">NIFTY</option>
                    <option value="BANKNIFTY">BANKNIFTY</option>
                    <option value="FINNIFTY">FINNIFTY</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Expiry Date</label>
                  <div className="flex space-x-2">
                    <input type="text" placeholder="DD" value={expiryDD} onChange={(e) => setExpiryDD(e.target.value)} className="flex-1 bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500" />
                    <span className="text-gray-400 self-center">-</span>
                    <input type="text" placeholder="MM" value={expiryMM} onChange={(e) => setExpiryMM(e.target.value)} className="flex-1 bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500" />
                    <span className="text-gray-400 self-center">-</span>
                    <input type="text" placeholder="YY" value={expiryYY} onChange={(e) => setExpiryYY(e.target.value)} className="flex-1 bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Start Date</label>
                  <div className="flex space-x-2">
                    <input type="text" placeholder="DD" value={startDD} onChange={(e) => setStartDD(e.target.value)} className="flex-1 bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500" />
                    <span className="text-gray-400 self-center">-</span>
                    <input type="text" placeholder="MM" value={startMM} onChange={(e) => setStartMM(e.target.value)} className="flex-1 bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500" />
                    <span className="text-gray-400 self-center">-</span>
                    <input type="text" placeholder="YY" value={startYY} onChange={(e) => setStartYY(e.target.value)} className="flex-1 bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">End Date</label>
                  <div className="flex space-x-2">
                    <input type="text" placeholder="DD" value={endDD} onChange={(e) => setEndDD(e.target.value)} className="flex-1 bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500" />
                    <span className="text-gray-400 self-center">-</span>
                    <input type="text" placeholder="MM" value={endMM} onChange={(e) => setEndMM(e.target.value)} className="flex-1 bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500" />
                    <span className="text-gray-400 self-center">-</span>
                    <input type="text" placeholder="YY" value={endYY} onChange={(e) => setEndYY(e.target.value)} className="flex-1 bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>
                </div>
              </div>
            </div>

            {/* Section 2: Strike Selection */}
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
              <h2 className="text-lg font-semibold mb-4 text-gray-100">Strike Selection (Master)</h2>
              
              <div className="space-y-3">
                {strikes.map((strike) => (
                  <div key={strike.id} className="flex items-center space-x-3 p-3 bg-gray-700 rounded-md">
                    <label className="flex items-center space-x-2">
                      <input 
                        type="checkbox" 
                        checked={strike.enabled}
                        onChange={(e) => updateStrike(strike.id, 'enabled', e.target.checked)}
                        className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500" 
                      />
                      <span className="text-sm text-gray-300">En</span>
                    </label>
                    
                    <label className="flex items-center space-x-2">
                      <input 
                        type="checkbox" 
                        checked={strike.chart}
                        onChange={(e) => updateStrike(strike.id, 'chart', e.target.checked)}
                        className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500" 
                      />
                      <span className="text-sm text-gray-300">Chart</span>
                    </label>
                    
                    <label className="flex items-center space-x-2">
                      <input 
                        type="checkbox" 
                        checked={strike.index}
                        onChange={(e) => updateStrike(strike.id, 'index', e.target.checked)}
                        className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500" 
                      />
                      <span className="text-sm text-gray-300">Ind</span>
                    </label>
                    
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-300">Strike {strike.id} {strike.isATM ? '(ATM)' : ''}</span>
                      <input 
                        type="text" 
                        value={strike.price}
                        onChange={(e) => updateStrike(strike.id, 'price', e.target.value)}
                        className="w-20 bg-gray-600 border border-gray-500 rounded px-2 py-1 text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" 
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Section 3: Strategy Tag */}
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
              <h2 className="text-lg font-semibold mb-4 text-gray-100">Strategy Tag</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Strategy Name</label>
                  <input 
                    type="text" 
                    value={strategyTag}
                    onChange={(e) => setStrategyTag(e.target.value)}
                    className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500" 
                    placeholder="Enter strategy name"
                  />
                </div>
              </div>
            </div>

            {/* Section 4: Capital */}
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
              <h2 className="text-lg font-semibold mb-4 text-gray-100">Capital Management</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Total Capital</label>
                  <input 
                    type="text" 
                    value={totalCapital}
                    onChange={(e) => setTotalCapital(e.target.value)}
                    className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500" 
                    placeholder="500000"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Max Risk %</label>
                  <input 
                    type="text" 
                    value={maxRiskPercent}
                    onChange={(e) => setMaxRiskPercent(e.target.value)}
                    className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500" 
                    placeholder="2"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Daily Loss Limit</label>
                  <input 
                    type="text" 
                    value={dailyLossLimit}
                    onChange={(e) => setDailyLossLimit(e.target.value)}
                    className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500" 
                    placeholder="10000"
                  />
                </div>
              </div>
            </div>

            {/* Section 5: Logic Settings */}
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
              <h2 className="text-lg font-semibold mb-4 text-gray-100">Logic Settings</h2>
              
              <div className="space-y-4">
                <div className="flex items-center space-x-4">
                  <div className="flex-1">
                    <label className="block text-sm font-medium text-gray-300 mb-2">Calc Mode</label>
                    <select 
                      value={calcMode} 
                      onChange={(e) => setCalcMode(e.target.value)}
                      className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="Auto">Auto</option>
                      <option value="Manual">Manual</option>
                    </select>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <input 
                      type="checkbox" 
                      id="filterChop"
                      checked={filterChop}
                      onChange={(e) => setFilterChop(e.target.checked)}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500" 
                    />
                    <label htmlFor="filterChop" className="text-sm text-gray-300">Filter Chop &gt;</label>
                    <input 
                      type="text" 
                      value={chopValue}
                      onChange={(e) => setChopValue(e.target.value)}
                      className="w-16 bg-gray-700 border border-gray-600 rounded px-2 py-1 text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" 
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Breakdown Window</label>
                  <input 
                    type="text" 
                    value={breakdownWindow}
                    onChange={(e) => setBreakdownWindow(e.target.value)}
                    className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500" 
                  />
                </div>

                <div className="flex space-x-6">
                  <label className="flex items-center space-x-2">
                    <input 
                      type="checkbox" 
                      checked={useMomentum}
                      onChange={(e) => setUseMomentum(e.target.checked)}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500" 
                    />
                    <span className="text-sm text-gray-300">Use Momentum</span>
                  </label>
                  
                  <label className="flex items-center space-x-2">
                    <input 
                      type="checkbox" 
                      checked={useTrend}
                      onChange={(e) => setUseTrend(e.target.checked)}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500" 
                    />
                    <span className="text-sm text-gray-300">Use Trend</span>
                  </label>
                  
                  <label className="flex items-center space-x-2">
                    <input 
                      type="checkbox" 
                      checked={useVWAPRev}
                      onChange={(e) => setUseVWAPRev(e.target.checked)}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500" 
                    />
                    <span className="text-sm text-gray-300">Use VWAP Rev</span>
                  </label>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Min Rev Size</label>
                  <input 
                    type="text" 
                    value={minRevSize}
                    onChange={(e) => setMinRevSize(e.target.value)}
                    className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500" 
                  />
                </div>

                <div>
                  <label className="flex items-center space-x-2 mb-2">
                    <input 
                      type="checkbox" 
                      checked={restrictVWAPScope}
                      onChange={(e) => setRestrictVWAPScope(e.target.checked)}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500" 
                    />
                    <span className="text-sm text-gray-300">Restrict VWAP Scope?</span>
                  </label>
                  
                  {restrictVWAPScope && (
                    <div className="flex space-x-4 ml-6">
                      {Object.entries(vwapScopes).map(([key, value]) => (
                        <label key={key} className="flex items-center space-x-1">
                          <input 
                            type="checkbox" 
                            checked={value}
                            onChange={(e) => setVWAPScopes(prev => ({ ...prev, [key]: e.target.checked }))}
                            className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500" 
                          />
                          <span className="text-sm text-gray-300">{key}</span>
                        </label>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Right Column */}
          <div className="space-y-6">
            
            {/* Section 6: Short Strategy */}
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
              <h2 className="text-lg font-semibold mb-4 text-gray-100">Short Strategy</h2>
              
              <div className="space-y-4">
                <div className="flex items-center space-x-4">
                  <label className="flex items-center space-x-2">
                    <input 
                      type="checkbox" 
                      checked={enableShort}
                      onChange={(e) => setEnableShort(e.target.checked)}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500" 
                    />
                    <span className="text-sm text-gray-300">Enable Short</span>
                  </label>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">Lots</label>
                    <input 
                      type="text" 
                      value={shortLots}
                      onChange={(e) => setShortLots(e.target.value)}
                      className="w-16 bg-gray-700 border border-gray-600 rounded px-2 py-1 text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" 
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Start Time</label>
                  <input 
                    type="text" 
                    value={shortStartTime}
                    onChange={(e) => setShortStartTime(e.target.value)}
                    className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500" 
                    placeholder="09:15"
                  />
                </div>

                <label className="flex items-center space-x-2">
                  <input 
                    type="checkbox" 
                    checked={shortIgnoreLogic}
                    onChange={(e) => setShortIgnoreLogic(e.target.checked)}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500" 
                  />
                  <span className="text-sm text-gray-300">Ignore Logic - Consider start time instead</span>
                </label>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Max Short Trades (0=Unl.)</label>
                  <input 
                    type="text" 
                    value={maxShortTrades}
                    onChange={(e) => setMaxShortTrades(e.target.value)}
                    className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500" 
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Restrict Scope?</label>
                  <div className="flex space-x-4">
                    {Object.entries(shortScopes).map(([key, value]) => (
                      <label key={key} className="flex items-center space-x-1">
                        <input 
                          type="checkbox" 
                          checked={value}
                          onChange={(e) => setShortScopes(prev => ({ ...prev, [key]: e.target.checked }))}
                          className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500" 
                        />
                        <span className="text-sm text-gray-300">{key}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  <span className="text-sm text-gray-300">Time Exit?</span>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-300">H</span>
                    <input 
                      type="text" 
                      value={shortTimeExitH}
                      onChange={(e) => setShortTimeExitH(e.target.value)}
                      className="w-12 bg-gray-700 border border-gray-600 rounded px-2 py-1 text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" 
                    />
                    <span className="text-sm text-gray-300">M</span>
                    <input 
                      type="text" 
                      value={shortTimeExitM}
                      onChange={(e) => setShortTimeExitM(e.target.value)}
                      className="w-12 bg-gray-700 border border-gray-600 rounded px-2 py-1 text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" 
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Fixed SL</label>
                    <input 
                      type="text" 
                      value={shortFixedSL}
                      onChange={(e) => setShortFixedSL(e.target.value)}
                      className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500" 
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Fixed TGT</label>
                    <input 
                      type="text" 
                      value={shortFixedTGT}
                      onChange={(e) => setShortFixedTGT(e.target.value)}
                      className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500" 
                    />
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  <label className="flex items-center space-x-2">
                    <input 
                      type="checkbox" 
                      checked={shortSmartSL}
                      onChange={(e) => setShortSmartSL(e.target.checked)}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500" 
                    />
                    <span className="text-sm text-gray-300">Smart SL Disable &gt; Pts</span>
                  </label>
                  <input 
                    type="text" 
                    value={shortSmartSLPts}
                    onChange={(e) => setShortSmartSLPts(e.target.value)}
                    className="w-16 bg-gray-700 border border-gray-600 rounded px-2 py-1 text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" 
                  />
                </div>

                <div className="flex items-center space-x-4">
                  <label className="flex items-center space-x-2">
                    <input 
                      type="checkbox" 
                      checked={shortTrailingSL}
                      onChange={(e) => setShortTrailingSL(e.target.checked)}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500" 
                    />
                    <span className="text-sm text-gray-300">Trailing SL | Act:</span>
                  </label>
                  <input 
                    type="text" 
                    value={shortTrailAct}
                    onChange={(e) => setShortTrailAct(e.target.value)}
                    className="w-12 bg-gray-700 border border-gray-600 rounded px-2 py-1 text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" 
                  />
                  <span className="text-sm text-gray-300">| Dist:</span>
                  <input 
                    type="text" 
                    value={shortTrailDist}
                    onChange={(e) => setShortTrailDist(e.target.value)}
                    className="w-12 bg-gray-700 border border-gray-600 rounded px-2 py-1 text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" 
                  />
                </div>
              </div>
            </div>

            {/* Section 7: Long Strategy */}
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
              <h2 className="text-lg font-semibold mb-4 text-gray-100">Long Strategy</h2>
              
              <div className="space-y-4">
                <div className="flex items-center space-x-4">
                  <label className="flex items-center space-x-2">
                    <input 
                      type="checkbox" 
                      checked={enableLong}
                      onChange={(e) => setEnableLong(e.target.checked)}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500" 
                    />
                    <span className="text-sm text-gray-300">Enable Long</span>
                  </label>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">Lots</label>
                    <input 
                      type="text" 
                      value={longLots}
                      onChange={(e) => setLongLots(e.target.value)}
                      className="w-16 bg-gray-700 border border-gray-600 rounded px-2 py-1 text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" 
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Max Long Trades (0=Unl.)</label>
                  <input 
                    type="text" 
                    value={maxLongTrades}
                    onChange={(e) => setMaxLongTrades(e.target.value)}
                    className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500" 
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Long Start Time</label>
                  <input 
                    type="text" 
                    value={longStartTime}
                    onChange={(e) => setLongStartTime(e.target.value)}
                    className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500" 
                  />
                </div>

                <label className="flex items-center space-x-2">
                  <input 
                    type="checkbox" 
                    checked={longIgnoreLogic}
                    onChange={(e) => setLongIgnoreLogic(e.target.checked)}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500" 
                  />
                  <span className="text-sm text-gray-300">Ignore Logic - Consider start time instead</span>
                </label>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">ADX</label>
                  <input 
                    type="text" 
                    value={longADX}
                    onChange={(e) => setLongADX(e.target.value)}
                    className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500" 
                  />
                </div>

                <label className="flex items-center space-x-2">
                  <input 
                    type="checkbox" 
                    checked={strictEntry}
                    onChange={(e) => setStrictEntry(e.target.checked)}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500" 
                  />
                  <span className="text-sm text-gray-300">Strict Entry</span>
                </label>

                <div className="flex items-center space-x-4">
                  <span className="text-sm text-gray-300">Time Exit?</span>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-300">H</span>
                    <input 
                      type="text" 
                      value={longTimeExitH}
                      onChange={(e) => setLongTimeExitH(e.target.value)}
                      className="w-12 bg-gray-700 border border-gray-600 rounded px-2 py-1 text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" 
                    />
                    <span className="text-sm text-gray-300">M</span>
                    <input 
                      type="text" 
                      value={longTimeExitM}
                      onChange={(e) => setLongTimeExitM(e.target.value)}
                      className="w-12 bg-gray-700 border border-gray-600 rounded px-2 py-1 text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" 
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Restrict Scope?</label>
                  <div className="flex space-x-4">
                    {Object.entries(longScopes).map(([key, value]) => (
                      <label key={key} className="flex items-center space-x-1">
                        <input 
                          type="checkbox" 
                          checked={value}
                          onChange={(e) => setLongScopes(prev => ({ ...prev, [key]: e.target.checked }))}
                          className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500" 
                        />
                        <span className="text-sm text-gray-300">{key}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Fixed SL</label>
                    <input 
                      type="text" 
                      value={longFixedSL}
                      onChange={(e) => setLongFixedSL(e.target.value)}
                      className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500" 
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Fixed TGT</label>
                    <input 
                      type="text" 
                      value={longFixedTGT}
                      onChange={(e) => setLongFixedTGT(e.target.value)}
                      className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500" 
                    />
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  <label className="flex items-center space-x-2">
                    <input 
                      type="checkbox" 
                      checked={longTrailingSL}
                      onChange={(e) => setLongTrailingSL(e.target.checked)}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500" 
                    />
                    <span className="text-sm text-gray-300">Trailing SL | Act:</span>
                  </label>
                  <input 
                    type="text" 
                    value={longTrailAct}
                    onChange={(e) => setLongTrailAct(e.target.value)}
                    className="w-12 bg-gray-700 border border-gray-600 rounded px-2 py-1 text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" 
                  />
                  <span className="text-sm text-gray-300">| Dist:</span>
                  <input 
                    type="text" 
                    value={longTrailDist}
                    onChange={(e) => setLongTrailDist(e.target.value)}
                    className="w-12 bg-gray-700 border border-gray-600 rounded px-2 py-1 text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" 
                  />
                </div>
              </div>
            </div>

            {/* Section 8: Visuals */}
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
              <h2 className="text-lg font-semibold mb-4 text-gray-100">Visuals</h2>
              
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Main Table</label>
                    <select 
                      value={mainTable} 
                      onChange={(e) => setMainTable(e.target.value)}
                      className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="Hide">Hide</option>
                      <option value="Show">Show</option>
                      <option value="Top">Top</option>
                      <option value="Bottom">Bottom</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">P&L Table</label>
                    <select 
                      value={pnlTable} 
                      onChange={(e) => setPnlTable(e.target.value)}
                      className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="Hide">Hide</option>
                      <option value="Top">Top</option>
                      <option value="Bottom">Bottom</option>
                      <option value="Left">Left</option>
                      <option value="Right">Right</option>
                    </select>
                  </div>
                </div>

                {/* Display Options */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Display Options</label>
                  <div className="grid grid-cols-2 gap-4">
                    <label className="flex items-center space-x-2">
                      <input 
                        type="checkbox" 
                        checked={showRegime}
                        onChange={(e) => setShowRegime(e.target.checked)}
                        className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500" 
                      />
                      <span className="text-sm text-gray-300">Regime</span>
                    </label>
                    
                    <label className="flex items-center space-x-2">
                      <input 
                        type="checkbox" 
                        checked={showIndReg}
                        onChange={(e) => setShowIndReg(e.target.checked)}
                        className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500" 
                      />
                      <span className="text-sm text-gray-300">Ind.Reg</span>
                    </label>
                    
                    <label className="flex items-center space-x-2">
                      <input 
                        type="checkbox" 
                        checked={showTMode}
                        onChange={(e) => setShowTMode(e.target.checked)}
                        className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500" 
                      />
                      <span className="text-sm text-gray-300">T.mode</span>
                    </label>
                    
                    <label className="flex items-center space-x-2">
                      <input 
                        type="checkbox" 
                        checked={showTType}
                        onChange={(e) => setShowTType(e.target.checked)}
                        className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500" 
                      />
                      <span className="text-sm text-gray-300">T.type</span>
                    </label>
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  <label className="flex items-center space-x-2">
                    <input 
                      type="checkbox" 
                      checked={showSuperTrend}
                      onChange={(e) => setShowSuperTrend(e.target.checked)}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500" 
                    />
                    <span className="text-sm text-gray-300">SuperTrend Fac</span>
                  </label>
                  <input 
                    type="text" 
                    value={superTrendFac}
                    onChange={(e) => setSuperTrendFac(e.target.value)}
                    className="w-12 bg-gray-700 border border-gray-600 rounded px-2 py-1 text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" 
                  />
                  <span className="text-sm text-gray-300">Per</span>
                  <input 
                    type="text" 
                    value={superTrendPer}
                    onChange={(e) => setSuperTrendPer(e.target.value)}
                    className="w-12 bg-gray-700 border border-gray-600 rounded px-2 py-1 text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" 
                  />
                </div>

                <div className="flex items-center space-x-6">
                  <label className="flex items-center space-x-2">
                    <input 
                      type="checkbox" 
                      checked={showEMA20}
                      onChange={(e) => setShowEMA20(e.target.checked)}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500" 
                    />
                    <span className="text-sm text-gray-300">EMA(20)</span>
                  </label>
                  
                  <label className="flex items-center space-x-2">
                    <input 
                      type="checkbox" 
                      checked={showVWAP}
                      onChange={(e) => setShowVWAP(e.target.checked)}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500" 
                    />
                    <span className="text-sm text-gray-300">VWAP</span>
                  </label>
                  
                  <label className="flex items-center space-x-2">
                    <input 
                      type="checkbox" 
                      checked={showVWMA}
                      onChange={(e) => setShowVWMA(e.target.checked)}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500" 
                    />
                    <span className="text-sm text-gray-300">VWMA Len</span>
                  </label>
                  <input 
                    type="text" 
                    value={vwmaLen}
                    onChange={(e) => setVWMALen(e.target.value)}
                    className="w-12 bg-gray-700 border border-gray-600 rounded px-2 py-1 text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" 
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="mt-8 text-center">
          <button 
            onClick={() => {
              // Handle save logic here
              alert('Settings saved successfully!');
            }}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Save Settings
          </button>
        </div>
      </div>
    </div>
  );
}
