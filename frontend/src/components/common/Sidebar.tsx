import { Link, useLocation } from 'react-router-dom';
import { Home, ImagePlus, Settings, Users, DollarSign, FileText, BarChart3 } from 'lucide-react';
import { useUIStore } from '@/store';
import { usePermissions } from '@/hooks';
import { ROUTES } from '@/utils/constants';
import { cn } from '@/utils';

interface NavItem {
  icon: typeof Home;
  label: string;
  path: string;
  permission?: { resource: string; action: 'create' | 'read' | 'update' | 'delete' | 'admin' };
}

const navItems: NavItem[] = [
  {
    icon: Home,
    label: 'Home',
    path: ROUTES.HOME,
  },
  {
    icon: ImagePlus,
    label: 'Generate',
    path: ROUTES.GENERATE,
  },
  {
    icon: BarChart3,
    label: 'Admin Dashboard',
    path: ROUTES.ADMIN,
    permission: { resource: 'users', action: 'read' },
  },
  {
    icon: Users,
    label: 'User Management',
    path: ROUTES.ADMIN_USERS,
    permission: { resource: 'users', action: 'admin' },
  },
  {
    icon: DollarSign,
    label: 'Budget Management',
    path: ROUTES.ADMIN_BUDGETS,
    permission: { resource: 'budget', action: 'read' },
  },
  {
    icon: FileText,
    label: 'Audit Logs',
    path: ROUTES.ADMIN_AUDIT,
    permission: { resource: 'audit', action: 'read' },
  },
  {
    icon: Settings,
    label: 'Model Config',
    path: ROUTES.ADMIN_MODELS,
    permission: { resource: 'models', action: 'admin' },
  },
];

export const Sidebar = () => {
  const { sidebarOpen } = useUIStore();
  const { hasPermission } = usePermissions();
  const location = useLocation();

  if (!sidebarOpen) return null;

  return (
    <aside className="fixed left-0 top-16 z-40 h-[calc(100vh-4rem)] w-64 border-r border-gray-200 bg-white">
      <nav className="flex flex-col gap-1 p-4">
        {navItems.map((item) => {
          // Check permissions
          if (item.permission && !hasPermission(item.permission.resource, item.permission.action)) {
            return null;
          }

          const isActive = location.pathname === item.path;
          const Icon = item.icon;

          return (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                'flex items-center gap-3 rounded-lg px-4 py-3 transition-colors',
                isActive
                  ? 'bg-primary-50 text-primary-700 font-medium'
                  : 'text-gray-700 hover:bg-gray-100'
              )}
            >
              <Icon size={20} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
};
