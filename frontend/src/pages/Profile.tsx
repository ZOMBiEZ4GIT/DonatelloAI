import { useAuth } from '@/hooks';
import { formatRoleName } from '@/utils';
import { User, Mail, Calendar, Shield } from 'lucide-react';

export const Profile = () => {
  const { user } = useAuth();

  if (!user) {
    return null;
  }

  return (
    <div className="mx-auto max-w-4xl p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Profile</h1>
        <p className="text-gray-600">Manage your account settings</p>
      </div>

      <div className="rounded-lg border border-gray-200 bg-white p-8 shadow-sm">
        <div className="mb-8 flex items-center gap-6">
          <div className="flex h-24 w-24 items-center justify-center rounded-full bg-primary-100 text-3xl font-bold text-primary-600">
            {user.email.charAt(0).toUpperCase()}
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{user.name || user.email}</h2>
            <p className="text-gray-600">{user.email}</p>
          </div>
        </div>

        <div className="space-y-6">
          <div className="flex items-center gap-4">
            <User className="h-5 w-5 text-gray-400" />
            <div>
              <p className="text-sm font-medium text-gray-500">User ID</p>
              <p className="text-gray-900">{user.id}</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <Mail className="h-5 w-5 text-gray-400" />
            <div>
              <p className="text-sm font-medium text-gray-500">Email</p>
              <p className="text-gray-900">{user.email}</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <Shield className="h-5 w-5 text-gray-400" />
            <div>
              <p className="text-sm font-medium text-gray-500">Role</p>
              <span className="inline-flex rounded-full bg-primary-100 px-3 py-1 text-sm font-medium text-primary-800">
                {formatRoleName(user.role)}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <Calendar className="h-5 w-5 text-gray-400" />
            <div>
              <p className="text-sm font-medium text-gray-500">Department ID</p>
              <p className="text-gray-900">{user.department_id}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
