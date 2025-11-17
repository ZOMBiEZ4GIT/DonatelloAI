import { Link } from 'react-router-dom';
import { Home } from 'lucide-react';
import { ROUTES } from '@/utils/constants';

export const NotFound = () => {
  return (
    <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center bg-gray-50">
      <div className="text-center">
        <h1 className="text-9xl font-bold text-gray-200">404</h1>
        <h2 className="mt-4 text-3xl font-bold text-gray-900">Page Not Found</h2>
        <p className="mt-2 text-gray-600">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <Link
          to={ROUTES.HOME}
          className="mt-8 inline-flex items-center gap-2 rounded-lg bg-primary-600 px-6 py-3 text-white transition-colors hover:bg-primary-700"
        >
          <Home size={20} />
          Back to Home
        </Link>
      </div>
    </div>
  );
};
