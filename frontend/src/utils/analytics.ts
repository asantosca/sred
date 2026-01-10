// Microsoft Clarity event tracking utilities

declare global {
  interface Window {
    clarity?: (...args: unknown[]) => void
  }
}

export const trackEvent = (
  eventName: string,
  _params?: Record<string, unknown>
) => {
  if (typeof window !== 'undefined' && window.clarity) {
    window.clarity('event', eventName)
  }
}

// Registration events
export const trackSignUp = (_method: string = 'email') => {
  trackEvent('sign_up')
}

export const trackSignUpConfirmed = () => {
  trackEvent('sign_up_confirmed')
}
