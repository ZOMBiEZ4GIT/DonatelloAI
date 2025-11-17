export enum UserRole {
  SUPER_ADMIN = 'super_admin',
  ORG_ADMIN = 'org_admin',
  DEPARTMENT_MANAGER = 'department_manager',
  POWER_USER = 'power_user',
  STANDARD_USER = 'standard_user',
}

export interface User {
  id: string;
  azure_ad_id: string;
  email: string;
  name?: string;
  department_id: string;
  role: UserRole;
  created_at: string;
  updated_at?: string;
  settings?: UserSettings;
}

export interface UserSettings {
  default_model?: string;
  notifications_enabled?: boolean;
  theme?: 'light' | 'dark';
  language?: string;
}

export interface Department {
  id: string;
  name: string;
  monthly_budget_aud: number;
  current_spend_aud: number;
  settings?: DepartmentSettings;
  created_at: string;
}

export interface DepartmentSettings {
  allowed_models?: string[];
  max_concurrent_generations?: number;
  auto_approve_users?: boolean;
}
