import { useState } from 'react';
import { PromptInput, ModelSelector, GenerationQueue, ProgressTracker } from '@/components/generation';
import { useGeneration } from '@/hooks';
import { ModelType, GenerationRequest } from '@/types';
import toast from 'react-hot-toast';

export const Generate = () => {
  const [prompt, setPrompt] = useState('');
  const [selectedModel, setSelectedModel] = useState<ModelType | undefined>();
  const [autoSelectModel, setAutoSelectModel] = useState(true);
  const [activeGenerationId, setActiveGenerationId] = useState<string | null>(null);

  const { create, isCreating } = useGeneration();

  const handleGenerate = () => {
    const request: GenerationRequest = {
      prompt,
      model: autoSelectModel ? undefined : selectedModel,
      auto_select_model: autoSelectModel,
    };

    create(request, {
      onSuccess: (generation) => {
        setActiveGenerationId(generation.id);
        setPrompt('');
      },
    });
  };

  return (
    <div className="mx-auto max-w-7xl p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Generate Images</h1>
        <p className="text-gray-600">Create stunning images with AI-powered generation</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Generation Form */}
        <div className="lg:col-span-2 space-y-6">
          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <PromptInput
              value={prompt}
              onChange={setPrompt}
              onSubmit={handleGenerate}
              disabled={isCreating}
            />
          </div>

          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <ModelSelector
              value={selectedModel}
              onChange={setSelectedModel}
              autoSelect={autoSelectModel}
              onAutoSelectChange={setAutoSelectModel}
            />
          </div>

          {activeGenerationId && (
            <ProgressTracker
              sessionId={activeGenerationId}
              onComplete={() => {
                toast.success('Image generated successfully!');
                setActiveGenerationId(null);
              }}
              onFailed={(data) => {
                toast.error(data.message || 'Generation failed');
                setActiveGenerationId(null);
              }}
            />
          )}
        </div>

        {/* Info Panel */}
        <div className="space-y-6">
          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <h3 className="mb-4 font-semibold text-gray-900">Tips for Better Results</h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>• Be specific and descriptive</li>
              <li>• Include style, mood, and lighting details</li>
              <li>• Mention artistic styles or references</li>
              <li>• Use negative prompts to avoid unwanted elements</li>
            </ul>
          </div>

          <div className="rounded-lg border border-blue-200 bg-blue-50 p-6">
            <h3 className="mb-2 font-semibold text-blue-900">Auto-Select Mode</h3>
            <p className="text-sm text-blue-700">
              Our AI analyzes your prompt and automatically selects the best model based on complexity, cost, and quality requirements.
            </p>
          </div>
        </div>
      </div>

      {/* Recent Generations */}
      <div className="mt-12">
        <GenerationQueue />
      </div>
    </div>
  );
};
