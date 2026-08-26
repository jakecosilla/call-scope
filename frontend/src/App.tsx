import React, { useState } from 'react';
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import { ApiClient } from './api/client';
import { Navbar } from './components/Navbar';
import { LoginPage } from './features/auth/LoginPage';
import { BatchProgress } from './features/batches/BatchProgress';
import { EvaluationView } from './features/evaluation/EvaluationView';
import { ResultsTable } from './features/results/ResultsTable';
import { UploadSection } from './features/upload/UploadSection';
import type { BatchSummary } from './types';

const queryClient = new QueryClient();

const DashboardContent: React.FC<{
  userEmail?: string;
  onLogout: () => void;
}> = ({ userEmail, onLogout }) => {
  const [activeTab, setActiveTab] = useState<'analysis' | 'evaluation'>('analysis');
  const [activeBatchId, setActiveBatchId] = useState<string | null>(null);

  const { data: batch } = useQuery<BatchSummary>({
    queryKey: ['batch', activeBatchId],
    queryFn: () => ApiClient.getBatch(activeBatchId!),
    enabled: !!activeBatchId,
    refetchInterval: (query) => {
      const b = query.state.data;
      if (!b) return 1000;
      if (b.status === 'completed' || b.status === 'completed_with_errors' || b.status === 'failed') {
        return false;
      }
      return 1000;
    },
  });

  return (
    <div className="min-h-screen bg-background text-white">
      <Navbar
        onLogout={onLogout}
        userEmail={userEmail}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {activeTab === 'analysis' ? (
          <>
            <UploadSection onBatchCreated={(id) => setActiveBatchId(id)} />

            {batch && (
              <>
                <BatchProgress batch={batch} />
                {batch.files && batch.files.length > 0 && <ResultsTable batch={batch} />}
              </>
            )}
          </>
        ) : (
          <EvaluationView batchId={activeBatchId || ''} />
        )}
      </main>
    </div>
  );
};

export function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(ApiClient.isAuthenticated());
  const [userEmail, setUserEmail] = useState<string>('');

  const handleLoginSuccess = (email: string) => {
    setUserEmail(email);
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    ApiClient.setToken(null);
    setIsAuthenticated(false);
  };

  return (
    <QueryClientProvider client={queryClient}>
      {!isAuthenticated ? (
        <LoginPage onLoginSuccess={handleLoginSuccess} />
      ) : (
        <DashboardContent userEmail={userEmail} onLogout={handleLogout} />
      )}
    </QueryClientProvider>
  );
}

export default App;
