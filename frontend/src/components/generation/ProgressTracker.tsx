import { useState } from 'react';
import { CheckCircle, Loader, XCircle } from 'lucide-react';
import { GenerationProgress, GenerationStatus } from '@/types';
import { useWebSocket } from '@/hooks';
import { formatDuration } from '@/utils';

interface ProgressTrackerProps {
  sessionId: string;
  onComplete?: (data: GenerationProgress) => void;
  onFailed?: (data: GenerationProgress) => void;
}

export const ProgressTracker = ({ sessionId, onComplete, onFailed }: ProgressTrackerProps) => {
  const [progress, setProgress] = useState<GenerationProgress | null>(null);

  useWebSocket({
    sessionId,
    onStarted: (data) => setProgress(data),
    onProgress: (data) => setProgress(data),
    onCompleted: (data) => {
      setProgress(data);
      onComplete?.(data);
    },
    onFailed: (data) => {
      setProgress(data);
      onFailed?.(data);
    },
  });

  if (!progress) {
    return null;
  }

  const isComplete = progress.status === GenerationStatus.COMPLETED;
  const isFailed = progress.status === GenerationStatus.FAILED;
  const isProcessing = !isComplete && !isFailed;

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="flex items-center gap-3">
        {isProcessing && <Loader className="h-5 w-5 animate-spin text-blue-500" />}
        {isComplete && <CheckCircle className="h-5 w-5 text-success-500" />}
        {isFailed && <XCircle className="h-5 w-5 text-error-500" />}

        <div className="flex-1">
          <p className="font-medium text-gray-900">
            {progress.message || `${progress.status}...`}
          </p>
          {progress.estimated_time_remaining_ms && (
            <p className="text-sm text-gray-600">
              ~{formatDuration(progress.estimated_time_remaining_ms)} remaining
            </p>
          )}
        </div>

        <div className="text-right">
          <p className="text-2xl font-bold text-gray-900">{progress.progress_percent}%</p>
        </div>
      </div>

      {isProcessing && (
        <div className="mt-3">
          <div className="h-2 overflow-hidden rounded-full bg-gray-200">
            <div
              className="h-full bg-primary-600 transition-all duration-300"
              style={{ width: `${progress.progress_percent}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
};
