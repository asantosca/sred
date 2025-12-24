// ChatInterface component - Main chat interface with message display and streaming

import { useEffect, useRef, useState, useCallback } from 'react'
import { User, Bot, ThumbsUp, ThumbsDown, Copy, Check, Lightbulb, X, ChevronDown, ChevronUp } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import type { Message } from '@/types/chat'
import SourceCitations from './SourceCitations'
import FeedbackModal from './FeedbackModal'
import { useChatTracking } from '@/hooks/useChatTracking'

interface ChatInterfaceProps {
  messages: Message[]
  conversationId?: string | null
  streamingContent?: string
  isStreaming?: boolean
  pendingUserMessage?: string | null
  onSubmitFeedback?: (messageId: string, rating: number, category?: string) => void
  onViewDocument?: (documentId: string) => void
  suggestions?: string[] | null
  onDismissSuggestions?: () => void
}

export default function ChatInterface({
  messages,
  conversationId,
  streamingContent,
  isStreaming = false,
  pendingUserMessage = null,
  onSubmitFeedback,
  onViewDocument,
  suggestions = null,
  onDismissSuggestions,
}: ChatInterfaceProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const scrollContainerRef = useRef<HTMLDivElement>(null)

  // Feedback modal state
  const [feedbackModal, setFeedbackModal] = useState<{
    isOpen: boolean
    messageId: string
    rating: -1 | 1
  } | null>(null)

  // Copy feedback state (show checkmark briefly after copy)
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null)

  // Suggestions expanded state
  const [suggestionsExpanded, setSuggestionsExpanded] = useState(true)

  // Use the chat tracking hook for implicit signals
  const { trackCopy, trackSourceClick } = useChatTracking(conversationId || null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, streamingContent, pendingUserMessage])

  // Handle copying message content
  const handleCopyMessage = useCallback((messageId: string, content: string) => {
    navigator.clipboard.writeText(content).then(() => {
      setCopiedMessageId(messageId)
      trackCopy(messageId)
      setTimeout(() => setCopiedMessageId(null), 2000)
    })
  }, [trackCopy])

  // Handle source click with tracking
  const handleSourceClick = useCallback((messageId: string, documentId: string) => {
    trackSourceClick(messageId, documentId)
    onViewDocument?.(documentId)
  }, [trackSourceClick, onViewDocument])

  // Open feedback modal instead of submitting directly
  const handleFeedbackClick = useCallback((messageId: string, rating: -1 | 1) => {
    setFeedbackModal({ isOpen: true, messageId, rating })
  }, [])

  // Handle successful feedback submission
  const handleFeedbackSuccess = useCallback(() => {
    if (feedbackModal && onSubmitFeedback) {
      onSubmitFeedback(feedbackModal.messageId, feedbackModal.rating)
    }
  }, [feedbackModal, onSubmitFeedback])

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    })
  }

  const renderMessage = (message: Message) => {
    const isUser = message.role === 'user'

    return (
      <div
        key={message.id}
        className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
      >
        {/* Avatar */}
        <div
          className={`flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full ${
            isUser ? 'bg-blue-600' : 'bg-gray-700'
          }`}
        >
          {isUser ? (
            <User className="h-4 w-4 text-white" />
          ) : (
            <Bot className="h-4 w-4 text-white" />
          )}
        </div>

        {/* Message content */}
        <div className={`flex-1 ${isUser ? 'text-right' : 'text-left'}`}>
          <div className="mb-1 flex items-center gap-2">
            {isUser ? (
              <>
                <span className="text-xs text-gray-500">
                  {formatTime(message.created_at)}
                </span>
                <span className="text-sm font-medium text-gray-900">You</span>
              </>
            ) : (
              <>
                <span className="text-sm font-medium text-gray-900">
                  AI Assistant
                </span>
                <span className="text-xs text-gray-500">
                  {formatTime(message.created_at)}
                </span>
              </>
            )}
          </div>

          <div
            className={`inline-block max-w-[85%] rounded-lg px-4 py-2 ${
              isUser
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-900'
            }`}
          >
            {isUser ? (
              <div className="whitespace-pre-wrap break-words text-sm">
                {message.content}
              </div>
            ) : (
              <div className="prose prose-sm max-w-none prose-headings:mt-3 prose-headings:mb-2 prose-p:my-1 prose-ul:my-1 prose-li:my-0">
                <ReactMarkdown>{message.content}</ReactMarkdown>
              </div>
            )}
          </div>

          {/* Source citations for assistant messages */}
          {!isUser && message.sources && message.sources.length > 0 && (
            <div className="mt-2">
              <SourceCitations
                sources={message.sources}
                onViewDocument={(docId) => handleSourceClick(message.id, docId)}
              />
            </div>
          )}

          {/* Action buttons for assistant messages */}
          {!isUser && (
            <div className="mt-2 flex items-center gap-2">
              {/* Copy button */}
              <button
                onClick={() => handleCopyMessage(message.id, message.content)}
                className="rounded p-1 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600"
                title="Copy response"
              >
                {copiedMessageId === message.id ? (
                  <Check className="h-4 w-4 text-green-600" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </button>

              {/* Feedback buttons */}
              {onSubmitFeedback && (
                <>
                  <button
                    onClick={() => handleFeedbackClick(message.id, 1)}
                    className={`rounded p-1 transition-colors ${
                      message.rating === 1
                        ? 'bg-green-100 text-green-600'
                        : 'text-gray-400 hover:bg-gray-100 hover:text-green-600'
                    }`}
                    title="Helpful"
                  >
                    <ThumbsUp className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => handleFeedbackClick(message.id, -1)}
                    className={`rounded p-1 transition-colors ${
                      message.rating === -1
                        ? 'bg-red-100 text-red-600'
                        : 'text-gray-400 hover:bg-gray-100 hover:text-red-600'
                    }`}
                    title="Not helpful"
                  >
                    <ThumbsDown className="h-4 w-4" />
                  </button>
                </>
              )}

              {message.model_name && (
                <span className="ml-2 text-xs text-gray-400">
                  {message.model_name}
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div
      ref={scrollContainerRef}
      className="flex-1 overflow-y-auto bg-white p-4"
    >
      {messages.length === 0 && !isStreaming && !pendingUserMessage ? (
        <div className="flex h-full flex-col items-center justify-center text-center">
          <Bot className="h-16 w-16 text-gray-300" />
          <h3 className="mt-4 text-lg font-medium text-gray-900">
            Start a conversation
          </h3>
          <p className="mt-2 max-w-md text-sm text-gray-500">
            Ask questions about your documents. The AI will search through your
            documents and provide answers with citations.
          </p>
        </div>
      ) : (
        <div className="space-y-6 px-2">
          {messages.map(renderMessage)}

          {/* Pending user message (optimistic update) */}
          {pendingUserMessage && (
            <div className="flex gap-3 flex-row-reverse">
              <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-blue-600">
                <User className="h-4 w-4 text-white" />
              </div>
              <div className="flex-1 text-right">
                <div className="mb-1 flex items-center gap-2">
                  <span className="text-xs text-gray-500">Just now</span>
                  <span className="text-sm font-medium text-gray-900">You</span>
                </div>
                <div className="inline-block max-w-[85%] rounded-lg bg-blue-600 px-4 py-2 text-white">
                  <div className="whitespace-pre-wrap break-words text-sm">
                    {pendingUserMessage}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Streaming message */}
          {isStreaming && streamingContent && (
            <div className="flex gap-3">
              <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gray-700">
                <Bot className="h-4 w-4 text-white" />
              </div>
              <div className="flex-1">
                <div className="mb-1 flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-900">
                    AI Assistant
                  </span>
                  <span className="text-xs text-gray-500">typing...</span>
                </div>
                <div className="inline-block max-w-[85%] rounded-lg bg-gray-100 px-4 py-2 text-gray-900">
                  <div className="prose prose-sm max-w-none prose-headings:mt-3 prose-headings:mb-2 prose-p:my-1 prose-ul:my-1 prose-li:my-0">
                    <ReactMarkdown>{streamingContent.replace(/\[CONFIDENCE:\s*(HIGH|MEDIUM|LOW)\]/g, '')}</ReactMarkdown>
                  </div>
                  <span className="inline-block h-4 w-1 animate-pulse bg-gray-900"></span>
                </div>
              </div>
            </div>
          )}

          {/* Question improvement suggestions */}
          {suggestions && suggestions.length > 0 && !isStreaming && (
            <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50">
              <div
                className="flex cursor-pointer items-center justify-between px-4 py-2"
                onClick={() => setSuggestionsExpanded(!suggestionsExpanded)}
              >
                <div className="flex items-center gap-2">
                  <Lightbulb className="h-4 w-4 text-amber-600" />
                  <span className="text-sm font-medium text-amber-800">
                    Tips to improve your question
                  </span>
                </div>
                <div className="flex items-center gap-1">
                  {suggestionsExpanded ? (
                    <ChevronUp className="h-4 w-4 text-amber-600" />
                  ) : (
                    <ChevronDown className="h-4 w-4 text-amber-600" />
                  )}
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      onDismissSuggestions?.()
                    }}
                    className="rounded p-1 text-amber-600 hover:bg-amber-100"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              </div>
              {suggestionsExpanded && (
                <div className="border-t border-amber-200 px-4 py-3">
                  <ul className="space-y-1.5">
                    {suggestions.map((suggestion, index) => (
                      <li key={index} className="flex items-start gap-2 text-sm text-amber-800">
                        <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-amber-500" />
                        {suggestion}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      )}

      {/* Feedback Modal */}
      {feedbackModal && (
        <FeedbackModal
          isOpen={feedbackModal.isOpen}
          onClose={() => setFeedbackModal(null)}
          messageId={feedbackModal.messageId}
          rating={feedbackModal.rating}
          onSuccess={handleFeedbackSuccess}
        />
      )}
    </div>
  )
}
