import { GENERATION_LIMITS } from './constants';

export const validatePrompt = (prompt: string): { valid: boolean; error?: string } => {
  if (!prompt || prompt.trim().length === 0) {
    return { valid: false, error: 'Prompt is required' };
  }

  if (prompt.length < GENERATION_LIMITS.MIN_PROMPT_LENGTH) {
    return {
      valid: false,
      error: `Prompt must be at least ${GENERATION_LIMITS.MIN_PROMPT_LENGTH} characters`
    };
  }

  if (prompt.length > GENERATION_LIMITS.MAX_PROMPT_LENGTH) {
    return {
      valid: false,
      error: `Prompt must be less than ${GENERATION_LIMITS.MAX_PROMPT_LENGTH} characters`
    };
  }

  // Basic PII detection (more comprehensive on backend)
  const piiPatterns = [
    /\b\d{3}-\d{2}-\d{4}\b/, // SSN
    /\b\d{16}\b/, // Credit card
    /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/i, // Email
  ];

  for (const pattern of piiPatterns) {
    if (pattern.test(prompt)) {
      return {
        valid: false,
        error: 'Prompt appears to contain sensitive information (PII). Please remove before continuing.'
      };
    }
  }

  return { valid: true };
};

export const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

export const validateBudget = (budget: number): { valid: boolean; error?: string } => {
  if (budget < 0) {
    return { valid: false, error: 'Budget must be a positive number' };
  }

  if (budget > 1000000) {
    return { valid: false, error: 'Budget exceeds maximum allowed value' };
  }

  return { valid: true };
};

export const sanitizeInput = (input: string): string => {
  // Remove potential XSS vectors
  return input
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
    .replace(/\//g, '&#x2F;');
};
