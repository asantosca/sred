// Frontend types for documents and matters matching backend schemas

export interface Matter {
  id: string
  claim_number: string
  company_name: string
  project_type: string
  claim_status: string
  description: string | null
  opened_date: string
  closed_date: string | null
  lead_consultant_user_id: string | null
  company_id: string
  created_at: string
  updated_at: string | null
}

export interface MatterCreate {
  claim_number: string
  company_name: string
  project_type: string
  claim_status?: string
  description?: string
  opened_date: string
  closed_date?: string
  lead_consultant_user_id?: string
}

export interface MatterUpdate {
  claim_number?: string
  company_name?: string
  project_type?: string
  claim_status?: string
  description?: string
  opened_date?: string
  closed_date?: string
  lead_consultant_user_id?: string
}

export interface DocumentBase {
  id: string
  matter_id: string
  filename: string
  original_filename: string
  file_extension: string
  file_size_bytes: number
  file_hash: string
  mime_type: string | null

  // Classification
  document_type: string
  document_subtype: string | null
  document_title: string
  document_date: string
  document_status: string

  // Security
  confidentiality_level: string
  is_privileged: boolean

  // Processing status
  processing_status: string
  text_extracted: boolean
  indexed_for_search: boolean

  // Audit
  created_at: string
  created_by: string
  updated_at: string | null
  updated_by: string
}

export interface Document extends DocumentBase {
  // Optional metadata
  description: string | null
  date_received: string | null
  filed_date: string | null

  // AI-generated summary
  ai_summary: string | null
  ai_summary_generated_at: string | null

  // Version control
  is_current_version: boolean
  version_label: string | null
  version_number: number
  parent_document_id: string | null
  root_document_id: string | null

  // Security details
  privilege_attorney_client: boolean
  privilege_work_product: boolean
  privilege_settlement: boolean

  // Metadata
  internal_notes: string | null
  tags: string[] | null

  // Type-specific fields
  author: string | null
  recipient: string | null
  opposing_counsel: string | null
  opposing_party: string | null
  court_jurisdiction: string | null
  case_number: string | null
  judge_name: string | null
  contract_type: string | null
  contract_value: number | null
  contract_effective_date: string | null
  contract_expiration_date: string | null
  governing_law: string | null
  discovery_type: string | null
  propounding_party: string | null
  responding_party: string | null
  discovery_number: string | null
  response_due_date: string | null
  response_status: string | null
  exhibit_number: string | null
  correspondence_type: string | null
  cc: string | null
  subject: string | null
}

export interface DocumentWithMatter extends Document {
  claim_number: string
  company_name: string
  claim_status: string
}

export interface DocumentListResponse {
  documents: DocumentWithMatter[]
  total: number
  page: number
  size: number
  pages: number
  matter_id: string | null
}

// Quick Upload (5 required fields)
export interface QuickDocumentUpload {
  matter_id: string
  document_type: string
  document_title: string
  document_date: string
  confidentiality_level?: string
}

// Standard Upload (includes security and basic metadata)
export interface StandardDocumentUpload {
  matter_id: string
  document_title: string
  document_date: string
  document_status: string
  document_type: string
  document_subtype?: string

  // Security fields
  confidentiality_level?: string
  privilege_attorney_client?: boolean
  privilege_work_product?: boolean
  privilege_settlement?: boolean

  // Optional metadata
  description?: string
  internal_notes?: string
  tags?: string[]

  // Author/recipient info
  author?: string
  recipient?: string

  // Date fields
  date_received?: string
  filed_date?: string
}

export interface DocumentUploadResponse {
  document_id: string
  filename: string
  original_filename: string
  file_size_bytes: number
  document_title: string
  document_type: string
  matter_id: string
  storage_path: string
  file_hash: string
  upload_status: string
  message: string
  auto_detection_applied: boolean
  detected_enhancements: string[]
}

export interface DocumentDownloadResponse {
  download_url: string
  expires_at: string
  filename: string
  file_size_bytes: number
  mime_type: string
}

export interface FileValidationResult {
  valid: boolean
  errors: string[]
  file_extension: string
  mime_type: string
  file_size: number
}

// SR&ED Document type options
export const DOCUMENT_TYPES = [
  'Technical Report',
  'Lab Notebook',
  'Project Plan',
  'Timesheet',
  'Email',
  'Financial Record',
  'Invoice',
  'Meeting Notes',
  'Source Code',
  'Other'
] as const

export const DOCUMENT_STATUSES = [
  'draft',
  'final',
  'executed',
  'filed'
] as const

export const CONFIDENTIALITY_LEVELS = [
  'public',
  'internal',
  'standard_confidential',
  'highly_confidential',
  'attorney_eyes_only'
] as const

export const MATTER_STATUSES = [
  'active',
  'closed',
  'archived'
] as const
