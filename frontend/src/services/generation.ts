import apiClient from './api';
import { API_ENDPOINTS } from '@/utils/constants';
import {
  Generation,
  GenerationRequest,
  Model,
  PaginatedResponse,
} from '@/types';

export const generationService = {
  /**
   * Create a new image generation request
   */
  async create(request: GenerationRequest): Promise<Generation> {
    return apiClient.post<Generation>(API_ENDPOINTS.GENERATE, request);
  },

  /**
   * Get a specific generation by ID
   */
  async getById(id: string): Promise<Generation> {
    return apiClient.get<Generation>(API_ENDPOINTS.GENERATION(id));
  },

  /**
   * Get all generations for the current user
   */
  async getAll(params?: {
    page?: number;
    page_size?: number;
    status?: string;
    model?: string;
  }): Promise<PaginatedResponse<Generation>> {
    return apiClient.get<PaginatedResponse<Generation>>(API_ENDPOINTS.GENERATIONS, {
      params,
    });
  },

  /**
   * Delete a generation
   */
  async delete(id: string): Promise<void> {
    return apiClient.delete(API_ENDPOINTS.GENERATION(id));
  },

  /**
   * Get available models
   */
  async getModels(): Promise<Model[]> {
    return apiClient.get<Model[]>(API_ENDPOINTS.MODELS);
  },

  /**
   * Download generated image
   */
  async downloadImage(generation: Generation): Promise<void> {
    if (!generation.image_url) {
      throw new Error('No image URL available');
    }

    const response = await fetch(generation.image_url);
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `generation-${generation.id}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },
};
