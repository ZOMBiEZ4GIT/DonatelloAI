/**
 * Budget Management API Client
 *
 * Handles all budget-related API calls for user budget tracking and management.
 */

import axios from 'axios';
import { API_ENDPOINTS } from '../utils/constants';

export interface UserBudget {
  id: string;
  user_id: string;
  monthly_budget_aud: number;
  current_spend_aud: number;
  budget_period_year: number;
  budget_period_month: number;
  alert_threshold_percent: number;
  is_active: boolean;
  set_by_user_id?: string;
  created_at: string;
  updated_at: string;
  budget_remaining: number;
  budget_utilization_percent: number;
  is_over_budget: boolean;
  should_alert: boolean;
}

export interface UserBudgetCreate {
  user_id: string;
  monthly_budget_aud: number;
  budget_period_year: number;
  budget_period_month: number;
  alert_threshold_percent?: number;
}

export interface UserBudgetUpdate {
  monthly_budget_aud?: number;
  alert_threshold_percent?: number;
  is_active?: boolean;
}

export interface TeamMemberBudget {
  user_id: string;
  user_name?: string;
  user_email: string;
  monthly_budget_aud: number;
  current_spend_aud: number;
  budget_remaining: number;
  budget_utilization_percent: number;
  is_over_budget: boolean;
  should_alert: boolean;
  budget_period_year: number;
  budget_period_month: number;
}

export interface TeamBudgetOverview {
  total_team_budget: number;
  total_team_spend: number;
  total_team_remaining: number;
  average_utilization_percent: number;
  users_over_budget: number;
  users_near_threshold: number;
  team_members: TeamMemberBudget[];
}

/**
 * Get current user's budget
 */
export async function getMyBudget(
  year?: number,
  month?: number
): Promise<UserBudget> {
  const params = new URLSearchParams();
  if (year) params.append('year', year.toString());
  if (month) params.append('month', month.toString());

  const url = `${API_ENDPOINTS.BUDGETS.ME}${params.toString() ? '?' + params.toString() : ''}`;
  const response = await axios.get<UserBudget>(url);
  return response.data;
}

/**
 * Get a specific user's budget (managers only)
 */
export async function getUserBudget(
  userId: string,
  year?: number,
  month?: number
): Promise<UserBudget> {
  const params = new URLSearchParams();
  if (year) params.append('year', year.toString());
  if (month) params.append('month', month.toString());

  const url = `${API_ENDPOINTS.BUDGETS.USER(userId)}${params.toString() ? '?' + params.toString() : ''}`;
  const response = await axios.get<UserBudget>(url);
  return response.data;
}

/**
 * Set or update a user's budget (managers only)
 */
export async function setUserBudget(
  userId: string,
  budgetData: UserBudgetCreate
): Promise<UserBudget> {
  const response = await axios.post<UserBudget>(
    API_ENDPOINTS.BUDGETS.USER(userId),
    budgetData
  );
  return response.data;
}

/**
 * Update an existing budget (managers only)
 */
export async function updateBudget(
  budgetId: string,
  budgetData: UserBudgetUpdate
): Promise<UserBudget> {
  const response = await axios.patch<UserBudget>(
    API_ENDPOINTS.BUDGETS.UPDATE(budgetId),
    budgetData
  );
  return response.data;
}

/**
 * Get team budget overview (managers only)
 */
export async function getTeamBudgetOverview(
  year?: number,
  month?: number
): Promise<TeamBudgetOverview> {
  const params = new URLSearchParams();
  if (year) params.append('year', year.toString());
  if (month) params.append('month', month.toString());

  const url = `${API_ENDPOINTS.BUDGETS.TEAM_OVERVIEW}${params.toString() ? '?' + params.toString() : ''}`;
  const response = await axios.get<TeamBudgetOverview>(url);
  return response.data;
}
