// ConversationList component - Shows list of user's conversations

import { MessageSquare, Pin, Trash2, Archive } from 'lucide-react'
import type { Conversation } from '@/types/chat'
import Button from '@/components/ui/Button'

interface ConversationListProps {
  conversations: Conversation[]
  selectedConversationId?: string
  onSelectConversation: (conversationId: string) => void
  onDeleteConversation: (conversationId: string) => void
  onNewConversation: () => void
  loading?: boolean
}

export default function ConversationList({
  conversations,
  selectedConversationId,
  onSelectConversation,
  onDeleteConversation,
  onNewConversation,
  loading = false,
}: ConversationListProps) {
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  const truncateText = (text: string, maxLength: number) => {
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength) + '...'
  }

  return (
    <div className="flex h-full flex-col border-r border-gray-200 bg-white">
      {/* Header */}
      <div className="border-b border-gray-200 p-4">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Conversations</h2>
          <Button
            onClick={onNewConversation}
            variant="primary"
            size="sm"
          >
            New Chat
          </Button>
        </div>
      </div>

      {/* Conversation list */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center p-8">
            <div className="text-sm text-gray-500">Loading conversations...</div>
          </div>
        ) : conversations.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-8 text-center">
            <MessageSquare className="h-12 w-12 text-gray-300" />
            <p className="mt-2 text-sm text-gray-500">No conversations yet</p>
            <p className="mt-1 text-xs text-gray-400">
              Start a new chat to begin
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {conversations.map((conversation) => (
              <div
                key={conversation.id}
                onClick={() => onSelectConversation(conversation.id)}
                className={`w-full cursor-pointer px-4 py-3 text-left transition-colors hover:bg-gray-50 ${
                  selectedConversationId === conversation.id
                    ? 'bg-blue-50 hover:bg-blue-50'
                    : ''
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      {conversation.is_pinned && (
                        <Pin className="h-3 w-3 flex-shrink-0 text-blue-600" />
                      )}
                      <h3 className="truncate text-sm font-medium text-gray-900">
                        {conversation.title || 'New Conversation'}
                      </h3>
                    </div>
                    {conversation.last_message_preview && (
                      <p className="mt-1 text-xs text-gray-500">
                        {truncateText(conversation.last_message_preview, 80)}
                      </p>
                    )}
                    <div className="mt-1 flex items-center gap-2 text-xs text-gray-400">
                      <span>
                        {formatDate(conversation.updated_at || conversation.created_at)}
                      </span>
                      {conversation.message_count !== undefined && (
                        <>
                          <span>•</span>
                          <span>{conversation.message_count} messages</span>
                        </>
                      )}
                    </div>
                  </div>
                  <div className="flex flex-shrink-0 items-center gap-1">
                    {conversation.is_archived && (
                      <Archive className="h-3 w-3 text-gray-400" />
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        if (
                          window.confirm(
                            'Are you sure you want to delete this conversation?'
                          )
                        ) {
                          onDeleteConversation(conversation.id)
                        }
                      }}
                      className="rounded p-1 text-gray-400 hover:bg-red-50 hover:text-red-600"
                      title="Delete conversation"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
