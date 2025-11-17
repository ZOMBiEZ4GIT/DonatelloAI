export interface ApiResponse<T = unknown> {
  data: T;
  message?: string;
  timestamp: string;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
  timestamp: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    page_size: number;
    total_items: number;
    total_pages: number;
  };
}

export interface UsageStats {
  total_generations: number;
  total_cost_aud: number;
  total_images: number;
  current_month_cost: number;
  budget_remaining: number;
  most_used_model: string;
}

export interface AuditLog {
  id: string;
  timestamp: string;
  user_id: string;
  user_email: string;
  action: string;
  resource_type: string;
  resource_id: string;
  ip_address: string;
  user_agent: string;
  details?: Record<string, unknown>;
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version: string;
  timestamp: string;
  services: {
    database: ServiceHealth;
    storage: ServiceHealth;
    models: ModelHealth[];
  };
}

export interface ServiceHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  latency_ms?: number;
  error?: string;
}

export interface ModelHealth {
  model: string;
  status: 'available' | 'degraded' | 'unavailable';
  success_rate?: number;
  avg_latency_ms?: number;
}
