// Workspace type definitions matching backend schemas

export interface WorkspaceMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export interface WorkspaceResponse {
  id: string
  claim_id: string
  workspace_md: string
  last_discovery_at?: string
  known_document_ids: string[]
  has_document_changes: boolean
  new_document_count: number
  created_at: string
  updated_at?: string
}

export interface WorkspaceWithHistory extends WorkspaceResponse {
  messages: WorkspaceMessage[]
}

export interface WorkspaceUpdateRequest {
  markdown: string
}

export interface WorkspaceDiscoverRequest {
  discovery_mode?: 'sred_first' | 'names_only' | 'clustering_only' | 'hybrid'
  generate_narratives?: boolean
  min_cluster_size?: number
}

export interface WorkspaceDiscoverResponse {
  workspace_id: string
  workspace_md: string
  projects_discovered: number
  high_confidence_count: number
  medium_confidence_count: number
  low_confidence_count: number
  orphan_count: number
  document_ids: string[]
}

export interface WorkspaceChatRequest {
  message: string
  stream?: boolean
}

export interface WorkspaceChatResponse {
  message_id: string
  content: string
  workspace_md: string
  workspace_was_edited: boolean
}

export interface ParsedProject {
  name: string
  start_date?: string
  end_date?: string
  contributors: Record<string, string>[]
  document_count: number
  has_narrative: boolean
}

export interface WorkspaceParseResponse {
  projects: ParsedProject[]
  parse_errors: string[]
}

export interface WorkspaceStreamChunk {
  type: 'content' | 'workspace_update' | 'done' | 'error'
  content?: string
  workspace_update?: string
  message_id?: string
  workspace_was_edited?: boolean
  error?: string
}
