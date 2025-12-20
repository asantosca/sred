import Link from 'next/link'
import Footer from '@/components/Footer'

export default function PrivacyPolicyPage() {
  return (
    <div className="min-h-screen bg-ink-950">
      {/* Hero */}
      <section className="relative pt-32 pb-12 px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="font-display text-4xl md:text-5xl text-cream-100 mb-4">Privacy Policy</h1>
          <p className="text-ink-400">Last Updated: November 9, 2025</p>
        </div>
      </section>

      {/* Content */}
      <section className="px-6 lg:px-8 pb-20">
        <div className="max-w-4xl mx-auto">
          <div className="prose-custom">
            <p className="text-lg text-ink-200 mb-8 leading-relaxed">
              BC Legal Tech (&quot;we&quot;, &quot;us&quot;, or &quot;our&quot;) is committed to protecting the privacy and confidentiality
              of your personal and professional information. This Privacy Policy explains how we collect, use,
              disclose, and safeguard your information when you use our AI-powered legal document intelligence
              platform (the &quot;Service&quot;).
            </p>

            <div className="glass-card rounded-sm p-5 mb-10 border-l-2 border-copper-500">
              <p className="text-sm text-ink-300">
                <strong className="text-copper-400">IMPORTANT:</strong> This is a template privacy policy. It must be reviewed and
                customized by a qualified lawyer before use. This template is provided for informational
                purposes only and does not constitute legal advice.
              </p>
            </div>

            {/* Section 1 */}
            <section className="mb-10">
              <h2 className="font-display text-2xl text-cream-100 mb-4">1. Information We Collect</h2>

              <h3 className="text-xl text-cream-100 mb-3">1.1 Information You Provide</h3>
              <ul className="list-disc pl-6 mb-4 space-y-2 text-ink-300">
                <li><strong className="text-cream-100">Account Information:</strong> Email address, name, law firm name, role, phone number</li>
                <li><strong className="text-cream-100">Documents:</strong> Legal documents you upload, including their content and metadata</li>
                <li><strong className="text-cream-100">Chat Conversations:</strong> Questions you ask and conversations with our AI assistant</li>
                <li><strong className="text-cream-100">Matter Information:</strong> Case details, client names, matter numbers, and related data</li>
                <li><strong className="text-cream-100">Payment Information:</strong> Billing details (processed securely through third-party payment processors)</li>
              </ul>

              <h3 className="text-xl text-cream-100 mb-3">1.2 Information We Collect Automatically</h3>
              <ul className="list-disc pl-6 mb-4 space-y-2 text-ink-300">
                <li><strong className="text-cream-100">Usage Data:</strong> Pages visited, features used, search queries, time spent on platform</li>
                <li><strong className="text-cream-100">Device Information:</strong> IP address, browser type, operating system, device identifiers</li>
                <li><strong className="text-cream-100">Cookies:</strong> Session cookies, preference cookies, and analytics cookies (see Cookie Policy)</li>
                <li><strong className="text-cream-100">Log Data:</strong> Access times, error logs, performance metrics</li>
              </ul>
            </section>

            {/* Section 2 */}
            <section className="mb-10">
              <h2 className="font-display text-2xl text-cream-100 mb-4">2. How We Use Your Information</h2>
              <p className="text-ink-300 mb-4">We use the information we collect to:</p>
              <ul className="list-disc pl-6 mb-4 space-y-2 text-ink-300">
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

            {/* Section 3 */}
            <section className="mb-10">
              <h2 className="font-display text-2xl text-cream-100 mb-4">3. AI and Third-Party Services</h2>

              <h3 className="text-xl text-cream-100 mb-3">3.1 AI Processing</h3>
              <p className="text-ink-300 mb-4">
                We use third-party AI services (including OpenAI and Anthropic) to provide semantic search
                and AI chat features. When you use these features:
              </p>
              <ul className="list-disc pl-6 mb-4 space-y-2 text-ink-300">
                <li>Document content is processed to generate embeddings for semantic search</li>
                <li>Your questions and relevant document excerpts are sent to AI services to generate responses</li>
                <li>We do NOT use your data to train third-party AI models (opt-out enforced)</li>
                <li>AI providers process data according to their privacy policies and data processing agreements</li>
              </ul>

              <h3 className="text-xl text-cream-100 mb-3">3.2 Other Third-Party Services</h3>
              <ul className="list-disc pl-6 mb-4 space-y-2 text-ink-300">
                <li><strong className="text-cream-100">AWS:</strong> Cloud infrastructure and storage (data stored in Canadian regions where possible)</li>
                <li><strong className="text-cream-100">Sentry:</strong> Error tracking and monitoring (configured for privacy)</li>
                <li><strong className="text-cream-100">Payment Processors:</strong> Stripe or similar (they have separate privacy policies)</li>
              </ul>
            </section>

            {/* Section 4 */}
            <section className="mb-10">
              <h2 className="font-display text-2xl text-cream-100 mb-4">4. Data Sharing and Disclosure</h2>
              <p className="text-ink-300 mb-4">We do NOT sell your personal information or legal documents to third parties.</p>

              <h3 className="text-xl text-cream-100 mb-3">We may share your information with:</h3>
              <ul className="list-disc pl-6 mb-4 space-y-2 text-ink-300">
                <li><strong className="text-cream-100">Your Law Firm:</strong> Other authorized users within your firm (based on access controls)</li>
                <li><strong className="text-cream-100">Service Providers:</strong> AWS, AI providers, payment processors (under strict data processing agreements)</li>
                <li><strong className="text-cream-100">Legal Requirements:</strong> If required by law, court order, or government request</li>
                <li><strong className="text-cream-100">Business Transfers:</strong> In connection with a merger, acquisition, or sale of assets (with notice)</li>
                <li><strong className="text-cream-100">With Your Consent:</strong> Any other sharing with your explicit permission</li>
              </ul>
            </section>

            {/* Section 5 */}
            <section className="mb-10">
              <h2 className="font-display text-2xl text-cream-100 mb-4">5. Data Security</h2>
              <p className="text-ink-300 mb-4">We implement industry-standard security measures including:</p>
              <ul className="list-disc pl-6 mb-4 space-y-2 text-ink-300">
                <li><strong className="text-cream-100">Encryption:</strong> TLS/SSL encryption in transit, AES-256 encryption at rest</li>
                <li><strong className="text-cream-100">Access Controls:</strong> Multi-factor authentication, role-based access, principle of least privilege</li>
                <li><strong className="text-cream-100">Data Isolation:</strong> Complete separation of data between law firms (multi-tenancy with row-level security)</li>
                <li><strong className="text-cream-100">Monitoring:</strong> 24/7 security monitoring, intrusion detection, regular security audits</li>
                <li><strong className="text-cream-100">Backups:</strong> Regular automated backups with encryption</li>
              </ul>
              <p className="text-ink-400">
                However, no system is 100% secure. We cannot guarantee absolute security of your data.
              </p>
            </section>

            {/* Section 6 */}
            <section className="mb-10">
              <h2 className="font-display text-2xl text-cream-100 mb-4">6. Data Retention</h2>
              <p className="text-ink-300 mb-4">We retain your information for as long as:</p>
              <ul className="list-disc pl-6 mb-4 space-y-2 text-ink-300">
                <li>Your account is active and the Service is in use</li>
                <li>Needed to comply with legal obligations (e.g., tax, legal, accounting requirements)</li>
                <li>Necessary to resolve disputes or enforce agreements</li>
              </ul>
              <p className="text-ink-400">
                Upon account termination, we will delete or anonymize your personal data within 90 days,
                except where retention is required by law.
              </p>
            </section>

            {/* Section 7 */}
            <section className="mb-10">
              <h2 className="font-display text-2xl text-cream-100 mb-4">7. Your Rights</h2>
              <p className="text-ink-300 mb-4">Under BC and Canadian privacy laws, you have the right to:</p>
              <ul className="list-disc pl-6 mb-4 space-y-2 text-ink-300">
                <li><strong className="text-cream-100">Access:</strong> Request a copy of your personal information</li>
                <li><strong className="text-cream-100">Correction:</strong> Request correction of inaccurate data</li>
                <li><strong className="text-cream-100">Deletion:</strong> Request deletion of your data (subject to legal obligations)</li>
                <li><strong className="text-cream-100">Export:</strong> Receive your data in a portable format</li>
                <li><strong className="text-cream-100">Opt-Out:</strong> Opt out of marketing communications</li>
                <li><strong className="text-cream-100">Withdraw Consent:</strong> Where processing is based on consent</li>
                <li><strong className="text-cream-100">Lodge Complaint:</strong> File a complaint with the BC Privacy Commissioner</li>
              </ul>
              <p className="text-ink-300">
                To exercise these rights, contact us at{' '}
                <a href="mailto:privacy@bclegaltech.ca" className="text-copper-400 hover:text-copper-300 transition-colors">
                  privacy@bclegaltech.ca
                </a>
              </p>
            </section>

            {/* Sections 8-11 */}
            <section className="mb-10">
              <h2 className="font-display text-2xl text-cream-100 mb-4">8. Children&apos;s Privacy</h2>
              <p className="text-ink-300">
                Our Service is not intended for individuals under 18. We do not knowingly collect
                information from children. If we learn we have collected information from a child,
                we will delete it immediately.
              </p>
            </section>

            <section className="mb-10">
              <h2 className="font-display text-2xl text-cream-100 mb-4">9. International Data Transfers</h2>
              <p className="text-ink-300">
                While we strive to store data in Canadian data centers, some service providers (e.g., AI services)
                may process data outside Canada. We ensure appropriate safeguards are in place through data
                processing agreements and standard contractual clauses.
              </p>
            </section>

            <section className="mb-10">
              <h2 className="font-display text-2xl text-cream-100 mb-4">10. Changes to This Policy</h2>
              <p className="text-ink-300">
                We may update this Privacy Policy from time to time. We will notify you of material changes
                by email or through the Service. Continued use after changes constitutes acceptance of the
                updated policy.
              </p>
            </section>

            <section className="mb-10">
              <h2 className="font-display text-2xl text-cream-100 mb-4">11. Contact Us</h2>
              <p className="text-ink-300 mb-4">
                If you have questions about this Privacy Policy or our privacy practices, contact us:
              </p>
              <p className="text-ink-300">
                Email: <a href="mailto:privacy@bclegaltech.ca" className="text-copper-400 hover:text-copper-300 transition-colors">privacy@bclegaltech.ca</a><br />
                Address: BC Legal Tech, British Columbia, Canada
              </p>
            </section>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  )
}
