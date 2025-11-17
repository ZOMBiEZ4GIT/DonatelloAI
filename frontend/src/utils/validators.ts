import { GENERATION_LIMITS } from './constants';

export interface ValidationResult {
  valid: boolean;
  error?: string;
  warnings?: string[];
  detectedIssues?: string[];
}

export const validatePrompt = (prompt: string): ValidationResult => {
  const warnings: string[] = [];
  const detectedIssues: string[] = [];

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

  // Comprehensive PII detection (enhanced patterns)
  const piiPatterns: { pattern: RegExp; type: string; severity: 'critical' | 'high' | 'medium' }[] = [
    // Critical - Credentials & Secrets
    { pattern: /\b(AKIA[0-9A-Z]{16})\b/, type: 'AWS Access Key', severity: 'critical' },
    { pattern: /\bAIza[0-9A-Za-z_\-]{35}\b/, type: 'Google API Key', severity: 'critical' },
    { pattern: /\bgh[pousr]_[A-Za-z0-9_]{36,255}\b/, type: 'GitHub Token', severity: 'critical' },
    { pattern: /\bgithub_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}\b/, type: 'GitHub PAT', severity: 'critical' },
    { pattern: /\beyJ[A-Za-z0-9_\-]*\.eyJ[A-Za-z0-9_\-]*\.[A-Za-z0-9_\-]*\b/, type: 'JWT Token', severity: 'critical' },
    { pattern: /-----BEGIN (?:RSA |EC )?PRIVATE KEY-----/, type: 'Private Key', severity: 'critical' },
    { pattern: /(?:mysql|postgres|mongodb|redis):\/\/[^\s]+:[^\s]+@[^\s]+/i, type: 'Database Connection String', severity: 'critical' },
    { pattern: /(?:password|passwd|pwd)[\s:=]+[^\s]{8,}/i, type: 'Password', severity: 'critical' },

    // High - Financial & Government IDs
    { pattern: /\b\d{3}-\d{2}-\d{4}\b/, type: 'Social Security Number', severity: 'high' },
    { pattern: /\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b/, type: 'Credit Card Number', severity: 'high' },
    { pattern: /\b[2-6]\d{3}\s?\d{5}\s?\d\b/, type: 'Medicare Number', severity: 'high' },
    { pattern: /\b\d{3}\s?\d{3}\s?\d{3}\b/, type: 'Tax File Number', severity: 'high' },
    { pattern: /\b[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}\b/, type: 'IBAN', severity: 'high' },

    // Medium - Contact Information
    { pattern: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/, type: 'Email Address', severity: 'medium' },
    { pattern: /\b(?:\+?61|0)[2-478](?:[ -]?[0-9]){8}\b/, type: 'Phone Number (AU)', severity: 'medium' },
    { pattern: /\b\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b/, type: 'Phone Number (US)', severity: 'medium' },
    { pattern: /\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b/, type: 'IP Address', severity: 'medium' },
  ];

  // Security threat patterns
  const securityPatterns: { pattern: RegExp; type: string }[] = [
    { pattern: /<script[^>]*>.*?<\/script>/i, type: 'Script injection attempt' },
    { pattern: /javascript:/i, type: 'JavaScript protocol' },
    { pattern: /on\w+\s*=/i, type: 'Event handler injection' },
    { pattern: /\.\.\//i, type: 'Path traversal attempt' },
    { pattern: /(?:ignore|disregard|forget)\s+(?:previous|above|all)\s+(?:instructions|prompts|commands)/i, type: 'Prompt injection attempt' },
  ];

  // Check PII patterns
  for (const { pattern, type, severity } of piiPatterns) {
    if (pattern.test(prompt)) {
      detectedIssues.push(type);
      if (severity === 'critical' || severity === 'high') {
        return {
          valid: false,
          error: `Prompt contains sensitive information: ${type}. Please remove before continuing.`,
          detectedIssues
        };
      } else if (severity === 'medium') {
        warnings.push(`Detected ${type} - consider removing`);
      }
    }
  }

  // Check security threat patterns
  for (const { pattern, type } of securityPatterns) {
    if (pattern.test(prompt)) {
      return {
        valid: false,
        error: `Security violation detected: ${type}`,
        detectedIssues: [...detectedIssues, type]
      };
    }
  }

  // Check for null bytes or control characters
  if (/\x00/.test(prompt)) {
    return {
      valid: false,
      error: 'Prompt contains invalid null bytes',
      detectedIssues
    };
  }

  // Check for excessive control characters
  const controlChars = prompt.split('').filter(c => {
    const code = c.charCodeAt(0);
    return code < 32 && c !== '\n' && c !== '\r' && c !== '\t';
  });

  if (controlChars.length > 0) {
    return {
      valid: false,
      error: 'Prompt contains invalid control characters',
      detectedIssues
    };
  }

  return {
    valid: true,
    warnings: warnings.length > 0 ? warnings : undefined,
    detectedIssues: detectedIssues.length > 0 ? detectedIssues : undefined
  };
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
