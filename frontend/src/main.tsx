// Application entry point

import React from 'react'
import ReactDOM from 'react-dom/client'
import * as Sentry from '@sentry/react'
import App from './App'
import './index.css'

// Initialize Sentry for error tracking
console.log('Sentry Check:', {
  isProd: import.meta.env.PROD,
  hasDSN: !!import.meta.env.VITE_SENTRY_DSN,
  dsn: import.meta.env.VITE_SENTRY_DSN,
  mode: import.meta.env.MODE,
})

// Temporarily allow Sentry in all modes for testing (will restrict to PROD later)
if (import.meta.env.VITE_SENTRY_DSN) {
  console.log('Initializing Sentry...')
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    environment: import.meta.env.VITE_SENTRY_ENVIRONMENT || import.meta.env.MODE,
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration({
        maskAllText: true, // Mask all text for privacy (legal documents)
        blockAllMedia: true, // Block all media
      }),
    ],
    // Performance Monitoring
    tracesSampleRate: 0.1, // 10% of transactions for performance monitoring
    // Session Replay (for debugging)
    replaysSessionSampleRate: 0.1, // 10% of sessions
    replaysOnErrorSampleRate: 1.0, // 100% of sessions with errors
    // Don't send errors from dev server (port 5173), but allow preview server (port 4173)
    beforeSend(event) {
      console.log('Sentry beforeSend called, port:', window.location.port)
      // Block dev server (npm run dev) but allow preview/production
      if (window.location.port === '5173') {
        console.log('Blocking error from dev server')
        return null
      }
      console.log('Sending error to Sentry')
      return event
    },
  })
  console.log('Sentry initialized successfully')

  // Expose Sentry globally for testing (remove in production)
  ;(window as any).Sentry = Sentry
  console.log('Sentry is now available globally. Try: Sentry.captureException(new Error("test"))')
} else {
  console.log('Sentry NOT initialized:', {
    reason: !import.meta.env.PROD ? 'Not production mode' : 'No DSN configured'
  })
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
