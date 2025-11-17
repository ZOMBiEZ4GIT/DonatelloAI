import { useQuery } from '@tanstack/react-query';
import { UserPlus, Edit, Trash2 } from 'lucide-react';
import { apiClient } from '@/services';
import { User } from '@/types';
import { QUERY_KEYS, API_ENDPOINTS } from '@/utils/constants';
import { formatDate, formatRoleName } from '@/utils';
import { LoadingSpinner } from '@/components/common';

export const UserManagement = () => {
  const { data: users, isLoading } = useQuery({
    queryKey: QUERY_KEYS.USERS,
    queryFn: () => apiClient.get<User[]>(API_ENDPOINTS.USERS),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">User Management</h1>
          <p className="text-gray-600">Manage platform users and their roles</p>
        </div>
        <button className="flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-white transition-colors hover:bg-primary-700">
          <UserPlus size={20} />
          Add User
        </button>
      </div>

      <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Email
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Role
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Created
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {users?.map((user) => (
              <tr key={user.id} className="hover:bg-gray-50">
                <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-900">
                  {user.name || 'N/A'}
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                  {user.email}
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                  <span className="inline-flex rounded-full bg-primary-100 px-2 py-1 text-xs font-medium text-primary-800">
                    {formatRoleName(user.role)}
                  </span>
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                  {formatDate(user.created_at)}
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-right text-sm">
                  <button className="text-primary-600 hover:text-primary-900 mr-3">
                    <Edit size={18} />
                  </button>
                  <button className="text-error-600 hover:text-error-900">
                    <Trash2 size={18} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
