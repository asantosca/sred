import Link from 'next/link'
import Image from 'next/image'

const APP_URL = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'

export default function FeaturesPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Hero */}
      <section className="pt-16 pb-12 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-primary-50 to-white">
        <div className="max-w-7xl mx-auto text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Powerful Features for Legal Professionals
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Built specifically for BC law firms, combining AI intelligence with secure document management.
          </p>
        </div>
      </section>

      {/* Core Features */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          {/* Feature 1: Semantic Search */}
          <div className="grid md:grid-cols-2 gap-12 items-center mb-24">
            <div>
              <div className="inline-block bg-primary-100 text-primary-700 px-3 py-1 rounded-full text-sm font-semibold mb-4">
                INTELLIGENT SEARCH
              </div>
              <h2 className="text-4xl font-bold text-gray-900 mb-6">
                Semantic Search That Understands Legal Context
              </h2>
              <p className="text-lg text-gray-600 mb-6">
                Go beyond keyword matching. Our AI-powered semantic search understands legal concepts,
                terminology, and context to find exactly what you need.
              </p>
              <ul className="space-y-4">
                <li className="flex items-start">
                  <svg className="w-6 h-6 text-primary-600 mr-3 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <div>
                    <strong className="text-gray-900">Natural Language Queries</strong>
                    <p className="text-gray-600">Ask questions in plain English, get relevant results</p>
                  </div>
                </li>
                <li className="flex items-start">
                  <svg className="w-6 h-6 text-primary-600 mr-3 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <div>
                    <strong className="text-gray-900">Concept-Based Matching</strong>
                    <p className="text-gray-600">Find related documents even with different terminology</p>
                  </div>
                </li>
                <li className="flex items-start">
                  <svg className="w-6 h-6 text-primary-600 mr-3 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <div>
                    <strong className="text-gray-900">Citation Tracking</strong>
                    <p className="text-gray-600">Every result includes document source and page numbers</p>
                  </div>
                </li>
              </ul>
            </div>
              <div className="bg-gray-100 rounded-lg p-8 overflow-hidden">
                <Image
                  src="/images/pages_semantic_search.png"
                  alt="Document Library Interface"
                  width={600}
                  height={400}
                  className="rounded-lg"
                />
              </div>    
          </div>

          {/* Feature 2: AI Chat */}
          <div className="grid md:grid-cols-2 gap-12 items-center mb-24">
              <div className="bg-gray-100 rounded-lg p-8 overflow-hidden">
                <Image
                  src="/images/pages_chat_interface_illustration.png"
                  alt="Document Library Interface"
                  width={600}
                  height={400}
                  className="rounded-lg"
                />
            </div>
            <div className="order-1 md:order-2">
              <div className="inline-block bg-primary-100 text-primary-700 px-3 py-1 rounded-full text-sm font-semibold mb-4">
                AI ASSISTANT
              </div>
              <h2 className="text-4xl font-bold text-gray-900 mb-6">
                AI Chat Assistant That Knows Your Documents
              </h2>
              <p className="text-lg text-gray-600 mb-6">
                Ask questions about your legal documents and get instant, cited answers. Like having a
                junior associate who has read every document in your matter.
              </p>
              <ul className="space-y-4">
                <li className="flex items-start">
                  <svg className="w-6 h-6 text-primary-600 mr-3 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <div>
                    <strong className="text-gray-900">Conversational Interface</strong>
                    <p className="text-gray-600">Ask follow-up questions and refine your search</p>
                  </div>
                </li>
                <li className="flex items-start">
                  <svg className="w-6 h-6 text-primary-600 mr-3 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <div>
                    <strong className="text-gray-900">Always Cited Sources</strong>
                    <p className="text-gray-600">Every answer includes clickable source documents</p>
                  </div>
                </li>
                <li className="flex items-start">
                  <svg className="w-6 h-6 text-primary-600 mr-3 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <div>
                    <strong className="text-gray-900">Matter-Scoped Responses</strong>
                    <p className="text-gray-600">Search within specific cases or across all documents</p>
                  </div>
                </li>
              </ul>
            </div>
          </div>

          {/* Feature 3: Document Management */}
          <div className="grid md:grid-cols-2 gap-12 items-center mb-24">
            <div>
              <div className="inline-block bg-primary-100 text-primary-700 px-3 py-1 rounded-full text-sm font-semibold mb-4">
                DOCUMENT MANAGEMENT
              </div>
              <h2 className="text-4xl font-bold text-gray-900 mb-6">
                Organized, Secure Document Management
              </h2>
              <p className="text-lg text-gray-600 mb-6">
                Upload, organize, and manage legal documents by matter. Built for the way lawyers actually work.
              </p>
              <ul className="space-y-4">
                <li className="flex items-start">
                  <svg className="w-6 h-6 text-primary-600 mr-3 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <div>
                    <strong className="text-gray-900">Matter-Based Organization</strong>
                    <p className="text-gray-600">All documents organized by legal matters/cases</p>
                  </div>
                </li>
                <li className="flex items-start">
                  <svg className="w-6 h-6 text-primary-600 mr-3 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <div>
                    <strong className="text-gray-900">Auto-Classification</strong>
                    <p className="text-gray-600">Automatic detection of document types and metadata</p>
                  </div>
                </li>
                <li className="flex items-start">
                  <svg className="w-6 h-6 text-primary-600 mr-3 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <div>
                    <strong className="text-gray-900">Multiple Formats Supported</strong>
                    <p className="text-gray-600">PDF, DOCX, TXT, MSG, EML files up to 50MB</p>
                  </div>
                </li>
              </ul>
            </div>
            <div className="bg-gray-100 rounded-lg p-8 overflow-hidden">
                <Image
                  src="/images/pages_document_library_interface.png"
                  alt="Document Library Interface"
                  width={600}
                  height={400}
                  className="rounded-lg"
                />
            </div>
          </div>

          {/* Feature 4: Security */}
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div className="bg-gray-100 rounded-lg p-8 overflow-hidden">
                <Image
                  src="/images/pages_document_library_interface.png"
                  alt="Document Library Interface"
                  width={600}
                  height={400}
                  className="rounded-lg"
                />
            </div>
            <div className="order-1 md:order-2">
              <div className="inline-block bg-primary-100 text-primary-700 px-3 py-1 rounded-full text-sm font-semibold mb-4">
                SECURITY & COMPLIANCE
              </div>
              <h2 className="text-4xl font-bold text-gray-900 mb-6">
                Bank-Level Security for Confidential Documents
              </h2>
              <p className="text-lg text-gray-600 mb-6">
                Built from the ground up with legal compliance and data security as top priorities.
              </p>
              <ul className="space-y-4">
                <li className="flex items-start">
                  <svg className="w-6 h-6 text-primary-600 mr-3 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <div>
                    <strong className="text-gray-900">Complete Data Isolation</strong>
                    <p className="text-gray-600">Your firm's data is completely isolated from other firms</p>
                  </div>
                </li>
                <li className="flex items-start">
                  <svg className="w-6 h-6 text-primary-600 mr-3 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <div>
                    <strong className="text-gray-900">BC Privacy Law Compliant</strong>
                    <p className="text-gray-600">Full compliance with British Columbia privacy regulations</p>
                  </div>
                </li>
                <li className="flex items-start">
                  <svg className="w-6 h-6 text-primary-600 mr-3 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <div>
                    <strong className="text-gray-900">Encrypted Storage</strong>
                    <p className="text-gray-600">All documents encrypted at rest and in transit</p>
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-primary-700 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl font-bold text-white mb-6">
            Ready to Transform Your Legal Document Management?
          </h2>
          <p className="text-xl text-primary-100 mb-8">
            Start your free trial today. No credit card required.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href={`${APP_URL}/register`}
              className="inline-block bg-white text-primary-700 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-gray-100 transition-colors"
            >
              Start Free Trial
            </a>
            <Link
              href="/contact"
              className="inline-block bg-primary-600 text-white border-2 border-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-primary-800 transition-colors"
            >
              Contact Sales
            </Link>
          </div>
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
