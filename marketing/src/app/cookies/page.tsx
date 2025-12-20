import Link from 'next/link'
import Footer from '@/components/Footer'

export default function CookiePolicyPage() {
  return (
    <div className="min-h-screen bg-ink-950">
      {/* Hero */}
      <section className="relative pt-32 pb-12 px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="font-display text-4xl md:text-5xl text-cream-100 mb-4">Cookie Policy</h1>
          <p className="text-ink-400">Last Updated: November 9, 2025</p>
        </div>
      </section>

      {/* Content */}
      <section className="px-6 lg:px-8 pb-20">
        <div className="max-w-4xl mx-auto">
          <div className="prose-custom">
            <p className="text-lg text-ink-200 mb-8 leading-relaxed">
              This Cookie Policy explains how BC Legal Tech (&quot;we&quot;, &quot;us&quot;, or &quot;our&quot;) uses cookies and
              similar technologies on our website and platform. By using our Service, you consent to
              the use of cookies as described in this policy.
            </p>

            {/* Section 1 */}
            <section className="mb-10">
              <h2 className="font-display text-2xl text-cream-100 mb-4">1. What Are Cookies?</h2>
              <p className="text-ink-300 mb-4">
                Cookies are small text files stored on your device (computer, tablet, or mobile) when
                you visit a website. They help websites remember your preferences, improve your experience,
                and provide analytics about how the site is used.
              </p>
              <p className="text-ink-400">
                Cookies can be &quot;session&quot; cookies (deleted when you close your browser) or &quot;persistent&quot;
                cookies (remain on your device until they expire or are deleted).
              </p>
            </section>

            {/* Section 2 */}
            <section className="mb-10">
              <h2 className="font-display text-2xl text-cream-100 mb-4">2. Types of Cookies We Use</h2>

              <h3 className="text-xl text-cream-100 mb-3">2.1 Strictly Necessary Cookies</h3>
              <p className="text-ink-300 mb-4">
                These cookies are essential for the Service to function and cannot be disabled:
              </p>
              <ul className="list-disc pl-6 mb-4 space-y-2 text-ink-300">
                <li><strong className="text-cream-100">Authentication:</strong> Keep you logged in and maintain your session</li>
                <li><strong className="text-cream-100">Security:</strong> Protect against CSRF attacks and ensure secure connections</li>
                <li><strong className="text-cream-100">Load Balancing:</strong> Distribute traffic across servers for performance</li>
              </ul>
              <p className="text-sm text-ink-500 italic mb-4">
                Legal Basis: These cookies are necessary for the performance of our contract with you.
              </p>

              <h3 className="text-xl text-cream-100 mb-3">2.2 Functional Cookies</h3>
              <p className="text-ink-300 mb-4">
                These cookies enable enhanced functionality and personalization:
              </p>
              <ul className="list-disc pl-6 mb-4 space-y-2 text-ink-300">
                <li><strong className="text-cream-100">Preferences:</strong> Remember your settings (language, timezone, display options)</li>
                <li><strong className="text-cream-100">Form Data:</strong> Save form progress to prevent data loss</li>
                <li><strong className="text-cream-100">UI State:</strong> Remember sidebar collapse state, filter preferences</li>
              </ul>

              <h3 className="text-xl text-cream-100 mb-3">2.3 Analytics Cookies</h3>
              <p className="text-ink-300 mb-4">
                These cookies help us understand how visitors use our website:
              </p>
              <ul className="list-disc pl-6 mb-4 space-y-2 text-ink-300">
                <li><strong className="text-cream-100">Usage Analytics:</strong> Pages visited, features used, time spent</li>
                <li><strong className="text-cream-100">Performance Monitoring:</strong> Page load times, errors encountered</li>
                <li><strong className="text-cream-100">User Behavior:</strong> Click patterns, navigation paths (anonymized)</li>
              </ul>
              <p className="text-ink-400 mb-4">
                We use privacy-focused analytics (Plausible or similar) that do not track users across websites
                and do not collect personal information.
              </p>
            </section>

            {/* Section 3 */}
            <section className="mb-10">
              <h2 className="font-display text-2xl text-cream-100 mb-4">3. Third-Party Cookies</h2>
              <p className="text-ink-300 mb-4">
                Some cookies are placed by third-party services we use:
              </p>

              <div className="overflow-x-auto mb-4">
                <table className="min-w-full border border-ink-700">
                  <thead className="bg-ink-900">
                    <tr>
                      <th className="px-4 py-3 border-b border-ink-700 text-left text-sm font-semibold text-cream-100">Service</th>
                      <th className="px-4 py-3 border-b border-ink-700 text-left text-sm font-semibold text-cream-100">Purpose</th>
                      <th className="px-4 py-3 border-b border-ink-700 text-left text-sm font-semibold text-cream-100">Type</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm text-ink-300">
                    <tr>
                      <td className="px-4 py-3 border-b border-ink-800">AWS CloudFront</td>
                      <td className="px-4 py-3 border-b border-ink-800">Content delivery, performance</td>
                      <td className="px-4 py-3 border-b border-ink-800">Necessary</td>
                    </tr>
                    <tr>
                      <td className="px-4 py-3 border-b border-ink-800">Sentry</td>
                      <td className="px-4 py-3 border-b border-ink-800">Error tracking (privacy-configured)</td>
                      <td className="px-4 py-3 border-b border-ink-800">Functional</td>
                    </tr>
                    <tr>
                      <td className="px-4 py-3 border-b border-ink-800">Plausible Analytics</td>
                      <td className="px-4 py-3 border-b border-ink-800">Privacy-focused website analytics</td>
                      <td className="px-4 py-3 border-b border-ink-800">Analytics</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>

            {/* Section 4 */}
            <section className="mb-10">
              <h2 className="font-display text-2xl text-cream-100 mb-4">4. How Long Do Cookies Last?</h2>

              <h3 className="text-xl text-cream-100 mb-3">Session Cookies</h3>
              <p className="text-ink-300 mb-4">
                Automatically deleted when you close your browser. Used for session management and security.
              </p>

              <h3 className="text-xl text-cream-100 mb-3">Persistent Cookies</h3>
              <ul className="list-disc pl-6 mb-4 space-y-2 text-ink-300">
                <li><strong className="text-cream-100">Authentication tokens:</strong> 7-30 days (configurable)</li>
                <li><strong className="text-cream-100">Preferences:</strong> 365 days</li>
                <li><strong className="text-cream-100">Analytics:</strong> 30-90 days</li>
                <li><strong className="text-cream-100">Cookie consent:</strong> 365 days</li>
              </ul>
            </section>

            {/* Section 5 */}
            <section className="mb-10">
              <h2 className="font-display text-2xl text-cream-100 mb-4">5. How to Manage Cookies</h2>

              <h3 className="text-xl text-cream-100 mb-3">5.1 Cookie Consent Banner</h3>
              <p className="text-ink-300 mb-4">
                When you first visit our website, you&apos;ll see a cookie consent banner. You can:
              </p>
              <ul className="list-disc pl-6 mb-4 space-y-2 text-ink-300">
                <li>Accept all cookies</li>
                <li>Reject non-essential cookies</li>
                <li>Customize your cookie preferences</li>
              </ul>
              <p className="text-ink-400 mb-4">
                You can change your preferences at any time by clicking &quot;Cookie Settings&quot; in the footer.
              </p>

              <h3 className="text-xl text-cream-100 mb-3">5.2 Browser Settings</h3>
              <p className="text-ink-300 mb-4">
                Most browsers allow you to control cookies through their settings:
              </p>
              <ul className="list-disc pl-6 mb-4 space-y-2 text-ink-300">
                <li><strong className="text-cream-100">Chrome:</strong> Settings → Privacy and Security → Cookies</li>
                <li><strong className="text-cream-100">Firefox:</strong> Settings → Privacy &amp; Security → Cookies</li>
                <li><strong className="text-cream-100">Safari:</strong> Preferences → Privacy → Cookies</li>
                <li><strong className="text-cream-100">Edge:</strong> Settings → Privacy → Cookies</li>
              </ul>
              <p className="text-sm text-ink-500 italic">
                Note: Blocking strictly necessary cookies will prevent you from using the Service.
              </p>
            </section>

            {/* Section 6 */}
            <section className="mb-10">
              <h2 className="font-display text-2xl text-cream-100 mb-4">6. Do Not Track Signals</h2>
              <p className="text-ink-300">
                We respect Do Not Track (DNT) browser signals. When DNT is enabled, we will not set
                analytics or marketing cookies, only strictly necessary and functional cookies required
                for the Service to work.
              </p>
            </section>

            {/* Section 7 */}
            <section className="mb-10">
              <h2 className="font-display text-2xl text-cream-100 mb-4">7. Updates to This Policy</h2>
              <p className="text-ink-300">
                We may update this Cookie Policy to reflect changes in our practices or legal requirements.
                We will notify you of material changes by updating the &quot;Last Updated&quot; date and, where
                appropriate, providing notice through the Service.
              </p>
            </section>

            {/* Section 8 */}
            <section className="mb-10">
              <h2 className="font-display text-2xl text-cream-100 mb-4">8. Contact Us</h2>
              <p className="text-ink-300 mb-4">
                If you have questions about our use of cookies, contact us:
              </p>
              <p className="text-ink-300">
                Email: <a href="mailto:privacy@bclegaltech.ca" className="text-copper-400 hover:text-copper-300 transition-colors">privacy@bclegaltech.ca</a><br />
                Address: BC Legal Tech, British Columbia, Canada
              </p>
            </section>

            {/* Summary Table */}
            <section className="mb-10">
              <h2 className="font-display text-2xl text-cream-100 mb-4">Cookie Summary</h2>
              <div className="overflow-x-auto">
                <table className="min-w-full border border-ink-700">
                  <thead className="bg-ink-900">
                    <tr>
                      <th className="px-4 py-3 border-b border-ink-700 text-left text-sm font-semibold text-cream-100">Cookie Type</th>
                      <th className="px-4 py-3 border-b border-ink-700 text-left text-sm font-semibold text-cream-100">Purpose</th>
                      <th className="px-4 py-3 border-b border-ink-700 text-left text-sm font-semibold text-cream-100">Can Be Disabled?</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm text-ink-300">
                    <tr>
                      <td className="px-4 py-3 border-b border-ink-800 font-semibold text-cream-100">Strictly Necessary</td>
                      <td className="px-4 py-3 border-b border-ink-800">Authentication, security, core functionality</td>
                      <td className="px-4 py-3 border-b border-ink-800 text-red-400">No</td>
                    </tr>
                    <tr>
                      <td className="px-4 py-3 border-b border-ink-800 font-semibold text-cream-100">Functional</td>
                      <td className="px-4 py-3 border-b border-ink-800">Remember preferences, enhance experience</td>
                      <td className="px-4 py-3 border-b border-ink-800 text-green-400">Yes</td>
                    </tr>
                    <tr>
                      <td className="px-4 py-3 border-b border-ink-800 font-semibold text-cream-100">Analytics</td>
                      <td className="px-4 py-3 border-b border-ink-800">Understand usage, improve service</td>
                      <td className="px-4 py-3 border-b border-ink-800 text-green-400">Yes</td>
                    </tr>
                    <tr>
                      <td className="px-4 py-3 border-b border-ink-800 font-semibold text-cream-100">Marketing</td>
                      <td className="px-4 py-3 border-b border-ink-800">Not currently used</td>
                      <td className="px-4 py-3 border-b border-ink-800 text-ink-500">N/A</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  )
}
