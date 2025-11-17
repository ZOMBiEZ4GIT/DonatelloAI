import { useAuthStore } from '@/store';
import { RolePermissions, Permission, UserRole } from '@/types';

export const usePermissions = () => {
  const user = useAuthStore((state) => state.user);

  const hasPermission = (resource: string, action: Permission['action']): boolean => {
    if (!user) return false;

    const permissions = RolePermissions[user.role as UserRole];

    // Check for wildcard admin permission
    if (permissions.some((p) => p.resource === '*' && p.action === 'admin')) {
      return true;
    }

    // Check for specific permission
    return permissions.some(
      (p) => (p.resource === resource || p.resource === '*') &&
             (p.action === action || p.action === 'admin')
    );
  };

  const canCreate = (resource: string) => hasPermission(resource, 'create');
  const canRead = (resource: string) => hasPermission(resource, 'read');
  const canUpdate = (resource: string) => hasPermission(resource, 'update');
  const canDelete = (resource: string) => hasPermission(resource, 'delete');
  const canAdmin = (resource: string) => hasPermission(resource, 'admin');

  const isSuperAdmin = user?.role === UserRole.SUPER_ADMIN;
  const isOrgAdmin = user?.role === UserRole.ORG_ADMIN || isSuperAdmin;
  const isDepartmentManager = user?.role === UserRole.DEPARTMENT_MANAGER || isOrgAdmin;
  const isPowerUser = user?.role === UserRole.POWER_USER || isDepartmentManager;

  return {
    hasPermission,
    canCreate,
    canRead,
    canUpdate,
    canDelete,
    canAdmin,
    isSuperAdmin,
    isOrgAdmin,
    isDepartmentManager,
    isPowerUser,
  };
};
