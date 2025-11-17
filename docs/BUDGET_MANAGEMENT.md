# User Budget Management

## Overview

The User Budget Management feature allows managers to set monthly budgets for individual team members and track their spending on image generation. Users can view their budget status in real-time, and managers can monitor team-wide budget utilization.

## Features

### For Users
- **Real-time Budget Tracking**: View current spend vs. allocated budget
- **Visual Progress Indicators**: Color-coded progress bars showing budget utilization
- **Budget Alerts**: Automatic warnings when approaching budget limits
- **Monthly Budget Widget**: Dashboard widget showing budget status at a glance

### For Managers
- **Set User Budgets**: Allocate monthly budgets for team members
- **Team Budget Overview**: Monitor all team members' budget utilization
- **Budget Period Management**: Set budgets for specific months/years
- **Alert Threshold Configuration**: Customize when users receive budget warnings
- **Budget Status Indicators**: Quickly identify users who are over budget or near limits

## Database Schema

### UserBudget Table
```sql
CREATE TABLE user_budgets (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE,
    monthly_budget_aud NUMERIC(10, 2) NOT NULL,
    current_spend_aud NUMERIC(10, 2) DEFAULT 0.00,
    budget_period_year INTEGER NOT NULL,
    budget_period_month INTEGER NOT NULL (1-12),
    alert_threshold_percent INTEGER DEFAULT 80,
    is_active BOOLEAN DEFAULT TRUE,
    set_by_user_id VARCHAR(36),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API Endpoints

### Get My Budget
```http
GET /api/v1/budgets/me?year=2025&month=11
```
Returns the current user's budget for the specified period (or current month if not specified).

**Response:**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "monthly_budget_aud": 500.00,
  "current_spend_aud": 345.67,
  "budget_remaining": 154.33,
  "budget_utilization_percent": 69.13,
  "is_over_budget": false,
  "should_alert": false,
  "alert_threshold_percent": 80,
  "budget_period_year": 2025,
  "budget_period_month": 11,
  "created_at": "2025-11-17T19:15:00Z",
  "updated_at": "2025-11-17T20:30:00Z"
}
```

### Set User Budget (Managers Only)
```http
POST /api/v1/budgets/users/{user_id}
```

**Request Body:**
```json
{
  "user_id": "uuid",
  "monthly_budget_aud": 500.00,
  "budget_period_year": 2025,
  "budget_period_month": 11,
  "alert_threshold_percent": 80
}
```

**Response:** Same as Get My Budget

### Get Team Budget Overview (Managers Only)
```http
GET /api/v1/budgets/team/overview?year=2025&month=11
```

**Response:**
```json
{
  "total_team_budget": 5000.00,
  "total_team_spend": 3456.78,
  "total_team_remaining": 1543.22,
  "average_utilization_percent": 69.14,
  "users_over_budget": 2,
  "users_near_threshold": 3,
  "team_members": [
    {
      "user_id": "uuid",
      "user_name": "John Doe",
      "user_email": "john@example.com",
      "monthly_budget_aud": 500.00,
      "current_spend_aud": 345.67,
      "budget_remaining": 154.33,
      "budget_utilization_percent": 69.13,
      "is_over_budget": false,
      "should_alert": false,
      "budget_period_year": 2025,
      "budget_period_month": 11
    }
  ]
}
```

### Update Budget (Managers Only)
```http
PATCH /api/v1/budgets/{budget_id}
```

**Request Body:**
```json
{
  "monthly_budget_aud": 600.00,
  "alert_threshold_percent": 85,
  "is_active": true
}
```

## Usage Guide

### For Users

1. **View Your Budget**
   - Navigate to the Dashboard (Admin > Dashboard)
   - The Budget Widget will appear if a budget has been set for you
   - Shows: Budget amount, current spend, remaining budget, and progress bar

2. **Budget Status Indicators**
   - **Green (On Track)**: Under alert threshold
   - **Yellow (Near Limit)**: At or above alert threshold
   - **Red (Over Budget)**: Exceeded monthly budget

3. **Budget Alerts**
   - Warning appears when you reach the alert threshold (default 80%)
   - Error appears when you exceed your budget
   - Contact your manager to request a budget increase

### For Managers

1. **View Team Budget Overview**
   - Navigate to Admin > Budgets
   - View summary cards showing total team budget, spend, and remaining
   - See list of all team members with their budget status

2. **Set a User Budget**
   - Click "Set Budget" next to a team member
   - Enter the monthly budget amount in AUD
   - Select the budget period (year and month)
   - Adjust alert threshold (default 80%)
   - Click "Set Budget" to save

3. **Monitor Budget Usage**
   - Users near threshold are highlighted in yellow
   - Users over budget are highlighted in red
   - Progress bars show visual representation of utilization
   - Summary shows count of users needing attention

## Budget Enforcement

Budgets can be configured with different enforcement modes in the backend settings:

- **Hard**: Block image generation when budget is exceeded
- **Soft**: Allow generation but send alerts to user and manager
- **Warn**: Only show warnings, no restrictions

Default mode: **Hard** (configured in `backend/app/core/config.py`)

## Cost Tracking

Costs are automatically tracked when images are generated:

```python
# Example: Adding cost to user budget
from app.services.budget_service import BudgetService

# After successful generation
await BudgetService.add_cost_to_budget(
    db=db,
    user_id=user_id,
    cost_aud=generation_cost
)
```

Cost per model (AUD):
- DALL-E 3: $0.08
- Stable Diffusion XL: $0.02
- Adobe Firefly: $0.10
- Azure AI Image: $0.05

## Frontend Components

### BudgetWidget
Displays current user's budget status on the dashboard.

**Usage:**
```tsx
import { BudgetWidget } from '@/components/budgets';

<BudgetWidget />
```

### SetBudgetModal
Modal for managers to set/update user budgets.

**Usage:**
```tsx
import { SetBudgetModal } from '@/components/budgets';

<SetBudgetModal
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  userId="user-uuid"
  userEmail="user@example.com"
  userName="John Doe"
/>
```

### TeamBudgetOverview
Complete team budget management interface for managers.

**Usage:**
```tsx
import { TeamBudgetOverview } from '@/components/budgets';

<TeamBudgetOverview />
```

## Permissions

Budget management follows the role hierarchy:

- **STANDARD_USER**: Can view own budget only
- **POWER_USER**: Can view own budget only
- **DEPARTMENT_MANAGER**: Can set budgets for users in their department
- **ORG_ADMIN**: Can set budgets for all users in the organization
- **SUPER_ADMIN**: Can set budgets for any user

## Database Migrations

To apply the budget management schema:

```bash
cd backend
alembic upgrade head
```

The migration creates:
- `user_budgets` table
- Foreign key constraints
- Indexes for performance

## Configuration

Budget settings in `backend/app/core/config.py`:

```python
# Default department budget
DEFAULT_DEPARTMENT_BUDGET_AUD: float = 5000.00

# Budget enforcement mode (hard, soft, warn)
BUDGET_ENFORCEMENT: Literal["hard", "soft", "warn"] = "hard"

# Alert threshold (percentage)
COST_ALERT_THRESHOLD_PERCENT: int = 80

# Maximum cost per image (safety limit)
MAX_COST_PER_IMAGE_AUD: float = 0.50
```

## Troubleshooting

### Budget Widget Not Showing
- Budget widget only appears if a budget has been set (budget > 0)
- Check if you're on the Dashboard page
- Verify budget exists for current month

### Can't Set User Budget
- Ensure you have manager role (DEPARTMENT_MANAGER or higher)
- For department managers, user must be in your department
- Check API endpoint is accessible

### Budget Not Updating
- Costs are added when generation completes successfully
- Budget updates happen in real-time
- Check browser console for API errors
- Verify budget service is tracking costs correctly

## Future Enhancements

Potential improvements for future versions:

1. **Budget Rollover**: Allow unused budget to roll over to next month
2. **Budget Forecasting**: Predict when user will reach budget based on usage patterns
3. **Budget Notifications**: Email/push notifications when approaching limits
4. **Budget Reports**: Historical budget usage reports and analytics
5. **Budget Approval Workflow**: Require approval for budget increases
6. **Multi-Currency Support**: Support for currencies beyond AUD
7. **Budget Templates**: Pre-defined budget templates for common roles
8. **Automated Budget Resets**: Automatic monthly budget resets

## Support

For issues or questions about budget management:
- Check logs in Application Insights
- Review audit logs for budget changes
- Contact platform administrators
