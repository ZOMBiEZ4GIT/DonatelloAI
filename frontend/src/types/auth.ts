import { UserRole } from './user';

export interface LoginRequest {
  redirect_uri?: string;
}

export interface AuthState {
  isAuthenticated: boolean;
  user: AuthUser | null;
  accessToken: string | null;
  isLoading: boolean;
  error: string | null;
}

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  department_id: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token?: string;
  expires_in: number;
  token_type: string;
}

export interface Permission {
  resource: string;
  action: 'create' | 'read' | 'update' | 'delete' | 'admin';
}

export const RolePermissions: Record<UserRole, Permission[]> = {
  [UserRole.SUPER_ADMIN]: [
    { resource: '*', action: 'admin' },
  ],
  [UserRole.ORG_ADMIN]: [
    { resource: 'users', action: 'admin' },
    { resource: 'departments', action: 'admin' },
    { resource: 'models', action: 'admin' },
    { resource: 'audit', action: 'read' },
    { resource: 'generations', action: 'admin' },
  ],
  [UserRole.DEPARTMENT_MANAGER]: [
    { resource: 'users', action: 'create' },
    { resource: 'users', action: 'read' },
    { resource: 'users', action: 'update' },
    { resource: 'department', action: 'update' },
    { resource: 'budget', action: 'read' },
    { resource: 'generations', action: 'read' },
  ],
  [UserRole.POWER_USER]: [
    { resource: 'generations', action: 'create' },
    { resource: 'generations', action: 'read' },
    { resource: 'generations', action: 'delete' },
  ],
  [UserRole.STANDARD_USER]: [
    { resource: 'generations', action: 'create' },
    { resource: 'generations', action: 'read' },
  ],
};
