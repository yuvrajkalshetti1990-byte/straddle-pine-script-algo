'use client'

import React, { useState, useEffect } from "react";
import Navbar from "./Navbar";
import Sidebar from "./Sidebar";
import LoginModal from "../LoginModal";
import TradingSettingsModal from "../TradingSettingsModal";
import StrategySettingsModal from "../StrategySettingsModal";

interface User {
  id: number;
  firstName: string;
  lastName: string;
  email: string;
  plan: string;
  avatar?: string;
}

type Props = { children: React.ReactNode };

const MainLayout: React.FC<Props> = ({ children }) => {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isLoginOpen, setIsLoginOpen] = useState(false);
  const [isStrategyOpen, setIsStrategyOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isSidebarVisible, setIsSidebarVisible] = useState(true);
  const [user, setUser] = useState<User | null>(null);

  // Load user from localStorage on component mount
  useEffect(() => {
    const savedUser = localStorage.getItem('tradingUser');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    }
  }, []);

  const handleLogin = (userData: User) => {
    setUser(userData);
    localStorage.setItem('tradingUser', JSON.stringify(userData));
    setIsLoginOpen(false);
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('tradingUser');
    localStorage.removeItem('tradingSettings');
  };

  return (
    <div className="min-h-screen bg-zinc-900">
      <Navbar 
        onSettingsClick={() => setIsSettingsOpen(true)}
        onMobileMenuToggle={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        isMobileMenuOpen={isMobileMenuOpen}
        isSidebarVisible={isSidebarVisible}
        onSidebarToggle={() => setIsSidebarVisible(!isSidebarVisible)}
        user={user || undefined}
        onLogin={() => setIsLoginOpen(true)}
        onLogout={handleLogout}
      />
      
      <div className="flex">
        <Sidebar 
          isMobileMenuOpen={isMobileMenuOpen}
          isSidebarVisible={isSidebarVisible}
          onSettingsClick={() => setIsSettingsOpen(true)}
          onTradingClick={() => setIsStrategyOpen(true)}
          onAIAssistantClick={() => {}}
          onClose={() => setIsMobileMenuOpen(false)}
        />
        
        {/* Main Content */}
        <main className={`flex-1 pt-14 min-h-screen bg-zinc-50 transition-all duration-300 ${isSidebarVisible ? 'lg:pl-56' : 'lg:pl-0'}`}>
          <div className="w-full px-1">
            {children}
          </div>
        </main>
      </div>

      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Login Modal */}
      <LoginModal 
        isOpen={isLoginOpen}
        onClose={() => setIsLoginOpen(false)}
        onLogin={handleLogin}
      />

      {/* Trading Settings Modal */}
      <TradingSettingsModal 
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />

      {/* Strategy Settings Modal with Trading Tab */}
      <StrategySettingsModal 
        isOpen={isStrategyOpen}
        onClose={() => setIsStrategyOpen(false)}
        defaultTab="trading"
      />
    </div>
  );
};

export default MainLayout;
