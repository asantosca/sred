// useChatTracking.ts - Hook for tracking chat interactions for quality analytics

import { useEffect, useRef, useCallback } from 'react'
import { chatApi } from '@/lib/api'

/**
 * Hook for tracking implicit user interaction signals in chat.
 *
 * Tracks:
 * - Session start/end for abandonment detection
 * - Text copy events (indicates useful response)
 * - Source citation clicks (indicates engagement)
 *
 * These signals help analyze AI response quality beyond explicit feedback.
 */
export function useChatTracking(conversationId: string | null) {
  const sessionStartedRef = useRef(false)

  // Track session start when conversation is loaded
  useEffect(() => {
    if (conversationId && !sessionStartedRef.current) {
      sessionStartedRef.current = true
      chatApi.trackSignal({
        signal_type: 'session_start',
        conversation_id: conversationId,
      })
    }

    // Track session end on visibility change or unmount
    const handleVisibilityChange = () => {
      if (document.hidden && conversationId) {
        chatApi.trackSignal({
          signal_type: 'session_end',
          conversation_id: conversationId,
        })
      } else if (!document.hidden && conversationId) {
        // User came back - restart session
        chatApi.trackSignal({
          signal_type: 'session_start',
          conversation_id: conversationId,
        })
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      // Track session end on unmount
      if (conversationId) {
        chatApi.trackSignal({
          signal_type: 'session_end',
          conversation_id: conversationId,
        })
      }
    }
  }, [conversationId])

  // Reset session tracking when conversation changes
  useEffect(() => {
    sessionStartedRef.current = false
  }, [conversationId])

  /**
   * Track when user copies response text
   */
  const trackCopy = useCallback((messageId: string) => {
    if (!conversationId) return
    chatApi.trackSignal({
      signal_type: 'copy',
      conversation_id: conversationId,
      message_id: messageId,
    })
  }, [conversationId])

  /**
   * Track when user clicks on a cited source document
   */
  const trackSourceClick = useCallback((messageId: string, documentId: string) => {
    if (!conversationId) return
    chatApi.trackSignal({
      signal_type: 'source_click',
      conversation_id: conversationId,
      message_id: messageId,
      document_id: documentId,
    })
  }, [conversationId])

  return { trackCopy, trackSourceClick }
}

export default useChatTracking
