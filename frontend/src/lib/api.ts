// API client with axios and auth interceptors

import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import type {
  AuthResponse,
  LoginRequest,
  RegistrationRequest,
  RegistrationResponse,
  PasswordResetRequest,
  PasswordResetConfirm,
  PasswordChange,
  UserProfileUpdate,
  AvatarUploadResponse,
  RefreshTokenRequest,
  Token,
} from '@/types/auth'

// Create axios instance
const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean
    }

    // If error is 401 and we haven't retried yet, try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const { data } = await axios.post<Token>('/api/v1/auth/refresh', {
            refresh_token: refreshToken,
          })

          // Update tokens in localStorage
          localStorage.setItem('access_token', data.access_token)
          if (data.refresh_token) {
            localStorage.setItem('refresh_token', data.refresh_token)
          }

          // Retry original request with new token
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${data.access_token}`
          }
          return api(originalRequest)
        } catch (refreshError) {
          // Refresh failed, clear tokens and redirect to login
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
          return Promise.reject(refreshError)
        }
      }
    }

    return Promise.reject(error)
  }
)

// Auth API endpoints
export const authApi = {
  // Login
  login: (data: LoginRequest) =>
    api.post<AuthResponse>('/auth/login', data),

  // Register new company
  register: (data: RegistrationRequest) =>
    api.post<RegistrationResponse>('/auth/register', data),

  // Get current user
  me: () => api.get<AuthResponse>('/auth/me'),

  // Logout
  logout: (refresh_token: string) =>
    api.post('/auth/logout', { refresh_token }),

  // Refresh token
  refresh: (data: RefreshTokenRequest) =>
    api.post<Token>('/auth/refresh', data),

  // Password reset request
  requestPasswordReset: (data: PasswordResetRequest) =>
    api.post('/auth/password-reset/request', data),

  // Verify password reset token
  verifyPasswordResetToken: (token: string) =>
    api.get(`/auth/password-reset/verify?token=${token}`),

  // Confirm password reset
  confirmPasswordReset: (data: PasswordResetConfirm) =>
    api.post<AuthResponse>('/auth/password-reset/confirm', data),

  // Verify email confirmation token
  verifyEmailConfirmationToken: (token: string) =>
    api.get(`/auth/confirm-email/verify?token=${token}`),

  // Confirm email (activate account)
  confirmEmail: (token: string) =>
    api.get<AuthResponse>(`/auth/confirm-email?token=${token}`),

  // Change password
  changePassword: (data: PasswordChange) =>
    api.post('/auth/change-password', data),
}

// User API endpoints
export const userApi = {
  // Get my profile
  getMyProfile: () => api.get('/users/me'),

  // Update my profile
  updateMyProfile: (data: UserProfileUpdate) =>
    api.patch('/users/me', data),

  // Upload avatar
  uploadAvatar: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post<AvatarUploadResponse>('/users/me/avatar', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },
}

// Matters API endpoints
export const mattersApi = {
  // List all matters
  list: (params?: { status?: string; page?: number; size?: number }) =>
    api.get('/matters/', { params }),

  // Get matter by ID
  get: (matterId: string) =>
    api.get(`/matters/${matterId}`),

  // Create new matter
  create: (data: any) =>
    api.post('/matters/', data),

  // Update matter
  update: (matterId: string, data: any) =>
    api.patch(`/matters/${matterId}`, data),

  // Delete matter
  delete: (matterId: string) =>
    api.delete(`/matters/${matterId}`),
}

// Documents API endpoints
export const documentsApi = {
  // List documents (all or filtered by matter)
  list: (params?: { matter_id?: string; page?: number; size?: number; document_type?: string }) =>
    api.get('/documents/', { params }),

  // Get document by ID
  get: (documentId: string) =>
    api.get(`/documents/${documentId}`),

  // Upload document (Quick Upload mode)
  upload: (file: File, metadata: any) => {
    const formData = new FormData()
    formData.append('file', file)

    // Append metadata as form fields
    Object.keys(metadata).forEach(key => {
      const value = metadata[key]
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          formData.append(key, JSON.stringify(value))
        } else {
          formData.append(key, value.toString())
        }
      }
    })

    return api.post('/documents/upload/quick', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },

  // Download document
  download: (documentId: string) =>
    api.get(`/documents/${documentId}/download`),

  // Delete document
  delete: (documentId: string) =>
    api.delete(`/documents/${documentId}`),

  // Update document metadata
  update: (documentId: string, data: {
    document_title?: string
    document_type?: string
    document_date?: string
    document_status?: string
    description?: string
    confidentiality_level?: string
    is_privileged?: boolean
    tags?: string[]
    internal_notes?: string
  }) => api.patch(`/documents/${documentId}`, data),
}

// Chat API endpoints
import type {
  ChatRequest,
  ChatResponse,
  ConversationListResponse,
  ConversationWithMessages,
  ConversationUpdate,
  MessageFeedback,
  Conversation,
} from '@/types/chat'

export const chatApi = {
  // List conversations
  listConversations: (params?: {
    page?: number
    page_size?: number
    include_archived?: boolean
    matter_id?: string
  }) =>
    api.get<ConversationListResponse>('/chat/conversations', { params }),

  // Search conversations
  searchConversations: (params: {
    q: string
    page?: number
    page_size?: number
  }) =>
    api.get<ConversationListResponse>('/chat/conversations/search', { params }),

  // Get conversation with messages
  getConversation: (conversationId: string) =>
    api.get<ConversationWithMessages>(`/chat/conversations/${conversationId}`),

  // Update conversation (title, pin, archive)
  updateConversation: (conversationId: string, data: ConversationUpdate) =>
    api.patch<Conversation>(`/chat/conversations/${conversationId}`, data),

  // Delete conversation
  deleteConversation: (conversationId: string) =>
    api.delete(`/chat/conversations/${conversationId}`),

  // Send message (non-streaming)
  sendMessage: (data: ChatRequest) =>
    api.post<ChatResponse>('/chat/message', data),

  // Send message with streaming (returns EventSource-compatible response)
  sendMessageStream: async (data: ChatRequest) => {
    const token = localStorage.getItem('access_token')

    if (!token) {
      throw new Error('No authentication token found. Please log in again.')
    }

    const response = await fetch('/api/v1/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    })

    // If 401, try to refresh token and retry
    if (response.status === 401) {
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          // Refresh the token
          const { data: tokenData } = await axios.post<Token>('/api/v1/auth/refresh', {
            refresh_token: refreshToken,
          })

          // Update tokens
          localStorage.setItem('access_token', tokenData.access_token)
          if (tokenData.refresh_token) {
            localStorage.setItem('refresh_token', tokenData.refresh_token)
          }

          // Retry with new token
          return fetch('/api/v1/chat/stream', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${tokenData.access_token}`,
            },
            body: JSON.stringify(data),
          })
        } catch (refreshError) {
          // Refresh failed, clear tokens and redirect
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
          throw new Error('Session expired. Please log in again.')
        }
      } else {
        // No refresh token, redirect to login
        window.location.href = '/login'
        throw new Error('Session expired. Please log in again.')
      }
    }

    return response
  },

  // Submit message feedback
  submitFeedback: (messageId: string, feedback: MessageFeedback) =>
    api.post(`/chat/messages/${messageId}/feedback`, feedback),

  // Link conversation to a matter (after AI suggestion)
  linkToMatter: (conversationId: string, matterId: string) =>
    api.post<{ success: boolean; conversation_id: string; matter_id: string; matter_name: string }>(
      `/chat/conversations/${conversationId}/link-matter`,
      { matter_id: matterId }
    ),

  // Send help desk message (platform assistance, no RAG)
  sendHelpMessage: (data: { message: string }) =>
    api.post<{ content: string }>('/chat/help', data),
}

// Usage API endpoints
export const usageApi = {
  // Get usage summary
  getSummary: () =>
    api.get('/usage/summary'),

  // Get detailed usage stats
  getStats: () =>
    api.get('/usage/stats'),

  // Get plan limits
  getLimits: () =>
    api.get('/usage/limits'),
}

// Briefing API endpoints
export interface BriefingResponse {
  briefing_date: string
  content: string
  generated_at: string
  is_fresh: boolean
}

export const briefingApi = {
  // Get today's briefing (generates if needed)
  getToday: (regenerate = false) =>
    api.get<BriefingResponse>('/briefing/today', { params: { regenerate } }),

  // Get past briefings
  getHistory: (limit = 7) =>
    api.get<BriefingResponse[]>('/briefing/history', { params: { limit } }),
}

// Billable hours API endpoints
import type {
  BillableSession,
  BillableSessionCreate,
  BillableSessionUpdate,
  BillableSessionListResponse,
} from '@/types/billable'

export const billableApi = {
  // Create billable session from conversation
  create: (data: BillableSessionCreate) =>
    api.post<BillableSession>('/billable', data),

  // List billable sessions
  list: (params?: {
    page?: number
    page_size?: number
    matter_id?: string
    include_exported?: boolean
    start_date?: string
    end_date?: string
  }) =>
    api.get<BillableSessionListResponse>('/billable', { params }),

  // Get single session
  get: (sessionId: string) =>
    api.get<BillableSession>(`/billable/${sessionId}`),

  // Update session
  update: (sessionId: string, data: BillableSessionUpdate) =>
    api.patch<BillableSession>(`/billable/${sessionId}`, data),

  // Delete session
  delete: (sessionId: string) =>
    api.delete(`/billable/${sessionId}`),

  // Regenerate AI description
  regenerateDescription: (sessionId: string) =>
    api.post<{ session_id: string; ai_description: string }>(
      `/billable/${sessionId}/regenerate-description`
    ),

  // Mark sessions as exported
  export: (sessionIds: string[]) =>
    api.post<{ exported_count: number; sessions: BillableSession[] }>(
      '/billable/export',
      { session_ids: sessionIds }
    ),

  // Get unbilled conversations (matter-scoped conversations without billable sessions)
  getUnbilled: (params?: { matter_id?: string }) =>
    api.get<{
      total_unbilled: number
      conversations: Array<{
        id: string
        title: string
        matter_id: string
        matter_name: string
        updated_at: string
        created_at: string
      }>
      by_matter: Array<{
        matter_id: string
        matter_name: string
        unbilled_count: number
      }>
    }>('/billable/unbilled/conversations', { params }),
}

// Timeline API endpoints
import type {
  DocumentEvent,
  DocumentEventWithContext,
  DocumentEventCreate,
  DocumentEventUpdate,
  TimelineListResponse,
  TimelineQuery,
} from '@/types/timeline'

export const timelineApi = {
  // List events with filters
  list: (params?: TimelineQuery) =>
    api.get<TimelineListResponse>('/timeline', { params }),

  // Get events for a specific matter
  listByMatter: (matterId: string, params?: Omit<TimelineQuery, 'matter_id'>) =>
    api.get<TimelineListResponse>(`/timeline/matter/${matterId}`, { params }),

  // Get events for a specific document
  listByDocument: (documentId: string, params?: { include_superseded?: boolean; page?: number; page_size?: number }) =>
    api.get<TimelineListResponse>(`/timeline/document/${documentId}`, { params }),

  // Get single event
  get: (eventId: string) =>
    api.get<DocumentEventWithContext>(`/timeline/${eventId}`),

  // Create event
  create: (data: DocumentEventCreate) =>
    api.post<DocumentEvent>('/timeline', data),

  // Update event
  update: (eventId: string, data: DocumentEventUpdate) =>
    api.patch<DocumentEvent>(`/timeline/${eventId}`, data),

  // Delete event
  delete: (eventId: string) =>
    api.delete(`/timeline/${eventId}`),
}

export default api
