import React from 'react';
import { AlertTriangle, CheckCircle2, Clock, Loader2 } from 'lucide-react';
import type { BatchSummary } from '../../types';

interface BatchProgressProps {
  batch: BatchSummary;
}

export const BatchProgress: React.FC<BatchProgressProps> = ({ batch }) => {
  const isTerminal =
    batch.status === 'completed' || batch.status === 'completed_with_errors' || batch.status === 'failed';

  return (
    <div className="glass-panel p-6 rounded-2xl border border-gray-800 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-2">
            <h3 className="text-lg font-bold text-white">Batch Analysis Progress</h3>
            <span
              className={`px-2.5 py-0.5 text-xs font-semibold rounded-full border ${
                batch.status === 'completed'
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                  : batch.status === 'completed_with_errors'
                  ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                  : batch.status === 'failed'
                  ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                  : 'bg-blue-500/10 text-blue-400 border-blue-500/20'
              }`}
            >
              {batch.status.replace('_', ' ').toUpperCase()}
            </span>
          </div>
          <p className="text-xs text-gray-400 mt-1">Batch ID: {batch.batch_id}</p>
        </div>

        <div className="flex items-center space-x-4 text-sm">
          <div className="text-right">
            <span className="text-2xl font-bold text-white">{batch.progress_percentage}%</span>
            <p className="text-xs text-gray-400">
              {batch.processed_files + batch.failed_files} / {batch.total_files} files processed
            </p>
          </div>
        </div>
      </div>

      <div className="w-full bg-gray-900 rounded-full h-3 overflow-hidden border border-gray-800 relative">
        <div
          className={`h-full transition-all duration-500 rounded-full ${
            batch.status === 'completed'
              ? 'bg-gradient-to-r from-blue-500 to-emerald-500'
              : batch.status === 'completed_with_errors'
              ? 'bg-gradient-to-r from-blue-500 to-amber-500'
              : batch.status === 'failed'
              ? 'bg-rose-500'
              : 'bg-gradient-to-r from-blue-600 to-cyan-400 animate-pulse'
          }`}
          style={{ width: `${Math.max(batch.progress_percentage, 5)}%` }}
        />
      </div>

      <div className="flex items-center justify-between text-xs text-gray-400 pt-2 border-t border-gray-800/80">
        <div className="flex items-center space-x-4">
          <span className="flex items-center space-x-1 text-emerald-400">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>{batch.processed_files} Completed</span>
          </span>
          {batch.failed_files > 0 && (
            <span className="flex items-center space-x-1 text-rose-400">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>{batch.failed_files} Failed (isolated)</span>
            </span>
          )}
        </div>

        <div className="flex items-center space-x-1">
          {!isTerminal ? (
            <>
              <Loader2 className="w-3.5 h-3.5 text-blue-400 animate-spin" />
              <span>Processing inference...</span>
            </>
          ) : (
            <>
              <Clock className="w-3.5 h-3.5 text-gray-400" />
              <span>Finished at {batch.completed_at ? new Date(batch.completed_at).toLocaleTimeString() : 'now'}</span>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
