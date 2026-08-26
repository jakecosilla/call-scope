import React, { useState } from 'react';
import { Lock, Mail, Shield, Sparkles, Waves } from 'lucide-react';
import { ApiClient } from '../../api/client';

interface LoginPageProps {
  onLoginSuccess: (email: string) => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const data = await ApiClient.login(username, password);
      onLoginSuccess(data.username);
    } catch (err: unknown) {
      const errMessage = err instanceof Error ? err.message : 'Authentication failed. Please verify credentials.';
      setError(errMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleFillEvaluatorCredentials = () => {
    setUsername('evaluator@callscope.ai');
    setPassword('CallScope2026!EvalSecret');
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center p-4">
      <div className="w-full max-w-md glass-panel p-8 rounded-2xl shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/10 rounded-full blur-2xl -mr-10 -mt-10 pointer-events-none" />
        
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-500 to-cyan-400 mb-4 shadow-xl shadow-blue-500/20">
            <Waves className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">CallScope AI</h1>
          <p className="text-sm text-gray-400 mt-1">Sign in with evaluator credentials to analyze call audio</p>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm flex items-center space-x-2">
            <span className="font-semibold">Error:</span>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">Username / Email</label>
            <div className="relative">
              <Mail className="w-5 h-5 text-gray-400 absolute left-3 top-3" />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="evaluator@callscope.ai"
                required
                className="w-full bg-gray-900/80 border border-gray-700/80 rounded-xl pl-10 pr-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">Password</label>
            <div className="relative">
              <Lock className="w-5 h-5 text-gray-400 absolute left-3 top-3" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                required
                className="w-full bg-gray-900/80 border border-gray-700/80 rounded-xl pl-10 pr-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-medium rounded-xl shadow-lg shadow-blue-500/25 transition-all flex items-center justify-center space-x-2 disabled:opacity-50"
          >
            {loading ? (
              <span className="inline-block animate-spin text-white">🌀</span>
            ) : (
              <>
                <Shield className="w-4 h-4" />
                <span>Authenticate & Access Dashboard</span>
              </>
            )}
          </button>
        </form>

        <div className="mt-6 pt-6 border-t border-gray-800 text-center">
          <button
            onClick={handleFillEvaluatorCredentials}
            className="inline-flex items-center space-x-1.5 text-xs text-blue-400 hover:text-blue-300 font-medium transition"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Auto-fill Evaluator Credentials</span>
          </button>
        </div>
      </div>
    </div>
  );
};
