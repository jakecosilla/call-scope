import React, { useState } from 'react';
import JSZip from 'jszip';
import { AlertCircle, CheckCircle2, Cpu, FileAudio, FolderArchive, Sparkles, Upload } from 'lucide-react';
import { ApiClient } from '../../api/client';
import type { ManifestValidation } from '../../types';

interface UploadSectionProps {
  onBatchCreated: (batchId: string) => void;
}

export const UploadSection: React.FC<UploadSectionProps> = ({ onBatchCreated }) => {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [approach, setApproach] = useState<'approach_a' | 'approach_b'>('approach_a');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [manifestValidation, setManifestValidation] = useState<ManifestValidation | null>(null);

  const ALLOWED_EXTENSIONS = ['.zip', '.ogg', '.wav', '.mp3', '.flac', '.m4a', '.aac', '.csv'];

  const processSelectedFiles = (files: FileList | File[]) => {
    const fileArray = Array.from(files);
    const valid = fileArray.filter(f => {
      const ext = f.name.substring(f.name.lastIndexOf('.')).toLowerCase();
      return ALLOWED_EXTENSIONS.includes(ext);
    });

    if (valid.length === 0) {
      setError('No supported audio files (.ogg, .wav, .mp3, .flac, .m4a) or .zip archives found.');
      setSelectedFiles([]);
      return;
    }

    setSelectedFiles(valid);
    setError(null);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processSelectedFiles(e.target.files);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processSelectedFiles(e.dataTransfer.files);
    }
  };

  const handleStartAnalysis = async () => {
    if (selectedFiles.length === 0) return;
    setUploading(true);
    setError(null);

    try {
      let uploadFile: File;

      if (selectedFiles.length === 1) {
        uploadFile = selectedFiles[0];
      } else {
        const zip = new JSZip();
        selectedFiles.forEach(f => {
          const cleanName = f.name.split('/').pop() || f.name;
          zip.file(cleanName, f);
        });
        const zipBlob = await zip.generateAsync({ type: 'blob' });
        uploadFile = new File([zipBlob], 'callscope_batch.zip', { type: 'application/zip' });
      }

      const response = await ApiClient.uploadBatch(uploadFile, approach);
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
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center space-x-2">
            <FolderArchive className="w-5 h-5 text-blue-400" />
            <span>Upload Evaluation Batch</span>
          </h2>
          <p className="text-xs text-gray-400 mt-1">
            Upload audio clips or ZIP archives for acoustic & prosody analysis.
          </p>
        </div>

        <div className="flex items-center bg-gray-900/80 p-1.5 rounded-xl border border-gray-800 self-start md:self-auto">
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
            <span>Acoustic Signal Engine</span>
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
            <span>Foundation SER Model</span>
          </button>
        </div>
      </div>

      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all ${
          selectedFiles.length > 0
            ? 'border-blue-500/60 bg-blue-500/5'
            : 'border-gray-700/80 hover:border-gray-600 bg-gray-900/40'
        }`}
      >
        <input
          type="file"
          accept=".zip,.ogg,.wav,.mp3,.flac,.m4a,.aac,.csv"
          id="batch-file-input"
          multiple
          onChange={handleFileChange}
          className="hidden"
        />

        {selectedFiles.length > 0 ? (
          <div className="flex flex-col items-center space-y-3">
            <div className="w-12 h-12 rounded-xl bg-blue-500/20 text-blue-400 flex items-center justify-center">
              <FileAudio className="w-6 h-6" />
            </div>
            <div>
              <p className="text-base font-semibold text-white">
                {selectedFiles.length === 1 ? selectedFiles[0].name : `${selectedFiles.length} files selected`}
              </p>
              <p className="text-xs text-gray-400 max-w-lg truncate">
                {selectedFiles.length === 1
                  ? `${(selectedFiles[0].size / (1024 * 1024)).toFixed(2)} MB file ready for analysis`
                  : selectedFiles.map(f => f.name.split('/').pop()).join(', ')}
              </p>
            </div>
            <label
              htmlFor="batch-file-input"
              className="text-xs text-blue-400 hover:text-blue-300 cursor-pointer font-medium"
            >
              Choose different files
            </label>
          </div>
        ) : (
          <div className="flex flex-col items-center space-y-3">
            <div className="w-12 h-12 rounded-xl bg-gray-800 text-gray-400 flex items-center justify-center">
              <Upload className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-200">
                Drag & drop evaluation audio clip(s) or <span className="text-blue-400">ZIP</span> archive
              </p>
              <p className="text-xs text-gray-400 mt-1">
                Supported formats: .ogg, .wav, .mp3, .flac, .m4a, .zip with optional labels.csv manifest
              </p>
            </div>
            <div className="pt-2">
              <label
                htmlFor="batch-file-input"
                className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-xl cursor-pointer shadow-md shadow-blue-500/20 transition-all inline-block"
              >
                Browse Files
              </label>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm flex items-center space-x-2">
          <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {manifestValidation && manifestValidation.total_manifest_rows !== undefined && (
        <div className="p-4 rounded-xl bg-gray-900/90 border border-gray-800 text-xs space-y-2">
          <div className="flex items-center justify-between text-gray-300 font-semibold">
            <span className="flex items-center space-x-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Manifest Summary</span>
            </span>
            <span>{(manifestValidation.matched_files ?? 0)} / {(manifestValidation.total_manifest_rows ?? 0)} clips matched</span>
          </div>
          {(manifestValidation.unmatched_audio_files ?? []).length > 0 && (
            <p className="text-amber-400">Unmatched audio clips: {manifestValidation.unmatched_audio_files.join(', ')}</p>
          )}
          {(manifestValidation.missing_audio_files ?? []).length > 0 && (
            <p className="text-rose-400">Missing audio clips: {manifestValidation.missing_audio_files.join(', ')}</p>
          )}
        </div>
      )}

      <div className="flex justify-end">
        <button
          type="button"
          disabled={selectedFiles.length === 0 || uploading}
          onClick={handleStartAnalysis}
          className={`px-6 py-2.5 rounded-xl font-semibold text-sm transition-all flex items-center space-x-2 ${
            selectedFiles.length > 0 && !uploading
              ? 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/25 cursor-pointer'
              : 'bg-gray-800 text-gray-500 cursor-not-allowed border border-gray-700'
          }`}
        >
          {uploading ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              <span>Uploading & Analyzing...</span>
            </>
          ) : (
            <span>Start Analysis Batch</span>
          )}
        </button>
      </div>
    </div>
  );
};
