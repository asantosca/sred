// Forgot Password page - Request password reset

import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { authApi } from '@/lib/api'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Card, { CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import Alert from '@/components/ui/Alert'

const forgotPasswordSchema = z.object({
  email: z.string().email('Invalid email address'),
})

type ForgotPasswordFormData = z.infer<typeof forgotPasswordSchema>

export default function ForgotPasswordPage() {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordFormData>({
    resolver: zodResolver(forgotPasswordSchema),
  })

  const onSubmit = async (data: ForgotPasswordFormData) => {
    setIsSubmitting(true)
    setError(null)

    try {
      await authApi.requestPasswordReset(data)
      setSuccess(true)
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail || 'Failed to send reset email. Please try again.'
      setError(errorMessage)
    } finally {
      setIsSubmitting(false)
    }
  }

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
            <CardTitle>Reset your password</CardTitle>
            <CardDescription>
              Enter your email and we'll send you a link to reset your password
            </CardDescription>
          </CardHeader>

          <CardContent>
            {error && (
              <Alert variant="error" className="mb-4">
                {error}
              </Alert>
            )}

            {success && (
              <>
                <Alert variant="success" className="mb-4" title="Email sent!">
                  If the email exists, a password reset link has been sent. Please
                  check your email for instructions.
                </Alert>
                <Button
                  variant="outline"
                  size="md"
                  className="w-full"
                  onClick={() => setSuccess(false)}
                >
                  Send to a different email
                </Button>
              </>
            )}

            {!success && (
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                <Input
                  label="Email address"
                  type="email"
                  autoComplete="email"
                  placeholder="you@example.com"
                  error={errors.email?.message}
                  {...register('email')}
                />

                <Button
                  type="submit"
                  variant="primary"
                  size="lg"
                  className="w-full"
                  isLoading={isSubmitting}
                >
                  Send Reset Link
                </Button>
              </form>
            )}

            <div className="mt-6 text-center">
              <Link
                to="/login"
                className="text-sm font-medium text-primary-600 hover:text-primary-500"
              >
                Back to sign in
              </Link>
            </div>
          </CardContent>
        </Card>

        <p className="mt-8 text-center text-xs text-gray-500">
          &copy; {new Date().getFullYear()} BC Legal Tech. All rights reserved.
        </p>
      </div>
    </div>
  )
}
