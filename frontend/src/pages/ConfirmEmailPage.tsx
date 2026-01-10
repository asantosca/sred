// Email Confirmation page - Activate account after registration

import { useState, useEffect, useRef } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import { authApi } from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { trackSignUpConfirmed } from '@/utils/analytics'
import Button from '@/components/ui/Button'
import Card, { CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import Alert from '@/components/ui/Alert'
import { CheckCircle, XCircle } from 'lucide-react'

export default function ConfirmEmailPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')

  const { setAuth } = useAuthStore()
  const [isConfirming, setIsConfirming] = useState(true)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Prevent double-execution in React StrictMode
  const hasConfirmed = useRef(false)

  useEffect(() => {
    const confirmEmail = async () => {
      if (!token) {
        setError('Invalid or missing confirmation token')
        setIsConfirming(false)
        return
      }

      // Prevent duplicate API calls
      if (hasConfirmed.current) {
        return
      }
      hasConfirmed.current = true

      try {
        // Confirm email (activates account and returns auth tokens)
        const response = await authApi.confirmEmail(token)

        // Auto-login after email confirmation
        setAuth(response.data)
        setSuccess(true)
        trackSignUpConfirmed()

        // Redirect to dashboard after 2 seconds
        setTimeout(() => {
          navigate('/dashboard')
        }, 2000)
      } catch (err: any) {
        const errorMessage =
          err.response?.data?.detail || 'Invalid or expired confirmation token'
        setError(errorMessage)
      } finally {
        setIsConfirming(false)
      }
    }

    confirmEmail()
  }, [token, navigate, setAuth])

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-md">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">BC Legal Tech</h1>
          <p className="mt-2 text-sm text-gray-600">
            AI-Powered Legal Document Intelligence
          </p>
        </div>

        <Card className="mt-8">
          <CardHeader>
            <CardTitle>Email Confirmation</CardTitle>
            <CardDescription>
              Activating your account...
            </CardDescription>
          </CardHeader>

          <CardContent>
            {isConfirming && (
              <div className="text-center py-8">
                <div className="inline-block h-12 w-12 animate-spin rounded-full border-4 border-solid border-primary-600 border-r-transparent"></div>
                <p className="mt-4 text-sm text-gray-600">
                  Confirming your email address...
                </p>
              </div>
            )}

            {!isConfirming && success && (
              <div className="text-center py-8">
                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
                  <CheckCircle className="h-10 w-10 text-green-600" />
                </div>
                <h3 className="mt-4 text-lg font-semibold text-gray-900">
                  Email confirmed!
                </h3>
                <p className="mt-2 text-sm text-gray-600">
                  Your account has been activated. Redirecting to your dashboard...
                </p>
              </div>
            )}

            {!isConfirming && error && !success && (
              <>
                <div className="text-center py-8">
                  <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-red-100">
                    <XCircle className="h-10 w-10 text-red-600" />
                  </div>
                  <h3 className="mt-4 text-lg font-semibold text-gray-900">
                    Confirmation failed
                  </h3>
                </div>

                <Alert variant="error" className="mb-4">
                  {error}
                </Alert>

                <div className="space-y-2">
                  <Button
                    variant="primary"
                    size="lg"
                    className="w-full"
                    onClick={() => navigate('/register')}
                  >
                    Create a new account
                  </Button>

                  <div className="text-center">
                    <Link
                      to="/login"
                      className="text-sm font-medium text-primary-600 hover:text-primary-500"
                    >
                      Back to sign in
                    </Link>
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        <p className="mt-8 text-center text-xs text-gray-500">
          &copy; 2024 BC Legal Tech. All rights reserved.
        </p>
      </div>
    </div>
  )
}
