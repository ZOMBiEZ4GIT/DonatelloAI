import { useAuth } from '@/hooks';
import { LogIn, LogOut } from 'lucide-react';

export const LoginButton = () => {
  const { isAuthenticated, login, logout, isLoading } = useAuth();

  if (isLoading) {
    return (
      <button className="flex items-center gap-2 rounded-lg bg-gray-200 px-4 py-2 text-gray-400" disabled>
        Loading...
      </button>
    );
  }

  if (isAuthenticated) {
    return (
      <button
        onClick={logout}
        className="flex items-center gap-2 rounded-lg bg-error-500 px-4 py-2 text-white transition-colors hover:bg-error-600"
      >
        <LogOut size={18} />
        <span>Logout</span>
      </button>
    );
  }

  return (
    <button
      onClick={login}
      className="flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-white transition-colors hover:bg-primary-700"
    >
      <LogIn size={18} />
      <span>Login with Azure AD</span>
    </button>
  );
};
