'use client'

import Link from 'next/link'
import { useForm } from 'react-hook-form'
import { useState } from 'react'
import { config } from '@/lib/config'
import Footer from '@/components/Footer'

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
    <div className="min-h-screen bg-ink-950">
      {/* Hero */}
      <section className="relative pt-32 pb-16 px-6 lg:px-8 overflow-hidden">
        <div className="absolute inset-0">
          <div className="absolute top-0 left-1/3 w-96 h-96 bg-copper-500/5 rounded-full blur-3xl" />
        </div>

        <div className="relative max-w-7xl mx-auto text-center">
          <div className="flex items-center justify-center gap-4 mb-6">
            <div className="accent-line" />
            <span className="text-copper-400 text-sm font-medium tracking-widest uppercase">
              Get in Touch
            </span>
            <div className="accent-line transform rotate-180" />
          </div>
          <h1 className="font-display text-5xl md:text-6xl text-cream-100 leading-tight mb-6">
            Contact Us
          </h1>
          <p className="text-ink-300 text-xl max-w-3xl mx-auto leading-relaxed">
            Interested in BC Legal Tech? Stay updated on new features, beta programs, and exclusive offers for BC law firms.
          </p>
        </div>
      </section>

      {/* Waitlist Form */}
      <section id="waitlist" className="py-10 px-6 lg:px-8">
        <div className="max-w-3xl mx-auto">
          <div className="glass-card rounded-sm p-8 lg:p-10">

            {submitStatus === 'success' && (
              <div className="mb-6 p-4 bg-green-500/10 border border-green-500/30 rounded-sm">
                <p className="text-green-400 font-semibold">Success!</p>
                <p className="text-green-300/80">Thank you for your interest! You&apos;ll receive updates on new features and exclusive offers.</p>
              </div>
            )}

            {submitStatus === 'error' && (
              <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-sm">
                <p className="text-red-400 font-semibold">Error</p>
                <p className="text-red-300/80">{errorMessage}</p>
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              {/* Full Name */}
              <div>
                <label htmlFor="full_name" className="block text-sm text-ink-300 mb-2">
                  Full Name <span className="text-copper-500">*</span>
                </label>
                <input
                  id="full_name"
                  type="text"
                  {...register('full_name', { required: 'Full name is required' })}
                  className="input-field"
                  placeholder="John Smith"
                />
                {errors.full_name && (
                  <p className="mt-1 text-sm text-red-400">{errors.full_name.message}</p>
                )}
              </div>

              {/* Email */}
              <div>
                <label htmlFor="email" className="block text-sm text-ink-300 mb-2">
                  Email Address <span className="text-copper-500">*</span>
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
                  className="input-field"
                  placeholder="john@lawfirm.ca"
                />
                {errors.email && (
                  <p className="mt-1 text-sm text-red-400">{errors.email.message}</p>
                )}
              </div>

              {/* Law Firm Name */}
              <div>
                <label htmlFor="company_name" className="block text-sm text-ink-300 mb-2">
                  Law Firm Name
                </label>
                <input
                  id="company_name"
                  type="text"
                  {...register('company_name')}
                  className="input-field"
                  placeholder="Smith & Associates"
                />
              </div>

              {/* Phone */}
              <div>
                <label htmlFor="phone" className="block text-sm text-ink-300 mb-2">
                  Phone Number <span className="text-ink-500">(Optional)</span>
                </label>
                <input
                  id="phone"
                  type="tel"
                  {...register('phone')}
                  className="input-field"
                  placeholder="(604) 555-1234"
                />
              </div>

              {/* Message */}
              <div>
                <label htmlFor="message" className="block text-sm text-ink-300 mb-2">
                  Message <span className="text-ink-500">(Optional)</span>
                </label>
                <textarea
                  id="message"
                  {...register('message')}
                  rows={4}
                  className="input-field resize-none"
                  placeholder="Tell us about your needs or ask any questions..."
                />
              </div>

              {/* CASL Consent Checkbox */}
              <div className="p-5 border border-ink-700 rounded-sm bg-ink-900/50">
                <div className="flex items-start gap-3">
                  <div className="flex items-center h-5 mt-0.5">
                    <input
                      id="consent_marketing"
                      type="checkbox"
                      {...register('consent_marketing', {
                        required: 'You must consent to receive updates to join the waitlist'
                      })}
                      className="w-4 h-4 bg-ink-800 border-ink-600 rounded text-copper-500 focus:ring-copper-500 focus:ring-offset-ink-900"
                    />
                  </div>
                  <div>
                    <label htmlFor="consent_marketing" className="text-sm text-ink-300">
                      <span className="font-medium text-cream-100">I consent to receive commercial electronic messages</span> from BC Legal Tech,
                      including product updates, beta program invitations, feature announcements, and promotional offers.
                      I understand I can unsubscribe at any time by clicking the unsubscribe link in any email.{' '}
                      <span className="text-copper-500">*</span>
                    </label>
                    {errors.consent_marketing && (
                      <p className="mt-1 text-sm text-red-400">{errors.consent_marketing.message}</p>
                    )}
                    <p className="mt-2 text-xs text-ink-500">
                      This consent is required under Canada&apos;s Anti-Spam Legislation (CASL).
                      Transactional emails (password resets, account notifications) do not require consent.
                    </p>
                  </div>
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isSubmitting}
                className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Submitting...' : 'Request Early Access'}
              </button>

              <p className="text-sm text-ink-500 text-center">
                By submitting this form, you agree to our{' '}
                <Link href="/privacy" className="text-copper-400 hover:text-copper-300 transition-colors">Privacy Policy</Link>
                {' '}and{' '}
                <Link href="/terms" className="text-copper-400 hover:text-copper-300 transition-colors">Terms of Service</Link>.
              </p>
            </form>
          </div>
        </div>
      </section>

      {/* Contact Info */}
      <section className="py-20 px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="font-display text-3xl text-cream-100 mb-4">
              Other Ways to Reach Us
            </h2>
          </div>

          <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
            <div className="glass-card rounded-sm p-8 group hover:glow-copper transition-all duration-500">
              <div className="w-12 h-12 rounded-sm bg-copper-500/10 flex items-center justify-center mb-6 group-hover:bg-copper-500/20 transition-colors">
                <svg className="w-6 h-6 text-copper-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 className="font-display text-xl text-cream-100 mb-4">Email</h3>
              <p className="text-ink-400 mb-2">
                For general inquiries:
              </p>
              <a href="mailto:hello@bclegaltech.ca" className="text-copper-400 hover:text-copper-300 transition-colors">
                hello@bclegaltech.ca
              </a>
              <p className="text-ink-400 mt-4 mb-2">
                For support:
              </p>
              <a href="mailto:support@bclegaltech.ca" className="text-copper-400 hover:text-copper-300 transition-colors">
                support@bclegaltech.ca
              </a>
            </div>

            <div className="glass-card rounded-sm p-8 group hover:glow-copper transition-all duration-500">
              <div className="w-12 h-12 rounded-sm bg-copper-500/10 flex items-center justify-center mb-6 group-hover:bg-copper-500/20 transition-colors">
                <svg className="w-6 h-6 text-copper-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <h3 className="font-display text-xl text-cream-100 mb-4">Location</h3>
              <p className="text-ink-400">
                Based in British Columbia, Canada
              </p>
              <p className="text-ink-400 mt-2">
                Serving BC law firms province-wide
              </p>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  )
}
