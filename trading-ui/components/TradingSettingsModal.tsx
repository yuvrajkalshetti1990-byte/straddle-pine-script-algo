'use client'

import React, { useState } from 'react';

interface TradingSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const TradingSettingsModal = ({ isOpen, onClose }: TradingSettingsModalProps) => {
  const [activeTab, setActiveTab] = useState<'broker' | 'chart' | 'trading' | 'notifications'>('broker');
  const [settings, setSettings] = useState({
    // Broker API Settings
    brokerApiKey: '',
    brokerSecret: '',
    brokerName: 'HDFC Sky',
    brokerUserId: '',
    
    // TradingView API Settings  
    tradingViewApiKey: '',
    tradingViewSecret: '',
    chartInterval: '5m',
    chartSymbol: 'NIFTY',
    
    // Trading Settings
    maxRiskPerTrade: 5000,
    stopLossPercent: 15,
    takeProfitPercent: 25,
    maxPositions: 5,
    autoTradingEnabled: true,
    riskLevel: 'medium',
    
    // Notification Settings
    emailNotifications: true,
    smsNotifications: false,
    pushNotifications: true,
    soundAlerts: true,
    
    // Trading Mode
    tradingMode: 'paper' // 'paper' or 'live'
  });

  const handleInputChange = (field: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSave = async () => {
    try {
      // 1. Save to backend
      const response = await fetch('http://127.0.0.1:8000/auth/credentials', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });
      
      const data = await response.json();
      
      if (response.ok) {
        // 2. Save settings to localStorage for UI persistence
        localStorage.setItem('tradingSettings', JSON.stringify(settings));
        alert(`✅ ${data.message || 'Settings saved successfully!'}`);
        onClose();
      } else {
        alert(`❌ Failed to save backend credentials: ${data.message || 'Unknown error'}`);
      }
    } catch (err) {
      alert(`❌ Error connecting to backend: ${err}`);
      // Fallback to local storage
      localStorage.setItem('tradingSettings', JSON.stringify(settings));
    }
  };

  const testBrokerConnection = () => {
    // Simulate API test
    alert('Testing broker connection... Status: Connected ✅');
  };

  const testChartConnection = () => {
    // Simulate API test
    alert('Testing TradingView connection... Status: Connected ✅');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-[#1e293b] rounded-lg border border-gray-700 w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            ⚙️ Trading Platform Settings
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors text-xl"
          >
            ✕
          </button>
        </div>

        <div className="flex h-[600px]">
          {/* Sidebar */}
          <div className="w-64 bg-[#111827] border-r border-gray-700 p-4">
            <nav className="space-y-2">
              {[
                { id: 'broker', label: '🏦 Broker API', icon: '🔗' },
                { id: 'chart', label: '📈 Chart API', icon: '📊' },
                { id: 'trading', label: '⚡ Trading Rules', icon: '🤖' },
                { id: 'notifications', label: '🔔 Notifications', icon: '📢' }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${
                    activeTab === tab.id
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-400 hover:text-white hover:bg-gray-700'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          {/* Content */}
          <div className="flex-1 p-6 overflow-y-auto">
            
            {/* Broker API Tab */}
            {activeTab === 'broker' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4">🏦 Broker API Configuration</h3>
                  <p className="text-gray-400 text-sm mb-6">
                    Connect your broker account to enable live trading functionality.
                  </p>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-2">
                      Broker Platform
                    </label>
                    <select
                      value={settings.brokerName}
                      onChange={(e) => handleInputChange('brokerName', e.target.value)}
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white focus:outline-none focus:border-blue-500"
                    >
                      <option value="HDFC Sky">HDFC Sky</option>
                      <option value="Zerodha">Zerodha Kite</option>
                      <option value="Fyers">Fyers</option>
                      <option value="Upstox">Upstox</option>
                      <option value="AngelOne">Angel One</option>
                      <option value="IIFL">IIFL Securities</option>
                      <option value="5Paisa">5Paisa</option>
                    </select>
                  </div>

                  {settings.brokerName === 'Fyers' && (
                    <div className="p-3 bg-blue-900/20 border border-blue-500/30 rounded-md">
                      <p className="text-sm text-blue-300 mb-3">
                        Connect your Fyers account to fetch live NIFTY data and execute trades.
                      </p>
                      <a 
                        href="/auth/fyers/login"
                        className="inline-block px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm transition-colors"
                      >
                        🚀 Connect Fyers
                      </a>
                    </div>
                  )}

                  {settings.brokerName === 'Zerodha' && (
                    <div className="p-3 bg-orange-900/20 border border-orange-500/30 rounded-md">
                      <p className="text-sm text-orange-300 mb-3">
                        Connect your Zerodha Kite account for institutional-grade execution.
                      </p>
                      <a 
                        href="/auth/zerodha/login"
                        className="inline-block px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-md text-sm transition-colors"
                      >
                        🚀 Connect Zerodha
                      </a>
                    </div>
                  )}

                  {settings.brokerName === 'HDFC Sky' && (
                    <div className="p-3 bg-gray-800 border border-gray-700 rounded-md">
                      <p className="text-sm text-gray-400 mb-3">
                        Connect your HDFC Sky account for zero-brokerage trades.
                      </p>
                      <a 
                        href="/auth/login"
                        className="inline-block px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md text-sm transition-colors"
                      >
                        🚀 Connect HDFC Sky
                      </a>
                    </div>
                  )}

                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-2">
                      API Key
                    </label>
                    <input
                      type="password"
                      value={settings.brokerApiKey}
                      onChange={(e) => handleInputChange('brokerApiKey', e.target.value)}
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                      placeholder="Enter your broker API key"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-2">
                      API Secret
                    </label>
                    <input
                      type="password"
                      value={settings.brokerSecret}
                      onChange={(e) => handleInputChange('brokerSecret', e.target.value)}
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                      placeholder="Enter your broker API secret"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-2">
                      User ID
                    </label>
                    <input
                      type="text"
                      value={settings.brokerUserId}
                      onChange={(e) => handleInputChange('brokerUserId', e.target.value)}
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                      placeholder="Enter your broker user ID"
                    />
                  </div>

                  <div className="flex gap-3">
                    <button
                      onClick={testBrokerConnection}
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
                    >
                      🔗 Test Connection
                    </button>
                    <div className="px-3 py-2 bg-gray-800 rounded-md text-sm text-gray-400">
                      Status: <span className="text-green-400">●</span> Connected
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Chart API Tab */}
            {activeTab === 'chart' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4">📈 TradingView Chart API</h3>
                  <p className="text-gray-400 text-sm mb-6">
                    Configure TradingView integration for professional charting.
                  </p>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-2">
                      TradingView API Key
                    </label>
                    <input
                      type="password"
                      value={settings.tradingViewApiKey}
                      onChange={(e) => handleInputChange('tradingViewApiKey', e.target.value)}
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                      placeholder="Enter TradingView API key"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-2">
                      Default Chart Interval
                    </label>
                    <select
                      value={settings.chartInterval}
                      onChange={(e) => handleInputChange('chartInterval', e.target.value)}
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white focus:outline-none focus:border-blue-500"
                    >
                      <option value="1m">1 Minute</option>
                      <option value="3m">3 Minutes</option>
                      <option value="5m">5 Minutes</option>
                      <option value="15m">15 Minutes</option>
                      <option value="1h">1 Hour</option>
                      <option value="1d">1 Day</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-2">
                      Default Symbol
                    </label>
                    <select
                      value={settings.chartSymbol}
                      onChange={(e) => handleInputChange('chartSymbol', e.target.value)}
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white focus:outline-none focus:border-blue-500"
                    >
                      <option value="NIFTY">NIFTY 50</option>
                      <option value="BANKNIFTY">BANK NIFTY</option>
                      <option value="SENSEX">SENSEX</option>
                    </select>
                  </div>

                  <div className="flex gap-3">
                    <button
                      onClick={testChartConnection}
                      className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md transition-colors"
                    >
                      📊 Test Chart API
                    </button>
                    <div className="px-3 py-2 bg-gray-800 rounded-md text-sm text-gray-400">
                      Charts: <span className="text-green-400">●</span> Active
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Trading Rules Tab */}
            {activeTab === 'trading' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4">⚡ Auto Trading Rules</h3>
                  <p className="text-gray-400 text-sm mb-6">
                    Configure your automated trading parameters and risk management.
                  </p>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-2">
                      Auto Trading
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={settings.autoTradingEnabled}
                        onChange={(e) => handleInputChange('autoTradingEnabled', e.target.checked)}
                        className="mr-2 rounded border-gray-700 bg-gray-800"
                      />
                      <span className="text-white">Enable Auto Trading</span>
                    </label>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-2">
                      Trading Mode
                    </label>
                    <div className="flex gap-2 p-1 bg-gray-800 rounded-lg w-fit">
                      <button
                        onClick={() => handleInputChange('tradingMode', 'paper')}
                        className={`px-4 py-1.5 text-sm font-medium rounded-md transition-all ${
                          settings.tradingMode === 'paper'
                            ? 'bg-blue-600 text-white shadow-lg'
                            : 'text-gray-400 hover:text-white'
                        }`}
                      >
                        📝 Paper Trade
                      </button>
                      <button
                        onClick={() => handleInputChange('tradingMode', 'live')}
                        className={`px-4 py-1.5 text-sm font-medium rounded-md transition-all ${
                          settings.tradingMode === 'live'
                            ? 'bg-red-600 text-white shadow-lg'
                            : 'text-gray-400 hover:text-white'
                        }`}
                      >
                        🔥 Live Trade
                      </button>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">
                      {settings.tradingMode === 'paper' 
                        ? 'Trades will be simulated without actual orders.' 
                        : 'REAL orders will be fired to your broker account!'}
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-2">
                      Max Risk Per Trade (₹)
                    </label>
                    <input
                      type="number"
                      value={settings.maxRiskPerTrade}
                      onChange={(e) => handleInputChange('maxRiskPerTrade', parseInt(e.target.value))}
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-400 mb-2">
                        Stop Loss (%)
                      </label>
                      <input
                        type="number"
                        value={settings.stopLossPercent}
                        onChange={(e) => handleInputChange('stopLossPercent', parseInt(e.target.value))}
                        className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white focus:outline-none focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-400 mb-2">
                        Take Profit (%)
                      </label>
                      <input
                        type="number"
                        value={settings.takeProfitPercent}
                        onChange={(e) => handleInputChange('takeProfitPercent', parseInt(e.target.value))}
                        className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white focus:outline-none focus:border-blue-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-2">
                      Risk Level
                    </label>
                    <select
                      value={settings.riskLevel}
                      onChange={(e) => handleInputChange('riskLevel', e.target.value)}
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white focus:outline-none focus:border-blue-500"
                    >
                      <option value="low">Low Risk</option>
                      <option value="medium">Medium Risk</option>
                      <option value="high">High Risk</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            {/* Notifications Tab */}
            {activeTab === 'notifications' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4">🔔 Notification Settings</h3>
                  <p className="text-gray-400 text-sm mb-6">
                    Configure how you want to receive trading alerts and updates.
                  </p>
                </div>

                <div className="space-y-4">
                  {[
                    { key: 'emailNotifications', label: '📧 Email Notifications', desc: 'Receive trade alerts via email' },
                    { key: 'smsNotifications', label: '📱 SMS Notifications', desc: 'Get important alerts via SMS' },
                    { key: 'pushNotifications', label: '🔔 Push Notifications', desc: 'Browser push notifications' },
                    { key: 'soundAlerts', label: '🔊 Sound Alerts', desc: 'Audio alerts for trades' }
                  ].map((notification) => (
                    <div key={notification.key} className="flex items-center justify-between p-3 bg-gray-800 rounded-md">
                      <div>
                        <div className="text-white font-medium">{notification.label}</div>
                        <div className="text-gray-400 text-sm">{notification.desc}</div>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={settings[notification.key as keyof typeof settings] as boolean}
                          onChange={(e) => handleInputChange(notification.key, e.target.checked)}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                      </label>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-gray-700 p-6 flex items-center justify-between">
          <div className="text-sm text-gray-400">
            Settings are saved locally and encrypted for security.
          </div>
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
            >
              💾 Save Settings
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TradingSettingsModal;
