// Billable hours type definitions

export interface BillableSession {
  id: string
  user_id: string
  company_id: string
  conversation_id: string
  conversation_title?: string
  matter_id?: string
  matter_name?: string

  // Timing
  started_at: string
  ended_at?: string
  duration_minutes?: number

  // Descriptions
  ai_description?: string
  description?: string

  // Billing details
  activity_code?: string
  is_billable: boolean
  is_exported: boolean
  exported_at?: string

  // Audit
  created_at: string
  updated_at?: string
}

export interface BillableSessionCreate {
  conversation_id: string
  generate_description?: boolean
}

export interface BillableSessionUpdate {
  description?: string
  duration_minutes?: number
  activity_code?: string
  is_billable?: boolean
  matter_id?: string
}

export interface BillableSessionListResponse {
  sessions: BillableSession[]
  total: number
  page: number
  page_size: number
  total_minutes: number
}
