import { useModels } from '@/hooks';
import { ModelType } from '@/types';
import { formatCurrency } from '@/utils';
import { cn } from '@/utils';
import { LoadingSpinner } from '@/components/common';

interface ModelSelectorProps {
  value?: ModelType;
  onChange: (model: ModelType | undefined) => void;
  autoSelect?: boolean;
  onAutoSelectChange?: (auto: boolean) => void;
}

export const ModelSelector = ({ value, onChange, autoSelect, onAutoSelectChange }: ModelSelectorProps) => {
  const { data: models, isLoading } = useModels();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-4">
        <LoadingSpinner />
      </div>
    );
  }

  const enabledModels = models?.filter((m) => m.enabled) || [];

  return (
    <div className="space-y-3">
      <label className="block text-sm font-medium text-gray-700">
        Model Selection
      </label>

      {onAutoSelectChange && (
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={autoSelect}
            onChange={(e) => onAutoSelectChange(e.target.checked)}
            className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-2 focus:ring-primary-500"
          />
          <span className="text-sm text-gray-700">Auto-select best model</span>
        </label>
      )}

      {!autoSelect && (
        <div className="grid gap-3 sm:grid-cols-2">
          {enabledModels.map((model) => (
            <button
              key={model.id}
              onClick={() => onChange(model.type)}
              className={cn(
                'rounded-lg border-2 p-4 text-left transition-all',
                value === model.type
                  ? 'border-primary-600 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300'
              )}
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-medium text-gray-900">{model.name}</h3>
                  <p className="text-xs text-gray-500">{model.provider}</p>
                </div>
                {value === model.type && (
                  <div className="h-5 w-5 rounded-full bg-primary-600 flex items-center justify-center">
                    <svg className="h-3 w-3 text-white" fill="currentColor" viewBox="0 0 12 12">
                      <path d="M3.707 5.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4a1 1 0 00-1.414-1.414L5 6.586 3.707 5.293z" />
                    </svg>
                  </div>
                )}
              </div>
              <div className="mt-2 text-sm text-gray-600">
                <p>{formatCurrency(model.cost_per_image_aud)} per image</p>
                <p className="text-xs">SLA: {model.sla}%</p>
              </div>
            </button>
          ))}
        </div>
      )}

      {autoSelect && (
        <div className="rounded-lg bg-blue-50 p-4 text-sm text-blue-800">
          Our AI will automatically select the best model based on your prompt complexity, budget, and quality requirements.
        </div>
      )}
    </div>
  );
};
