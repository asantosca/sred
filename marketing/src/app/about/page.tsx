import Link from 'next/link'
import Footer from '@/components/Footer'

const APP_URL = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-ink-950">
      {/* Hero */}
      <section className="relative pt-32 pb-20 px-6 lg:px-8 overflow-hidden">
        <div className="absolute inset-0">
          <div className="absolute top-0 right-1/3 w-96 h-96 bg-copper-500/5 rounded-full blur-3xl" />
        </div>

        <div className="relative max-w-7xl mx-auto text-center">
          <div className="flex items-center justify-center gap-4 mb-6">
            <div className="accent-line" />
            <span className="text-copper-400 text-sm font-medium tracking-widest uppercase">
              Our Story
            </span>
            <div className="accent-line transform rotate-180" />
          </div>
          <h1 className="font-display text-5xl md:text-6xl text-cream-100 leading-tight mb-6">
            About
            <span className="block gradient-text">BC Legal Tech</span>
          </h1>
          <p className="text-ink-300 text-xl max-w-3xl mx-auto leading-relaxed">
            Building the future of legal document intelligence for British Columbia law firms.
          </p>
        </div>
      </section>

      {/* Mission */}
      <section className="py-20 px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <h2 className="font-display text-3xl md:text-4xl text-cream-100 mb-8 text-center">
            Our Mission
          </h2>
          <p className="text-ink-300 text-xl text-center mb-12 leading-relaxed">
            To empower BC law firms with AI-powered document intelligence that saves time,
            improves accuracy, and enhances client service.
          </p>
          <div className="glass-card rounded-sm p-8 lg:p-10">
            <p className="text-ink-200 text-lg leading-relaxed">
              Legal professionals spend countless hours searching through documents, reviewing case files,
              and trying to find relevant information. We believe there&apos;s a better way. By combining
              cutting-edge AI technology with deep understanding of legal workflows, we&apos;re building
              tools that let lawyers focus on what they do best: serving their clients.
            </p>
          </div>
        </div>
      </section>

      {/* Why BC */}
      <section className="py-20 px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-display text-3xl md:text-4xl text-cream-100 mb-4">
              Why BC Law Firms?
            </h2>
            <p className="text-ink-400 text-lg">
              Built with local expertise for local professionals
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <div className="glass-card rounded-sm p-8 group hover:glow-copper transition-all duration-500">
              <div className="w-12 h-12 rounded-sm bg-copper-500/10 flex items-center justify-center mb-6 group-hover:bg-copper-500/20 transition-colors">
                <svg className="w-6 h-6 text-copper-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <h3 className="font-display text-xl text-cream-100 mb-3">Local Focus</h3>
              <p className="text-ink-400 leading-relaxed">
                Built specifically for British Columbia legal professionals, understanding local
                terminology, practices, and requirements.
              </p>
            </div>

            <div className="glass-card rounded-sm p-8 group hover:glow-copper transition-all duration-500">
              <div className="w-12 h-12 rounded-sm bg-copper-500/10 flex items-center justify-center mb-6 group-hover:bg-copper-500/20 transition-colors">
                <svg className="w-6 h-6 text-copper-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <h3 className="font-display text-xl text-cream-100 mb-3">Privacy First</h3>
              <p className="text-ink-400 leading-relaxed">
                Complete compliance with BC and Canadian privacy laws. Your client data stays
                secure and confidential.
              </p>
            </div>

            <div className="glass-card rounded-sm p-8 group hover:glow-copper transition-all duration-500">
              <div className="w-12 h-12 rounded-sm bg-copper-500/10 flex items-center justify-center mb-6 group-hover:bg-copper-500/20 transition-colors">
                <svg className="w-6 h-6 text-copper-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </div>
              <h3 className="font-display text-xl text-cream-100 mb-3">All Firm Sizes</h3>
              <p className="text-ink-400 leading-relaxed">
                Whether you&apos;re a solo practitioner or a multi-lawyer firm, our platform scales
                to meet your needs.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Values */}
      <section className="py-20 px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-display text-3xl md:text-4xl text-cream-100 mb-4">
              Our Values
            </h2>
          </div>

          <div className="space-y-8">
            <div className="glass-card rounded-sm p-8 flex items-start gap-6 group hover:glow-copper transition-all duration-500">
              <div className="w-14 h-14 rounded-sm bg-copper-500/10 flex items-center justify-center flex-shrink-0 group-hover:bg-copper-500/20 transition-colors">
                <svg className="w-7 h-7 text-copper-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <div>
                <h3 className="font-display text-2xl text-cream-100 mb-2">Security & Privacy</h3>
                <p className="text-ink-300 text-lg leading-relaxed">
                  Legal documents contain sensitive information. We treat your data with the highest
                  level of security and never compromise on privacy.
                </p>
              </div>
            </div>

            <div className="glass-card rounded-sm p-8 flex items-start gap-6 group hover:glow-copper transition-all duration-500">
              <div className="w-14 h-14 rounded-sm bg-copper-500/10 flex items-center justify-center flex-shrink-0 group-hover:bg-copper-500/20 transition-colors">
                <svg className="w-7 h-7 text-copper-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div>
                <h3 className="font-display text-2xl text-cream-100 mb-2">Speed & Accuracy</h3>
                <p className="text-ink-300 text-lg leading-relaxed">
                  Time is money in legal practice. Our AI delivers fast, accurate results so you can
                  focus on billable work and client service.
                </p>
              </div>
            </div>

            <div className="glass-card rounded-sm p-8 flex items-start gap-6 group hover:glow-copper transition-all duration-500">
              <div className="w-14 h-14 rounded-sm bg-copper-500/10 flex items-center justify-center flex-shrink-0 group-hover:bg-copper-500/20 transition-colors">
                <svg className="w-7 h-7 text-copper-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              </div>
              <div>
                <h3 className="font-display text-2xl text-cream-100 mb-2">Built for Lawyers</h3>
                <p className="text-ink-300 text-lg leading-relaxed">
                  We design our platform with legal workflows in mind. Every feature is built to match
                  how lawyers actually work.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6 lg:px-8 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-copper-600/10 via-copper-500/5 to-transparent" />
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-copper-500/10 rounded-full blur-3xl" />

        <div className="relative max-w-4xl mx-auto text-center">
          <h2 className="font-display text-4xl md:text-5xl text-cream-100 mb-6">
            Ready to Get Started?
          </h2>
          <p className="text-ink-300 text-xl mb-10">
            Join BC law firms who are transforming how they manage legal documents with AI.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a href={`${APP_URL}/register`} className="btn-primary text-center">
              Start Free Trial
            </a>
            <Link href="/contact" className="btn-secondary text-center">
              Contact Us
            </Link>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  )
}
