import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, Download } from 'lucide-react';
import { apiClient } from '@/services';
import { AuditLog, PaginatedResponse } from '@/types';
import { QUERY_KEYS, API_ENDPOINTS } from '@/utils/constants';
import { formatDateTime } from '@/utils';
import { LoadingSpinner } from '@/components/common';

export const AuditLogViewer = () => {
  const [page, setPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: [...QUERY_KEYS.AUDIT_LOGS, page, searchQuery],
    queryFn: () =>
      apiClient.get<PaginatedResponse<AuditLog>>(API_ENDPOINTS.AUDIT_LOGS, {
        params: { page, page_size: 20, search: searchQuery || undefined },
      }),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const logs = data?.data || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Audit Logs</h1>
          <p className="text-gray-600">Complete audit trail of all platform activities</p>
        </div>
        <button className="flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-white transition-colors hover:bg-primary-700">
          <Download size={20} />
          Export
        </button>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search logs..."
          className="w-full rounded-lg border border-gray-300 py-2 pl-10 pr-4 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
        />
      </div>

      <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Timestamp
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                User
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Action
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Resource
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                IP Address
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {logs.map((log) => (
              <tr key={log.id} className="hover:bg-gray-50">
                <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900">
                  {formatDateTime(log.timestamp)}
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                  {log.user_email}
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900">
                  {log.action}
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                  {log.resource_type}
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                  {log.ip_address}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {data && data.pagination.total_pages > 1 && (
        <div className="flex justify-center gap-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm disabled:opacity-50"
          >
            Previous
          </button>
          <span className="flex items-center px-4 text-sm text-gray-700">
            Page {page} of {data.pagination.total_pages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(data.pagination.total_pages, p + 1))}
            disabled={page === data.pagination.total_pages}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};
