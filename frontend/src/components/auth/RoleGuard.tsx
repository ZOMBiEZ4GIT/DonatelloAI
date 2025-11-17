import { ReactNode } from 'react';
import { usePermissions } from '@/hooks';
import { Permission } from '@/types';

interface RoleGuardProps {
  children: ReactNode;
  resource: string;
  action: Permission['action'];
  fallback?: ReactNode;
}

export const RoleGuard = ({ children, resource, action, fallback = null }: RoleGuardProps) => {
  const { hasPermission } = usePermissions();

  if (!hasPermission(resource, action)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};
