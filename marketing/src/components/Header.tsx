'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

const APP_URL = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'

export default function Header() {
  const [scrolled, setScrolled] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        scrolled
          ? 'bg-ink-950/90 backdrop-blur-lg border-b border-ink-800/50'
          : 'bg-transparent'
      }`}
    >
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="flex justify-between items-center h-20">
          {/* Logo */}
          <Link href="/" className="group flex items-center gap-3">
            <div className="w-10 h-10 rounded-sm bg-gradient-to-br from-copper-500 to-copper-600 flex items-center justify-center transform group-hover:scale-105 transition-transform duration-300">
              <span className="font-display text-ink-950 text-lg font-bold">BC</span>
            </div>
            <div className="hidden sm:block">
              <span className="font-display text-xl text-cream-100 tracking-tight">
                Legal Tech
              </span>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-10">
            <Link
              href="/features"
              className="text-ink-200 hover:text-copper-400 transition-colors duration-300 text-sm tracking-wide link-underline"
            >
              Features
            </Link>
            <Link
              href="/pricing"
              className="text-ink-200 hover:text-copper-400 transition-colors duration-300 text-sm tracking-wide link-underline"
            >
              Pricing
            </Link>
            <Link
              href="/about"
              className="text-ink-200 hover:text-copper-400 transition-colors duration-300 text-sm tracking-wide link-underline"
            >
              About
            </Link>
            <Link
              href="/contact"
              className="text-ink-200 hover:text-copper-400 transition-colors duration-300 text-sm tracking-wide link-underline"
            >
              Contact
            </Link>

            {/* Divider */}
            <div className="w-px h-6 bg-ink-700" />

            {/* Auth */}
            <a
              href={`${APP_URL}/login`}
              className="text-cream-100 hover:text-copper-400 transition-colors duration-300 text-sm font-medium tracking-wide"
            >
              Login
            </a>
            <a
              href={`${APP_URL}/register`}
              className="btn-primary text-sm px-5 py-2.5"
            >
              Get Started
            </a>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 text-cream-100 hover:text-copper-400 transition-colors"
            aria-label="Toggle menu"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              {mobileMenuOpen ? (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M6 18L18 6M6 6l12 12"
                />
              ) : (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              )}
            </svg>
          </button>
        </div>

        {/* Mobile Menu */}
        <div
          className={`md:hidden overflow-hidden transition-all duration-300 ${
            mobileMenuOpen ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
          }`}
        >
          <div className="py-6 space-y-4 border-t border-ink-800/50">
            <Link
              href="/features"
              className="block text-ink-200 hover:text-copper-400 transition-colors py-2"
              onClick={() => setMobileMenuOpen(false)}
            >
              Features
            </Link>
            <Link
              href="/pricing"
              className="block text-ink-200 hover:text-copper-400 transition-colors py-2"
              onClick={() => setMobileMenuOpen(false)}
            >
              Pricing
            </Link>
            <Link
              href="/about"
              className="block text-ink-200 hover:text-copper-400 transition-colors py-2"
              onClick={() => setMobileMenuOpen(false)}
            >
              About
            </Link>
            <Link
              href="/contact"
              className="block text-ink-200 hover:text-copper-400 transition-colors py-2"
              onClick={() => setMobileMenuOpen(false)}
            >
              Contact
            </Link>
            <div className="pt-4 space-y-3 border-t border-ink-800/50">
              <a
                href={`${APP_URL}/login`}
                className="block text-cream-100 hover:text-copper-400 transition-colors py-2"
              >
                Login
              </a>
              <a
                href={`${APP_URL}/register`}
                className="btn-primary inline-block text-center w-full"
              >
                Get Started
              </a>
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}
