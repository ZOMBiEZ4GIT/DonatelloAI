import { Link } from 'react-router-dom';
import { Menu, Bell, User } from 'lucide-react';
import { useAuth } from '@/hooks';
import { useUIStore } from '@/store';
import { LoginButton } from '@/components/auth';
import { ROUTES, APP_CONFIG } from '@/utils/constants';

export const Header = () => {
  const { isAuthenticated, user } = useAuth();
  const { toggleSidebar } = useUIStore();

  return (
    <header className="sticky top-0 z-50 border-b border-gray-200 bg-white shadow-sm">
      <div className="flex h-16 items-center justify-between px-6">
        <div className="flex items-center gap-4">
          {isAuthenticated && (
            <button
              onClick={toggleSidebar}
              className="rounded-lg p-2 text-gray-600 transition-colors hover:bg-gray-100"
              aria-label="Toggle sidebar"
            >
              <Menu size={24} />
            </button>
          )}
          <Link to={ROUTES.HOME} className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-600 text-white font-bold">
              EIG
            </div>
            <div>
              <h1 className="text-lg font-bold text-gray-900">{APP_CONFIG.name}</h1>
              <p className="text-xs text-gray-500">v{APP_CONFIG.version}</p>
            </div>
          </Link>
        </div>

        <div className="flex items-center gap-4">
          {isAuthenticated && (
            <>
              <button
                className="rounded-lg p-2 text-gray-600 transition-colors hover:bg-gray-100"
                aria-label="Notifications"
              >
                <Bell size={20} />
              </button>
              <Link
                to={ROUTES.PROFILE}
                className="flex items-center gap-2 rounded-lg px-3 py-2 text-gray-700 transition-colors hover:bg-gray-100"
              >
                <User size={20} />
                <span className="hidden md:inline">{user?.email}</span>
              </Link>
            </>
          )}
          <LoginButton />
        </div>
      </div>
    </header>
  );
};
