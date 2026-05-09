"use client";

import { useState, useRef, useEffect } from 'react';

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


interface AITradingChatProps {
  isOpen: boolean;
  onClose: () => void;
  currentData?: {
    nifty: number;
    vix: number;
    selectedStrike?: string;
  };
}

const AITradingChat = ({ isOpen, onClose, currentData }: AITradingChatProps) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 1,
      type: 'ai',
      message: "🤖 Hello! I'm your AI Trading Assistant. I can analyze market conditions and provide trading suggestions based on current NIFTY, VIX, and technical indicators. How can I help you today?",
      timestamp: new Date().toLocaleTimeString()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isAdvancedSectionOpen, setIsAdvancedSectionOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const generateAIResponse = (userMessage: string): ChatMessage => {
    const lowerMessage = userMessage.toLowerCase();
    
    // Sample trading analysis based on keywords
    if (lowerMessage.includes('nifty') || lowerMessage.includes('market') || lowerMessage.includes('analysis')) {
      return {
        id: Date.now(),
        type: 'ai',
        message: "📊 Based on current market analysis:",
        timestamp: new Date().toLocaleTimeString(),
        analysis: {
          action: Math.random() > 0.5 ? 'BUY' : 'SELL',
          confidence: Math.round(75 + Math.random() * 20),
          target: 25950 + Math.round((Math.random() - 0.5) * 200),
          stopLoss: 25800 + Math.round((Math.random() - 0.5) * 100),
          reasoning: "Technical indicators suggest bullish momentum with RSI showing oversold conditions. VIX levels indicate reduced volatility. Strong support at 25800 levels."
        }
      };
    }

    if (lowerMessage.includes('vix') || lowerMessage.includes('volatility')) {
      return {
        id: Date.now(),
        type: 'ai',
        message: "📈 VIX Analysis: Current VIX levels suggest moderate volatility. This is favorable for option writing strategies. Consider iron condors or straddles for range-bound markets.",
        timestamp: new Date().toLocaleTimeString()
      };
    }

    if (lowerMessage.includes('buy') || lowerMessage.includes('call')) {
      return {
        id: Date.now(),
        type: 'ai',
        message: "🟢 BUY Signal Analysis:",
        timestamp: new Date().toLocaleTimeString(),
        analysis: {
          action: 'BUY',
          confidence: 82,
          target: 26100,
          stopLoss: 25750,
          reasoning: "Strong bullish divergence observed. RSI breaking above 50 with increasing volumes. Institutional buying detected."
        }
      };
    }

    if (lowerMessage.includes('sell') || lowerMessage.includes('put')) {
      return {
        id: Date.now(),
        type: 'ai',
        message: "🔴 SELL Signal Analysis:",
        timestamp: new Date().toLocaleTimeString(),
        analysis: {
          action: 'SELL',
          confidence: 78,
          target: 25650,
          stopLoss: 25950,
          reasoning: "Bearish pattern formation with resistance at current levels. VIX spike indicates increased uncertainty."
        }
      };
    }

    // Default responses
    const defaultResponses = [
      "I can help you with market analysis. Try asking about NIFTY trends, VIX levels, or specific trading strategies.",
      "Let me analyze the current market conditions for you. What specific instrument are you interested in?",
      "Based on technical indicators, I can provide buy/sell suggestions. What's your trading query?",
      "I'm analyzing live market data. Ask me about any strike price or trading strategy you're considering."
    ];

    return {
      id: Date.now(),
      type: 'ai',
      message: defaultResponses[Math.floor(Math.random() * defaultResponses.length)],
      timestamp: new Date().toLocaleTimeString()
    };
  };

  const handleSendMessage = () => {
    if (!inputMessage.trim()) return;

    // Add user message
    const userMessage: ChatMessage = {
      id: Date.now(),
      type: 'user',
      message: inputMessage,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsTyping(true);

    // Simulate AI thinking time
    setTimeout(() => {
      const aiResponse = generateAIResponse(inputMessage);
      setMessages(prev => [...prev, aiResponse]);
      setIsTyping(false);
    }, 1500 + Math.random() * 1000);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-[#1e293b] rounded-lg border border-gray-700 w-full max-w-2xl h-[600px] shadow-2xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            🤖 AI Trading Assistant
            <span className="text-xs bg-green-600 px-2 py-1 rounded-full">LIVE</span>
          </h3>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsAdvancedSectionOpen(!isAdvancedSectionOpen)}
              className="text-gray-400 hover:text-white transition-colors px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm"
            >
              📊 Advanced Analysis
            </button>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors text-xl"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Advanced Trading Analysis Section */}
        {isAdvancedSectionOpen && (
          <div className="bg-gray-900 border-b border-gray-700 p-4">
            <h4 className="text-white font-semibold mb-3 flex items-center gap-2">
              📈 Advanced Trading Analysis
              <span className="text-xs bg-blue-600 px-2 py-1 rounded-full">PRO</span>
            </h4>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Market Overview */}
              <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
                <h5 className="text-sm font-semibold text-green-400 mb-2">📊 Market Overview</h5>
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between">
                    <span className="text-gray-400">NIFTY:</span>
                    <span className="text-white">25,213.45</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">VIX:</span>
                    <span className="text-yellow-400">12.1</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">RSI:</span>
                    <span className="text-blue-400">64</span>
                  </div>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
                <h5 className="text-sm font-semibold text-blue-400 mb-2">⚡ Quick Actions</h5>
                <div className="space-y-2">
                  <button className="w-full text-xs bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded transition-colors">
                    Generate Buy Signal
                  </button>
                  <button className="w-full text-xs bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded transition-colors">
                    Generate Sell Signal
                  </button>
                  <button className="w-full text-xs bg-purple-600 hover:bg-purple-700 text-white px-3 py-1 rounded transition-colors">
                    Risk Analysis
                  </button>
                </div>
              </div>

              {/* Strategy Recommendations */}
              <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
                <h5 className="text-sm font-semibold text-orange-400 mb-2">🎯 Strategy Recommendations</h5>
                <div className="space-y-1 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                    <span className="text-gray-300">Iron Condor - High Probability</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-yellow-500 rounded-full"></span>
                    <span className="text-gray-300">Straddle - Medium Risk</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-red-500 rounded-full"></span>
                    <span className="text-gray-300">Naked Puts - Low Confidence</span>
                  </div>
                </div>
              </div>

              {/* Live Alerts */}
              <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
                <h5 className="text-sm font-semibold text-red-400 mb-2">🚨 Live Alerts</h5>
                <div className="space-y-1 text-xs text-gray-300">
                  <div className="flex items-center gap-2">
                    <span className="text-red-400">•</span>
                    <span>RSI Overbought Warning</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-yellow-400">•</span>
                    <span>Volume Spike Detected</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-green-400">•</span>
                    <span>Support Level Holding</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-3 flex justify-center">
              <button
                onClick={() => setIsAdvancedSectionOpen(false)}
                className="text-gray-400 hover:text-white transition-colors text-sm px-4 py-1 bg-gray-700 hover:bg-gray-600 rounded"
              >
                ▲ Collapse
              </button>
            </div>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-3 ${
                  msg.type === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-800 text-gray-100'
                }`}
              >
                <div className="text-sm">{msg.message}</div>
                
                {/* AI Analysis Card */}
                {msg.analysis && (
                  <div className="mt-3 bg-gray-900 rounded-lg p-3 border border-gray-700">
                    <div className="flex items-center justify-between mb-2">
                      <span className={`px-2 py-1 rounded text-xs font-bold ${
                        msg.analysis.action === 'BUY' ? 'bg-green-600' : 
                        msg.analysis.action === 'SELL' ? 'bg-red-600' : 'bg-yellow-600'
                      }`}>
                        {msg.analysis.action}
                      </span>
                      <span className="text-xs text-gray-400">
                        Confidence: {msg.analysis.confidence}%
                      </span>
                    </div>
                    
                    {msg.analysis.target && (
                      <div className="text-xs space-y-1">
                        <div className="flex justify-between">
                          <span className="text-gray-400">Target:</span>
                          <span className="text-green-400">₹{msg.analysis.target}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">Stop Loss:</span>
                          <span className="text-red-400">₹{msg.analysis.stopLoss}</span>
                        </div>
                      </div>
                    )}
                    
                    <div className="mt-2 text-xs text-gray-300 leading-relaxed">
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
            <div className="flex justify-start">
              <div className="bg-gray-800 text-gray-100 max-w-[80%] rounded-lg p-3">
                <div className="flex items-center space-x-2">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  <span className="text-sm text-gray-400">AI is analyzing...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-gray-700">
          <div className="flex items-center space-x-2">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about market analysis, buy/sell signals, VIX trends..."
              className="flex-1 px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputMessage.trim()}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
            >
              Send
            </button>
          </div>
          
          {/* Quick Suggestions */}
          <div className="flex flex-wrap gap-2 mt-2">
            {[
              'Analyze NIFTY trend',
              'VIX analysis',
              'Buy signal?',
              'Market outlook'
            ].map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => setInputMessage(suggestion)}
                className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded transition-colors"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      </div>

      <style jsx>{`
        .typing-indicator {
          display: inline-block;
        }
        .typing-indicator span {
          display: inline-block;
          width: 4px;
          height: 4px;
          border-radius: 50%;
          background-color: #9ca3af;
          margin: 0 1px;
          animation: typing 1.4s infinite ease-in-out;
        }
        .typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
        .typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
        @keyframes typing {
          0%, 80%, 100% { transform: scale(0); opacity: 0.5; }
          40% { transform: scale(1); opacity: 1; }
        }
      `}</style>
    </div>
  );
};

export default AITradingChat;