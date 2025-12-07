// Chat and conversation type definitions matching backend schemas

export interface MessageSource {
  document_id: string
  document_title: string
  chunk_id: string
  content: string
  page_number?: number
  similarity_score: number
  matter_id: string
  matter_name: string
}

export interface Message {
  id: string
  conversation_id: string
  role: 'user' | 'assistant'
  content: string
  sources?: MessageSource[]
  token_count?: number
  model_name?: string
  rating?: number
  feedback_text?: string
  created_at: string
}

export interface Conversation {
  id: string
  user_id: string
  company_id: string
  matter_id?: string
  matter_name?: string
  title?: string
  is_pinned: boolean
  is_archived: boolean
  created_at: string
  updated_at?: string
  message_count?: number
  last_message_preview?: string
}

export interface ConversationWithMessages extends Conversation {
  messages: Message[]
}

export interface ConversationListResponse {
  conversations: Conversation[]
  total: number
  page: number
  page_size: number
}

export interface ChatRequest {
  conversation_id?: string
  message: string
  matter_id?: string
  include_sources?: boolean
  max_context_chunks?: number
  similarity_threshold?: number
  stream?: boolean
}

export interface ChatResponse {
  conversation_id: string
  message: Message
  is_new_conversation: boolean
}

export interface ChatStreamChunk {
  type: 'content' | 'source' | 'done' | 'error'
  content?: string
  source?: MessageSource
  message_id?: string
  conversation_id?: string
  error?: string
}

export interface MessageFeedback {
  rating: number // -1 (thumbs down), 1 (thumbs up), or 1-5 stars
  feedback_text?: string
}

export interface ConversationUpdate {
  title?: string
  is_pinned?: boolean
  is_archived?: boolean
}
