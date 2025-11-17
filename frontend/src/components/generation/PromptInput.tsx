import { useState } from 'react';
import { Sparkles } from 'lucide-react';
import { validatePrompt, GENERATION_LIMITS } from '@/utils';
import { cn } from '@/utils';

interface PromptInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
}

export const PromptInput = ({ value, onChange, onSubmit, disabled }: PromptInputProps) => {
  const [error, setError] = useState<string | null>(null);

  const handleChange = (newValue: string) => {
    onChange(newValue);
    const validation = validatePrompt(newValue);
    setError(validation.valid ? null : validation.error || null);
  };

  const handleSubmit = () => {
    const validation = validatePrompt(value);
    if (!validation.valid) {
      setError(validation.error || null);
      return;
    }
    onSubmit();
  };

  const characterCount = value.length;
  const maxLength = GENERATION_LIMITS.MAX_PROMPT_LENGTH;

  return (
    <div className="space-y-2">
      <label htmlFor="prompt" className="block text-sm font-medium text-gray-700">
        Describe your image
      </label>
      <div className="relative">
        <textarea
          id="prompt"
          value={value}
          onChange={(e) => handleChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
              handleSubmit();
            }
          }}
          disabled={disabled}
          placeholder="A serene landscape with mountains at sunset..."
          className={cn(
            'w-full rounded-lg border px-4 py-3 pr-12 text-gray-900 placeholder-gray-400 transition-colors',
            'focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20',
            'disabled:cursor-not-allowed disabled:bg-gray-100 disabled:text-gray-500',
            error ? 'border-error-500' : 'border-gray-300',
            'min-h-32 resize-y'
          )}
          maxLength={maxLength}
        />
        <div className="absolute bottom-3 right-3 text-xs text-gray-400">
          {characterCount}/{maxLength}
        </div>
      </div>
      {error && (
        <p className="text-sm text-error-600">{error}</p>
      )}
      <button
        onClick={handleSubmit}
        disabled={disabled || !!error || !value.trim()}
        className={cn(
          'flex w-full items-center justify-center gap-2 rounded-lg px-6 py-3 font-medium text-white transition-colors',
          'disabled:cursor-not-allowed disabled:bg-gray-300',
          !disabled && !error && value.trim()
            ? 'bg-primary-600 hover:bg-primary-700'
            : 'bg-gray-300'
        )}
      >
        <Sparkles size={20} />
        Generate Image
      </button>
      <p className="text-xs text-gray-500">
        Press Ctrl+Enter to generate
      </p>
    </div>
  );
};
