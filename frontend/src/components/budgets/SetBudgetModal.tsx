/**
 * Set Budget Modal Component
 *
 * Modal for managers to set or update user budgets.
 */

import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { setUserBudget, UserBudgetCreate } from '../../api/budgets';
import { QUERY_KEYS, TOAST_MESSAGES } from '../../utils/constants';

interface SetBudgetModalProps {
  isOpen: boolean;
  onClose: () => void;
  userId: string;
  userEmail: string;
  userName?: string;
}

export const SetBudgetModal: React.FC<SetBudgetModalProps> = ({
  isOpen,
  onClose,
  userId,
  userEmail,
  userName,
}) => {
  const [budgetAmount, setBudgetAmount] = useState<string>('');
  const [alertThreshold, setAlertThreshold] = useState<number>(80);
  const [budgetYear, setBudgetYear] = useState<number>(new Date().getFullYear());
  const [budgetMonth, setBudgetMonth] = useState<number>(new Date().getMonth() + 1);

  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (data: UserBudgetCreate) => setUserBudget(userId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.TEAM_BUDGET_OVERVIEW });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.USER_BUDGET(userId) });
      alert(TOAST_MESSAGES.SAVE_SUCCESS);
      onClose();
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || TOAST_MESSAGES.SAVE_ERROR);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const amount = parseFloat(budgetAmount);
    if (isNaN(amount) || amount <= 0) {
      alert('Please enter a valid budget amount');
      return;
    }

    mutation.mutate({
      user_id: userId,
      monthly_budget_aud: amount,
      budget_period_year: budgetYear,
      budget_period_month: budgetMonth,
      alert_threshold_percent: alertThreshold,
    });
  };

  useEffect(() => {
    if (isOpen) {
      // Reset form when modal opens
      setBudgetAmount('');
      setAlertThreshold(80);
      setBudgetYear(new Date().getFullYear());
      setBudgetMonth(new Date().getMonth() + 1);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="border-b border-gray-200 px-6 py-4">
          <h3 className="text-lg font-semibold text-gray-900">Set User Budget</h3>
          <p className="text-sm text-gray-600 mt-1">
            {userName || userEmail}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-4">
          {/* Budget Amount */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Monthly Budget (AUD)
            </label>
            <div className="relative">
              <span className="absolute left-3 top-2 text-gray-500">$</span>
              <input
                type="number"
                step="0.01"
                min="0"
                value={budgetAmount}
                onChange={(e) => setBudgetAmount(e.target.value)}
                className="w-full pl-8 pr-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="0.00"
                required
              />
            </div>
          </div>

          {/* Budget Period */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Year
              </label>
              <input
                type="number"
                min="2020"
                max="2100"
                value={budgetYear}
                onChange={(e) => setBudgetYear(parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Month
              </label>
              <select
                value={budgetMonth}
                onChange={(e) => setBudgetMonth(parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              >
                {Array.from({ length: 12 }, (_, i) => i + 1).map((month) => (
                  <key={month} value={month}>
                    {new Date(2000, month - 1).toLocaleString('default', { month: 'long' })}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Alert Threshold */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Alert Threshold ({alertThreshold}%)
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={alertThreshold}
              onChange={(e) => setAlertThreshold(parseInt(e.target.value))}
              className="w-full"
            />
            <p className="text-xs text-gray-500 mt-1">
              Alert user when spending reaches this percentage of budget
            </p>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500"
              disabled={mutation.isPending}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={mutation.isPending}
            >
              {mutation.isPending ? 'Setting...' : 'Set Budget'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
