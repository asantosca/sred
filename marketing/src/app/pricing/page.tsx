import Link from 'next/link'
import Footer from '@/components/Footer'

const APP_URL = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-ink-950">
      {/* Hero */}
      <section className="relative pt-32 pb-20 px-6 lg:px-8 overflow-hidden">
        <div className="absolute inset-0">
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-copper-500/5 rounded-full blur-3xl" />
        </div>

        <div className="relative max-w-7xl mx-auto text-center">
          <div className="flex items-center justify-center gap-4 mb-6">
            <div className="accent-line" />
            <span className="text-copper-400 text-sm font-medium tracking-widest uppercase">
              Early Access
            </span>
            <div className="accent-line transform rotate-180" />
          </div>
          <h1 className="font-display text-5xl md:text-6xl text-cream-100 leading-tight mb-6">
            Simple, Transparent
            <span className="block gradient-text">Pricing</span>
          </h1>
          <p className="text-ink-300 text-xl max-w-3xl mx-auto leading-relaxed">
            Designed for BC law firms of all sizes. Start free, scale as you grow.
          </p>
        </div>
      </section>

      {/* Custom Pricing CTA */}
      <section className="py-16 px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="glass-card rounded-sm p-10 lg:p-14 text-center">
            <h2 className="font-display text-3xl md:text-4xl text-cream-100 mb-4">
              Custom Pricing for Your Firm
            </h2>
            <p className="text-ink-300 text-lg mb-8 max-w-2xl mx-auto leading-relaxed">
              We offer flexible pricing tailored to your firm&apos;s size and needs. Start your free trial today,
              or contact us to discuss enterprise pricing and volume discounts.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <a href={`${APP_URL}/register`} className="btn-primary text-center">
                Start Free Trial
              </a>
              <Link href="/contact" className="btn-secondary text-center">
                Contact Sales
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* What to Expect */}
      <section className="py-20 px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-display text-3xl md:text-4xl text-cream-100 mb-4">
              What to Expect
            </h2>
            <p className="text-ink-400 text-lg">
              Transparent pricing with no hidden fees
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <div className="glass-card rounded-sm p-8 group hover:glow-copper transition-all duration-500">
              <div className="w-12 h-12 rounded-sm bg-copper-500/10 flex items-center justify-center mb-6 group-hover:bg-copper-500/20 transition-colors">
                <svg className="w-6 h-6 text-copper-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
                </svg>
              </div>
              <h3 className="font-display text-xl text-cream-100 mb-3">Flexible Plans</h3>
              <p className="text-ink-400 leading-relaxed">
                Options for solo practitioners to multi-lawyer firms. Pay for what you need.
              </p>
            </div>

            <div className="glass-card rounded-sm p-8 group hover:glow-copper transition-all duration-500">
              <div className="w-12 h-12 rounded-sm bg-copper-500/10 flex items-center justify-center mb-6 group-hover:bg-copper-500/20 transition-colors">
                <svg className="w-6 h-6 text-copper-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="font-display text-xl text-cream-100 mb-3">Transparent Pricing</h3>
              <p className="text-ink-400 leading-relaxed">
                No hidden fees. Clear, straightforward pricing based on users and usage.
              </p>
            </div>

            <div className="glass-card rounded-sm p-8 group hover:glow-copper transition-all duration-500">
              <div className="w-12 h-12 rounded-sm bg-copper-500/10 flex items-center justify-center mb-6 group-hover:bg-copper-500/20 transition-colors">
                <svg className="w-6 h-6 text-copper-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7" />
                </svg>
              </div>
              <h3 className="font-display text-xl text-cream-100 mb-3">Early Access Benefits</h3>
              <p className="text-ink-400 leading-relaxed">
                Special rates for beta participants who join our waitlist now.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ or additional info could go here */}
      <section className="py-20 px-6 lg:px-8 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-copper-600/5 via-transparent to-copper-500/5" />

        <div className="relative max-w-4xl mx-auto text-center">
          <h2 className="font-display text-3xl text-cream-100 mb-6">
            Questions about pricing?
          </h2>
          <p className="text-ink-300 text-lg mb-8">
            Our team is happy to discuss your specific needs and find the right plan for your firm.
          </p>
          <Link href="/contact" className="btn-secondary inline-block">
            Get in Touch
          </Link>
        </div>
      </section>

      <Footer />
    </div>
  )
}
