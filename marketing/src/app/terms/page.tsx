import Link from 'next/link'
import Footer from '@/components/Footer'

export default function TermsOfServicePage() {
  return (
    <div className="min-h-screen bg-ink-950">
      {/* Hero */}
      <section className="relative pt-32 pb-12 px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="font-display text-4xl md:text-5xl text-cream-100 mb-4">Terms of Service</h1>
          <p className="text-ink-400">Last Updated: November 9, 2025</p>
        </div>
      </section>

      {/* Content */}
      <section className="px-6 lg:px-8 pb-20">
        <div className="max-w-4xl mx-auto">
          <div className="prose-custom">
            <p className="text-lg text-ink-200 mb-8 leading-relaxed">
              These Terms of Service (&quot;Terms&quot;) govern your access to and use of BC Legal Tech&apos;s
              AI-powered legal document intelligence platform (the &quot;Service&quot;). By accessing or using
              the Service, you agree to be bound by these Terms.
            </p>

            <div className="glass-card rounded-sm p-5 mb-10 border-l-2 border-copper-500">
              <p className="text-sm text-ink-300">
                <strong className="text-copper-400">IMPORTANT:</strong> This is a template Terms of Service. It must be reviewed
                and customized by a qualified lawyer before use. This template is provided for
                informational purposes only and does not constitute legal advice.
              </p>
            </div>

            {/* Section 1 */}
            <section className="mb-10">
              <h2 className="font-display text-2xl text-cream-100 mb-4">1. Acceptance of Terms</h2>
              <p className="text-ink-300 mb-4">
                By creating an account, accessing, or using the Service, you agree to:
              </p>
              <ul className="list-disc pl-6 mb-4 space-y-2 text-ink-300">
                <li>Be bound by these Terms and our Privacy Policy</li>
                <li>Comply with all applicable laws and regulations</li>
                <li>Have the legal authority to enter into this agreement</li>
                <li>Use the Service only for lawful purposes</li>
              </ul>
              <p className="text-ink-400">
                If you do not agree to these Terms, you may not use the Service.
              </p>
            </section>

            {/* Section 2 */}
            <section className="mb-10">
              <h2 className="font-display text-2xl text-cream-100 mb-4">2. Description of Service</h2>
              <p className="text-ink-300 mb-4">
                BC Legal Tech provides an AI-powered platform for legal document management,
                semantic search, and AI-assisted document analysis. The Service includes:
              </p>
              <ul className="list-disc pl-6 mb-4 space-y-2 text-ink-300">
                <li>Secure document storage and organization by legal matters</li>
                <li>Semantic search across your legal documents</li>
                <li>AI chat assistant for document analysis and Q&amp;A</li>
                <li>Document metadata management and classification</li>
                <li>Multi-user access with role-based permissions</li>
              </ul>
              <p className="text-ink-400">
                We reserve the right to modify, suspend, or discontinue any aspect of the Service
                at any time with reasonable notice.
              </p>
            </section>

            {/* Section 3 */}
            <section className="mb-10">
              <h2 className="font-display text-2xl text-cream-100 mb-4">3. User Accounts and Responsibilities</h2>

              <h3 className="text-xl text-cream-100 mb-3">3.1 Account Registration</h3>
              <ul className="list-disc pl-6 mb-4 space-y-2 text-ink-300">
                <li>You must provide accurate, current, and complete information</li>
                <li>You must maintain and update your account information</li>
                <li>You are responsible for all activities under your account</li>
                <li>You must notify us immediately of any unauthorized access</li>
              </ul>

              <h3 className="text-xl text-cream-100 mb-3">3.2 Account Security</h3>
              <ul className="list-disc pl-6 mb-4 space-y-2 text-ink-300">
                <li>You are responsible for maintaining the confidentiality of your password</li>
                <li>You must use a strong, unique password</li>
                <li>We recommend enabling multi-factor authentication</li>
                <li>You must not share your account credentials with others</li>
              </ul>

              <h3 className="text-xl text-cream-100 mb-3">3.3 Firm Accounts</h3>
              <p className="text-ink-400">
                If you register on behalf of a law firm, you represent that you have the authority
                to bind that firm to these Terms and that the firm agrees to be responsible for all
                users under its account.
              </p>
            </section>

            {/* Section 4 */}
            <section className="mb-10">
              <h2 className="font-display text-2xl text-cream-100 mb-4">4. Acceptable Use Policy</h2>
              <p className="text-ink-300 mb-4">You agree NOT to:</p>
              <ul className="list-disc pl-6 mb-4 space-y-2 text-ink-300">
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
              <p className="text-ink-400">
                Violation of this Acceptable Use Policy may result in immediate termination of your account.
              </p>
            </section>

            {/* Section 5 */}
            <section className="mb-10">
              <h2 className="font-display text-2xl text-cream-100 mb-4">5. Intellectual Property Rights</h2>

              <h3 className="text-xl text-cream-100 mb-3">5.1 Your Content</h3>
              <p className="text-ink-300 mb-4">
                You retain all ownership rights to documents and content you upload (&quot;Your Content&quot;).
                By uploading Your Content, you grant us a limited license to:
              </p>
              <ul className="list-disc pl-6 mb-4 space-y-2 text-ink-300">
                <li>Store, process, and display Your Content to provide the Service</li>
                <li>Generate embeddings and process Your Content with AI for search and chat features</li>
                <li>Back up Your Content for disaster recovery</li>
              </ul>
              <p className="text-ink-400 mb-4">
                This license ends when you delete Your Content or terminate your account, subject to
                reasonable backup retention periods.
              </p>

              <h3 className="text-xl text-cream-100 mb-3">5.2 Our Platform</h3>
              <p className="text-ink-400">
                The Service, including its software, design, features, and branding, is owned by
                BC Legal Tech and protected by copyright, trademark, and other intellectual property laws.
                You may not copy, modify, or create derivative works without our written permission.
              </p>
            </section>

            {/* Sections 6-14 abbreviated for length */}
            <section className="mb-10">
              <h2 className="font-display text-2xl text-cream-100 mb-4">6. Payment and Billing</h2>
              <ul className="list-disc pl-6 mb-4 space-y-2 text-ink-300">
                <li>Subscription fees are billed in advance on a monthly or annual basis</li>
                <li>Prices are subject to change with 30 days notice</li>
                <li>All fees are in Canadian Dollars (CAD) unless otherwise stated</li>
                <li>Taxes (GST/HST) will be added where applicable</li>
              </ul>
            </section>

            <section className="mb-10">
              <h2 className="font-display text-2xl text-cream-100 mb-4">7. Data and Confidentiality</h2>
              <p className="text-ink-300 mb-4">
                We understand that your legal documents contain confidential information. We will:
              </p>
              <ul className="list-disc pl-6 mb-4 space-y-2 text-ink-300">
                <li>Maintain appropriate technical and organizational security measures</li>
                <li>Not access your documents except as necessary to provide the Service or comply with law</li>
                <li>Not use your documents to train AI models (third-party opt-out enforced)</li>
                <li>Maintain complete data isolation between law firms</li>
              </ul>
            </section>

            <section className="mb-10">
              <h2 className="font-display text-2xl text-cream-100 mb-4">8. Warranties and Disclaimers</h2>
              <p className="text-ink-300 mb-4">
                AI-generated responses are provided for informational purposes only and should not be
                relied upon as legal advice. You are responsible for verifying all AI-generated information.
              </p>
              <p className="text-ink-200 font-semibold text-sm">
                THE SERVICE IS PROVIDED &quot;AS IS&quot; AND &quot;AS AVAILABLE&quot; WITHOUT WARRANTIES OF ANY KIND,
                EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO WARRANTIES OF MERCHANTABILITY,
                FITNESS FOR A PARTICULAR PURPOSE, OR NON-INFRINGEMENT.
              </p>
            </section>

            <section className="mb-10">
              <h2 className="font-display text-2xl text-cream-100 mb-4">9. Limitation of Liability</h2>
              <p className="text-ink-200 mb-4">TO THE MAXIMUM EXTENT PERMITTED BY LAW:</p>
              <ul className="list-disc pl-6 mb-4 space-y-2 text-ink-300">
                <li>BC Legal Tech shall not be liable for any indirect, incidental, special, consequential, or punitive damages</li>
                <li>Our total liability shall not exceed the fees you paid in the 12 months preceding the claim</li>
                <li>We are not liable for any loss of data, profits, revenue, or business opportunities</li>
              </ul>
            </section>

            <section className="mb-10">
              <h2 className="font-display text-2xl text-cream-100 mb-4">10. Termination</h2>
              <p className="text-ink-300 mb-4">
                You may cancel your subscription at any time through your account settings. Upon termination,
                your access to the Service will cease. You may request a data export within 30 days of termination.
              </p>
            </section>

            <section className="mb-10">
              <h2 className="font-display text-2xl text-cream-100 mb-4">11. Dispute Resolution</h2>
              <p className="text-ink-300 mb-4">
                These Terms are governed by the laws of British Columbia and Canada. In the event of any dispute,
                contact us at{' '}
                <a href="mailto:legal@bclegaltech.ca" className="text-copper-400 hover:text-copper-300 transition-colors">
                  legal@bclegaltech.ca
                </a>{' '}
                to attempt to resolve the matter informally. Any legal action must be brought in the courts of British Columbia.
              </p>
            </section>

            <section className="mb-10">
              <h2 className="font-display text-2xl text-cream-100 mb-4">12. Contact Information</h2>
              <p className="text-ink-300 mb-4">
                If you have questions about these Terms, please contact us:
              </p>
              <p className="text-ink-300">
                Email: <a href="mailto:legal@bclegaltech.ca" className="text-copper-400 hover:text-copper-300 transition-colors">legal@bclegaltech.ca</a><br />
                Address: BC Legal Tech, British Columbia, Canada
              </p>
            </section>

            <div className="glass-card rounded-sm p-6 mt-10">
              <p className="text-sm text-ink-300">
                By using BC Legal Tech, you acknowledge that you have read, understood, and agree to be
                bound by these Terms of Service.
              </p>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  )
}
