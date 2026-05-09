'use client'

import React, { useState, useEffect } from "react";
import { Menu, Settings, X, User, MoreVertical } from "lucide-react";
import AITradingChat from '../AITradingChat';

interface User {
  id: number;
  firstName: string;
  lastName: string;
  email: string;
  plan: string;
  avatar?: string;
}

interface NavbarProps {
  onSettingsClick: () => void;
  onMobileMenuToggle: () => void;
  isMobileMenuOpen: boolean;
  isSidebarVisible: boolean;
  onSidebarToggle: () => void;
  user?: User;
  onLogin: () => void;
  onLogout: () => void;
}

const Navbar: React.FC<NavbarProps> = ({ 
  onSettingsClick, 
  onMobileMenuToggle, 
  isMobileMenuOpen,
  isSidebarVisible,
  onSidebarToggle,
  user,
  onLogin,
  onLogout
}) => {
  const [showUserDropdown, setShowUserDropdown] = useState(false);
  const [showAIChat, setShowAIChat] = useState(false);
  const [niftyPrice, setNiftyPrice] = useState<number | null>(null);
  const [niftyChange, setNiftyChange] = useState<number | null>(null);
  const [connected, setConnected] = useState(false);
  const [broker, setBroker] = useState<string | null>(null);
  const [tradingMode, setTradingMode] = useState<'paper' | 'live'>('paper');
  const [lastUpdated, setLastUpdated] = useState<string>('');

  // Fetch NIFTY price on component mount and set up interval
  useEffect(() => {
    const fetchNiftyPrice = async () => {
      try {
        const response = await fetch('/api/market/nifty-price');
        const result = await response.json();
        
        if (result.status === 'success' && result.data?.price) {
          setNiftyPrice(result.data.price);
          setNiftyChange(result.data.changePercent ?? null);
          setConnected(result.connected ?? false);
          setLastUpdated(new Date().toLocaleTimeString('en-IN', { hour12: false }));
        } else {
          setConnected(result.connected ?? false);
        }
        
        // Fetch global status for broker info
        const statusRes = await fetch('/auth/status');
        const status = await statusRes.json();
        setBroker(status.broker);
        
        // Load trading mode from localStorage (synced with modal)
        const savedSettings = localStorage.getItem('tradingSettings');
        if (savedSettings) {
          const settings = JSON.parse(savedSettings);
          setTradingMode(settings.tradingMode || 'paper');
        }
      } catch (error) {
        console.error('Error fetching NIFTY price:', error);
        setConnected(false);
      }
    };

    fetchNiftyPrice();
    const interval = setInterval(fetchNiftyPrice, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="fixed top-0 left-0 right-0 h-14 bg-white/90 backdrop-blur border-b border-gray-200 z-50">
      <div className="h-full px-4 flex items-center justify-between">
        
        {/* Left side - Logo and Brand */}
        <div className="flex items-center space-x-3">
          {/* Mobile menu toggle */}
          <button
            onClick={onMobileMenuToggle}
            className="lg:hidden p-2 rounded-md text-gray-600 hover:bg-gray-100 transition-colors"
          >
            {isMobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          
          {/* Desktop sidebar toggle - three dots */}
          <button
            onClick={onSidebarToggle}
            className="hidden lg:flex p-2 rounded-md text-gray-600 hover:bg-gray-100 transition-colors"
            title={isSidebarVisible ? 'Hide Sidebar' : 'Show Sidebar'}
          >
            <MoreVertical size={20} />
          </button>
          
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">T</span>
            </div>
            <span className="text-lg font-semibold text-gray-800">Trading Platform</span>
          </div>
        </div>

        {/* Center - Market Status */}
        <div className="hidden md:flex items-center space-x-3 text-xs bg-gray-900 text-gray-300 px-4 py-1.5 rounded-full">
          <span>{new Date().toLocaleDateString('en-GB')}</span>
          <span className="text-gray-500">|</span>
          <span>Last Updated: {lastUpdated || '--:--:--'}</span>
          <span className="text-gray-500">|</span>
          <div className="flex items-center space-x-1">
            <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className={connected ? 'text-green-400' : 'text-red-400'}>
              {connected ? (broker || 'Connected') : 'Disconnected'}
            </span>
          </div>
          <span className="text-gray-500">|</span>
          <div className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
            tradingMode === 'live' ? 'bg-red-900/50 text-red-400 border border-red-500/50' : 'bg-blue-900/50 text-blue-400 border border-blue-500/50'
          }`}>
            {tradingMode}
          </div>
          <span className="text-gray-500">|</span>
          <div>
            <span className="text-gray-400">NIFTY: </span>
            {niftyPrice ? (
              <>
                <span className="text-white font-semibold">
                  {niftyPrice.toLocaleString('en-IN')}
                </span>
                {niftyChange !== null && (
                  <span className={`ml-1 ${niftyChange >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    ({niftyChange >= 0 ? '+' : ''}{niftyChange}%)
                  </span>
                )}
              </>
            ) : (
              <span className="text-gray-500">--</span>
            )}
          </div>
        </div>

        {/* Right side - User & Actions */}
        <div className="flex items-center space-x-2">
          
          {/* Settings Button */}
          <button
            onClick={onSettingsClick}
            className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            title="Trading Settings"
          >
            <Settings size={18} />
          </button>

          {/* User Profile or Login */}
          {user ? (
            <div className="relative">
              <button
                onClick={() => setShowUserDropdown(!showUserDropdown)}
                className="flex items-center space-x-2 p-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <div className="w-7 h-7 bg-blue-500 rounded-full flex items-center justify-center">
                  <span className="text-white font-semibold text-xs">
                    {user.firstName[0]}{user.lastName[0]}
                  </span>
                </div>
                <div className="hidden sm:block text-left">
                  <div className="text-sm font-medium text-gray-900">
                    {user.firstName} {user.lastName}
                  </div>
                  <div className="text-xs text-gray-500">{user.plan} Plan</div>
                </div>
              </button>

              {/* User Dropdown */}
              {showUserDropdown && (
                <>
                  <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50">
                    <div className="px-4 py-3 border-b border-gray-100">
                      <div className="text-sm font-medium text-gray-900">{user.firstName} {user.lastName}</div>
                      <div className="text-sm text-gray-500">{user.email}</div>
                    </div>
                    
                    <button
                      onClick={() => {
                        setShowUserDropdown(false);
                        onSettingsClick();
                      }}
                      className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center"
                    >
                      <Settings size={16} className="mr-3" />
                      Trading Settings
                    </button>
                    
                    <button
                      onClick={() => {
                        setShowUserDropdown(false);
                        setShowAIChat(true);
                      }}
                      className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center"
                    >
                      🤖
                      <span className="ml-3">AI Trading Assistant</span>
                    </button>
                    
                    <button
                      onClick={() => {
                        setShowUserDropdown(false);
                      }}
                      className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center"
                    >
                      <User size={16} className="mr-3" />
                      Your Profile
                    </button>
                    
                    <div className="border-t border-gray-100 mt-2 pt-2">
                      <button
                        onClick={() => {
                          setShowUserDropdown(false);
                          onLogout();
                        }}
                        className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center"
                      >
                        <svg className="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                        </svg>
                        Sign Out
                      </button>
                    </div>
                  </div>
                  
                  {/* Click outside to close dropdown */}
                  <div
                    className="fixed inset-0 z-40"
                    onClick={() => setShowUserDropdown(false)}
                  />
                </>
              )}
            </div>
          ) : (
            <button
              onClick={onLogin}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
            >
              Sign In
            </button>
          )}
        </div>
      </div>

      {/* AI Trading Chat Modal */}
      <AITradingChat 
        isOpen={showAIChat}
        onClose={() => setShowAIChat(false)}
        currentData={{
          nifty: 25850,
          vix: 12.5
        }}
      />
    </header>
  );
};

export default Navbar;
