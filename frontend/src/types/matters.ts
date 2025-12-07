// Matter/Case type definitions

export interface Matter {
  id: string
  company_id: string
  matter_number: string
  client_name: string
  matter_type: string
  matter_status: string
  description: string | null
  opened_date: string // ISO date string
  closed_date: string | null // ISO date string
  lead_attorney_user_id: string | null
  created_at: string
  created_by: string
  updated_at: string | null
  updated_by: string
  // Current user's permissions (from MatterWithDetails)
  user_can_upload?: boolean
  user_can_edit?: boolean
  user_can_delete?: boolean
}

export interface MatterCreate {
  matter_number: string
  client_name: string
  matter_type: string
  matter_status?: string
  description?: string
  opened_date: string // ISO date string YYYY-MM-DD
  closed_date?: string | null
  lead_attorney_user_id?: string | null
}

export interface MatterUpdate {
  matter_number?: string
  client_name?: string
  matter_type?: string
  matter_status?: string
  description?: string
  opened_date?: string
  closed_date?: string | null
  lead_attorney_user_id?: string | null
}

export interface MatterListResponse {
  matters: Matter[]
  total: number
  page: number
  size: number
  pages: number
}

// Matter type options (from backend)
export const MATTER_TYPES = [
  'Civil Litigation',
  'Family Law',
  'Real Estate',
  'Corporate',
  'Employment',
  'Criminal Defense',
  'Estate Planning',
  'Immigration',
  'Personal Injury',
  'Other',
] as const

export type MatterType = typeof MATTER_TYPES[number]

// Matter status options
export const MATTER_STATUSES = [
  'active',
  'pending',
  'closed',
  'on_hold',
] as const

export type MatterStatus = typeof MATTER_STATUSES[number]
