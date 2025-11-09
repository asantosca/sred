'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

export default function CookieConsent() {
  const [showBanner, setShowBanner] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [preferences, setPreferences] = useState({
    necessary: true, // Always true, can't be disabled
    functional: true,
    analytics: true,
  })

  useEffect(() => {
    // Check if user has already made a choice
    const consent = localStorage.getItem('cookie-consent')
    if (!consent) {
      // Show banner after a short delay for better UX
      setTimeout(() => setShowBanner(true), 1000)
    } else {
      // Load saved preferences
      try {
        const saved = JSON.parse(consent)
        setPreferences(saved)
      } catch (e) {
        // Invalid JSON, show banner again
        setShowBanner(true)
      }
    }
  }, [])

  const handleAcceptAll = () => {
    const allAccepted = {
      necessary: true,
      functional: true,
      analytics: true,
    }
    savePreferences(allAccepted)
  }

  const handleRejectNonEssential = () => {
    const onlyNecessary = {
      necessary: true,
      functional: false,
      analytics: false,
    }
    savePreferences(onlyNecessary)
  }

  const handleSavePreferences = () => {
    savePreferences(preferences)
  }

  const savePreferences = (prefs: typeof preferences) => {
    localStorage.setItem('cookie-consent', JSON.stringify(prefs))
    localStorage.setItem('cookie-consent-date', new Date().toISOString())
    setPreferences(prefs)
    setShowBanner(false)
    setShowSettings(false)
  }

  const handleToggle = (key: keyof typeof preferences) => {
    if (key === 'necessary') return // Can't disable necessary cookies
    setPreferences(prev => ({ ...prev, [key]: !prev[key] }))
  }

  if (!showBanner) return null

  return (
    <>
      {/* Cookie Consent Banner */}
      <div className="fixed bottom-0 left-0 right-0 z-50 bg-white border-t-2 border-gray-200 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {!showSettings ? (
            /* Simple Banner */
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  We Value Your Privacy
                </h3>
                <p className="text-sm text-gray-600">
                  We use cookies to enhance your experience, analyze site usage, and improve our service.
                  By clicking "Accept All", you consent to our use of cookies.{' '}
                  <Link href="/cookies" className="text-primary-600 hover:text-primary-700 underline">
                    Learn more
                  </Link>
                </p>
              </div>
              <div className="flex flex-col sm:flex-row gap-3 w-full md:w-auto">
                <button
                  onClick={() => setShowSettings(true)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  Cookie Settings
                </button>
                <button
                  onClick={handleRejectNonEssential}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  Reject Non-Essential
                </button>
                <button
                  onClick={handleAcceptAll}
                  className="px-4 py-2 bg-primary-600 text-white rounded-md text-sm font-medium hover:bg-primary-700 transition-colors"
                >
                  Accept All
                </button>
              </div>
            </div>
          ) : (
            /* Settings Panel */
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  Cookie Preferences
                </h3>
                <button
                  onClick={() => setShowSettings(false)}
                  className="text-gray-500 hover:text-gray-700"
                  aria-label="Close settings"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="space-y-4 mb-6">
                {/* Necessary Cookies */}
                <div className="flex items-start justify-between pb-4 border-b border-gray-200">
                  <div className="flex-1 pr-4">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-semibold text-gray-900">Strictly Necessary</h4>
                      <span className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded">
                        Always Active
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">
                      These cookies are essential for the website to function and cannot be disabled.
                      They enable core functionality like security, authentication, and session management.
                    </p>
                  </div>
                  <div className="flex-shrink-0">
                    <div className="w-12 h-6 bg-gray-400 rounded-full cursor-not-allowed opacity-50">
                      <div className="w-5 h-5 bg-white rounded-full shadow transform translate-x-6 mt-0.5"></div>
                    </div>
                  </div>
                </div>

                {/* Functional Cookies */}
                <div className="flex items-start justify-between pb-4 border-b border-gray-200">
                  <div className="flex-1 pr-4">
                    <h4 className="font-semibold text-gray-900 mb-1">Functional Cookies</h4>
                    <p className="text-sm text-gray-600">
                      These cookies enable enhanced functionality like remembering your preferences
                      and settings for a better user experience.
                    </p>
                  </div>
                  <div className="flex-shrink-0">
                    <button
                      onClick={() => handleToggle('functional')}
                      className={`w-12 h-6 rounded-full transition-colors ${
                        preferences.functional ? 'bg-primary-600' : 'bg-gray-300'
                      }`}
                      aria-label="Toggle functional cookies"
                    >
                      <div
                        className={`w-5 h-5 bg-white rounded-full shadow transform transition-transform mt-0.5 ${
                          preferences.functional ? 'translate-x-6' : 'translate-x-1'
                        }`}
                      ></div>
                    </button>
                  </div>
                </div>

                {/* Analytics Cookies */}
                <div className="flex items-start justify-between">
                  <div className="flex-1 pr-4">
                    <h4 className="font-semibold text-gray-900 mb-1">Analytics Cookies</h4>
                    <p className="text-sm text-gray-600">
                      These cookies help us understand how visitors use our website, allowing us to
                      improve our service. All data is anonymized and aggregated.
                    </p>
                  </div>
                  <div className="flex-shrink-0">
                    <button
                      onClick={() => handleToggle('analytics')}
                      className={`w-12 h-6 rounded-full transition-colors ${
                        preferences.analytics ? 'bg-primary-600' : 'bg-gray-300'
                      }`}
                      aria-label="Toggle analytics cookies"
                    >
                      <div
                        className={`w-5 h-5 bg-white rounded-full shadow transform transition-transform mt-0.5 ${
                          preferences.analytics ? 'translate-x-6' : 'translate-x-1'
                        }`}
                      ></div>
                    </button>
                  </div>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-3">
                <button
                  onClick={handleRejectNonEssential}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  Reject Non-Essential
                </button>
                <button
                  onClick={handleSavePreferences}
                  className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-md text-sm font-medium hover:bg-primary-700 transition-colors"
                >
                  Save Preferences
                </button>
              </div>

              <p className="text-xs text-gray-500 mt-4 text-center">
                Read our{' '}
                <Link href="/cookies" className="text-primary-600 hover:text-primary-700 underline">
                  Cookie Policy
                </Link>{' '}
                and{' '}
                <Link href="/privacy" className="text-primary-600 hover:text-primary-700 underline">
                  Privacy Policy
                </Link>{' '}
                for more information.
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  )
}
