// ChatPage - Main chat page with conversation management and streaming

import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import DashboardLayout from '@/components/layout/DashboardLayout'
import ConversationList from '@/components/chat/ConversationList'
import ChatInterface from '@/components/chat/ChatInterface'
import MessageInput from '@/components/chat/MessageInput'
import MatterSelectorCompact from '@/components/chat/MatterSelectorCompact'
import Alert from '@/components/ui/Alert'
import Button from '@/components/ui/Button'
import { chatApi, billableApi } from '@/lib/api'
import type { ChatStreamChunk } from '@/types/chat'
import { Clock } from 'lucide-react'

export default function ChatPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [selectedConversationId, setSelectedConversationId] = useState<
    string | null
  >(null)
  const [selectedMatterId, setSelectedMatterId] = useState<string | null>(null)
  const [streamingContent, setStreamingContent] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [pendingUserMessage, setPendingUserMessage] = useState<string | null>(null)
  const [localMessages, setLocalMessages] = useState<any[]>([])
  const [searchQuery, setSearchQuery] = useState('')

  // Fetch conversations
  const { data: conversationsData, isLoading: loadingConversations } = useQuery({
    queryKey: ['conversations'],
    queryFn: async () => {
      const response = await chatApi.listConversations({ page_size: 50 })
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

    try {
      const response = await chatApi.sendMessageStream({
        conversation_id: selectedConversationId || undefined,
        message,
        matter_id: selectedMatterId || undefined,
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

            // Clear streaming state AFTER messages are loaded
            setIsStreaming(false)
            setStreamingContent('')

            // Refresh conversation list
            queryClient.invalidateQueries({ queryKey: ['conversations'] })

            // If new conversation was created, select it
            if (parsed.conversation_id && !selectedConversationId) {
              setSelectedConversationId(parsed.conversation_id)
            }
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
    setSelectedMatterId(null)
    setLocalMessages([])
    setPendingUserMessage(null)
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
          />
        </div>

        {/* Main chat area */}
        <div className="flex flex-1 flex-col">
          {/* Conversation header with Track Time button */}
          {selectedConversationId && messages.length > 0 && (
            <div className="flex items-center justify-between border-b border-gray-200 bg-white px-4 py-2">
              <div className="text-sm text-gray-600">
                {conversationData?.title || 'Conversation'}
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
            streamingContent={streamingContent}
            isStreaming={isStreaming}
            pendingUserMessage={pendingUserMessage}
            onSubmitFeedback={(messageId, rating) =>
              submitFeedbackMutation.mutate({ messageId, rating })
            }
            onViewDocument={handleViewDocument}
          />

          {/* Matter selector - only shown for new conversations */}
          {!selectedConversationId && (
            <MatterSelectorCompact
              value={selectedMatterId}
              onChange={setSelectedMatterId}
              disabled={isStreaming}
            />
          )}

          <MessageInput
            onSendMessage={handleSendMessage}
            disabled={isStreaming || loadingMessages}
            placeholder={
              selectedConversationId
                ? 'Ask a follow-up question...'
                : selectedMatterId
                  ? 'Ask about documents in this matter...'
                  : 'Start a new conversation...'
            }
          />
        </div>
      </div>
    </DashboardLayout>
  )
}
