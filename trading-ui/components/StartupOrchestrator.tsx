'use client';

import React, { useState, useEffect } from 'react';
import { Play, ShieldAlert, CheckCircle2, Loader2, AlertCircle, RefreshCw } from 'lucide-react';
import LoginModal from './LoginModal';

interface StartupStatus {
  state: 'IDLE' | 'STARTING' | 'AUTHENTICATING' | 'WARMING_UP' | 'READY' | 'ERROR';
  message: string;
  details?: string;
}

const StartupOrchestrator = ({ selectedIndex = 'NIFTY', onStatusChange }: { selectedIndex: string, onStatusChange?: (running: boolean) => void }) => {
  const [status, setStatus] = useState<StartupStatus>({ state: 'IDLE', message: 'Ready to Start' });
  const [showLogin, setShowLogin] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const startEngine = async () => {
    if (isProcessing || status.state === 'STARTING' || status.state === 'AUTHENTICATING') return;
    
    setIsProcessing(true);
    setStatus({ state: 'STARTING', message: 'Starting Engine...' });
    
    try {
      const res = await fetch('/api/v1/strategy/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ index: selectedIndex })
      });

      // DEFENSIVE: Check content-type before parsing JSON
      const contentType = res.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) {
        const text = await res.text();
        throw new Error(`Invalid server response (Non-JSON): ${text.substring(0, 50)}...`);
      }

      const result = await res.json();

      if (result.status === 'success') {
        setStatus({ state: 'WARMING_UP', message: 'Warming Up Indicators...' });
        localStorage.removeItem('engine_auto_start');
        localStorage.removeItem('engine_retry_count');
      } else if (result.message?.toLowerCase().includes('auth') || result.message?.toLowerCase().includes('token')) {
        // Only retry if we haven't exceeded max retries
        const retryCount = parseInt(localStorage.getItem('engine_retry_count') || '0');
        if (retryCount >= 3) {
           setStatus({ 
             state: 'ERROR', 
             message: 'Authentication Loop Detected', 
             details: 'Maximum retry attempts exceeded. Please clear auth lock and try manual login.' 
           });
           localStorage.removeItem('engine_auto_start');
           return;
        }

        localStorage.setItem('engine_auto_start', 'true');
        setStatus({ state: 'AUTHENTICATING', message: 'Authenticating with Broker...' });
        
        setTimeout(() => {
          window.location.href = '/auth/fyers/login';
        }, 800);
      } else {
        setStatus({ state: 'ERROR', message: 'Startup Failed', details: result.message });
        // Don't clear retry count on error, but stop auto-start
        localStorage.removeItem('engine_auto_start');
      }
    } catch (error: any) {
      console.error('Startup error:', error);
      setStatus({ 
        state: 'ERROR', 
        message: 'Connection Error', 
        details: error.message || 'Check backend server' 
      });
      localStorage.removeItem('engine_auto_start');
    } finally {
      setIsProcessing(false);
    }
  };

  const stopEngine = async () => {
    setIsProcessing(true);
    try {
      await fetch('/api/v1/strategy/stop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ index: selectedIndex })
      });
      setStatus({ state: 'IDLE', message: 'Ready to Start' });
      localStorage.removeItem('engine_auto_start');
      localStorage.removeItem('engine_retry_count');
      if (onStatusChange) onStatusChange(false);
    } catch (error) {
      console.error('Stop failed', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const clearAuthLock = () => {
    localStorage.removeItem('engine_auto_start');
    localStorage.removeItem('engine_retry_count');
    setStatus({ state: 'IDLE', message: 'Auth Lock Cleared' });
  };

  useEffect(() => {
    let interval: NodeJS.Timeout;

    if (status.state === 'WARMING_UP' || status.state === 'STARTING' || status.state === 'READY') {
      interval = setInterval(async () => {
        try {
          const res = await fetch(`/api/v1/strategy/status?index=${selectedIndex}`);
          if (!res.ok) return;
          const result = await res.json();
          
          if (result.status === 'success' && result.data) {
            const data = result.data;
            
            if (!data.engineRunning) {
              if (status.state !== 'IDLE' && status.state !== 'STARTING' && status.state !== 'AUTHENTICATING' && status.state !== 'ERROR') {
                setStatus({ state: 'IDLE', message: 'Engine Stopped' });
                if (onStatusChange) onStatusChange(false);
              }
              return;
            }

            if (onStatusChange) onStatusChange(true);

            if (data.isWarmingUp) {
              setStatus({ state: 'WARMING_UP', message: 'Warming Up Indicators...', details: `Bar Index: ${data.barIndex || 0}` });
            } else {
              setStatus({ state: 'READY', message: 'Ready for Market', details: `${data.index} Active | ${data.regime || 'WAIT'}` });
            }
          }
        } catch (e) {
          console.error('Status poll failed', e);
        }
      }, 2000);
    }

    return () => clearInterval(interval);
  }, [status.state, selectedIndex, onStatusChange]);

  // Handle Auto-Resume after OAuth callback
  useEffect(() => {
    const shouldAutoStart = localStorage.getItem('engine_auto_start');
    const retryCount = parseInt(localStorage.getItem('engine_retry_count') || '0');

    if (shouldAutoStart === 'true') {
      if (retryCount >= 3) {
        console.error('Max startup retries exceeded. Manual intervention required.');
        setStatus({ 
          state: 'ERROR', 
          message: 'Startup Loop Blocked', 
          details: 'Automatic resume stopped after 3 failed attempts.' 
        });
        localStorage.removeItem('engine_auto_start');
        return;
      }

      localStorage.removeItem('engine_auto_start');
      localStorage.setItem('engine_retry_count', (retryCount + 1).toString());
      
      setTimeout(() => {
        startEngine();
      }, 1000);
    }
  }, []);

  // If login successful, retry startup
  const handleLoginSuccess = () => {
    setShowLogin(false);
    localStorage.removeItem('engine_retry_count');
    startEngine();
  };

  return (
    <div className="flex flex-col gap-3">
      <div className={`p-4 rounded-2xl border backdrop-blur-md transition-all duration-500 ${
        status.state === 'READY' ? 'bg-green-500/10 border-green-500/30' : 
        status.state === 'ERROR' ? 'bg-red-500/10 border-red-500/30' :
        status.state === 'WARMING_UP' ? 'bg-blue-500/10 border-blue-500/30' :
        'bg-gray-800/50 border-gray-700'
      }`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className={`p-3 rounded-xl ${
              status.state === 'READY' ? 'bg-green-500/20 text-green-400' :
              status.state === 'ERROR' ? 'bg-red-500/20 text-red-400' :
              status.state === 'WARMING_UP' || status.state === 'STARTING' || status.state === 'AUTHENTICATING' ? 'bg-blue-500/20 text-blue-400' :
              'bg-gray-700 text-gray-400'
            }`}>
              {status.state === 'READY' && <CheckCircle2 size={24} />}
              {status.state === 'ERROR' && <AlertCircle size={24} />}
              {(status.state === 'WARMING_UP' || status.state === 'STARTING' || status.state === 'AUTHENTICATING') && <Loader2 size={24} className="animate-spin" />}
              {status.state === 'IDLE' && <Play size={24} />}
            </div>
            
            <div>
              <div className="text-lg font-bold text-white tracking-tight">{status.message}</div>
              {status.details && <div className="text-xs text-gray-400 uppercase tracking-widest mt-0.5">{status.details}</div>}
            </div>
          </div>

          <div className="flex gap-2">
            {status.state === 'ERROR' && (
              <button 
                onClick={clearAuthLock}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-xl text-sm font-bold transition-all"
              >
                Clear Auth Lock
              </button>
            )}
            {(status.state === 'IDLE' || status.state === 'ERROR' || status.state === 'STARTING' || status.state === 'AUTHENTICATING') ? (
              <button 
                onClick={startEngine}
                disabled={isProcessing || status.state === 'STARTING' || status.state === 'AUTHENTICATING'}
                className={`px-6 py-2.5 rounded-xl font-bold shadow-lg transition-all flex items-center gap-2 ${
                  isProcessing || status.state === 'STARTING' || status.state === 'AUTHENTICATING'
                    ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-500 text-white shadow-blue-900/20'
                }`}
              >
                {status.state === 'AUTHENTICATING' ? (
                  <>
                    <Loader2 size={18} className="animate-spin" />
                    Authenticating...
                  </>
                ) : status.state === 'STARTING' ? (
                  <>
                    <Loader2 size={18} className="animate-spin" />
                    Starting...
                  </>
                ) : (
                  <>
                    <Play size={18} fill="currentColor" />
                    Start Engine
                  </>
                )}
              </button>
            ) : (
              <button 
                onClick={stopEngine}
                disabled={isProcessing}
                className="px-6 py-2.5 bg-gray-700 hover:bg-red-600/80 text-white rounded-xl font-bold transition-all flex items-center gap-2 disabled:opacity-50"
              >
                <RefreshCw size={18} className={isProcessing ? 'animate-spin' : ''} />
                Stop
              </button>
            )}
          </div>
        </div>

        {status.state === 'AUTHENTICATING' && (
          <div className="mt-4 p-3 bg-orange-500/10 border border-orange-500/30 rounded-xl flex items-center justify-between">
            <span className="text-sm text-orange-300">Broker session required. Please authenticate.</span>
            <button 
              onClick={() => {
                localStorage.setItem('engine_auto_start', 'true');
                setStatus({ state: 'AUTHENTICATING', message: 'Authenticating...' });
                setTimeout(() => {
                  window.location.href = '/auth/fyers/login';
                }, 500);
              }}
              disabled={status.state === 'AUTHENTICATING'}
              className="px-4 py-1.5 bg-orange-600 hover:bg-orange-500 text-white text-xs font-bold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {status.state === 'AUTHENTICATING' ? 'Authenticating...' : 'Login to Fyers'}
            </button>
          </div>
        )}
      </div>

      <LoginModal 
        isOpen={showLogin} 
        onClose={() => setShowLogin(false)} 
        onSuccess={handleLoginSuccess}
      />
    </div>
  );
};

export default StartupOrchestrator;
