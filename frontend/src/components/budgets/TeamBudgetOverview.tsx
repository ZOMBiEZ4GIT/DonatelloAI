/**
 * Team Budget Overview Component
 *
 * Displays budget overview for all team members. Managers can view
 * their team's budget status and set individual budgets.
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getTeamBudgetOverview } from '../../api/budgets';
import { QUERY_KEYS } from '../../utils/constants';
import { SetBudgetModal } from './SetBudgetModal';

export const TeamBudgetOverview: React.FC = () => {
  const [selectedUser, setSelectedUser] = useState<{
    id: string;
    email: string;
    name?: string;
  } | null>(null);

  const { data: overview, isLoading, error } = useQuery({
    queryKey: QUERY_KEYS.TEAM_BUDGET_OVERVIEW,
    queryFn: () => getTeamBudgetOverview(),
    refetchInterval: 60000, // Refetch every minute
  });

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="h-24 bg-gray-200 rounded"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="text-center text-red-600">
          <p>Failed to load team budget overview</p>
        </div>
      </div>
    );
  }

  if (!overview) return null;

  const getUtilizationColor = (percentage: number) => {
    if (percentage >= 100) return 'text-red-600';
    if (percentage >= 80) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getProgressBarColor = (percentage: number) => {
    if (percentage >= 100) return 'bg-red-500';
    if (percentage >= 80) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Team Budget Overview</h2>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-blue-50 rounded-lg p-4">
          <p className="text-sm text-blue-600 font-medium">Total Budget</p>
          <p className="text-2xl font-bold text-blue-900">
            ${overview.total_team_budget.toFixed(2)}
          </p>
        </div>

        <div className="bg-purple-50 rounded-lg p-4">
          <p className="text-sm text-purple-600 font-medium">Total Spent</p>
          <p className="text-2xl font-bold text-purple-900">
            ${overview.total_team_spend.toFixed(2)}
          </p>
        </div>

        <div className="bg-green-50 rounded-lg p-4">
          <p className="text-sm text-green-600 font-medium">Remaining</p>
          <p className="text-2xl font-bold text-green-900">
            ${overview.total_team_remaining.toFixed(2)}
          </p>
        </div>

        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-sm text-gray-600 font-medium">Avg Utilization</p>
          <p className={`text-2xl font-bold ${getUtilizationColor(overview.average_utilization_percent)}`}>
            {overview.average_utilization_percent.toFixed(1)}%
          </p>
        </div>
      </div>

      {/* Alert Summary */}
      {(overview.users_over_budget > 0 || overview.users_near_threshold > 0) && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
          <p className="text-sm font-medium text-yellow-800">
            {overview.users_over_budget > 0 && (
              <span className="mr-4">
                {overview.users_over_budget} user{overview.users_over_budget > 1 ? 's' : ''} over
                budget
              </span>
            )}
            {overview.users_near_threshold > 0 && (
              <span>
                {overview.users_near_threshold} user{overview.users_near_threshold > 1 ? 's' : ''} near
                threshold
              </span>
            )}
          </p>
        </div>
      )}

      {/* Team Members Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                User
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Budget
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Spent
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Remaining
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Progress
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {overview.team_members.map((member) => {
              const progressPercentage = Math.min(member.budget_utilization_percent, 100);

              return (
                <tr key={member.user_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {member.user_name || member.user_email}
                      </div>
                      {member.user_name && (
                        <div className="text-sm text-gray-500">{member.user_email}</div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${member.monthly_budget_aud.toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${member.current_spend_aud.toFixed(2)}
                  </td>
                  <td className={`px-6 py-4 whitespace-nowrap text-sm ${getUtilizationColor(member.budget_utilization_percent)}`}>
                    ${member.budget_remaining.toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="w-32">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full transition-all ${getProgressBarColor(
                              member.budget_utilization_percent
                            )}`}
                            style={{ width: `${progressPercentage}%` }}
                          ></div>
                        </div>
                        <span className={`text-xs font-medium ${getUtilizationColor(member.budget_utilization_percent)}`}>
                          {progressPercentage.toFixed(0)}%
                        </span>
                      </div>
                      {member.is_over_budget && (
                        <span className="text-xs text-red-600 font-medium">Over Budget</span>
                      )}
                      {member.should_alert && !member.is_over_budget && (
                        <span className="text-xs text-yellow-600 font-medium">Near Limit</span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <button
                      onClick={() =>
                        setSelectedUser({
                          id: member.user_id,
                          email: member.user_email,
                          name: member.user_name,
                        })
                      }
                      className="text-blue-600 hover:text-blue-800 font-medium"
                    >
                      Set Budget
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {overview.team_members.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            <p>No team members found</p>
          </div>
        )}
      </div>

      {/* Set Budget Modal */}
      {selectedUser && (
        <SetBudgetModal
          isOpen={!!selectedUser}
          onClose={() => setSelectedUser(null)}
          userId={selectedUser.id}
          userEmail={selectedUser.email}
          userName={selectedUser.name}
        />
      )}
    </div>
  );
};
