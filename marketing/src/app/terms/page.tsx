import Link from 'next/link'

export default function TermsOfServicePage() {
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
        <h1 className="text-4xl font-bold text-gray-900 mb-4">Terms of Service</h1>
        <p className="text-gray-600 mb-8">Last Updated: November 9, 2025</p>

        <div className="prose prose-lg max-w-none">
          <p className="text-lg text-gray-700 mb-6">
            These Terms of Service ("Terms") govern your access to and use of BC Legal Tech's
            AI-powered legal document intelligence platform (the "Service"). By accessing or using
            the Service, you agree to be bound by these Terms.
          </p>

          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-8">
            <p className="text-sm text-yellow-800">
              <strong>IMPORTANT:</strong> This is a template Terms of Service. It must be reviewed
              and customized by a qualified lawyer before use. This template is provided for
              informational purposes only and does not constitute legal advice.
            </p>
          </div>

          {/* 1. Acceptance of Terms */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">1. Acceptance of Terms</h2>
            <p className="mb-4">
              By creating an account, accessing, or using the Service, you agree to:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Be bound by these Terms and our Privacy Policy</li>
              <li>Comply with all applicable laws and regulations</li>
              <li>Have the legal authority to enter into this agreement</li>
              <li>Use the Service only for lawful purposes</li>
            </ul>
            <p className="text-gray-700">
              If you do not agree to these Terms, you may not use the Service.
            </p>
          </section>

          {/* 2. Description of Service */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">2. Description of Service</h2>
            <p className="mb-4">
              BC Legal Tech provides an AI-powered platform for legal document management,
              semantic search, and AI-assisted document analysis. The Service includes:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Secure document storage and organization by legal matters</li>
              <li>Semantic search across your legal documents</li>
              <li>AI chat assistant for document analysis and Q&A</li>
              <li>Document metadata management and classification</li>
              <li>Multi-user access with role-based permissions</li>
            </ul>
            <p className="text-gray-700">
              We reserve the right to modify, suspend, or discontinue any aspect of the Service
              at any time with reasonable notice.
            </p>
          </section>

          {/* 3. User Accounts */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">3. User Accounts and Responsibilities</h2>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">3.1 Account Registration</h3>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>You must provide accurate, current, and complete information</li>
              <li>You must maintain and update your account information</li>
              <li>You are responsible for all activities under your account</li>
              <li>You must notify us immediately of any unauthorized access</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">3.2 Account Security</h3>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>You are responsible for maintaining the confidentiality of your password</li>
              <li>You must use a strong, unique password</li>
              <li>We recommend enabling multi-factor authentication</li>
              <li>You must not share your account credentials with others</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">3.3 Firm Accounts</h3>
            <p className="text-gray-700">
              If you register on behalf of a law firm, you represent that you have the authority
              to bind that firm to these Terms and that the firm agrees to be responsible for all
              users under its account.
            </p>
          </section>

          {/* 4. Acceptable Use */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">4. Acceptable Use Policy</h2>
            <p className="mb-4">You agree NOT to:</p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Violate any laws or regulations</li>
              <li>Infringe on intellectual property rights of others</li>
              <li>Upload malicious code, viruses, or harmful content</li>
              <li>Attempt to gain unauthorized access to the Service or other accounts</li>
              <li>Use the Service to harass, abuse, or harm others</li>
              <li>Reverse engineer, decompile, or disassemble any part of the Service</li>
              <li>Use automated systems (bots, scrapers) without authorization</li>
              <li>Resell or redistribute the Service without permission</li>
              <li>Use the Service for any illegal or fraudulent purpose</li>
              <li>Interfere with or disrupt the Service or servers</li>
            </ul>
            <p className="text-gray-700">
              Violation of this Acceptable Use Policy may result in immediate termination of your account.
            </p>
          </section>

          {/* 5. Intellectual Property */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">5. Intellectual Property Rights</h2>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">5.1 Your Content</h3>
            <p className="mb-4">
              You retain all ownership rights to documents and content you upload ("Your Content").
              By uploading Your Content, you grant us a limited license to:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Store, process, and display Your Content to provide the Service</li>
              <li>Generate embeddings and process Your Content with AI for search and chat features</li>
              <li>Back up Your Content for disaster recovery</li>
            </ul>
            <p className="text-gray-700 mb-4">
              This license ends when you delete Your Content or terminate your account, subject to
              reasonable backup retention periods.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">5.2 Our Platform</h3>
            <p className="text-gray-700">
              The Service, including its software, design, features, and branding, is owned by
              BC Legal Tech and protected by copyright, trademark, and other intellectual property laws.
              You may not copy, modify, or create derivative works without our written permission.
            </p>
          </section>

          {/* 6. Payment and Billing */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">6. Payment and Billing</h2>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">6.1 Subscription Plans</h3>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Subscription fees are billed in advance on a monthly or annual basis</li>
              <li>Prices are subject to change with 30 days notice</li>
              <li>All fees are in Canadian Dollars (CAD) unless otherwise stated</li>
              <li>Taxes (GST/HST) will be added where applicable</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">6.2 Refunds</h3>
            <p className="text-gray-700 mb-4">
              Subscription fees are generally non-refundable. We may offer pro-rated refunds at
              our discretion for annual subscriptions canceled within the first 30 days.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">6.3 Payment Failures</h3>
            <p className="text-gray-700">
              If payment fails, we will attempt to notify you and retry payment. Continued payment
              failure may result in account suspension or termination.
            </p>
          </section>

          {/* 7. Data and Confidentiality */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">7. Data and Confidentiality</h2>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">7.1 Your Confidential Information</h3>
            <p className="text-gray-700 mb-4">
              We understand that your legal documents contain confidential information. We will:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Maintain appropriate technical and organizational security measures</li>
              <li>Not access your documents except as necessary to provide the Service or comply with law</li>
              <li>Not use your documents to train AI models (third-party opt-out enforced)</li>
              <li>Maintain complete data isolation between law firms</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">7.2 Data Responsibility</h3>
            <p className="text-gray-700">
              You are responsible for ensuring you have the right to upload and process documents
              containing client information. You represent that your use of the Service complies
              with all applicable professional and ethical obligations, including client confidentiality rules.
            </p>
          </section>

          {/* 8. Warranties and Disclaimers */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">8. Warranties and Disclaimers</h2>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">8.1 Service Availability</h3>
            <p className="text-gray-700 mb-4">
              We strive for 99.5% uptime but do not guarantee uninterrupted access. The Service may
              be unavailable due to maintenance, updates, or technical issues.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">8.2 AI Accuracy</h3>
            <p className="text-gray-700 mb-4">
              AI-generated responses are provided for informational purposes only and should not be
              relied upon as legal advice. You are responsible for verifying all AI-generated information.
              AI may produce inaccurate or incomplete results.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">8.3 Disclaimer</h3>
            <p className="text-gray-700 font-semibold">
              THE SERVICE IS PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND,
              EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO WARRANTIES OF MERCHANTABILITY,
              FITNESS FOR A PARTICULAR PURPOSE, OR NON-INFRINGEMENT.
            </p>
          </section>

          {/* 9. Limitation of Liability */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">9. Limitation of Liability</h2>
            <p className="text-gray-700 mb-4">
              TO THE MAXIMUM EXTENT PERMITTED BY LAW:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>BC Legal Tech shall not be liable for any indirect, incidental, special, consequential,
                  or punitive damages</li>
              <li>Our total liability shall not exceed the fees you paid in the 12 months preceding the claim</li>
              <li>We are not liable for any loss of data, profits, revenue, or business opportunities</li>
              <li>We are not liable for delays or failures caused by circumstances beyond our reasonable control</li>
            </ul>
            <p className="text-gray-700">
              Some jurisdictions do not allow limitation of liability for certain damages, so these
              limitations may not apply to you.
            </p>
          </section>

          {/* 10. Indemnification */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">10. Indemnification</h2>
            <p className="text-gray-700">
              You agree to indemnify and hold harmless BC Legal Tech from any claims, damages, losses,
              or expenses (including legal fees) arising from:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Your use of the Service</li>
              <li>Your violation of these Terms</li>
              <li>Your violation of any law or regulation</li>
              <li>Your violation of any third-party rights</li>
              <li>Content you upload to the Service</li>
            </ul>
          </section>

          {/* 11. Termination */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">11. Termination</h2>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">11.1 Termination by You</h3>
            <p className="text-gray-700 mb-4">
              You may cancel your subscription at any time through your account settings. Cancellation
              takes effect at the end of the current billing period.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">11.2 Termination by Us</h3>
            <p className="text-gray-700 mb-4">
              We may suspend or terminate your account immediately if you:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Violate these Terms</li>
              <li>Fail to pay subscription fees</li>
              <li>Engage in fraudulent or illegal activity</li>
              <li>Pose a security risk to the Service</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">11.3 Effect of Termination</h3>
            <p className="text-gray-700">
              Upon termination, your access to the Service will cease. You may request a data export
              within 30 days of termination. After 90 days, we will delete your data in accordance
              with our Privacy Policy.
            </p>
          </section>

          {/* 12. Dispute Resolution */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">12. Dispute Resolution</h2>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">12.1 Governing Law</h3>
            <p className="text-gray-700 mb-4">
              These Terms are governed by the laws of British Columbia and Canada, without regard to
              conflict of law principles.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">12.2 Dispute Resolution Process</h3>
            <p className="text-gray-700 mb-4">
              In the event of any dispute, you agree to first contact us at{' '}
              <a href="mailto:legal@bclegaltech.ca" className="text-primary-600 hover:text-primary-700">
                legal@bclegaltech.ca
              </a>{' '}
              to attempt to resolve the matter informally.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">12.3 Jurisdiction</h3>
            <p className="text-gray-700">
              Any legal action must be brought in the courts of British Columbia, and you consent
              to the exclusive jurisdiction of such courts.
            </p>
          </section>

          {/* 13. General Provisions */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">13. General Provisions</h2>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">13.1 Changes to Terms</h3>
            <p className="text-gray-700 mb-4">
              We may modify these Terms at any time. We will notify you of material changes by email
              or through the Service at least 30 days before they take effect. Continued use after
              changes take effect constitutes acceptance.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">13.2 Entire Agreement</h3>
            <p className="text-gray-700 mb-4">
              These Terms, together with our Privacy Policy, constitute the entire agreement between
              you and BC Legal Tech regarding the Service.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">13.3 Severability</h3>
            <p className="text-gray-700 mb-4">
              If any provision is found to be unenforceable, the remaining provisions will remain in
              full force and effect.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">13.4 Waiver</h3>
            <p className="text-gray-700 mb-4">
              Our failure to enforce any right or provision does not constitute a waiver of that right.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">13.5 Assignment</h3>
            <p className="text-gray-700">
              You may not assign or transfer these Terms without our written consent. We may assign
              these Terms to any affiliate or successor.
            </p>
          </section>

          {/* 14. Contact Information */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">14. Contact Information</h2>
            <p className="text-gray-700 mb-4">
              If you have questions about these Terms, please contact us:
            </p>
            <p className="text-gray-700">
              Email: <a href="mailto:legal@bclegaltech.ca" className="text-primary-600 hover:text-primary-700">legal@bclegaltech.ca</a><br />
              Address: BC Legal Tech, British Columbia, Canada
            </p>
          </section>

          <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 mt-8">
            <p className="text-sm text-gray-700">
              By using BC Legal Tech, you acknowledge that you have read, understood, and agree to be
              bound by these Terms of Service.
            </p>
          </div>
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
