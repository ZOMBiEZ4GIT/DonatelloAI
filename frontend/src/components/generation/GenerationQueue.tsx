import { useGenerations } from '@/hooks';
import { LoadingSpinner } from '@/components/common';
import { ImageViewer } from './ImageViewer';
import { formatRelativeTime, formatCurrency } from '@/utils';
import { GenerationStatus } from '@/types';
import { Clock, CheckCircle, XCircle, Loader } from 'lucide-react';

export const GenerationQueue = () => {
  const { data, isLoading } = useGenerations({ page: 1, page_size: 10 });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const generations = data?.data || [];

  if (generations.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-gray-50 p-8 text-center">
        <p className="text-gray-600">No generations yet. Start creating!</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">Recent Generations</h2>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {generations.map((generation) => {
          const statusIcons = {
            [GenerationStatus.PENDING]: <Clock className="h-4 w-4 text-gray-400" />,
            [GenerationStatus.QUEUED]: <Clock className="h-4 w-4 text-blue-500" />,
            [GenerationStatus.PROCESSING]: <Loader className="h-4 w-4 animate-spin text-blue-500" />,
            [GenerationStatus.COMPLETED]: <CheckCircle className="h-4 w-4 text-success-500" />,
            [GenerationStatus.FAILED]: <XCircle className="h-4 w-4 text-error-500" />,
            [GenerationStatus.CANCELLED]: <XCircle className="h-4 w-4 text-gray-400" />,
          };

          return (
            <div
              key={generation.id}
              className="overflow-hidden rounded-lg border border-gray-200 bg-white transition-shadow hover:shadow-md"
            >
              {generation.status === GenerationStatus.COMPLETED && generation.image_url ? (
                <ImageViewer generation={generation} />
              ) : (
                <div className="flex aspect-square items-center justify-center bg-gray-100">
                  <div className="text-center">
                    {statusIcons[generation.status]}
                    <p className="mt-2 text-sm capitalize text-gray-600">{generation.status}</p>
                  </div>
                </div>
              )}
              <div className="p-3">
                <p className="truncate text-sm text-gray-700">{generation.prompt}</p>
                <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
                  <span>{formatRelativeTime(generation.created_at)}</span>
                  <span>{formatCurrency(generation.cost_aud)}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
