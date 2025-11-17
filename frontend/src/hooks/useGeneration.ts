import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { generationService } from '@/services';
import { GenerationRequest, Generation } from '@/types';
import { QUERY_KEYS, TOAST_MESSAGES } from '@/utils/constants';
import toast from 'react-hot-toast';

export const useGeneration = () => {
  const queryClient = useQueryClient();

  // Create generation mutation
  const createMutation = useMutation({
    mutationFn: (request: GenerationRequest) => generationService.create(request),
    onSuccess: () => {
      toast.success(TOAST_MESSAGES.GENERATION_STARTED);
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.GENERATIONS });
    },
    onError: (error: Error) => {
      toast.error(error.message || TOAST_MESSAGES.GENERATION_FAILED);
    },
  });

  // Delete generation mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => generationService.delete(id),
    onSuccess: () => {
      toast.success(TOAST_MESSAGES.DELETE_SUCCESS);
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.GENERATIONS });
    },
    onError: (error: Error) => {
      toast.error(error.message || TOAST_MESSAGES.DELETE_ERROR);
    },
  });

  return {
    create: createMutation.mutate,
    delete: deleteMutation.mutate,
    isCreating: createMutation.isPending,
    isDeleting: deleteMutation.isPending,
  };
};

export const useGenerations = (params?: {
  page?: number;
  page_size?: number;
  status?: string;
  model?: string;
}) => {
  return useQuery({
    queryKey: [...QUERY_KEYS.GENERATIONS, params],
    queryFn: () => generationService.getAll(params),
  });
};

export const useGenerationById = (id: string) => {
  return useQuery({
    queryKey: QUERY_KEYS.GENERATION(id),
    queryFn: () => generationService.getById(id),
    enabled: !!id,
  });
};

export const useModels = () => {
  return useQuery({
    queryKey: QUERY_KEYS.MODELS,
    queryFn: () => generationService.getModels(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useDownloadImage = () => {
  const downloadMutation = useMutation({
    mutationFn: (generation: Generation) => generationService.downloadImage(generation),
    onSuccess: () => {
      toast.success('Image downloaded successfully');
    },
    onError: () => {
      toast.error('Failed to download image');
    },
  });

  return {
    download: downloadMutation.mutate,
    isDownloading: downloadMutation.isPending,
  };
};
