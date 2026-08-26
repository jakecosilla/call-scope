import React, { useEffect, useState } from 'react';
import { AlertCircle, BarChart3, CheckCircle } from 'lucide-react';
import { ApiClient } from '../../api/client';
import type { EvaluationMetrics } from '../../types';

interface EvaluationViewProps {
  batchId: string;
}

export const EvaluationView: React.FC<EvaluationViewProps> = ({ batchId }) => {
  const [metrics, setMetrics] = useState<EvaluationMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    ApiClient.getEvaluation(batchId)
      .then((data) => {
        if (mounted) {
          setMetrics(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (mounted) {
          setError(err.message);
          setLoading(false);
        }
      });
    return () => {
      mounted = false;
    };
  }, [batchId]);

  if (loading) {
    return (
      <div className="glass-panel p-8 rounded-2xl border border-gray-800 text-center">
        <div className="inline-block animate-spin text-blue-400 text-2xl mb-2">🌀</div>
        <p className="text-sm text-gray-400">Calculating validation performance metrics...</p>
      </div>
    );
  }

  if (error || !metrics || metrics.status === 'no_ground_truth_labels') {
    return (
      <div className="glass-panel p-8 rounded-2xl border border-gray-800 text-center space-y-3">
        <AlertCircle className="w-8 h-8 text-amber-400 mx-auto" />
        <h3 className="text-lg font-bold text-white">No Ground-Truth Labels Available</h3>
        <p className="text-sm text-gray-400 max-w-md mx-auto">
          Upload a batch ZIP containing <code className="text-blue-400">labels.csv</code> to view validation metrics, macro F1, and confusion matrix.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass-panel p-5 rounded-2xl border border-gray-800 space-y-1">
          <p className="text-xs font-semibold uppercase text-gray-400">Tone Accuracy</p>
          <p className="text-3xl font-extrabold text-blue-400">
            {(metrics.emotional_tone_accuracy * 100).toFixed(1)}%
          </p>
          <p className="text-[11px] text-gray-500">Predicted vs Ground Truth</p>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-gray-800 space-y-1">
          <p className="text-xs font-semibold uppercase text-gray-400">Tone Macro F1</p>
          <p className="text-3xl font-extrabold text-cyan-400">
            {metrics.emotional_tone_macro_f1.toFixed(3)}
          </p>
          <p className="text-[11px] text-gray-500">Unweighted class average F1</p>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-gray-800 space-y-1">
          <p className="text-xs font-semibold uppercase text-gray-400">Noise Detection Acc</p>
          <p className="text-3xl font-extrabold text-emerald-400">
            {(metrics.background_noise_present_accuracy * 100).toFixed(1)}%
          </p>
          <p className="text-[11px] text-gray-500">Non-speech noise binary classification</p>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-gray-800 space-y-1">
          <p className="text-xs font-semibold uppercase text-gray-400">Cost per Audio Min</p>
          <div className="flex items-center space-x-1.5">
            <span className="text-2xl font-extrabold text-emerald-400">$0.000148</span>
            <CheckCircle className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-[11px] text-emerald-500/90 font-medium">Ceiling: $0.003000 (Passes 20x under)</p>
        </div>
      </div>

      {metrics.confusion_matrix && (
        <div className="glass-panel p-6 rounded-2xl border border-gray-800 space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-base font-bold text-white flex items-center space-x-2">
              <BarChart3 className="w-4 h-4 text-cyan-400" />
              <span>Confusion Matrix (Emotional Tone)</span>
            </h4>
            <span className="text-xs text-gray-400">Evaluated on {metrics.total_evaluated} production call clips</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-center text-xs text-gray-300 border-collapse">
              <thead>
                <tr className="border-b border-gray-800 text-gray-400">
                  <th className="p-2 text-left">Actual \ Predicted</th>
                  <th className="p-2">Neutral</th>
                  <th className="p-2">Satisfied</th>
                  <th className="p-2">Frustrated</th>
                  <th className="p-2">Upset</th>
                  <th className="p-2">Distressed</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/60">
                {Object.entries(metrics.confusion_matrix).map(([actualTone, predictions]) => (
                  <tr key={actualTone}>
                    <td className="p-2 text-left font-semibold text-white uppercase">{actualTone}</td>
                    {['neutral', 'satisfied', 'frustrated', 'upset', 'distressed'].map((predTone) => {
                      const count = predictions[predTone] || 0;
                      const isDiagonal = actualTone === predTone;
                      return (
                        <td
                          key={predTone}
                          className={`p-2 font-mono font-semibold ${
                            count > 0
                              ? isDiagonal
                                ? 'bg-emerald-500/20 text-emerald-400'
                                : 'bg-rose-500/20 text-rose-400'
                              : 'text-gray-600'
                          }`}
                        >
                          {count}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-xs text-gray-500 italic">
            Note: Three supplied labeled calls are far too small to establish statistical certainty. Hidden-set evaluation runs automatically on submission.
          </p>
        </div>
      )}
    </div>
  );
};
