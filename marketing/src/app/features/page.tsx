import Link from 'next/link'
import Image from 'next/image'
import Footer from '@/components/Footer'

const APP_URL = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'

export default function FeaturesPage() {
  return (
    <div className="min-h-screen bg-ink-950">
      {/* Hero */}
      <section className="relative pt-32 pb-20 px-6 lg:px-8 overflow-hidden">
        {/* Background */}
        <div className="absolute inset-0">
          <div className="absolute top-0 right-1/4 w-96 h-96 bg-copper-500/5 rounded-full blur-3xl" />
        </div>

        <div className="relative max-w-7xl mx-auto text-center">
          <div className="flex items-center justify-center gap-4 mb-6">
            <div className="accent-line" />
            <span className="text-copper-400 text-sm font-medium tracking-widest uppercase">
              Platform Capabilities
            </span>
            <div className="accent-line transform rotate-180" />
          </div>
          <h1 className="font-display text-5xl md:text-6xl text-cream-100 leading-tight mb-6">
            Powerful Features for
            <span className="block gradient-text">Legal Professionals</span>
          </h1>
          <p className="text-ink-300 text-xl max-w-3xl mx-auto leading-relaxed">
            Built specifically for BC law firms, combining AI intelligence with secure document management.
          </p>
        </div>
      </section>

      {/* Core Features */}
      <section className="py-20 px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          {/* Feature 1: Semantic Search */}
          <div className="grid lg:grid-cols-2 gap-16 items-center mb-32">
            <div>
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-copper-500/30 bg-copper-500/10 mb-6">
                <span className="text-copper-400 text-sm font-medium tracking-wide">Intelligent Search</span>
              </div>
              <h2 className="font-display text-4xl text-cream-100 mb-6 leading-tight">
                Semantic Search That Understands Legal Context
              </h2>
              <p className="text-ink-300 text-lg mb-8 leading-relaxed">
                Go beyond keyword matching. Our AI-powered semantic search understands legal concepts,
                terminology, and context to find exactly what you need.
              </p>
              <ul className="space-y-5">
                <li className="flex items-start gap-4">
                  <div className="w-6 h-6 rounded-full bg-copper-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <svg className="w-3 h-3 text-copper-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <strong className="text-cream-100 block mb-1">Natural Language Queries</strong>
                    <p className="text-ink-400">Ask questions in plain English, get relevant results</p>
                  </div>
                </li>
                <li className="flex items-start gap-4">
                  <div className="w-6 h-6 rounded-full bg-copper-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <svg className="w-3 h-3 text-copper-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <strong className="text-cream-100 block mb-1">Concept-Based Matching</strong>
                    <p className="text-ink-400">Find related documents even with different terminology</p>
                  </div>
                </li>
                <li className="flex items-start gap-4">
                  <div className="w-6 h-6 rounded-full bg-copper-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <svg className="w-3 h-3 text-copper-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <strong className="text-cream-100 block mb-1">Citation Tracking</strong>
                    <p className="text-ink-400">Every result includes document source and page numbers</p>
                  </div>
                </li>
              </ul>
            </div>
            <div className="glass-card rounded-sm p-8 lg:p-10">
              <Image
                src="/images/pages_semantic_search.png"
                alt="Semantic Search Interface"
                width={600}
                height={400}
                className="rounded-sm"
              />
            </div>
          </div>

          {/* Feature 2: AI Chat */}
          <div className="grid lg:grid-cols-2 gap-16 items-center mb-32">
            <div className="glass-card rounded-sm p-8 lg:p-10 order-2 lg:order-1">
              <Image
                src="/images/pages_chat_interface_illustration.png"
                alt="AI Chat Interface"
                width={600}
                height={400}
                className="rounded-sm"
              />
            </div>
            <div className="order-1 lg:order-2">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-copper-500/30 bg-copper-500/10 mb-6">
                <span className="text-copper-400 text-sm font-medium tracking-wide">AI Assistant</span>
              </div>
              <h2 className="font-display text-4xl text-cream-100 mb-6 leading-tight">
                AI Chat Assistant That Knows Your Documents
              </h2>
              <p className="text-ink-300 text-lg mb-8 leading-relaxed">
                Ask questions about your legal documents and get instant, cited answers. Like having a
                junior associate who has read every document in your matter.
              </p>
              <ul className="space-y-5">
                <li className="flex items-start gap-4">
                  <div className="w-6 h-6 rounded-full bg-copper-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <svg className="w-3 h-3 text-copper-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <strong className="text-cream-100 block mb-1">Conversational Interface</strong>
                    <p className="text-ink-400">Ask follow-up questions and refine your search</p>
                  </div>
                </li>
                <li className="flex items-start gap-4">
                  <div className="w-6 h-6 rounded-full bg-copper-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <svg className="w-3 h-3 text-copper-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <strong className="text-cream-100 block mb-1">Always Cited Sources</strong>
                    <p className="text-ink-400">Every answer includes clickable source documents</p>
                  </div>
                </li>
                <li className="flex items-start gap-4">
                  <div className="w-6 h-6 rounded-full bg-copper-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <svg className="w-3 h-3 text-copper-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <strong className="text-cream-100 block mb-1">Matter-Scoped Responses</strong>
                    <p className="text-ink-400">Search within specific cases or across all documents</p>
                  </div>
                </li>
              </ul>
            </div>
          </div>

          {/* Feature 3: Document Management */}
          <div className="grid lg:grid-cols-2 gap-16 items-center mb-32">
            <div>
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-copper-500/30 bg-copper-500/10 mb-6">
                <span className="text-copper-400 text-sm font-medium tracking-wide">Document Management</span>
              </div>
              <h2 className="font-display text-4xl text-cream-100 mb-6 leading-tight">
                Organized, Secure Document Management
              </h2>
              <p className="text-ink-300 text-lg mb-8 leading-relaxed">
                Upload, organize, and manage legal documents by matter. Built for the way lawyers actually work.
              </p>
              <ul className="space-y-5">
                <li className="flex items-start gap-4">
                  <div className="w-6 h-6 rounded-full bg-copper-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <svg className="w-3 h-3 text-copper-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <strong className="text-cream-100 block mb-1">Matter-Based Organization</strong>
                    <p className="text-ink-400">All documents organized by legal matters/cases</p>
                  </div>
                </li>
                <li className="flex items-start gap-4">
                  <div className="w-6 h-6 rounded-full bg-copper-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <svg className="w-3 h-3 text-copper-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <strong className="text-cream-100 block mb-1">Auto-Classification</strong>
                    <p className="text-ink-400">Automatic detection of document types and metadata</p>
                  </div>
                </li>
                <li className="flex items-start gap-4">
                  <div className="w-6 h-6 rounded-full bg-copper-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <svg className="w-3 h-3 text-copper-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <strong className="text-cream-100 block mb-1">Multiple Formats Supported</strong>
                    <p className="text-ink-400">PDF, DOCX, TXT, MSG, EML files up to 50MB</p>
                  </div>
                </li>
              </ul>
            </div>
            <div className="glass-card rounded-sm p-8 lg:p-10">
              <Image
                src="/images/pages_document_library_interface.png"
                alt="Document Library Interface"
                width={600}
                height={400}
                className="rounded-sm"
              />
            </div>
          </div>

          {/* Feature 4: Security */}
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div className="glass-card rounded-sm p-8 lg:p-10 order-2 lg:order-1">
              <Image
                src="/images/pages_document_library_interface.png"
                alt="Security Features"
                width={600}
                height={400}
                className="rounded-sm"
              />
            </div>
            <div className="order-1 lg:order-2">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-copper-500/30 bg-copper-500/10 mb-6">
                <span className="text-copper-400 text-sm font-medium tracking-wide">Security & Compliance</span>
              </div>
              <h2 className="font-display text-4xl text-cream-100 mb-6 leading-tight">
                Bank-Level Security for Confidential Documents
              </h2>
              <p className="text-ink-300 text-lg mb-8 leading-relaxed">
                Built from the ground up with legal compliance and data security as top priorities.
              </p>
              <ul className="space-y-5">
                <li className="flex items-start gap-4">
                  <div className="w-6 h-6 rounded-full bg-copper-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <svg className="w-3 h-3 text-copper-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <strong className="text-cream-100 block mb-1">Complete Data Isolation</strong>
                    <p className="text-ink-400">Your firm&apos;s data is completely isolated from other firms</p>
                  </div>
                </li>
                <li className="flex items-start gap-4">
                  <div className="w-6 h-6 rounded-full bg-copper-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <svg className="w-3 h-3 text-copper-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <strong className="text-cream-100 block mb-1">BC Privacy Law Compliant</strong>
                    <p className="text-ink-400">Full compliance with British Columbia privacy regulations</p>
                  </div>
                </li>
                <li className="flex items-start gap-4">
                  <div className="w-6 h-6 rounded-full bg-copper-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <svg className="w-3 h-3 text-copper-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <strong className="text-cream-100 block mb-1">Encrypted Storage</strong>
                    <p className="text-ink-400">All documents encrypted at rest and in transit</p>
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6 lg:px-8 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-copper-600/10 via-copper-500/5 to-transparent" />
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-copper-500/10 rounded-full blur-3xl" />

        <div className="relative max-w-4xl mx-auto text-center">
          <h2 className="font-display text-4xl md:text-5xl text-cream-100 mb-6">
            Ready to Transform Your
            <span className="block gradient-text">Legal Document Management?</span>
          </h2>
          <p className="text-ink-300 text-xl mb-10">
            Start your free trial today. No credit card required.
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
      </section>

      <Footer />
    </div>
  )
}
