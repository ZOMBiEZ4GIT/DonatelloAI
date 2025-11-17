import { Routes, Route, Navigate } from 'react-router-dom';
import { Dashboard, UserManagement, AuditLogViewer } from '@/components/admin';
import { usePermissions } from '@/hooks';

export const Admin = () => {
  const { canRead } = usePermissions();

  // Check if user has admin access
  if (!canRead('users')) {
    return (
      <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">Access Denied</h1>
          <p className="mt-2 text-gray-600">
            You don't have permission to access the admin panel.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <Routes>
        <Route index element={<Dashboard />} />
        <Route path="users" element={<UserManagement />} />
        <Route path="audit" element={<AuditLogViewer />} />
        <Route path="*" element={<Navigate to="/admin" replace />} />
      </Routes>
    </div>
  );
};
