// Claim type definitions (maps to backend API)

export interface Claim {
  id: string
  company_id: string
  // SR&ED field names
  claim_number: string
  company_name: string
  project_type: string
  claim_status: string
  // Common fields
  description: string | null
  opened_date: string // ISO date string
  closed_date: string | null // ISO date string
  lead_consultant_user_id: string | null
  // SR&ED-specific fields
  fiscal_year_end?: string | null
  naics_code?: string | null
  cra_business_number?: string | null
  total_eligible_expenditures?: number | null
  federal_credit_estimate?: number | null
  provincial_credit_estimate?: number | null
  // Project-specific fields (for AI context in T661 generation)
  project_title?: string | null
  project_objective?: string | null
  technology_focus?: string | null
  // Audit fields
  created_at: string
  created_by: string
  updated_at: string | null
  updated_by: string
  // Current user's permissions (from ClaimWithDetails)
  user_can_upload?: boolean
  user_can_edit?: boolean
  user_can_delete?: boolean
}

export interface ClaimCreate {
  claim_number: string
  company_name: string
  project_type: string
  claim_status?: string
  description?: string
  opened_date: string // ISO date string YYYY-MM-DD
  closed_date?: string | null
  lead_consultant_user_id?: string | null
  fiscal_year_end?: string | null
  naics_code?: string | null
  cra_business_number?: string | null
  // Project-specific fields (for AI context in T661 generation)
  project_title?: string | null
  project_objective?: string | null
  technology_focus?: string | null
}

export interface ClaimUpdate {
  claim_number?: string
  company_name?: string
  project_type?: string
  claim_status?: string
  description?: string
  opened_date?: string
  closed_date?: string | null
  lead_consultant_user_id?: string | null
  fiscal_year_end?: string | null
  naics_code?: string | null
  cra_business_number?: string | null
  total_eligible_expenditures?: number | null
  federal_credit_estimate?: number | null
  provincial_credit_estimate?: number | null
  // Project-specific fields (for AI context in T661 generation)
  project_title?: string | null
  project_objective?: string | null
  technology_focus?: string | null
}

export interface ClaimListResponse {
  claims: Claim[]
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
