// Main App component with routing

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import ProtectedRoute from '@/components/layout/ProtectedRoute'
import ErrorBoundary from '@/components/ErrorBoundary'

// Auth pages
import LoginPage from '@/pages/LoginPage'
import RegisterPage from '@/pages/RegisterPage'
import ForgotPasswordPage from '@/pages/ForgotPasswordPage'
import ResetPasswordPage from '@/pages/ResetPasswordPage'
import ConfirmEmailPage from '@/pages/ConfirmEmailPage'

// Protected pages
import DashboardPage from '@/pages/DashboardPage'
import ProfilePage from '@/pages/ProfilePage'
import DocumentsPage from '@/pages/DocumentsPage'
import ChatPage from '@/pages/ChatPage'
import MattersPage from '@/pages/MattersPage'
import CreateMatterPage from '@/pages/CreateMatterPage'
import MatterDetailPage from '@/pages/MatterDetailPage'

// Create a query client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
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
                primary: '#10b981',
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
        <BrowserRouter>
          <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route path="/confirm-email" element={<ConfirmEmailPage />} />

          {/* Protected routes */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            }
          />

          {/* Documents route */}
          <Route
            path="/documents"
            element={
              <ProtectedRoute>
                <DocumentsPage />
              </ProtectedRoute>
            }
          />

          {/* Matters routes */}
          <Route
            path="/matters"
            element={
              <ProtectedRoute>
                <MattersPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/matters/new"
            element={
              <ProtectedRoute>
                <CreateMatterPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/matters/:matterId"
            element={
              <ProtectedRoute>
                <MatterDetailPage />
              </ProtectedRoute>
            }
          />

          {/* Chat route */}
          <Route
            path="/chat"
            element={
              <ProtectedRoute>
                <ChatPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/users"
            element={
              <ProtectedRoute>
                <div className="flex h-screen items-center justify-center">
                  <div className="text-center">
                    <h1 className="text-2xl font-bold text-gray-900">Users</h1>
                    <p className="mt-2 text-gray-600">Coming soon...</p>
                  </div>
                </div>
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <div className="flex h-screen items-center justify-center">
                  <div className="text-center">
                    <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
                    <p className="mt-2 text-gray-600">Coming soon...</p>
                  </div>
                </div>
              </ProtectedRoute>
            }
          />

          {/* Redirect root to dashboard */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />

          {/* 404 page */}
          <Route
            path="*"
            element={
              <div className="flex h-screen items-center justify-center bg-gray-50">
                <div className="text-center">
                  <h1 className="text-6xl font-bold text-gray-900">404</h1>
                  <p className="mt-2 text-xl text-gray-600">Page not found</p>
                  <a
                    href="/dashboard"
                    className="mt-4 inline-block text-primary-600 hover:text-primary-500"
                  >
                    Go to dashboard
                  </a>
                </div>
              </div>
            }
          />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
    </ErrorBoundary>
  )
}

export default App
