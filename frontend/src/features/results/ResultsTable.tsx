import React, { useState } from 'react';
import { FileCode, FileSpreadsheet, Volume2, Waves } from 'lucide-react';
import { ApiClient } from '../../api/client';
import type { BatchSummary, CallAnalysisFileResult } from '../../types';

interface ResultsTableProps {
  batch: BatchSummary;
}

export const ResultsTable: React.FC<ResultsTableProps> = ({ batch }) => {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredFiles = batch.files.filter((f) =>
    f.filename.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getToneBadge = (tone?: string) => {
    switch (tone) {
      case 'satisfied':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'upset':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
      case 'frustrated':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'distressed':
        return 'bg-purple-500/10 text-purple-400 border-purple-500/20';
      default:
        return 'bg-gray-500/10 text-gray-300 border-gray-500/20';
    }
  };

  const getQualityBadge = (quality?: string) => {
    switch (quality) {
      case 'clear':
        return 'bg-emerald-500/10 text-emerald-400';
      case 'slightly_impaired':
        return 'bg-amber-500/10 text-amber-400';
      case 'severely_impaired':
        return 'bg-rose-500/10 text-rose-400';
      default:
        return 'bg-gray-500/10 text-gray-400';
    }
  };

  return (
    <div className="glass-panel rounded-2xl border border-gray-800 overflow-hidden space-y-4 p-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center space-x-2">
            <Volume2 className="w-5 h-5 text-blue-400" />
            <span>Analysis Results ({batch.files.length} audio clips)</span>
          </h3>
          <p className="text-xs text-gray-400">Structured assessment prediction outputs for production call audio</p>
        </div>

        <div className="flex items-center space-x-3">
          <input
            type="text"
            placeholder="Search audio filename..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="bg-gray-900/80 border border-gray-800 rounded-xl px-3 py-1.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />

          <a
            href={ApiClient.getExportCsvUrl(batch.batch_id)}
            download
            className="px-3 py-1.5 bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 border border-blue-500/30 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition"
          >
            <FileSpreadsheet className="w-3.5 h-3.5" />
            <span>Download CSV</span>
          </a>

          <a
            href={ApiClient.getExportJsonUrl(batch.batch_id)}
            download
            className="px-3 py-1.5 bg-purple-600/20 hover:bg-purple-600/30 text-purple-400 border border-purple-500/30 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition"
          >
            <FileCode className="w-3.5 h-3.5" />
            <span>Download JSON</span>
          </a>
        </div>
      </div>

      <div className="overflow-x-auto rounded-xl border border-gray-800">
        <table className="w-full text-left text-xs text-gray-300">
          <thead className="bg-gray-900/90 uppercase font-semibold text-gray-400 border-b border-gray-800">
            <tr>
              <th className="py-3 px-4">Filename</th>
              <th className="py-3 px-4">Emotional Tone</th>
              <th className="py-3 px-4">Intensity</th>
              <th className="py-3 px-4">Background Noise</th>
              <th className="py-3 px-4">Audio Quality</th>
              <th className="py-3 px-4">Overlap</th>
              <th className="py-3 px-4">Long Silence</th>
              <th className="py-3 px-4">Confidence</th>
              <th className="py-3 px-4">Latency / Cost</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800/60 bg-gray-900/30">
            {filteredFiles.map((f: CallAnalysisFileResult) => (
              <tr key={f.file_id} className="hover:bg-gray-800/40 transition">
                <td className="py-3.5 px-4 font-mono font-medium text-white flex items-center space-x-2">
                  <Waves className="w-3.5 h-3.5 text-blue-400" />
                  <span>{f.filename}</span>
                </td>

                <td className="py-3.5 px-4">
                  {f.prediction ? (
                    <span
                      className={`px-2.5 py-1 rounded-full border text-[11px] font-semibold uppercase ${getToneBadge(
                        f.prediction.emotional_tone
                      )}`}
                    >
                      {f.prediction.emotional_tone}
                    </span>
                  ) : (
                    <span className="text-rose-400 font-semibold">FAILED</span>
                  )}
                </td>

                <td className="py-3.5 px-4 font-medium text-gray-300">
                  {f.prediction ? f.prediction.emotional_intensity : '-'}
                </td>

                <td className="py-3.5 px-4">
                  {f.prediction ? (
                    <div>
                      <span
                        className={`font-semibold ${
                          f.prediction.background_noise_present ? 'text-amber-400' : 'text-gray-400'
                        }`}
                      >
                        {f.prediction.background_noise_present ? 'PRESENT' : 'None'}
                      </span>
                      {f.prediction.background_noise_present && (
                        <p className="text-[10px] text-gray-400">
                          {f.prediction.background_noise_type || 'noise'} ({f.prediction.background_noise_severity})
                        </p>
                      )}
                    </div>
                  ) : (
                    '-'
                  )}
                </td>

                <td className="py-3.5 px-4">
                  {f.prediction ? (
                    <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${getQualityBadge(f.prediction.audio_quality)}`}>
                      {f.prediction.audio_quality.replace('_', ' ')}
                    </span>
                  ) : (
                    '-'
                  )}
                </td>

                <td className="py-3.5 px-4">
                  {f.prediction ? (
                    <span
                      className={`font-medium ${
                        f.prediction.speaker_overlap_present ? 'text-amber-400 font-semibold' : 'text-gray-500'
                      }`}
                    >
                      {f.prediction.speaker_overlap_present ? 'Yes' : 'No'}
                    </span>
                  ) : (
                    '-'
                  )}
                </td>

                <td className="py-3.5 px-4">
                  {f.prediction ? (
                    <span
                      className={`font-medium ${
                        f.prediction.long_silence_present ? 'text-amber-400 font-semibold' : 'text-gray-500'
                      }`}
                    >
                      {f.prediction.long_silence_present ? 'Yes' : 'No'}
                    </span>
                  ) : (
                    '-'
                  )}
                </td>

                <td className="py-3.5 px-4">
                  {f.prediction ? (
                    <div className="flex items-center space-x-2">
                      <div className="w-12 bg-gray-800 rounded-full h-1.5 overflow-hidden">
                        <div
                          className="bg-blue-500 h-full rounded-full"
                          style={{ width: `${f.prediction.confidence * 100}%` }}
                        />
                      </div>
                      <span className="font-mono text-[11px] font-semibold text-white">
                        {f.prediction.confidence.toFixed(2)}
                      </span>
                    </div>
                  ) : (
                    '-'
                  )}
                </td>

                <td className="py-3.5 px-4 font-mono text-[11px] text-gray-400">
                  {f.metadata ? (
                    <div>
                      <span>{f.metadata.total_duration_seconds}s</span>
                      <p className="text-[10px] text-emerald-400">${f.metadata.estimated_cost_per_audio_minute_usd.toFixed(6)}/min</p>
                    </div>
                  ) : (
                    <span className="text-rose-400 text-[10px]">{f.error_message || 'Error'}</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
