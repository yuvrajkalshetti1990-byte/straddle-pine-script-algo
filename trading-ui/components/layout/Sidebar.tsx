'use client'

import React, { useState, useRef, useEffect } from "react";
import { BarChart3, TrendingUp, Settings, User, ShieldX, FileText } from "lucide-react";

interface ChatMessage {
  id: number;
  type: 'user' | 'ai';
  message: string;
  timestamp: string;
  analysis?: {
    action: 'BUY' | 'SELL' | 'HOLD';
    confidence: number;
    target?: number;
    stopLoss?: number;
    reasoning: string;
  };
}

interface SidebarProps {
  isMobileMenuOpen: boolean;
  isSidebarVisible: boolean;
  onSettingsClick: () => void;
  onTradingClick: () => void;
  onAIAssistantClick: () => void;
  onClose: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isMobileMenuOpen, isSidebarVisible, onSettingsClick, onTradingClick, onAIAssistantClick, onClose }) => {
  // AI Chat state from local version
  const [showAIChat, setShowAIChat] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 1,
      type: 'ai',
      message: "🤖 Hi! I'm your AI Trading Assistant. Ask me about market trends, NIFTY analysis, or trading strategies!",
      timestamp: new Date().toLocaleTimeString()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Kill switch state from remote version
  const [killSwitchActive, setKillSwitchActive] = useState(false);
  const [showKillSwitchConfirm, setShowKillSwitchConfirm] = useState(false);

  // Multiple accounts state
  const [selectedAccount, setSelectedAccount] = useState('TD2024001');
  const [showAccountSwitcher, setShowAccountSwitcher] = useState(false);
  const accounts = [
    { id: 'TD2024001', name: 'Main Account', status: 'ACTIVE' },
    { id: 'TD2024002', name: 'Secondary Account', status: 'ACTIVE' },
    { id: 'TD2024003', name: 'Demo Account', status: 'DEMO' }
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const generateAIResponse = (userMessage: string): ChatMessage => {
    const lowerMessage = userMessage.toLowerCase();
    
    if (lowerMessage.includes('nifty') || lowerMessage.includes('market')) {
      return {
        id: Date.now(),
        type: 'ai',
        message: "📊 NIFTY Analysis:",
        timestamp: new Date().toLocaleTimeString(),
        analysis: {
          action: Math.random() > 0.5 ? 'BUY' : 'SELL',
          confidence: Math.round(75 + Math.random() * 20),
          target: 25950 + Math.round((Math.random() - 0.5) * 200),
          stopLoss: 25800 + Math.round((Math.random() - 0.5) * 100),
          reasoning: "Strong support at 25,800. RSI oversold. Bullish divergence detected."
        }
      };
    }

    if (lowerMessage.includes('vix')) {
      return {
        id: Date.now(),
        type: 'ai',
        message: "📈 VIX at 14.2 suggests moderate volatility. Good for option writing strategies.",
        timestamp: new Date().toLocaleTimeString()
      };
    }

    const responses = [
      "I can help with market analysis. Try asking about NIFTY or VIX trends!",
      "What trading strategy are you considering? I can provide insights.",
      "Current market shows mixed signals. Any specific stock you're tracking?"
    ];

    return {
      id: Date.now(),
      type: 'ai',
      message: responses[Math.floor(Math.random() * responses.length)],
      timestamp: new Date().toLocaleTimeString()
    };
  };

  const handleSendMessage = () => {
    if (!inputMessage.trim()) return;

    const userMessage: ChatMessage = {
      id: Date.now(),
      type: 'user',
      message: inputMessage,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsTyping(true);

    setTimeout(() => {
      const aiResponse = generateAIResponse(inputMessage);
      setMessages(prev => [...prev, aiResponse]);
      setIsTyping(false);
    }, 1000);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };

  // Kill switch functions from remote version
  const handleKillSwitch = () => {
    if (killSwitchActive) {
      // Already active, can't disable until next day
      return;
    }
    setShowKillSwitchConfirm(true);
  };

  const confirmKillSwitch = () => {
    setKillSwitchActive(true);
    setShowKillSwitchConfirm(false);
    console.log('Kill switch activated - Trading disabled until next day');
  };
  
  const menuItems = [
    { name: "Dashboard", icon: BarChart3, href: "/", action: undefined },
    { name: "Trades", icon: TrendingUp, href: undefined, action: onTradingClick },
  ];

  const handleMenuClick = (callback?: () => void) => {
    onClose(); // Close mobile menu
    callback?.(); // Execute additional callback if provided
  };

  return (
    <aside className={`
      fixed top-14 left-0 bottom-0 w-56 bg-white/95 border-r border-gray-200 z-40 transition-transform duration-300
      ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}
      ${isSidebarVisible ? 'lg:translate-x-0' : 'lg:-translate-x-full'}
    `}>
      <nav className="h-full overflow-auto px-4 py-6">
        {/* User Account Section */}
        <div className="mb-6 p-4 bg-gray-50 rounded-lg border">
          <div className="flex items-center space-x-3 mb-3">
            <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
              <User className="w-5 h-5 text-white" />
            </div>
            <div className="flex-1">
              <div className="font-medium text-gray-900">Yuvraj</div>
              <div className="text-sm text-gray-500">Premium User</div>
            </div>
            <button
              onClick={() => setShowAccountSwitcher(!showAccountSwitcher)}
              className="text-gray-600 hover:text-blue-600 font-bold text-lg"
              title="Switch Account"
            >
              ↔️
            </button>
          </div>
          
          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-gray-600">Account ID:</span>
              <span className="font-mono text-gray-900">{selectedAccount}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Status:</span>
              <span className={`font-semibold ${killSwitchActive ? 'text-red-600' : 'text-green-600'}`}>
                {killSwitchActive ? 'DISABLED' : 'ACTIVE'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Last Login:</span>
              <span className="text-gray-900">Today 9:15 AM</span>
            </div>
          </div>

          {/* Account Switcher Dropdown */}
          {showAccountSwitcher && (
            <div className="mt-3 p-2 bg-white border border-gray-300 rounded-lg space-y-1">
              {accounts.map((account) => (
                <button
                  key={account.id}
                  onClick={() => {
                    setSelectedAccount(account.id);
                    setShowAccountSwitcher(false);
                  }}
                  className={`w-full text-left px-2 py-1.5 rounded text-xs transition-colors ${
                    selectedAccount === account.id
                      ? 'bg-blue-100 text-blue-700 font-semibold'
                      : 'hover:bg-gray-100 text-gray-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span>{account.name}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-200">
                      {account.status}
                    </span>
                  </div>
                  <div className="text-[10px] text-gray-500">{account.id}</div>
                </button>
              ))}
              <button
                onClick={() => alert('Add new account coming soon!')}
                className="w-full text-left px-2 py-2 text-xs text-blue-600 hover:bg-blue-50 rounded font-semibold"
              >
                + Add New Account
              </button>
            </div>
          )}
        </div>

        {/* Kill Switch */}
        <div className="mb-6">
          {!killSwitchActive ? (
            // Show Kill Switch when trading is active
            <button
              onClick={handleKillSwitch}
              className="w-full flex items-center justify-center space-x-2 p-3 rounded-lg border-2 border-red-500 bg-red-500 text-white hover:bg-red-600 transition-colors"
            >
              <ShieldX className="w-5 h-5 text-white" />
              <span className="font-semibold">KILL SWITCH</span>
            </button>
          ) : (
            // Show both disabled status and enable button when trading is disabled
            <div className="space-y-2">
              <div className="w-full flex items-center justify-center space-x-2 p-3 rounded-lg border-2 border-red-500 bg-red-50 text-red-700">
                <ShieldX className="w-5 h-5 text-red-500" />
                <span className="font-semibold">TRADING DISABLED</span>
              </div>
              <button
                onClick={() => {
                  setKillSwitchActive(false);
                  console.log('Trading enabled');
                }}
                className="w-full p-2 rounded-lg bg-green-500 text-white hover:bg-green-600 transition-colors text-sm font-medium"
              >
                Enable Trading
              </button>
            </div>
          )}
          <p className="text-xs text-gray-500 mt-2 text-center">
            {killSwitchActive 
              ? 'Trading disabled until next day' 
              : 'Click to disable trading immediately'
            }
          </p>
        </div>

        {/* Navigation Menu */}
        <ul className="space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon;
            return (
              <li key={item.name}>
                {item.href ? (
                  <a
                    href={item.href}
                    onClick={() => handleMenuClick()}
                    className="flex items-center space-x-3 rounded-md px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 transition-colors"
                  >
                    <Icon size={18} />
                    <span>{item.name}</span>
                  </a>
                ) : (
                  <button
                    onClick={() => handleMenuClick(item.action)}
                    className="flex items-center space-x-3 w-full rounded-md px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 transition-colors"
                  >
                    <Icon size={18} />
                    <span>{item.name}</span>
                  </button>
                )}
              </li>
            );
          })}

          {/* My Trades */}
          <li>
            <button
              onClick={() => handleMenuClick(() => window.location.href = '/trades')}
              className="flex items-center space-x-3 w-full rounded-md px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 transition-colors"
            >
              <FileText size={18} className="w-[18px] h-[18px]" />
              <span>My Trades</span>
            </button>
          </li>
          
          {/* Settings as sidebar item for mobile */}
          <li>
            <button
              onClick={() => handleMenuClick(onSettingsClick)}
              className="flex items-center space-x-3 w-full rounded-md px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 transition-colors"
            >
              <Settings size={18} className="w-[18px] h-[18px]" />
              <span>Settings</span>
            </button>
          </li>

          {/* AI Assistant */}
          <li>
            <button
              onClick={() => setShowAIChat(!showAIChat)}
              className="flex items-center space-x-3 w-full rounded-md px-3 py-2 text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 transition-colors"
            >
              <span className="text-lg">🤖</span>
              <span>AI Assistant</span>
              <span className="text-xs bg-green-500 px-2 py-0.5 rounded-full ml-auto">LIVE</span>
            </button>
          </li>

          {/* AI Chat Interface */}
          {showAIChat && (
            <li className="mt-2">
              <div className="bg-gray-900 rounded-lg border border-gray-700 mx-2">
                {/* Chat Messages */}
                <div className="h-64 overflow-y-auto p-3 space-y-2">
                  {messages.map((msg) => (
                    <div key={msg.id} className={`${msg.type === 'user' ? 'text-right' : 'text-left'}`}>
                      <div className={`inline-block max-w-[90%] rounded-lg p-2 text-xs ${
                        msg.type === 'user' 
                          ? 'bg-blue-600 text-white' 
                          : 'bg-gray-800 text-gray-100'
                      }`}>
                        <div>{msg.message}</div>
                        
                        {/* AI Analysis Card */}
                        {msg.analysis && (
                          <div className="mt-2 bg-gray-950 rounded p-2 border border-gray-600">
                            <div className="flex items-center justify-between mb-1">
                              <span className={`px-1 py-0.5 rounded text-xs font-bold ${
                                msg.analysis.action === 'BUY' ? 'bg-green-600' : 'bg-red-600'
                              }`}>
                                {msg.analysis.action}
                              </span>
                              <span className="text-xs text-gray-400">
                                {msg.analysis.confidence}%
                              </span>
                            </div>
                            
                            {msg.analysis.target && (
                              <div className="text-xs space-y-0.5">
                                <div className="flex justify-between">
                                  <span className="text-gray-400">Target:</span>
                                  <span className="text-green-400">₹{msg.analysis.target}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-400">SL:</span>
                                  <span className="text-red-400">₹{msg.analysis.stopLoss}</span>
                                </div>
                              </div>
                            )}
                            
                            <div className="mt-1 text-xs text-gray-300 leading-tight">
                              {msg.analysis.reasoning}
                            </div>
                          </div>
                        )}
                        
                        <div className="text-xs text-gray-400 mt-1">
                          {msg.timestamp}
                        </div>
                      </div>
                    </div>
                  ))}
                  
                  {isTyping && (
                    <div className="text-left">
                      <div className="inline-block bg-gray-800 text-gray-100 rounded-lg p-2 text-xs">
                        <div className="flex items-center space-x-1">
                          <span className="typing-dot"></span>
                          <span className="typing-dot"></span>
                          <span className="typing-dot"></span>
                          <span className="text-gray-400 ml-2">AI thinking...</span>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  <div ref={messagesEndRef} />
                </div>

                {/* Chat Input */}
                <div className="p-2 border-t border-gray-700">
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      value={inputMessage}
                      onChange={(e) => setInputMessage(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder="Ask about NIFTY, VIX..."
                      className="flex-1 px-2 py-1 bg-gray-800 border border-gray-600 rounded text-white text-xs focus:outline-none focus:border-blue-500"
                    />
                    <button
                      onClick={handleSendMessage}
                      disabled={!inputMessage.trim()}
                      className="px-2 py-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded text-xs transition-colors"
                    >
                      Send
                    </button>
                  </div>
                </div>
              </div>
            </li>
          )}
        </ul>

        <style jsx>{`
          .typing-dot {
            display: inline-block;
            width: 3px;
            height: 3px;
            border-radius: 50%;
            background-color: #9ca3af;
            animation: typing 1.4s infinite ease-in-out;
          }
          .typing-dot:nth-child(1) { animation-delay: -0.32s; }
          .typing-dot:nth-child(2) { animation-delay: -0.16s; }
          @keyframes typing {
            0%, 80%, 100% { transform: scale(0); opacity: 0.5; }
            40% { transform: scale(1); opacity: 1; }
          }
        `}</style>
      </nav>

      {/* Kill Switch Confirmation Modal */}
      {showKillSwitchConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-80 mx-4">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                <ShieldX className="w-6 h-6 text-red-600" />
              </div>
              <div>
                <h3 className="font-bold text-gray-900">Activate Kill Switch</h3>
                <p className="text-sm text-gray-600">This action cannot be undone</p>
              </div>
            </div>
            
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
              <p className="text-sm text-red-800">
                <strong>Warning:</strong> Activating the kill switch will immediately disable all trading functionality until tomorrow. This action cannot be reversed today.
              </p>
            </div>
            
            <div className="flex space-x-3">
              <button
                onClick={() => setShowKillSwitchConfirm(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={confirmKillSwitch}
                className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors font-semibold"
              >
                Activate
              </button>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
};

export default Sidebar;
