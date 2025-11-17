/**
 * Budget Management Admin Page
 *
 * Admin page for managing user budgets. Allows managers to view team budgets
 * and set individual user budgets.
 */

import React from 'react';
import { TeamBudgetOverview } from '../../components/budgets';

export const BudgetManagement: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Budget Management</h1>
          <p className="mt-2 text-sm text-gray-600">
            Monitor and manage budgets for your team members
          </p>
        </div>

        <TeamBudgetOverview />
      </div>
    </div>
  );
};
