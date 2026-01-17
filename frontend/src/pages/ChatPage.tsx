// ChatPage - Main chat page with conversation management and streaming

import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useSearchParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import DashboardLayout from '@/components/layout/DashboardLayout'
import ConversationList from '@/components/chat/ConversationList'
import ChatInterface from '@/components/chat/ChatInterface'
import MessageInput, { MessageInputHandle } from '@/components/chat/MessageInput'
import ClaimSelectorCompact from '@/components/chat/ClaimSelectorCompact'
import Alert from '@/components/ui/Alert'
import Button from '@/components/ui/Button'
import { chatApi, billableApi, claimsApi } from '@/lib/api'
import type { ChatStreamChunk, ClaimSuggestion } from '@/types/chat'
import ClaimSuggestionBanner from '@/components/chat/ClaimSuggestionBanner'
import { Clock, Briefcase } from 'lucide-react'

export default function ChatPage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const queryClient = useQueryClient()
  const messageInputRef = useRef<MessageInputHandle>(null)

  // Get claim ID from URL query param (e.g., /chat?matter=uuid)
  const claimFromUrl = searchParams.get('matter')
  // If history=true, we're viewing conversation history for a claim
  const showHistoryForClaim = searchParams.get('history') === 'true' && claimFromUrl

  const [selectedConversationId, setSelectedConversationId] = useState<
    string | null
  >(null)
  const [selectedClaimId, setSelectedClaimId] = useState<string | null>(claimFromUrl)
  const [streamingContent, setStreamingContent] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [pendingUserMessage, setPendingUserMessage] = useState<string | null>(null)
  const [localMessages, setLocalMessages] = useState<any[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [claimSuggestion, setClaimSuggestion] = useState<ClaimSuggestion | null>(null)
  const [isLinkingClaim, setIsLinkingClaim] = useState(false)
  const [conversationClaimFilter, setConversationClaimFilter] = useState<string | null>(null)
  const [questionSuggestions, setQuestionSuggestions] = useState<string[] | null>(null)

  // Fetch claims for filter dropdown
  const { data: claimsData } = useQuery({
    queryKey: ['claims', 'all'],
    queryFn: async () => {
      const response = await claimsApi.list({ size: 100 })
      return response.data
    },
  })

  // Determine which claim filter to use
  const effectiveClaimFilter = showHistoryForClaim ? claimFromUrl : conversationClaimFilter

  // Fetch conversations (optionally filtered by claim)
  const { data: conversationsData, isLoading: loadingConversations } = useQuery({
    queryKey: ['conversations', effectiveClaimFilter],
    queryFn: async () => {
      const response = await chatApi.listConversations({
        page_size: 50,
        matter_id: effectiveClaimFilter || undefined,
      })
      return response.data
    },
  })

  // Search conversations
  const { data: searchData, isLoading: isSearching } = useQuery({
    queryKey: ['conversations', 'search', searchQuery],
    queryFn: async () => {
      const response = await chatApi.searchConversations({ q: searchQuery, page_size: 50 })
      return response.data
    },
    enabled: searchQuery.length >= 2,
  })

  const handleSearch = (query: string) => {
    setSearchQuery(query)
  }

  // Fetch selected conversation with messages
  const { data: conversationData, isLoading: loadingMessages } = useQuery({
    queryKey: ['conversation', selectedConversationId],
    queryFn: async () => {
      if (!selectedConversationId) return null
      const response = await chatApi.getConversation(selectedConversationId)
      return response.data
    },
    enabled: !!selectedConversationId,
  })

  // Sync local messages with conversation data
  useEffect(() => {
    if (conversationData?.messages) {
      setLocalMessages(conversationData.messages)
    }
  }, [conversationData?.messages])

  // Delete conversation mutation
  const deleteConversationMutation = useMutation({
    mutationFn: (conversationId: string) =>
      chatApi.deleteConversation(conversationId),
    onSuccess: (_, deletedId) => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
      if (selectedConversationId === deletedId) {
        setSelectedConversationId(null)
      }
      toast.success('Conversation deleted')
    },
    onError: () => {
      toast.error('Failed to delete conversation')
    },
  })

  // Submit feedback mutation
  const submitFeedbackMutation = useMutation({
    mutationFn: ({ messageId, rating }: { messageId: string; rating: number }) =>
      chatApi.submitFeedback(messageId, { rating }),
    onSuccess: (_, { rating }) => {
      queryClient.invalidateQueries({ queryKey: ['conversation', selectedConversationId] })
      toast.success(rating > 0 ? 'Thank you for your feedback!' : 'Feedback submitted')
    },
    onError: () => {
      toast.error('Failed to submit feedback')
    },
  })

  // Track time mutation
  const trackTimeMutation = useMutation({
    mutationFn: (conversationId: string) =>
      billableApi.create({ conversation_id: conversationId, generate_description: true }),
    onSuccess: () => {
      toast.success('Billable session created')
      navigate('/billable')
    },
    onError: () => {
      toast.error('Failed to create billable session')
    },
  })

  // Parse SSE stream
  const parseSSEChunk = (chunk: string): ChatStreamChunk | null => {
    try {
      // SSE format: "data: {json}\n\n"
      const lines = chunk.split('\n')
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const jsonStr = line.substring(6)
          return JSON.parse(jsonStr)
        }
      }
      return null
    } catch (error) {
      console.error('Error parsing SSE chunk:', error)
      return null
    }
  }

  // Send message with streaming
  const handleSendMessage = async (message: string) => {
    setError(null)
    setStreamingContent('')
    setIsStreaming(true)
    setPendingUserMessage(message) // Show user's message immediately
    setQuestionSuggestions(null) // Clear previous suggestions

    try {
      const response = await chatApi.sendMessageStream({
        conversation_id: selectedConversationId || undefined,
        message,
        matter_id: selectedClaimId || undefined,
        include_sources: true,
        max_context_chunks: 5,
        similarity_threshold: 0.5,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('No response body')
      }

      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const chunks = buffer.split('\n\n')
        buffer = chunks.pop() || ''

        for (const chunk of chunks) {
          if (!chunk.trim()) continue

          const parsed = parseSSEChunk(chunk)
          if (!parsed) continue

          if (parsed.type === 'content' && parsed.content) {
            setStreamingContent((prev) => prev + parsed.content)
          } else if (parsed.type === 'done') {
            // Determine the conversation ID to refresh
            const conversationIdToRefresh = parsed.conversation_id || selectedConversationId

            // Fetch the conversation messages and update local state directly
            if (conversationIdToRefresh) {
              const conversationResponse = await chatApi.getConversation(conversationIdToRefresh)
              const conversationWithMessages = conversationResponse.data

              // Update local messages directly
              setLocalMessages(conversationWithMessages.messages)

              // Update the query cache for future use
              queryClient.setQueryData(['conversation', conversationIdToRefresh], conversationWithMessages)

              // Clear pending message now that we have real messages
              setPendingUserMessage(null)
            }

            // Store question improvement suggestions if any
            if (parsed.suggestions && parsed.suggestions.length > 0) {
              setQuestionSuggestions(parsed.suggestions)
            }

            // Clear streaming state AFTER messages are loaded
            setIsStreaming(false)
            setStreamingContent('')

            // Return focus to input
            setTimeout(() => messageInputRef.current?.focus(), 100)

            // Refresh conversation list
            queryClient.invalidateQueries({ queryKey: ['conversations'] })

            // If new conversation was created, select it
            if (parsed.conversation_id && !selectedConversationId) {
              setSelectedConversationId(parsed.conversation_id)
            }
          } else if (parsed.type === 'claim_suggestion' && parsed.claim_suggestion) {
            // AI detected this query may relate to a claim
            setClaimSuggestion(parsed.claim_suggestion)
          } else if (parsed.type === 'error' && parsed.error) {
            setError(parsed.error)
            setIsStreaming(false)
            setPendingUserMessage(null) // Clear pending message on error
          }
        }
      }
    } catch (err) {
      console.error('Error sending message:', err)
      setError(err instanceof Error ? err.message : 'Failed to send message')
      setIsStreaming(false)
      setStreamingContent('')
      setPendingUserMessage(null) // Clear pending message on error
    }
  }

  const handleNewConversation = () => {
    setSelectedConversationId(null)
    setSelectedClaimId(null)
    setLocalMessages([])
    setPendingUserMessage(null)
    setClaimSuggestion(null)
    setQuestionSuggestions(null)
    // Clear the claim query param from URL
    if (searchParams.has('matter')) {
      searchParams.delete('matter')
      setSearchParams(searchParams, { replace: true })
    }
    // Focus the message input
    setTimeout(() => messageInputRef.current?.focus(), 100)
  }

  // Handle accepting claim suggestion
  const handleAcceptClaimSuggestion = async () => {
    if (!claimSuggestion || !selectedConversationId) return

    setIsLinkingClaim(true)
    try {
      const response = await chatApi.linkToClaim(
        selectedConversationId,
        claimSuggestion.claim_id
      )

      // Update local state
      setSelectedClaimId(claimSuggestion.claim_id)
      setClaimSuggestion(null)

      // Refresh conversation data to get updated title and claim_name
      queryClient.invalidateQueries({ queryKey: ['conversation', selectedConversationId] })
      queryClient.invalidateQueries({ queryKey: ['conversations'] })

      toast.success(`Linked to ${response.data.matter_name}`)
    } catch (err) {
      console.error('Failed to link conversation:', err)
      toast.error('Failed to link conversation to claim')
    } finally {
      setIsLinkingClaim(false)
    }
  }

  const handleViewDocument = (documentId: string) => {
    navigate(`/documents?id=${documentId}`)
  }

  const conversations = conversationsData?.conversations || []
  const messages = localMessages

  return (
    <DashboardLayout>
      <div className="flex h-[calc(100vh-4rem)]">
        {/* Sidebar with conversation list */}
        <div className="w-80 flex-shrink-0">
          <ConversationList
            conversations={conversations}
            selectedConversationId={selectedConversationId || undefined}
            onSelectConversation={setSelectedConversationId}
            onDeleteConversation={(id) => deleteConversationMutation.mutate(id)}
            onNewConversation={handleNewConversation}
            loading={loadingConversations}
            onSearch={handleSearch}
            searchResults={searchData?.conversations}
            isSearching={isSearching}
            claims={claimsData?.claims || []}
            selectedClaimFilter={conversationClaimFilter}
            onClaimFilterChange={setConversationClaimFilter}
          />
        </div>

        {/* Main chat area */}
        <div className="flex flex-1 flex-col">
          {/* Conversation header with Track Time button */}
          {selectedConversationId && messages.length > 0 && (
            <div className="flex items-center justify-between border-b border-gray-200 bg-white px-4 py-2">
              <div className="flex items-center gap-3">
                <div className="text-sm text-gray-600">
                  {conversationData?.title || 'Conversation'}
                </div>
                {conversationData?.matter_name ? (
                  <span className="inline-flex items-center gap-1 rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">
                    <Briefcase className="h-3 w-3" />
                    {conversationData.matter_name}
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 rounded-full bg-purple-100 px-2 py-0.5 text-xs font-medium text-purple-700">
                    General Analysis
                  </span>
                )}
              </div>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => trackTimeMutation.mutate(selectedConversationId)}
                disabled={trackTimeMutation.isPending}
              >
                <Clock className="mr-2 h-4 w-4" />
                {trackTimeMutation.isPending ? 'Creating...' : 'Track Time'}
              </Button>
            </div>
          )}

          {error && (
            <div className="p-4">
              <Alert variant="error">
                {error}
              </Alert>
            </div>
          )}

          <ChatInterface
            messages={messages}
            conversationId={selectedConversationId}
            streamingContent={streamingContent}
            isStreaming={isStreaming}
            pendingUserMessage={pendingUserMessage}
            onSubmitFeedback={(messageId, rating) =>
              submitFeedbackMutation.mutate({ messageId, rating })
            }
            onViewDocument={handleViewDocument}
            suggestions={questionSuggestions}
            onDismissSuggestions={() => setQuestionSuggestions(null)}
          />

          {/* Claim suggestion banner - shown when AI detects related claim */}
          {claimSuggestion && selectedConversationId && !conversationData?.matter_id && (
            <ClaimSuggestionBanner
              suggestion={claimSuggestion}
              onAccept={handleAcceptClaimSuggestion}
              onDismiss={() => setClaimSuggestion(null)}
              loading={isLinkingClaim}
            />
          )}

          {/* Claim selector - only shown for new conversations */}
          {!selectedConversationId && (
            <ClaimSelectorCompact
              value={selectedClaimId}
              onChange={setSelectedClaimId}
              disabled={isStreaming}
            />
          )}

          <MessageInput
            ref={messageInputRef}
            onSendMessage={handleSendMessage}
            disabled={isStreaming || loadingMessages}
            placeholder={
              selectedConversationId
                ? 'Ask a follow-up question...'
                : selectedClaimId
                  ? 'Ask about documents in this project...'
                  : 'Ask a general SR&ED question...'
            }
          />
        </div>
      </div>
    </DashboardLayout>
  )
}
