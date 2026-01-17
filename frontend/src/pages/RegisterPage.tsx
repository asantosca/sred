// Registration page for new company signup

import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import toast from 'react-hot-toast'
import { authApi } from '@/lib/api'
import { trackSignUp } from '@/utils/analytics'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Card, { CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import Alert from '@/components/ui/Alert'
import AuthLayout from '@/components/layout/AuthLayout'

const MARKETING_URL = import.meta.env.VITE_MARKETING_URL || 'http://localhost:3001'

const registerSchema = z.object({
  company_name: z.string().min(2, 'Company name must be at least 2 characters'),
  admin_email: z.string().email('Invalid email address'),
  admin_password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least one digit'),
  admin_first_name: z.string().optional(),
  admin_last_name: z.string().optional(),
})

type RegisterFormData = z.infer<typeof registerSchema>

export default function RegisterPage() {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  })

  const onSubmit = async (data: RegisterFormData) => {
    setIsSubmitting(true)
    setError(null)

    try {
      await authApi.register(data)
      setSuccess(true)
      trackSignUp('email')
      toast.success('Registration successful! Please check your email to confirm your account.')
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail || 'Registration failed. Please try again.'
      setError(errorMessage)
      toast.error(errorMessage)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <AuthLayout>
      <div className="w-full max-w-md">
        <Card>
          {!success && (
            <CardHeader>
              <CardTitle>Create your account</CardTitle>
              <CardDescription>
                Start your free trial - no credit card required
              </CardDescription>
            </CardHeader>
          )}

          <CardContent>
            {success ? (
              <div className="py-8 text-center">
                <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
                  <svg
                    className="h-10 w-10 text-green-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-gray-900">
                  Registration Successful!
                </h3>
                <p className="mt-4 text-base text-gray-600">
                  Check your inbox to validate the email account
                </p>
              </div>
            ) : (
              <>
                {error && (
                  <Alert variant="error" className="mb-4">
                    {error}
                  </Alert>
                )}

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                  <Input
                label="Company Name"
                type="text"
                placeholder="Company Name"
                error={errors.company_name?.message}
                {...register('company_name')}
                  />

                  <Input
                label="Admin Email"
                type="email"
                autoComplete="email"
                placeholder="admin@yourcompany.com"
                error={errors.admin_email?.message}
                helperText="This will be your login email"
                {...register('admin_email')}
                  />

                  <Input
                label="Password"
                type="password"
                autoComplete="new-password"
                placeholder="••••••••"
                error={errors.admin_password?.message}
                helperText="Min 8 chars, 1 uppercase, 1 lowercase, 1 digit"
                {...register('admin_password')}
                  />

                  <div className="grid grid-cols-2 gap-4">
                <Input
                  label="First Name (optional)"
                  type="text"
                  autoComplete="given-name"
                  placeholder="John"
                  error={errors.admin_first_name?.message}
                  {...register('admin_first_name')}
                />

                <Input
                  label="Last Name (optional)"
                  type="text"
                  autoComplete="family-name"
                  placeholder="Doe"
                  error={errors.admin_last_name?.message}
                  {...register('admin_last_name')}
                />
                  </div>

                  <div className="text-xs text-gray-500">
                By signing up, you agree to our{' '}
                <a
                  href={`${MARKETING_URL}/terms`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:text-primary-500 underline"
                >
                  Terms of Service
                </a>{' '}
                and{' '}
                <a
                  href={`${MARKETING_URL}/privacy`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:text-primary-500 underline"
                >
                  Privacy Policy
                </a>
                .
                  </div>

                  <Button
                type="submit"
                variant="primary"
                size="lg"
                className="w-full"
                isLoading={isSubmitting}
                disabled={success}
              >
                Create Account
                  </Button>
                </form>

                <div className="mt-6 text-center">
              <p className="text-sm text-gray-600">
                Already have an account?{' '}
                <Link
                  to="/login"
                  className="font-medium text-primary-600 hover:text-primary-500"
                >
                  Sign in
                </Link>
              </p>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </AuthLayout>
  )
}
