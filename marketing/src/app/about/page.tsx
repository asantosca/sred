import Link from 'next/link'

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Hero */}
      <section className="pt-16 pb-12 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-primary-50 to-white">
        <div className="max-w-7xl mx-auto text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            About BC Legal Tech
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            We're building the future of legal document intelligence for British Columbia law firms.
          </p>
        </div>
      </section>

      {/* Mission */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-4xl font-bold text-gray-900 mb-6 text-center">Our Mission</h2>
          <p className="text-xl text-gray-600 text-center mb-12">
            To empower BC law firms with AI-powered document intelligence that saves time,
            improves accuracy, and enhances client service.
          </p>
          <div className="bg-primary-50 p-8 rounded-lg">
            <p className="text-lg text-gray-700 leading-relaxed">
              Legal professionals spend countless hours searching through documents, reviewing case files,
              and trying to find relevant information. We believe there's a better way. By combining
              cutting-edge AI technology with deep understanding of legal workflows, we're building
              tools that let lawyers focus on what they do best: serving their clients.
            </p>
          </div>
        </div>
      </section>

      {/* Why BC */}
      <section className="py-20 bg-gray-50 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-4xl font-bold text-gray-900 mb-12 text-center">Why BC Law Firms?</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white p-8 rounded-lg">
              <h3 className="text-xl font-semibold mb-4 text-gray-900">Local Focus</h3>
              <p className="text-gray-600">
                Built specifically for British Columbia legal professionals, understanding local
                terminology, practices, and requirements.
              </p>
            </div>
            <div className="bg-white p-8 rounded-lg">
              <h3 className="text-xl font-semibold mb-4 text-gray-900">Privacy First</h3>
              <p className="text-gray-600">
                Complete compliance with BC and Canadian privacy laws. Your client data stays
                secure and confidential.
              </p>
            </div>
            <div className="bg-white p-8 rounded-lg">
              <h3 className="text-xl font-semibold mb-4 text-gray-900">Firm Sizes</h3>
              <p className="text-gray-600">
                Whether you're a solo practitioner or a multi-lawyer firm, our platform scales
                to meet your needs.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Values */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-4xl font-bold text-gray-900 mb-12 text-center">Our Values</h2>
          <div className="space-y-8 max-w-4xl mx-auto">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                </div>
              </div>
              <div className="ml-6">
                <h3 className="text-2xl font-semibold mb-2 text-gray-900">Security & Privacy</h3>
                <p className="text-gray-600 text-lg">
                  Legal documents contain sensitive information. We treat your data with the highest
                  level of security and never compromise on privacy.
                </p>
              </div>
            </div>

            <div className="flex items-start">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
              </div>
              <div className="ml-6">
                <h3 className="text-2xl font-semibold mb-2 text-gray-900">Speed & Accuracy</h3>
                <p className="text-gray-600 text-lg">
                  Time is money in legal practice. Our AI delivers fast, accurate results so you can
                  focus on billable work and client service.
                </p>
              </div>
            </div>

            <div className="flex items-start">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                </div>
              </div>
              <div className="ml-6">
                <h3 className="text-2xl font-semibold mb-2 text-gray-900">Built for Lawyers</h3>
                <p className="text-gray-600 text-lg">
                  We design our platform with legal workflows in mind. Every feature is built to match
                  how lawyers actually work.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-primary-700 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl font-bold text-white mb-6">
            Join Us on This Journey
          </h2>
          <p className="text-xl text-primary-100 mb-8">
            Be among the first BC law firms to experience the future of legal document management.
          </p>
          <a
            href="/#waitlist"
            className="inline-block bg-white text-primary-700 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-gray-100 transition-colors"
          >
            Join Our Waitlist
          </a>
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
