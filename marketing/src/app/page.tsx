import Link from 'next/link'

const APP_URL = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'

export default function HomePage() {
  return (
    <div className="min-h-screen bg-ink-950">
      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center overflow-hidden">
        {/* Background Elements */}
        <div className="absolute inset-0">
          {/* Gradient orbs */}
          <div className="absolute top-1/4 -left-32 w-96 h-96 bg-copper-500/10 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-copper-600/5 rounded-full blur-3xl" />

          {/* Grid pattern */}
          <div
            className="absolute inset-0 opacity-[0.02]"
            style={{
              backgroundImage: `linear-gradient(var(--ink-700) 1px, transparent 1px),
                               linear-gradient(90deg, var(--ink-700) 1px, transparent 1px)`,
              backgroundSize: '60px 60px',
            }}
          />

          {/* Diagonal accent line */}
          <div className="absolute top-0 right-0 w-px h-full bg-gradient-to-b from-transparent via-copper-500/20 to-transparent transform rotate-12 origin-top translate-x-40" />
        </div>

        <div className="relative max-w-7xl mx-auto px-6 lg:px-8 py-32 lg:py-40">
          <div className="grid lg:grid-cols-12 gap-12 items-center">
            {/* Left content */}
            <div className="lg:col-span-7 space-y-8">
              {/* Eyebrow */}
              <div className="flex items-center gap-4 opacity-0 animate-fade-up">
                <div className="accent-line" />
                <span className="text-copper-400 text-sm font-medium tracking-widest uppercase">
                  For BC Law Firms
                </span>
              </div>

              {/* Headline */}
              <h1 className="opacity-0 animate-fade-up-delay-1">
                <span className="block font-display text-5xl md:text-6xl lg:text-7xl text-cream-100 leading-[1.1] tracking-tight">
                  Legal Intelligence,
                </span>
                <span className="block font-display text-5xl md:text-6xl lg:text-7xl leading-[1.1] tracking-tight mt-2">
                  <span className="gradient-text">Reimagined</span>
                </span>
              </h1>

              {/* Description */}
              <p className="text-ink-300 text-lg md:text-xl max-w-xl leading-relaxed opacity-0 animate-fade-up-delay-2">
                Transform how you search, analyze, and understand legal documents.
                AI-powered semantic search built specifically for British Columbia legal professionals.
              </p>

              {/* CTA Buttons */}
              <div className="flex flex-col sm:flex-row gap-4 pt-4 opacity-0 animate-fade-up-delay-3">
                <a href={`${APP_URL}/register`} className="btn-primary text-center">
                  Start Free Trial
                </a>
                <Link href="/features" className="btn-secondary text-center">
                  Explore Features
                </Link>
              </div>

              {/* Social proof */}
              <div className="pt-8 opacity-0 animate-fade-up-delay-4">
                <p className="text-ink-400 text-sm">
                  Trusted by forward-thinking firms across British Columbia
                </p>
              </div>
            </div>

            {/* Right decorative element */}
            <div className="lg:col-span-5 hidden lg:block">
              <div className="relative">
                {/* Abstract document visualization */}
                <div className="relative w-full aspect-square">
                  {/* Floating cards */}
                  <div className="absolute top-0 right-0 w-64 h-40 glass-card rounded-sm p-6 transform rotate-3 animate-float opacity-0 animate-fade-up-delay-2">
                    <div className="space-y-3">
                      <div className="h-2 w-20 bg-copper-500/30 rounded-full" />
                      <div className="h-2 w-32 bg-ink-600 rounded-full" />
                      <div className="h-2 w-24 bg-ink-600 rounded-full" />
                      <div className="h-2 w-28 bg-ink-600 rounded-full" />
                    </div>
                  </div>

                  <div className="absolute top-1/4 left-0 w-56 h-36 glass-card rounded-sm p-5 transform -rotate-6 animate-float opacity-0 animate-fade-up-delay-3" style={{ animationDelay: '1s' }}>
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-8 h-8 rounded-full bg-copper-500/20 flex items-center justify-center">
                        <svg className="w-4 h-4 text-copper-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                      </div>
                      <div className="h-2 w-24 bg-ink-600 rounded-full" />
                    </div>
                    <div className="space-y-2">
                      <div className="h-2 w-full bg-copper-500/20 rounded-full" />
                      <div className="h-2 w-3/4 bg-ink-700 rounded-full" />
                    </div>
                  </div>

                  <div className="absolute bottom-12 right-8 w-48 h-32 glass-card rounded-sm p-5 transform rotate-6 animate-float opacity-0 animate-fade-up-delay-4" style={{ animationDelay: '2s' }}>
                    <div className="flex items-center gap-2 mb-3">
                      <div className="w-6 h-6 rounded-full bg-green-500/20 flex items-center justify-center">
                        <svg className="w-3 h-3 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                      <span className="text-xs text-ink-300">Analysis Complete</span>
                    </div>
                    <div className="space-y-2">
                      <div className="h-2 w-full bg-ink-700 rounded-full" />
                      <div className="h-2 w-2/3 bg-ink-700 rounded-full" />
                    </div>
                  </div>

                  {/* Center glow */}
                  <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-32 h-32 bg-copper-500/10 rounded-full blur-2xl" />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 opacity-0 animate-fade-up-delay-4">
          <div className="flex flex-col items-center gap-2 text-ink-500">
            <span className="text-xs tracking-widest uppercase">Scroll</span>
            <div className="w-px h-8 bg-gradient-to-b from-ink-500 to-transparent" />
          </div>
        </div>
      </section>

      {/* Section Divider */}
      <div className="section-divider max-w-7xl mx-auto" />

      {/* Features Section */}
      <section className="py-32 px-6 lg:px-8 relative overflow-hidden">
        {/* Background accent */}
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-copper-500/5 rounded-full blur-3xl" />

        <div className="max-w-7xl mx-auto relative">
          {/* Section header */}
          <div className="max-w-2xl mb-20">
            <div className="flex items-center gap-4 mb-6">
              <div className="accent-line" />
              <span className="text-copper-400 text-sm font-medium tracking-widest uppercase">
                Capabilities
              </span>
            </div>
            <h2 className="font-display text-4xl md:text-5xl text-cream-100 leading-tight mb-6">
              Everything you need to
              <span className="block gradient-text">master your documents</span>
            </h2>
            <p className="text-ink-300 text-lg leading-relaxed">
              Purpose-built tools that understand legal context and deliver results that matter.
            </p>
          </div>

          {/* Feature cards - asymmetric grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Feature 1 - Large */}
            <div className="lg:col-span-2 glass-card rounded-sm p-8 lg:p-10 group hover:glow-copper transition-all duration-500">
              <div className="flex flex-col lg:flex-row lg:items-start gap-8">
                <div className="w-14 h-14 rounded-sm bg-copper-500/10 flex items-center justify-center flex-shrink-0 group-hover:bg-copper-500/20 transition-colors">
                  <svg className="w-7 h-7 text-copper-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-display text-2xl text-cream-100 mb-3">
                    Semantic Search
                  </h3>
                  <p className="text-ink-300 leading-relaxed mb-6">
                    Find documents by meaning, not just keywords. Our AI understands legal concepts,
                    case law references, and statutory language to surface exactly what you need.
                  </p>
                  <div className="flex flex-wrap gap-3">
                    <span className="text-xs text-ink-400 px-3 py-1 border border-ink-700 rounded-full">
                      Conceptual matching
                    </span>
                    <span className="text-xs text-ink-400 px-3 py-1 border border-ink-700 rounded-full">
                      Citation detection
                    </span>
                    <span className="text-xs text-ink-400 px-3 py-1 border border-ink-700 rounded-full">
                      Cross-reference
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Feature 2 */}
            <div className="glass-card rounded-sm p-8 group hover:glow-copper transition-all duration-500">
              <div className="w-14 h-14 rounded-sm bg-copper-500/10 flex items-center justify-center mb-6 group-hover:bg-copper-500/20 transition-colors">
                <svg className="w-7 h-7 text-copper-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <h3 className="font-display text-2xl text-cream-100 mb-3">
                AI Assistant
              </h3>
              <p className="text-ink-300 leading-relaxed">
                Ask questions in plain language. Get instant answers with precise citations and source references.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="glass-card rounded-sm p-8 group hover:glow-copper transition-all duration-500">
              <div className="w-14 h-14 rounded-sm bg-copper-500/10 flex items-center justify-center mb-6 group-hover:bg-copper-500/20 transition-colors">
                <svg className="w-7 h-7 text-copper-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="font-display text-2xl text-cream-100 mb-3">
                Time Tracking
              </h3>
              <p className="text-ink-300 leading-relaxed">
                Automatic billable hour capture from your research sessions with AI-generated descriptions.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="glass-card rounded-sm p-8 group hover:glow-copper transition-all duration-500">
              <div className="w-14 h-14 rounded-sm bg-copper-500/10 flex items-center justify-center mb-6 group-hover:bg-copper-500/20 transition-colors">
                <svg className="w-7 h-7 text-copper-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              </div>
              <h3 className="font-display text-2xl text-cream-100 mb-3">
                Matter Management
              </h3>
              <p className="text-ink-300 leading-relaxed">
                Organize documents by case with granular access controls and team collaboration.
              </p>
            </div>

            {/* Feature 5 */}
            <div className="glass-card rounded-sm p-8 group hover:glow-copper transition-all duration-500">
              <div className="w-14 h-14 rounded-sm bg-copper-500/10 flex items-center justify-center mb-6 group-hover:bg-copper-500/20 transition-colors">
                <svg className="w-7 h-7 text-copper-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <h3 className="font-display text-2xl text-cream-100 mb-3">
                Secure & Compliant
              </h3>
              <p className="text-ink-300 leading-relaxed">
                Bank-level encryption, complete data isolation, and full BC privacy law compliance.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Section Divider */}
      <div className="section-divider max-w-7xl mx-auto" />

      {/* Waitlist Section */}
      <section id="waitlist" className="py-32 px-6 lg:px-8 relative overflow-hidden">
        {/* Background elements */}
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-copper-500/5 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-0 w-px h-64 bg-gradient-to-b from-transparent via-copper-500/30 to-transparent" />

        <div className="max-w-4xl mx-auto relative">
          <div className="text-center mb-12">
            <div className="flex items-center justify-center gap-4 mb-6">
              <div className="accent-line" />
              <span className="text-copper-400 text-sm font-medium tracking-widest uppercase">
                Early Access
              </span>
              <div className="accent-line transform rotate-180" />
            </div>
            <h2 className="font-display text-4xl md:text-5xl text-cream-100 leading-tight mb-6">
              Be among the first to
              <span className="block gradient-text">transform your practice</span>
            </h2>
            <p className="text-ink-300 text-lg max-w-2xl mx-auto">
              Join BC law firms already revolutionizing their document workflows.
              Get notified about beta access and exclusive early-adopter benefits.
            </p>
          </div>

          {/* Form */}
          <div className="glass-card rounded-sm p-8 lg:p-12">
            <form className="space-y-6">
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <label htmlFor="name" className="block text-sm text-ink-300 mb-2">
                    Full Name
                  </label>
                  <input
                    type="text"
                    id="name"
                    placeholder="Jane Doe"
                    className="input-field"
                    required
                  />
                </div>
                <div>
                  <label htmlFor="email" className="block text-sm text-ink-300 mb-2">
                    Work Email
                  </label>
                  <input
                    type="email"
                    id="email"
                    placeholder="jane@lawfirm.ca"
                    className="input-field"
                    required
                  />
                </div>
              </div>
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <label htmlFor="firm" className="block text-sm text-ink-300 mb-2">
                    Law Firm Name
                  </label>
                  <input
                    type="text"
                    id="firm"
                    placeholder="Doe & Associates"
                    className="input-field"
                  />
                </div>
                <div>
                  <label htmlFor="phone" className="block text-sm text-ink-300 mb-2">
                    Phone <span className="text-ink-500">(Optional)</span>
                  </label>
                  <input
                    type="tel"
                    id="phone"
                    placeholder="+1 (604) 555-0123"
                    className="input-field"
                  />
                </div>
              </div>
              <div className="pt-4">
                <button type="submit" className="btn-primary w-full md:w-auto">
                  Request Early Access
                </button>
              </div>
              <p className="text-ink-500 text-sm">
                We respect your privacy. No spam, ever. Read our{' '}
                <Link href="/privacy" className="text-copper-400 hover:text-copper-300 transition-colors">
                  privacy policy
                </Link>
                .
              </p>
            </form>
          </div>
        </div>
      </section>

      {/* Footer */}
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
    </div>
  )
}
