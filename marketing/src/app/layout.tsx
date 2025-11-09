import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'BC Legal Tech - AI-Powered Legal Document Intelligence',
  description: 'AI-powered legal document intelligence platform for law firms in British Columbia. Semantic search, document management, and AI chat assistance for legal professionals.',
  keywords: 'legal tech, BC law firms, document management, AI legal assistant, semantic search, British Columbia',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
