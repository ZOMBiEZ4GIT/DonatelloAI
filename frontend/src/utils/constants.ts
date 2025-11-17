export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export const AZURE_CONFIG = {
  clientId: import.meta.env.VITE_AZURE_CLIENT_ID || '',
  tenantId: import.meta.env.VITE_AZURE_TENANT_ID || '',
  redirectUri: import.meta.env.VITE_AZURE_REDIRECT_URI || window.location.origin,
};

export const APP_CONFIG = {
  name: import.meta.env.VITE_APP_NAME || 'Enterprise Image Generation Platform',
  version: import.meta.env.VITE_APP_VERSION || '0.1.0',
};

export const ROUTES = {
  HOME: '/',
  GENERATE: '/generate',
  ADMIN: '/admin',
  ADMIN_USERS: '/admin/users',
  ADMIN_DEPARTMENTS: '/admin/departments',
  ADMIN_BUDGETS: '/admin/budgets',
  ADMIN_AUDIT: '/admin/audit',
  ADMIN_MODELS: '/admin/models',
  PROFILE: '/profile',
  NOT_FOUND: '/404',
} as const;

export const API_ENDPOINTS = {
  // Auth
  LOGIN: '/api/v1/auth/login',
  LOGOUT: '/api/v1/auth/logout',
  ME: '/api/v1/auth/me',

  // Generations
  GENERATE: '/api/v1/generate',
  GENERATION: (id: string) => `/api/v1/generation/${id}`,
  GENERATIONS: '/api/v1/generations',
  BATCH_GENERATE: '/api/v1/generate/batch',

  // Models
  MODELS: '/api/v1/models',
  MODEL: (id: string) => `/api/v1/models/${id}`,

  // Users
  USERS: '/api/v1/admin/users',
  USER: (id: string) => `/api/v1/admin/users/${id}`,

  // Departments
  DEPARTMENTS: '/api/v1/admin/departments',
  DEPARTMENT: (id: string) => `/api/v1/admin/departments/${id}`,

  // Audit
  AUDIT_LOGS: '/api/v1/admin/audit-log',

  // Usage & Stats
  USAGE: '/api/v1/account/usage',
  HEALTH: '/api/v1/health',
} as const;

export const GENERATION_LIMITS = {
  MAX_PROMPT_LENGTH: 2000,
  MIN_PROMPT_LENGTH: 3,
  MAX_NEGATIVE_PROMPT_LENGTH: 1000,
  MAX_IMAGES_PER_REQUEST: 4,
  DEFAULT_IMAGE_SIZE: { width: 1024, height: 1024 },
} as const;

export const QUERY_KEYS = {
  AUTH_USER: ['auth', 'user'],
  GENERATIONS: ['generations'],
  GENERATION: (id: string) => ['generation', id],
  MODELS: ['models'],
  USERS: ['users'],
  USER: (id: string) => ['user', id],
  DEPARTMENTS: ['departments'],
  DEPARTMENT: (id: string) => ['department', id],
  AUDIT_LOGS: ['audit-logs'],
  USAGE_STATS: ['usage-stats'],
  HEALTH: ['health'],
} as const;

export const TOAST_MESSAGES = {
  GENERATION_STARTED: 'Image generation started!',
  GENERATION_COMPLETE: 'Image generated successfully!',
  GENERATION_FAILED: 'Image generation failed. Please try again.',
  SAVE_SUCCESS: 'Changes saved successfully',
  SAVE_ERROR: 'Failed to save changes',
  DELETE_SUCCESS: 'Deleted successfully',
  DELETE_ERROR: 'Failed to delete',
  BUDGET_EXCEEDED: 'Budget limit exceeded',
  UNAUTHORIZED: 'You do not have permission to perform this action',
} as const;

export const WEBSOCKET_EVENTS = {
  GENERATION_STARTED: 'generation.started',
  GENERATION_PROGRESS: 'generation.progress',
  GENERATION_COMPLETED: 'generation.completed',
  GENERATION_FAILED: 'generation.failed',
} as const;
