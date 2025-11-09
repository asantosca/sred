import Link from 'next/link'

export default function CookiePolicyPage() {
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
        <h1 className="text-4xl font-bold text-gray-900 mb-4">Cookie Policy</h1>
        <p className="text-gray-600 mb-8">Last Updated: November 9, 2025</p>

        <div className="prose prose-lg max-w-none">
          <p className="text-lg text-gray-700 mb-6">
            This Cookie Policy explains how BC Legal Tech ("we", "us", or "our") uses cookies and
            similar technologies on our website and platform. By using our Service, you consent to
            the use of cookies as described in this policy.
          </p>

          {/* 1. What Are Cookies */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">1. What Are Cookies?</h2>
            <p className="text-gray-700 mb-4">
              Cookies are small text files stored on your device (computer, tablet, or mobile) when
              you visit a website. They help websites remember your preferences, improve your experience,
              and provide analytics about how the site is used.
            </p>
            <p className="text-gray-700">
              Cookies can be "session" cookies (deleted when you close your browser) or "persistent"
              cookies (remain on your device until they expire or are deleted).
            </p>
          </section>

          {/* 2. Types of Cookies We Use */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">2. Types of Cookies We Use</h2>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">2.1 Strictly Necessary Cookies</h3>
            <p className="text-gray-700 mb-4">
              These cookies are essential for the Service to function and cannot be disabled:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li><strong>Authentication:</strong> Keep you logged in and maintain your session</li>
              <li><strong>Security:</strong> Protect against CSRF attacks and ensure secure connections</li>
              <li><strong>Load Balancing:</strong> Distribute traffic across servers for performance</li>
            </ul>
            <p className="text-sm text-gray-600 italic mb-4">
              Legal Basis: These cookies are necessary for the performance of our contract with you.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">2.2 Functional Cookies</h3>
            <p className="text-gray-700 mb-4">
              These cookies enable enhanced functionality and personalization:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li><strong>Preferences:</strong> Remember your settings (language, timezone, display options)</li>
              <li><strong>Form Data:</strong> Save form progress to prevent data loss</li>
              <li><strong>UI State:</strong> Remember sidebar collapse state, filter preferences</li>
            </ul>
            <p className="text-sm text-gray-600 italic mb-4">
              Legal Basis: These cookies are used with your consent.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">2.3 Analytics Cookies</h3>
            <p className="text-gray-700 mb-4">
              These cookies help us understand how visitors use our website:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li><strong>Usage Analytics:</strong> Pages visited, features used, time spent</li>
              <li><strong>Performance Monitoring:</strong> Page load times, errors encountered</li>
              <li><strong>User Behavior:</strong> Click patterns, navigation paths (anonymized)</li>
            </ul>
            <p className="text-gray-700 mb-4">
              We use privacy-focused analytics (Plausible or similar) that:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Do not track users across websites</li>
              <li>Do not collect personal information</li>
              <li>Store data in compliance with GDPR</li>
              <li>Provide aggregate statistics only</li>
            </ul>
            <p className="text-sm text-gray-600 italic mb-4">
              Legal Basis: These cookies are used with your consent.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">2.4 Marketing Cookies (Future)</h3>
            <p className="text-gray-700 mb-4">
              We do not currently use marketing or advertising cookies. If we introduce them in the
              future, we will update this policy and seek your consent.
            </p>
          </section>

          {/* 3. Third-Party Cookies */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">3. Third-Party Cookies</h2>
            <p className="text-gray-700 mb-4">
              Some cookies are placed by third-party services we use:
            </p>

            <div className="overflow-x-auto">
              <table className="min-w-full border border-gray-300 mb-4">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 border-b text-left text-sm font-semibold text-gray-900">Service</th>
                    <th className="px-4 py-2 border-b text-left text-sm font-semibold text-gray-900">Purpose</th>
                    <th className="px-4 py-2 border-b text-left text-sm font-semibold text-gray-900">Type</th>
                  </tr>
                </thead>
                <tbody className="text-sm text-gray-700">
                  <tr>
                    <td className="px-4 py-2 border-b">AWS CloudFront</td>
                    <td className="px-4 py-2 border-b">Content delivery, performance</td>
                    <td className="px-4 py-2 border-b">Necessary</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2 border-b">Sentry</td>
                    <td className="px-4 py-2 border-b">Error tracking (privacy-configured)</td>
                    <td className="px-4 py-2 border-b">Functional</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2 border-b">Plausible Analytics</td>
                    <td className="px-4 py-2 border-b">Privacy-focused website analytics</td>
                    <td className="px-4 py-2 border-b">Analytics</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <p className="text-gray-700">
              Each third-party service has its own privacy policy governing the use of cookies.
              We carefully select privacy-conscious providers.
            </p>
          </section>

          {/* 4. Cookie Duration */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">4. How Long Do Cookies Last?</h2>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">Session Cookies</h3>
            <p className="text-gray-700 mb-4">
              Automatically deleted when you close your browser. Used for session management and security.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">Persistent Cookies</h3>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li><strong>Authentication tokens:</strong> 7-30 days (configurable)</li>
              <li><strong>Preferences:</strong> 365 days</li>
              <li><strong>Analytics:</strong> 30-90 days</li>
              <li><strong>Cookie consent:</strong> 365 days</li>
            </ul>
          </section>

          {/* 5. Managing Cookies */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">5. How to Manage Cookies</h2>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">5.1 Cookie Consent Banner</h3>
            <p className="text-gray-700 mb-4">
              When you first visit our website, you'll see a cookie consent banner. You can:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Accept all cookies</li>
              <li>Reject non-essential cookies</li>
              <li>Customize your cookie preferences</li>
            </ul>
            <p className="text-gray-700 mb-4">
              You can change your preferences at any time by clicking "Cookie Settings" in the footer.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3">5.2 Browser Settings</h3>
            <p className="text-gray-700 mb-4">
              Most browsers allow you to control cookies through their settings:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li><strong>Chrome:</strong> Settings → Privacy and Security → Cookies</li>
              <li><strong>Firefox:</strong> Settings → Privacy & Security → Cookies</li>
              <li><strong>Safari:</strong> Preferences → Privacy → Cookies</li>
              <li><strong>Edge:</strong> Settings → Privacy → Cookies</li>
            </ul>
            <p className="text-gray-700 mb-4">
              You can:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Block all cookies</li>
              <li>Block third-party cookies only</li>
              <li>Delete existing cookies</li>
              <li>Set cookies to be deleted when you close the browser</li>
            </ul>
            <p className="text-sm text-gray-600 italic">
              Note: Blocking strictly necessary cookies will prevent you from using the Service.
            </p>
          </section>

          {/* 6. Do Not Track */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">6. Do Not Track Signals</h2>
            <p className="text-gray-700">
              We respect Do Not Track (DNT) browser signals. When DNT is enabled, we will not set
              analytics or marketing cookies, only strictly necessary and functional cookies required
              for the Service to work.
            </p>
          </section>

          {/* 7. Mobile Devices */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">7. Mobile Devices</h2>
            <p className="text-gray-700 mb-4">
              On mobile devices, similar technologies are used:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li><strong>Local Storage:</strong> Stores preferences and session data locally</li>
              <li><strong>Session Storage:</strong> Temporary storage cleared when you close the app</li>
              <li><strong>App-Specific IDs:</strong> Anonymous identifiers for analytics</li>
            </ul>
            <p className="text-gray-700">
              You can manage these through your device settings or clear them by clearing app data.
            </p>
          </section>

          {/* 8. Updates to This Policy */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">8. Updates to This Policy</h2>
            <p className="text-gray-700">
              We may update this Cookie Policy to reflect changes in our practices or legal requirements.
              We will notify you of material changes by updating the "Last Updated" date and, where
              appropriate, providing notice through the Service.
            </p>
          </section>

          {/* 9. Contact Us */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">9. Contact Us</h2>
            <p className="text-gray-700 mb-4">
              If you have questions about our use of cookies, contact us:
            </p>
            <p className="text-gray-700">
              Email: <a href="mailto:privacy@bclegaltech.ca" className="text-primary-600 hover:text-primary-700">privacy@bclegaltech.ca</a><br />
              Address: BC Legal Tech, British Columbia, Canada
            </p>
          </section>

          {/* Summary Table */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Cookie Summary</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full border border-gray-300">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 border-b text-left text-sm font-semibold text-gray-900">Cookie Type</th>
                    <th className="px-4 py-2 border-b text-left text-sm font-semibold text-gray-900">Purpose</th>
                    <th className="px-4 py-2 border-b text-left text-sm font-semibold text-gray-900">Can Be Disabled?</th>
                  </tr>
                </thead>
                <tbody className="text-sm text-gray-700">
                  <tr>
                    <td className="px-4 py-2 border-b font-semibold">Strictly Necessary</td>
                    <td className="px-4 py-2 border-b">Authentication, security, core functionality</td>
                    <td className="px-4 py-2 border-b text-red-600">No</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2 border-b font-semibold">Functional</td>
                    <td className="px-4 py-2 border-b">Remember preferences, enhance experience</td>
                    <td className="px-4 py-2 border-b text-green-600">Yes</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2 border-b font-semibold">Analytics</td>
                    <td className="px-4 py-2 border-b">Understand usage, improve service</td>
                    <td className="px-4 py-2 border-b text-green-600">Yes</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2 border-b font-semibold">Marketing</td>
                    <td className="px-4 py-2 border-b">Not currently used</td>
                    <td className="px-4 py-2 border-b text-gray-400">N/A</td>
                  </tr>
                </tbody>
              </table>
            </div>
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
