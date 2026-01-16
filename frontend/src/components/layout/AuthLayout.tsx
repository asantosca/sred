// Auth layout for login/register pages with header and footer

import { ReactNode } from 'react'

const MARKETING_URL = import.meta.env.VITE_MARKETING_URL || 'http://localhost:3001'

interface AuthLayoutProps {
  children: ReactNode
}

export default function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col bg-gray-50">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <a
              href={MARKETING_URL}
              className="text-2xl font-bold text-primary-700 hover:text-primary-800 transition-colors"
            >
              SR&ED Intelligence
            </a>
            <a
              href={MARKETING_URL}
              className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
            >
              Back to Home
            </a>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex flex-1 items-center justify-center px-4 py-12 sm:px-6 lg:px-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            <p className="text-xs text-gray-500">
              &copy; {new Date().getFullYear()} SR&ED Intelligence. All rights reserved.
            </p>
            <div className="flex gap-6 text-xs">
              <a
                href={`${MARKETING_URL}/privacy`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-600 hover:text-gray-900 transition-colors"
              >
                Privacy Policy
              </a>
              <a
                href={`${MARKETING_URL}/terms`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-600 hover:text-gray-900 transition-colors"
              >
                Terms of Service
              </a>
              <a
                href={`${MARKETING_URL}/contact`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-600 hover:text-gray-900 transition-colors"
              >
                Contact
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
