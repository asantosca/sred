// ConversationList component - Shows list of user's conversations

import { useState } from 'react'
import { MessageSquare, Pin, Trash2, Archive, Briefcase, Search, X, Filter } from 'lucide-react'
import type { Conversation } from '@/types/chat'
import Button from '@/components/ui/Button'

interface Matter {
  id: string
  matter_number: string
  client_name: string
}

interface ConversationListProps {
  conversations: Conversation[]
  selectedConversationId?: string
  onSelectConversation: (conversationId: string) => void
  onDeleteConversation: (conversationId: string) => void
  onNewConversation: () => void
  loading?: boolean
  onSearch?: (query: string) => void
  searchResults?: Conversation[]
  isSearching?: boolean
  matters?: Matter[]
  selectedMatterFilter?: string | null
  onMatterFilterChange?: (matterId: string | null) => void
}

export default function ConversationList({
  conversations,
  selectedConversationId,
  onSelectConversation,
  onDeleteConversation,
  onNewConversation,
  loading = false,
  onSearch,
  searchResults,
  isSearching = false,
  matters = [],
  selectedMatterFilter,
  onMatterFilterChange,
}: ConversationListProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [showSearch, setShowSearch] = useState(false)
  const [showMatterFilter, setShowMatterFilter] = useState(false)
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

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim().length >= 2 && onSearch) {
      onSearch(searchQuery.trim())
    }
  }

  const clearSearch = () => {
    setSearchQuery('')
    setShowSearch(false)
    if (onSearch) {
      onSearch('')
    }
  }

  // Use search results if available, otherwise use conversations
  const displayConversations = searchQuery && searchResults ? searchResults : conversations

  return (
    <div className="flex h-full flex-col border-r border-gray-200 bg-white">
      {/* Header */}
      <div className="border-b border-gray-200 p-4">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Conversations</h2>
          <div className="flex items-center gap-2">
            {onMatterFilterChange && matters.length > 0 && (
              <button
                onClick={() => setShowMatterFilter(!showMatterFilter)}
                className={`rounded p-1.5 transition-colors ${
                  showMatterFilter || selectedMatterFilter
                    ? 'bg-blue-100 text-blue-600'
                    : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700'
                }`}
                title="Filter by matter"
              >
                <Filter className="h-4 w-4" />
              </button>
            )}
            {onSearch && (
              <button
                onClick={() => setShowSearch(!showSearch)}
                className={`rounded p-1.5 transition-colors ${
                  showSearch
                    ? 'bg-blue-100 text-blue-600'
                    : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700'
                }`}
                title="Search conversations"
              >
                <Search className="h-4 w-4" />
              </button>
            )}
            <Button
              onClick={onNewConversation}
              variant="primary"
              size="sm"
            >
              New Chat
            </Button>
          </div>
        </div>

        {/* Matter filter dropdown */}
        {showMatterFilter && onMatterFilterChange && (
          <div className="mb-3">
            <select
              value={selectedMatterFilter || ''}
              onChange={(e) => onMatterFilterChange(e.target.value || null)}
              className="w-full rounded-md border border-gray-300 py-2 px-3 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="">All Matters</option>
              {matters.map((matter) => (
                <option key={matter.id} value={matter.id}>
                  {matter.matter_number} - {matter.client_name}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Search input */}
        {showSearch && onSearch && (
          <form onSubmit={handleSearch} className="relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by topic, case, or keyword..."
              className="w-full rounded-md border border-gray-300 py-2 pl-3 pr-8 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              autoFocus
            />
            {searchQuery && (
              <button
                type="button"
                onClick={clearSearch}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </form>
        )}
      </div>

      {/* Conversation list */}
      <div className="flex-1 overflow-y-auto">
        {loading || isSearching ? (
          <div className="flex items-center justify-center p-8">
            <div className="text-sm text-gray-500">
              {isSearching ? 'Searching...' : 'Loading conversations...'}
            </div>
          </div>
        ) : displayConversations.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-8 text-center">
            <MessageSquare className="h-12 w-12 text-gray-300" />
            <p className="mt-2 text-sm text-gray-500">
              {searchQuery ? 'No conversations found' : 'No conversations yet'}
            </p>
            <p className="mt-1 text-xs text-gray-400">
              {searchQuery ? 'Try different keywords' : 'Start a new chat to begin'}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {searchQuery && (
              <div className="bg-blue-50 px-4 py-2 text-xs text-blue-700">
                Found {displayConversations.length} conversation{displayConversations.length !== 1 ? 's' : ''} matching "{searchQuery}"
              </div>
            )}
            {displayConversations.map((conversation) => (
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
                    {conversation.matter_name && (
                      <div className="mt-1 flex items-center gap-1">
                        <span className="inline-flex items-center gap-1 rounded bg-blue-50 px-1.5 py-0.5 text-xs font-medium text-blue-700">
                          <Briefcase className="h-3 w-3" />
                          {truncateText(conversation.matter_name, 25)}
                        </span>
                      </div>
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
