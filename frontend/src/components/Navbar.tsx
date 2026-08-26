import React from 'react';
import { Activity, LogOut, ShieldCheck, Waves } from 'lucide-react';
import { ApiClient } from '../api/client';

interface NavbarProps {
  onLogout: () => void;
  userEmail?: string;
  activeTab: 'analysis' | 'evaluation';
  setActiveTab: (tab: 'analysis' | 'evaluation') => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onLogout, userEmail, activeTab, setActiveTab }) => {
  return (
    <header className="sticky top-0 z-50 border-b border-gray-800 glass-panel">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Waves className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg text-white tracking-tight">CallScope AI</span>
              <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
                v2026.08.26
              </span>
            </div>
            <p className="text-xs text-gray-400">Production Call Tone & Background Noise Analysis</p>
          </div>
        </div>

        {ApiClient.isAuthenticated() && (
          <div className="flex items-center space-x-6">
            <nav className="flex space-x-1 bg-gray-900/60 p-1 rounded-lg border border-gray-800">
              <button
                onClick={() => setActiveTab('analysis')}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${
                  activeTab === 'analysis'
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-gray-400 hover:text-gray-200'
                }`}
              >
                Analysis & Batches
              </button>
              <button
                onClick={() => setActiveTab('evaluation')}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all flex items-center space-x-1.5 ${
                  activeTab === 'evaluation'
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-gray-400 hover:text-gray-200'
                }`}
              >
                <Activity className="w-4 h-4" />
                <span>Model Metrics</span>
              </button>
            </nav>

            <div className="flex items-center space-x-3 border-l border-gray-800 pl-6">
              <div className="flex items-center space-x-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span className="text-sm font-medium text-gray-300">{userEmail || 'evaluator@callscope.ai'}</span>
              </div>
              <button
                onClick={onLogout}
                className="p-2 text-gray-400 hover:text-rose-400 transition-colors rounded-lg hover:bg-rose-500/10"
                title="Log out"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        )}
      </div>
    </header>
  );
};
