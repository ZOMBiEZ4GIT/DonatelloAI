export enum GenerationStatus {
  PENDING = 'pending',
  QUEUED = 'queued',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

export enum ModelType {
  DALLE_3 = 'dalle-3',
  STABLE_DIFFUSION_XL = 'stable-diffusion-xl',
  ADOBE_FIREFLY = 'adobe-firefly',
  AZURE_AI_IMAGE = 'azure-ai-image',
}

export interface GenerationRequest {
  prompt: string;
  model?: ModelType;
  negative_prompt?: string;
  width?: number;
  height?: number;
  num_images?: number;
  style?: string;
  quality?: 'standard' | 'hd';
  auto_select_model?: boolean;
}

export interface Generation {
  id: string;
  user_id: string;
  prompt: string;
  negative_prompt?: string;
  model_used: ModelType;
  status: GenerationStatus;
  image_url?: string;
  thumbnail_url?: string;
  cost_aud: number;
  generation_time_ms: number;
  metadata?: GenerationMetadata;
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

export interface GenerationMetadata {
  width: number;
  height: number;
  seed?: number;
  steps?: number;
  guidance_scale?: number;
  model_version?: string;
  content_filter_triggered?: boolean;
  pii_detected?: boolean;
}

export interface GenerationProgress {
  generation_id: string;
  status: GenerationStatus;
  progress_percent: number;
  estimated_time_remaining_ms?: number;
  message?: string;
}

export interface Model {
  id: string;
  name: string;
  provider: string;
  type: ModelType;
  cost_per_image_aud: number;
  sla: number;
  enabled: boolean;
  capabilities: ModelCapabilities;
}

export interface ModelCapabilities {
  max_width: number;
  max_height: number;
  supports_negative_prompt: boolean;
  supports_img2img: boolean;
  supports_inpainting: boolean;
  commercial_use: boolean;
}
