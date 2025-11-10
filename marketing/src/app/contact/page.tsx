'use client'

import Link from 'next/link'
import { useForm } from 'react-hook-form'
import { useState } from 'react'
import { config } from '@/lib/config'

interface WaitlistFormData {
  full_name: string
  email: string
  company_name?: string
  phone?: string
  message?: string
  consent_marketing: boolean
}

export default function ContactPage() {
  const { register, handleSubmit, formState: { errors }, reset } = useForm<WaitlistFormData>()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle')
  const [errorMessage, setErrorMessage] = useState('')

  const onSubmit = async (data: WaitlistFormData) => {
    setIsSubmitting(true)
    setSubmitStatus('idle')
    setErrorMessage('')

    try {
      const response = await fetch(`${config.apiUrl}/api/v1/public/waitlist`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...data,
          source: 'contact_page',
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to submit. Please try again.')
      }

      setSubmitStatus('success')
      reset()
    } catch (error) {
      setSubmitStatus('error')
      setErrorMessage(error instanceof Error ? error.message : 'Something went wrong. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Hero */}
      <section className="pt-16 pb-12 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-primary-50 to-white">
        <div className="max-w-7xl mx-auto text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Get in Touch
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Interested in BC Legal Tech? Stay updated on new features, beta programs, and exclusive offers for BC law firms.
          </p>
        </div>
      </section>

      {/* Waitlist Form */}
      <section id="waitlist" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto">
          <div className="bg-white border border-gray-200 rounded-lg p-8 shadow-sm">
            <h2 className="text-3xl font-bold text-gray-900 mb-6 text-center">Get Early Access</h2>

            {submitStatus === 'success' && (
              <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-md">
                <p className="text-green-800 font-semibold">Success!</p>
                <p className="text-green-700">Thank you for your interest! You'll receive updates on new features and exclusive offers.</p>
              </div>
            )}

            {submitStatus === 'error' && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
                <p className="text-red-800 font-semibold">Error</p>
                <p className="text-red-700">{errorMessage}</p>
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              {/* Full Name */}
              <div>
                <label htmlFor="full_name" className="block text-sm font-medium text-gray-700 mb-2">
                  Full Name <span className="text-red-500">*</span>
                </label>
                <input
                  id="full_name"
                  type="text"
                  {...register('full_name', { required: 'Full name is required' })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="John Smith"
                />
                {errors.full_name && (
                  <p className="mt-1 text-sm text-red-600">{errors.full_name.message}</p>
                )}
              </div>

              {/* Email */}
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                  Email Address <span className="text-red-500">*</span>
                </label>
                <input
                  id="email"
                  type="email"
                  {...register('email', {
                    required: 'Email is required',
                    pattern: {
                      value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                      message: 'Invalid email address',
                    },
                  })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="john@lawfirm.ca"
                />
                {errors.email && (
                  <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
                )}
              </div>

              {/* Law Firm Name */}
              <div>
                <label htmlFor="company_name" className="block text-sm font-medium text-gray-700 mb-2">
                  Law Firm Name
                </label>
                <input
                  id="company_name"
                  type="text"
                  {...register('company_name')}
                  className="w-full px-4 py-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="Smith & Associates"
                />
              </div>

              {/* Phone */}
              <div>
                <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-2">
                  Phone Number (Optional)
                </label>
                <input
                  id="phone"
                  type="tel"
                  {...register('phone')}
                  className="w-full px-4 py-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="(604) 555-1234"
                />
              </div>

              {/* Message */}
              <div>
                <label htmlFor="message" className="block text-sm font-medium text-gray-700 mb-2">
                  Message (Optional)
                </label>
                <textarea
                  id="message"
                  {...register('message')}
                  rows={4}
                  className="w-full px-4 py-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="Tell us about your needs or ask any questions..."
                />
              </div>

              {/* CASL Consent Checkbox */}
              <div className="border border-gray-200 rounded-md p-4 bg-gray-50">
                <div className="flex items-start">
                  <div className="flex items-center h-5">
                    <input
                      id="consent_marketing"
                      type="checkbox"
                      {...register('consent_marketing', {
                        required: 'You must consent to receive updates to join the waitlist'
                      })}
                      className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                    />
                  </div>
                  <div className="ml-3">
                    <label htmlFor="consent_marketing" className="text-sm text-gray-700">
                      <span className="font-medium">I consent to receive commercial electronic messages</span> from BC Legal Tech,
                      including product updates, beta program invitations, feature announcements, and promotional offers.
                      I understand I can unsubscribe at any time by clicking the unsubscribe link in any email.{' '}
                      <span className="text-red-500">*</span>
                    </label>
                    {errors.consent_marketing && (
                      <p className="mt-1 text-sm text-red-600">{errors.consent_marketing.message}</p>
                    )}
                    <p className="mt-2 text-xs text-gray-500">
                      This consent is required under Canada's Anti-Spam Legislation (CASL).
                      Transactional emails (password resets, account notifications) do not require consent.
                    </p>
                  </div>
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-primary-600 text-white px-8 py-4 rounded-md text-lg font-semibold hover:bg-primary-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Submitting...' : 'Request Early Access'}
              </button>

              <p className="text-sm text-gray-500 text-center">
                By submitting this form, you agree to our{' '}
                <Link href="/privacy" className="text-primary-600 hover:text-primary-700">Privacy Policy</Link>
                {' '}and{' '}
                <Link href="/terms" className="text-primary-600 hover:text-primary-700">Terms of Service</Link>.
              </p>
            </form>
          </div>
        </div>
      </section>

      {/* Contact Info */}
      <section className="py-20 bg-gray-50 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-gray-900 mb-12 text-center">Other Ways to Reach Us</h2>
          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            <div className="bg-white p-8 rounded-lg shadow-sm">
              <h3 className="text-xl font-semibold mb-4 text-gray-900">Email</h3>
              <p className="text-gray-600">
                For general inquiries:<br />
                <a href="mailto:hello@bclegaltech.ca" className="text-primary-600 hover:text-primary-700">
                  hello@bclegaltech.ca
                </a>
              </p>
              <p className="text-gray-600 mt-4">
                For support:<br />
                <a href="mailto:support@bclegaltech.ca" className="text-primary-600 hover:text-primary-700">
                  support@bclegaltech.ca
                </a>
              </p>
            </div>
            <div className="bg-white p-8 rounded-lg shadow-sm">
              <h3 className="text-xl font-semibold mb-4 text-gray-900">Location</h3>
              <p className="text-gray-600">
                Based in British Columbia, Canada<br />
                Serving BC law firms province-wide
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <h3 className="text-lg font-semibold mb-4">BC Legal Tech</h3>
              <p className="text-gray-400">
                AI-powered legal document intelligence for BC law firms.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Product</h4>
              <ul className="space-y-2">
                <li><Link href="/features" className="text-gray-400 hover:text-white">Features</Link></li>
                <li><Link href="/pricing" className="text-gray-400 hover:text-white">Pricing</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Company</h4>
              <ul className="space-y-2">
                <li><Link href="/about" className="text-gray-400 hover:text-white">About Us</Link></li>
                <li><Link href="/contact" className="text-gray-400 hover:text-white">Contact</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Legal</h4>
              <ul className="space-y-2">
                <li><Link href="/privacy" className="text-gray-400 hover:text-white">Privacy Policy</Link></li>
                <li><Link href="/terms" className="text-gray-400 hover:text-white">Terms of Service</Link></li>
                <li><Link href="/cookies" className="text-gray-400 hover:text-white">Cookie Policy</Link></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 pt-8 text-center text-gray-400">
            <p>&copy; 2025 BC Legal Tech. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
