import { useQuery } from '@tanstack/react-query';
import { TrendingUp, DollarSign, Image } from 'lucide-react';
import { apiClient } from '@/services';
import { UsageStats } from '@/types';
import { QUERY_KEYS, API_ENDPOINTS } from '@/utils/constants';
import { formatCurrency, formatNumber } from '@/utils';
import { LoadingSpinner } from '@/components/common';

export const Dashboard = () => {
  const { data: stats, isLoading } = useQuery({
    queryKey: QUERY_KEYS.USAGE_STATS,
    queryFn: () => apiClient.get<UsageStats>(API_ENDPOINTS.USAGE),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const cards = [
    {
      title: 'Total Generations',
      value: formatNumber(stats?.total_generations || 0),
      icon: Image,
      color: 'bg-blue-500',
    },
    {
      title: 'Total Cost',
      value: formatCurrency(stats?.total_cost_aud || 0),
      icon: DollarSign,
      color: 'bg-green-500',
    },
    {
      title: 'This Month',
      value: formatCurrency(stats?.current_month_cost || 0),
      icon: TrendingUp,
      color: 'bg-purple-500',
    },
    {
      title: 'Budget Remaining',
      value: formatCurrency(stats?.budget_remaining || 0),
      icon: DollarSign,
      color: 'bg-orange-500',
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600">Overview of your image generation usage</p>
      </div>

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <div key={card.title} className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
              <div className="flex items-center gap-4">
                <div className={`rounded-lg ${card.color} p-3 text-white`}>
                  <Icon size={24} />
                </div>
                <div>
                  <p className="text-sm text-gray-600">{card.title}</p>
                  <p className="text-2xl font-bold text-gray-900">{card.value}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {stats?.most_used_model && (
        <div className="rounded-lg border border-gray-200 bg-white p-6">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">Most Used Model</h2>
          <p className="text-gray-700">{stats.most_used_model}</p>
        </div>
      )}
    </div>
  );
};
