// Timeline types for document events

export type DatePrecision = 'day' | 'month' | 'year' | 'unknown'
export type ConfidenceLevel = 'high' | 'medium' | 'low'

export interface DocumentEvent {
  id: string
  company_id: string
  matter_id?: string
  document_id: string
  chunk_id?: string
  event_date: string // ISO date string
  event_description: string
  date_precision: DatePrecision
  confidence: ConfidenceLevel
  raw_date_text?: string
  is_user_created: boolean
  is_user_modified: boolean
  user_notes?: string
  document_version?: number
  superseded_at?: string
  created_at: string
  updated_at?: string
  created_by?: string
}

export interface DocumentEventWithContext extends DocumentEvent {
  document_title?: string
  document_filename?: string
  matter_name?: string
  matter_number?: string
  chunk_content?: string
}

export interface DocumentEventCreate {
  document_id: string
  event_date: string
  event_description: string
  date_precision?: DatePrecision
  confidence?: ConfidenceLevel
  raw_date_text?: string
  user_notes?: string
  matter_id?: string
}

export interface DocumentEventUpdate {
  event_date?: string
  event_description?: string
  date_precision?: DatePrecision
  confidence?: ConfidenceLevel
  user_notes?: string
}

export interface TimelineListResponse {
  events: DocumentEventWithContext[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}

export interface TimelineQuery {
  matter_id?: string
  document_id?: string
  date_from?: string
  date_to?: string
  confidence?: ConfidenceLevel
  include_superseded?: boolean
  user_created_only?: boolean
  page?: number
  page_size?: number
}
