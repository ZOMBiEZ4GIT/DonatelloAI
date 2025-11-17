import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { MsalProvider } from '@azure/msal-react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { authService } from '@/services';
import { ErrorBoundary, Header, Sidebar } from '@/components/common';
import { ProtectedRoute } from '@/components/auth';
import { Home, Generate, Admin, Profile, NotFound } from '@/pages';
import { ROUTES } from '@/utils/constants';
import { useUIStore } from '@/store';
import { cn } from '@/utils';

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 30000, // 30 seconds
    },
  },
});

function AppContent() {
  const { sidebarOpen } = useUIStore();

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="flex">
        <Sidebar />
        <main
          className={cn(
            'flex-1 transition-all duration-200',
            sidebarOpen ? 'ml-64' : 'ml-0'
          )}
        >
          <Routes>
            <Route path={ROUTES.HOME} element={<Home />} />
            <Route
              path={ROUTES.GENERATE}
              element={
                <ProtectedRoute>
                  <Generate />
                </ProtectedRoute>
              }
            />
            <Route
              path={`${ROUTES.ADMIN}/*`}
              element={
                <ProtectedRoute>
                  <Admin />
                </ProtectedRoute>
              }
            />
            <Route
              path={ROUTES.PROFILE}
              element={
                <ProtectedRoute>
                  <Profile />
                </ProtectedRoute>
              }
            />
            <Route path={ROUTES.NOT_FOUND} element={<NotFound />} />
            <Route path="*" element={<Navigate to={ROUTES.NOT_FOUND} replace />} />
          </Routes>
        </main>
      </div>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
          },
          success: {
            duration: 3000,
            iconTheme: {
              primary: '#22c55e',
              secondary: '#fff',
            },
          },
          error: {
            duration: 5000,
            iconTheme: {
              primary: '#ef4444',
              secondary: '#fff',
            },
          },
        }}
      />
    </div>
  );
}

function App() {
  const msalInstance = authService.getMsalInstance();

  useEffect(() => {
    // Initialize auth service
    authService.initialize().catch((error) => {
      console.error('Failed to initialize auth service:', error);
    });
  }, []);

  return (
    <ErrorBoundary>
      <MsalProvider instance={msalInstance}>
        <QueryClientProvider client={queryClient}>
          <BrowserRouter>
            <AppContent />
          </BrowserRouter>
        </QueryClientProvider>
      </MsalProvider>
    </ErrorBoundary>
  );
}

export default App;
