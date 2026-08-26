export type EmotionalTone = 'neutral' | 'satisfied' | 'frustrated' | 'upset' | 'distressed';
export type EmotionalIntensity = 'low' | 'medium' | 'high';
export type BackgroundNoiseSeverity = 'none' | 'low' | 'medium' | 'high';
export type AudioQuality = 'clear' | 'slightly_impaired' | 'severely_impaired';

export interface PredictionResult {
  emotional_tone: EmotionalTone;
  emotional_intensity: EmotionalIntensity;
  background_noise_present: boolean;
  background_noise_type: string;
  background_noise_severity: BackgroundNoiseSeverity;
  audio_quality: AudioQuality;
  speaker_overlap_present: boolean;
  long_silence_present: boolean;
  confidence: number;
}

export interface InternalInferenceMetadata {
  pipeline_version: string;
  approach: string;
  preprocessing_duration_seconds: number;
  inference_duration_seconds: number;
  total_duration_seconds: number;
  real_time_factor: number;
  audio_duration_seconds: number;
  estimated_cost_usd: number;
  estimated_cost_per_audio_minute_usd: number;
  raw_acoustic_features?: Record<string, unknown>;
}

export interface CallAnalysisFileResult {
  file_id: string;
  filename: string;
  status: 'completed' | 'failed' | 'processing';
  error_message?: string;
  prediction?: PredictionResult;
  metadata?: InternalInferenceMetadata;
}

export interface BatchSummary {
  batch_id: string;
  status: 'uploaded' | 'validating' | 'processing' | 'completed' | 'completed_with_errors' | 'failed';
  total_files: number;
  processed_files: number;
  failed_files: number;
  progress_percentage: number;
  created_at: string;
  completed_at?: string;
  files: CallAnalysisFileResult[];
}

export interface ManifestValidation {
  total_manifest_rows: number;
  matched_files: number;
  unmatched_audio_files: string[];
  missing_audio_files: string[];
  duplicate_manifest_rows: string[];
}

export interface UploadResponse {
  batch_id: string;
  status: string;
  manifest_validation?: ManifestValidation;
}

export interface EvaluationMetrics {
  status: string;
  total_evaluated: number;
  emotional_tone_accuracy: number;
  emotional_tone_macro_f1: number;
  emotional_intensity_accuracy: number;
  background_noise_present_accuracy: number;
  background_noise_severity_accuracy: number;
  audio_quality_accuracy: number;
  speaker_overlap_accuracy: number;
  long_silence_accuracy: number;
  per_class_metrics?: Record<string, { precision: number; recall: number; f1: number; support: number }>;
  confusion_matrix?: Record<string, Record<string, number>>;
  sample_size_note?: string;
}
