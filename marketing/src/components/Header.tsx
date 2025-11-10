'use client'

import Link from 'next/link'

const APP_URL = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'

export default function Header() {
  return (
    <nav className="border-b border-gray-200 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center">
            <Link href="/" className="text-2xl font-bold text-primary-700 hover:text-primary-800">
              BC Legal Tech
            </Link>
          </div>

          {/* Navigation Links */}
          <div className="hidden md:flex items-center space-x-8">
            <Link href="/features" className="text-gray-700 hover:text-primary-700 transition-colors">
              Features
            </Link>
            <Link href="/pricing" className="text-gray-700 hover:text-primary-700 transition-colors">
              Pricing
            </Link>
            <Link href="/about" className="text-gray-700 hover:text-primary-700 transition-colors">
              About
            </Link>
            <Link href="/contact" className="text-gray-700 hover:text-primary-700 transition-colors">
              Contact
            </Link>

            {/* Auth Buttons */}
            <a
              href={`${APP_URL}/login`}
              className="text-gray-700 hover:text-primary-700 transition-colors font-medium"
            >
              Login
            </a>
            <a
              href={`${APP_URL}/register`}
              className="bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700 transition-colors font-medium"
            >
              Get Started
            </a>
          </div>
        </div>
      </div>
    </nav>
  )
}
