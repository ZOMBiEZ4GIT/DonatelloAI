/**
 * Budget Widget Component
 *
 * Displays the current user's budget status with visual indicators.
 * Shows budget amount, current spend, and remaining budget.
 */

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getMyBudget } from '../../api/budgets';
import { QUERY_KEYS } from '../../utils/constants';

export const BudgetWidget: React.FC = () => {
  const { data: budget, isLoading, error } = useQuery({
    queryKey: QUERY_KEYS.MY_BUDGET,
    queryFn: () => getMyBudget(),
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
        <div className="h-8 bg-gray-200 rounded w-3/4"></div>
      </div>
    );
  }

  if (error || !budget) {
    return null; // Don't show widget if no budget or error
  }

  // If no budget is set (budget = 0), don't show the widget
  if (budget.monthly_budget_aud === 0) {
    return null;
  }

  const getStatusColor = () => {
    if (budget.is_over_budget) return 'text-red-600';
    if (budget.should_alert) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getProgressBarColor = () => {
    if (budget.is_over_budget) return 'bg-red-500';
    if (budget.should_alert) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const progressPercentage = Math.min(budget.budget_utilization_percent, 100);

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Monthly Budget</h3>
        <span className={`text-sm font-medium ${getStatusColor()}`}>
          {budget.is_over_budget
            ? 'Over Budget'
            : budget.should_alert
            ? 'Near Limit'
            : 'On Track'}
        </span>
      </div>

      <div className="space-y-4">
        {/* Budget Amount */}
        <div className="flex justify-between items-baseline">
          <span className="text-sm text-gray-600">Budget:</span>
          <span className="text-2xl font-bold text-gray-900">
            ${budget.monthly_budget_aud.toFixed(2)}
          </span>
        </div>

        {/* Progress Bar */}
        <div className="w-full">
          <div className="flex justify-between text-sm text-gray-600 mb-1">
            <span>Spent: ${budget.current_spend_aud.toFixed(2)}</span>
            <span>{progressPercentage.toFixed(0)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div
              className={`h-2.5 rounded-full transition-all duration-300 ${getProgressBarColor()}`}
              style={{ width: `${progressPercentage}%` }}
            ></div>
          </div>
        </div>

        {/* Remaining Budget */}
        <div className="flex justify-between items-baseline pt-2 border-t border-gray-200">
          <span className="text-sm text-gray-600">Remaining:</span>
          <span className={`text-xl font-semibold ${getStatusColor()}`}>
            ${budget.budget_remaining.toFixed(2)}
          </span>
        </div>

        {/* Warning Messages */}
        {budget.is_over_budget && (
          <div className="bg-red-50 border border-red-200 rounded-md p-3">
            <p className="text-sm text-red-800">
              You have exceeded your monthly budget. Please contact your manager.
            </p>
          </div>
        )}

        {budget.should_alert && !budget.is_over_budget && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
            <p className="text-sm text-yellow-800">
              You are approaching your budget limit ({budget.alert_threshold_percent}%).
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
