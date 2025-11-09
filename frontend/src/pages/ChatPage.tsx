// ChatPage - Main chat page with conversation management and streaming

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import DashboardLayout from '@/components/layout/DashboardLayout'
import ConversationList from '@/components/chat/ConversationList'
import ChatInterface from '@/components/chat/ChatInterface'
import MessageInput from '@/components/chat/MessageInput'
import Alert from '@/components/ui/Alert'
import { chatApi } from '@/lib/api'
import type { ChatStreamChunk } from '@/types/chat'

export default function ChatPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [selectedConversationId, setSelectedConversationId] = useState<
    string | null
  >(null)
  const [streamingContent, setStreamingContent] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch conversations
  const { data: conversationsData, isLoading: loadingConversations } = useQuery({
    queryKey: ['conversations'],
    queryFn: async () => {
      const response = await chatApi.listConversations({ page_size: 50 })
      return response.data
    },
  })

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

  // Delete conversation mutation
  const deleteConversationMutation = useMutation({
    mutationFn: (conversationId: string) =>
      chatApi.deleteConversation(conversationId),
    onSuccess: (_, deletedId) => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
      if (selectedConversationId === deletedId) {
        setSelectedConversationId(null)
      }
    },
  })

  // Submit feedback mutation
  const submitFeedbackMutation = useMutation({
    mutationFn: ({ messageId, rating }: { messageId: string; rating: number }) =>
      chatApi.submitFeedback(messageId, { rating }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversation', selectedConversationId] })
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

    try {
      const response = await chatApi.sendMessageStream({
        conversation_id: selectedConversationId || undefined,
        message,
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
            // Streaming complete
            setIsStreaming(false)
            setStreamingContent('')

            // Refresh conversation data
            queryClient.invalidateQueries({ queryKey: ['conversations'] })
            queryClient.invalidateQueries({ queryKey: ['conversation', selectedConversationId] })

            // If new conversation was created, select it
            if (parsed.message_id && !selectedConversationId) {
              // Get the conversation ID from the message
              // We'll need to refetch conversations to get the new one
              queryClient.invalidateQueries({ queryKey: ['conversations'] })
            }
          } else if (parsed.type === 'error' && parsed.error) {
            setError(parsed.error)
            setIsStreaming(false)
          }
        }
      }
    } catch (err) {
      console.error('Error sending message:', err)
      setError(err instanceof Error ? err.message : 'Failed to send message')
      setIsStreaming(false)
      setStreamingContent('')
    }
  }

  const handleNewConversation = () => {
    setSelectedConversationId(null)
  }

  const handleViewDocument = (documentId: string) => {
    navigate(`/documents?id=${documentId}`)
  }

  const conversations = conversationsData?.conversations || []
  const messages = conversationData?.messages || []

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
          />
        </div>

        {/* Main chat area */}
        <div className="flex flex-1 flex-col">
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
            onSubmitFeedback={(messageId, rating) =>
              submitFeedbackMutation.mutate({ messageId, rating })
            }
            onViewDocument={handleViewDocument}
          />

          <MessageInput
            onSendMessage={handleSendMessage}
            disabled={isStreaming || loadingMessages}
            placeholder={
              selectedConversationId
                ? 'Ask a follow-up question...'
                : 'Start a new conversation...'
            }
          />
        </div>
      </div>
    </DashboardLayout>
  )
}
