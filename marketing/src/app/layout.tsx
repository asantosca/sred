import type { Metadata } from 'next'
import { Playfair_Display, Sora } from 'next/font/google'
import './globals.css'
import Header from '@/components/Header'
import CookieConsent from '@/components/CookieConsent'

const playfair = Playfair_Display({
  subsets: ['latin'],
  variable: '--font-display',
  display: 'swap',
})

const sora = Sora({
  subsets: ['latin'],
  variable: '--font-body',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'BC Legal Tech - AI-Powered Legal Document Intelligence',
  description: 'AI-powered legal document intelligence platform for law firms in British Columbia. Semantic search, document management, and AI chat assistance for legal professionals.',
  keywords: 'legal tech, BC law firms, document management, AI legal assistant, semantic search, British Columbia',
  icons: {
    icon: '/bclt_icon.png',
    apple: '/bclt_icon.png',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${playfair.variable} ${sora.variable}`}>
      <body className="font-body bg-ink-950 text-cream-100 antialiased">
        {/* Noise texture overlay for depth */}
        <div className="noise-overlay" aria-hidden="true" />

        <Header />
        <main>{children}</main>
        <CookieConsent />
      </body>
    </html>
  )
}
