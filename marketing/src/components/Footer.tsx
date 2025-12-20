import Link from 'next/link'

export default function Footer() {
  return (
    <footer className="border-t border-ink-800/50 py-16 px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="grid md:grid-cols-2 lg:grid-cols-5 gap-12 mb-16">
          {/* Brand */}
          <div className="lg:col-span-2">
            <Link href="/" className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-sm bg-gradient-to-br from-copper-500 to-copper-600 flex items-center justify-center">
                <span className="font-display text-ink-950 text-lg font-bold">BC</span>
              </div>
              <span className="font-display text-xl text-cream-100 tracking-tight">
                Legal Tech
              </span>
            </Link>
            <p className="text-ink-400 leading-relaxed max-w-sm">
              AI-powered legal document intelligence designed exclusively for British Columbia law firms.
            </p>
          </div>

          {/* Product */}
          <div>
            <h4 className="text-cream-100 font-medium mb-6 text-sm tracking-wider uppercase">
              Product
            </h4>
            <ul className="space-y-4">
              <li>
                <Link href="/features" className="text-ink-400 hover:text-copper-400 transition-colors link-underline">
                  Features
                </Link>
              </li>
              <li>
                <Link href="/pricing" className="text-ink-400 hover:text-copper-400 transition-colors link-underline">
                  Pricing
                </Link>
              </li>
            </ul>
          </div>

          {/* Company */}
          <div>
            <h4 className="text-cream-100 font-medium mb-6 text-sm tracking-wider uppercase">
              Company
            </h4>
            <ul className="space-y-4">
              <li>
                <Link href="/about" className="text-ink-400 hover:text-copper-400 transition-colors link-underline">
                  About Us
                </Link>
              </li>
              <li>
                <Link href="/contact" className="text-ink-400 hover:text-copper-400 transition-colors link-underline">
                  Contact
                </Link>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h4 className="text-cream-100 font-medium mb-6 text-sm tracking-wider uppercase">
              Legal
            </h4>
            <ul className="space-y-4">
              <li>
                <Link href="/privacy" className="text-ink-400 hover:text-copper-400 transition-colors link-underline">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link href="/terms" className="text-ink-400 hover:text-copper-400 transition-colors link-underline">
                  Terms of Service
                </Link>
              </li>
              <li>
                <Link href="/cookies" className="text-ink-400 hover:text-copper-400 transition-colors link-underline">
                  Cookie Policy
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="border-t border-ink-800/50 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-ink-500 text-sm">
            &copy; 2025 BC Legal Tech. All rights reserved.
          </p>
          <div className="flex items-center gap-6">
            <span className="text-ink-600 text-sm">Built for BC law firms</span>
          </div>
        </div>
      </div>
    </footer>
  )
}
