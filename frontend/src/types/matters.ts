// Matter/Case type definitions (maps to backend API)

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

// SR&ED Project Type options
// These represent the categories of R&D projects eligible for SR&ED tax credits
export const PROJECT_TYPES = [
  'Software Development',
  'Manufacturing Process',
  'Product Design',
  'Chemical/Biological',
  'Engineering',
  'Other',
] as const

export type ProjectType = typeof PROJECT_TYPES[number]

// Legacy alias for compatibility with backend API
export const MATTER_TYPES = PROJECT_TYPES
export type MatterType = ProjectType

// SR&ED Claim Status options
// These track the lifecycle of an SR&ED claim from draft to final resolution
export const CLAIM_STATUSES = [
  'draft',
  'in_progress',
  'under_review',
  'submitted',
  'approved',
  'rejected',
] as const

export type ClaimStatus = typeof CLAIM_STATUSES[number]

// Legacy alias for compatibility with backend API
export const MATTER_STATUSES = CLAIM_STATUSES
export type MatterStatus = ClaimStatus
