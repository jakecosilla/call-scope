import React, { useState } from 'react';
import { AlertCircle, CheckCircle2, Cpu, FileAudio, FolderArchive, Sparkles, Upload } from 'lucide-react';
import { ApiClient } from '../../api/client';
import type { ManifestValidation } from '../../types';

interface UploadSectionProps {
  onBatchCreated: (batchId: string) => void;
}

export const UploadSection: React.FC<UploadSectionProps> = ({ onBatchCreated }) => {
  const [file, setFile] = useState<File | null>(null);
  const [approach, setApproach] = useState<'approach_a' | 'approach_b'>('approach_a');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [manifestValidation, setManifestValidation] = useState<ManifestValidation | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      if (!selected.name.endsWith('.zip')) {
        setError('Please upload a .zip archive containing call audio files and optional labels.csv');
        setFile(null);
        return;
      }
      setFile(selected);
      setError(null);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const selected = e.dataTransfer.files[0];
      if (!selected.name.endsWith('.zip')) {
        setError('Please upload a .zip archive containing call audio files and optional labels.csv');
        return;
      }
      setFile(selected);
      setError(null);
    }
  };

  const handleStartAnalysis = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);

    try {
      const response = await ApiClient.uploadBatch(file, approach);
      if (response.manifest_validation) {
        setManifestValidation(response.manifest_validation);
      }
      onBatchCreated(response.batch_id);
    } catch (err: unknown) {
      const errMessage = err instanceof Error ? err.message : 'Batch upload failed';
      setError(errMessage);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="glass-panel p-6 rounded-2xl border border-gray-800 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center space-x-2">
            <FolderArchive className="w-5 h-5 text-blue-400" />
            <span>Upload Evaluation Batch</span>
          </h2>
          <p className="text-sm text-gray-400 mt-0.5">
            Select a ZIP archive containing production call audio files (.ogg, .wav, .mp3) and an optional labels.csv
          </p>
        </div>

        <div className="flex items-center space-x-2 bg-gray-900/80 p-1.5 rounded-xl border border-gray-800">
          <button
            type="button"
            onClick={() => setApproach('approach_a')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center space-x-1.5 ${
              approach === 'approach_a'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            <Cpu className="w-3.5 h-3.5" />
            <span>Approach A (Acoustic SER)</span>
          </button>
          <button
            type="button"
            onClick={() => setApproach('approach_b')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center space-x-1.5 ${
              approach === 'approach_b'
                ? 'bg-purple-600 text-white shadow-sm'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Approach B (Foundation SER)</span>
          </button>
        </div>
      </div>

      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all ${
          file
            ? 'border-blue-500/60 bg-blue-500/5'
            : 'border-gray-700/80 hover:border-gray-600 bg-gray-900/40'
        }`}
      >
        <input
          type="file"
          accept=".zip"
          id="batch-file-input"
          onChange={handleFileChange}
          className="hidden"
        />

        {file ? (
          <div className="flex flex-col items-center space-y-3">
            <div className="w-12 h-12 rounded-xl bg-blue-500/20 text-blue-400 flex items-center justify-center">
              <FileAudio className="w-6 h-6" />
            </div>
            <div>
              <p className="text-base font-semibold text-white">{file.name}</p>
              <p className="text-xs text-gray-400">{(file.size / (1024 * 1024)).toFixed(2)} MB archive ready</p>
            </div>
            <label
              htmlFor="batch-file-input"
              className="text-xs text-blue-400 hover:text-blue-300 cursor-pointer font-medium"
            >
              Choose different file
            </label>
          </div>
        ) : (
          <label htmlFor="batch-file-input" className="cursor-pointer flex flex-col items-center space-y-3">
            <div className="w-12 h-12 rounded-xl bg-gray-800 text-gray-400 flex items-center justify-center">
              <Upload className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-200">
                Drag and drop evaluation batch <span className="text-blue-400">ZIP</span> here
              </p>
              <p className="text-xs text-gray-400 mt-1">Supports call_001.ogg, call_002.ogg, call_003.ogg & labels.csv</p>
            </div>
          </label>
        )}
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm flex items-center space-x-2">
          <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {manifestValidation && (
        <div className="p-4 rounded-xl bg-gray-900/80 border border-gray-800 text-sm space-y-2">
          <div className="flex items-center space-x-2 text-emerald-400 font-semibold">
            <CheckCircle2 className="w-4 h-4" />
            <span>CSV Manifest Verified ({manifestValidation.matched_files} matched files)</span>
          </div>
          {manifestValidation.unmatched_audio_files.length > 0 && (
            <p className="text-xs text-amber-400">
              Unmatched Audio Files: {manifestValidation.unmatched_audio_files.join(', ')}
            </p>
          )}
        </div>
      )}

      <div className="flex justify-end">
        <button
          onClick={handleStartAnalysis}
          disabled={!file || uploading}
          className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-sm font-medium rounded-xl shadow-lg shadow-blue-500/20 disabled:opacity-50 transition-all flex items-center space-x-2"
        >
          {uploading ? (
            <span>Extracting & Processing Batch...</span>
          ) : (
            <>
              <Upload className="w-4 h-4" />
              <span>Start Batch Analysis</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
