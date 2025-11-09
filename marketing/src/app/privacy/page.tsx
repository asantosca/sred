import Link from 'next/link'

export default function PrivacyPolicyPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link href="/" className="flex items-center">
              <span className="text-2xl font-bold text-primary-700">BC Legal Tech</span>
            </Link>
            <div className="hidden md:flex items-center space-x-8">
              <Link href="/features" className="text-gray-700 hover:text-primary-700">
                Features
              </Link>
              <Link href="/about" className="text-gray-700 hover:text-primary-700">
                About
              </Link>
              <Link href="/contact" className="text-gray-700 hover:text-primary-700">
                Contact
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">Privacy Policy</h1>
        <p className="text-gray-600 mb-8">Last Updated: November 9, 2025</p>

        <div className="prose prose-lg max-w-none">
          <p className="text-lg text-gray-700 mb-6">
            BC Legal Tech ("we", "us", or "our") is committed to protecting the privacy and confidentiality
            of your personal and professional information. This Privacy Policy explains how we collect, use,
            disclose, and safeguard your information when you use our AI-powered legal document intelligence
            platform (the "Service").
          </p>

          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-8">
            <p className="text-sm text-yellow-800">
              <strong>IMPORTANT:</strong> This is a template privacy policy. It must be reviewed and
              customized by a qualified lawyer before use. This template is provided for informational
              purposes only and does not constitute legal advice.
            </p>
          </div>

          {/* 1. Information We Collect */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">1. Information We Collect</h2>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">1.1 Information You Provide</h3>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li><strong>Account Information:</strong> Email address, name, law firm name, role, phone number</li>
              <li><strong>Documents:</strong> Legal documents you upload, including their content and metadata</li>
              <li><strong>Chat Conversations:</strong> Questions you ask and conversations with our AI assistant</li>
              <li><strong>Matter Information:</strong> Case details, client names, matter numbers, and related data</li>
              <li><strong>Payment Information:</strong> Billing details (processed securely through third-party payment processors)</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">1.2 Information We Collect Automatically</h3>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li><strong>Usage Data:</strong> Pages visited, features used, search queries, time spent on platform</li>
              <li><strong>Device Information:</strong> IP address, browser type, operating system, device identifiers</li>
              <li><strong>Cookies:</strong> Session cookies, preference cookies, and analytics cookies (see Cookie Policy)</li>
              <li><strong>Log Data:</strong> Access times, error logs, performance metrics</li>
            </ul>
          </section>

          {/* 2. How We Use Your Information */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">2. How We Use Your Information</h2>
            <p className="mb-4">We use the information we collect to:</p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Provide, maintain, and improve the Service</li>
              <li>Process and store your legal documents securely</li>
              <li>Generate AI-powered responses to your questions</li>
              <li>Provide semantic search across your documents</li>
              <li>Send service-related communications (password resets, system notifications)</li>
              <li>Process billing and payments</li>
              <li>Analyze usage patterns to improve our platform</li>
              <li>Detect and prevent fraud, abuse, or security incidents</li>
              <li>Comply with legal obligations</li>
            </ul>
          </section>

          {/* 3. AI and Third-Party Services */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">3. AI and Third-Party Services</h2>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">3.1 AI Processing</h3>
            <p className="mb-4">
              We use third-party AI services (including OpenAI and Anthropic) to provide semantic search
              and AI chat features. When you use these features:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Document content is processed to generate embeddings for semantic search</li>
              <li>Your questions and relevant document excerpts are sent to AI services to generate responses</li>
              <li>We do NOT use your data to train third-party AI models (opt-out enforced)</li>
              <li>AI providers process data according to their privacy policies and data processing agreements</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">3.2 Other Third-Party Services</h3>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li><strong>AWS:</strong> Cloud infrastructure and storage (data stored in Canadian regions where possible)</li>
              <li><strong>Sentry:</strong> Error tracking and monitoring (configured for privacy)</li>
              <li><strong>Payment Processors:</strong> Stripe or similar (they have separate privacy policies)</li>
            </ul>
          </section>

          {/* 4. Data Sharing and Disclosure */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">4. Data Sharing and Disclosure</h2>
            <p className="mb-4">We do NOT sell your personal information or legal documents to third parties.</p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">We may share your information with:</h3>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li><strong>Your Law Firm:</strong> Other authorized users within your firm (based on access controls)</li>
              <li><strong>Service Providers:</strong> AWS, AI providers, payment processors (under strict data processing agreements)</li>
              <li><strong>Legal Requirements:</strong> If required by law, court order, or government request</li>
              <li><strong>Business Transfers:</strong> In connection with a merger, acquisition, or sale of assets (with notice)</li>
              <li><strong>With Your Consent:</strong> Any other sharing with your explicit permission</li>
            </ul>
          </section>

          {/* 5. Data Security */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">5. Data Security</h2>
            <p className="mb-4">We implement industry-standard security measures including:</p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li><strong>Encryption:</strong> TLS/SSL encryption in transit, AES-256 encryption at rest</li>
              <li><strong>Access Controls:</strong> Multi-factor authentication, role-based access, principle of least privilege</li>
              <li><strong>Data Isolation:</strong> Complete separation of data between law firms (multi-tenancy with row-level security)</li>
              <li><strong>Monitoring:</strong> 24/7 security monitoring, intrusion detection, regular security audits</li>
              <li><strong>Backups:</strong> Regular automated backups with encryption</li>
            </ul>
            <p className="text-gray-700">
              However, no system is 100% secure. We cannot guarantee absolute security of your data.
            </p>
          </section>

          {/* 6. Data Retention */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">6. Data Retention</h2>
            <p className="mb-4">We retain your information for as long as:</p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Your account is active and the Service is in use</li>
              <li>Needed to comply with legal obligations (e.g., tax, legal, accounting requirements)</li>
              <li>Necessary to resolve disputes or enforce agreements</li>
            </ul>
            <p className="text-gray-700">
              Upon account termination, we will delete or anonymize your personal data within 90 days,
              except where retention is required by law.
            </p>
          </section>

          {/* 7. Your Rights */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">7. Your Rights</h2>
            <p className="mb-4">Under BC and Canadian privacy laws, you have the right to:</p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li><strong>Access:</strong> Request a copy of your personal information</li>
              <li><strong>Correction:</strong> Request correction of inaccurate data</li>
              <li><strong>Deletion:</strong> Request deletion of your data (subject to legal obligations)</li>
              <li><strong>Export:</strong> Receive your data in a portable format</li>
              <li><strong>Opt-Out:</strong> Opt out of marketing communications</li>
              <li><strong>Withdraw Consent:</strong> Where processing is based on consent</li>
              <li><strong>Lodge Complaint:</strong> File a complaint with the BC Privacy Commissioner</li>
            </ul>
            <p className="text-gray-700">
              To exercise these rights, contact us at{' '}
              <a href="mailto:privacy@bclegaltech.ca" className="text-primary-600 hover:text-primary-700">
                privacy@bclegaltech.ca
              </a>
            </p>
          </section>

          {/* 8. Children's Privacy */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">8. Children's Privacy</h2>
            <p className="text-gray-700">
              Our Service is not intended for individuals under 18. We do not knowingly collect
              information from children. If we learn we have collected information from a child,
              we will delete it immediately.
            </p>
          </section>

          {/* 9. International Data Transfers */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">9. International Data Transfers</h2>
            <p className="text-gray-700">
              While we strive to store data in Canadian data centers, some service providers (e.g., AI services)
              may process data outside Canada. We ensure appropriate safeguards are in place through data
              processing agreements and standard contractual clauses.
            </p>
          </section>

          {/* 10. Changes to This Policy */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">10. Changes to This Policy</h2>
            <p className="text-gray-700">
              We may update this Privacy Policy from time to time. We will notify you of material changes
              by email or through the Service. Continued use after changes constitutes acceptance of the
              updated policy.
            </p>
          </section>

          {/* 11. Contact Us */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">11. Contact Us</h2>
            <p className="text-gray-700 mb-4">
              If you have questions about this Privacy Policy or our privacy practices, contact us:
            </p>
            <p className="text-gray-700">
              Email: <a href="mailto:privacy@bclegaltech.ca" className="text-primary-600 hover:text-primary-700">privacy@bclegaltech.ca</a><br />
              Address: BC Legal Tech, British Columbia, Canada
            </p>
          </section>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12 px-4 sm:px-6 lg:px-8 mt-12">
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
