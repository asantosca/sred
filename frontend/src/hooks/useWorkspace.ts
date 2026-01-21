// React Query hooks for Project Workspace

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState, useCallback, useRef } from 'react'
import { workspaceApi } from '@/lib/api'
import type {
  WorkspaceDiscoverRequest,
  WorkspaceStreamChunk,
} from '@/types/workspace'

// Query keys
export const workspaceKeys = {
  all: ['workspace'] as const,
  detail: (claimId: string) => [...workspaceKeys.all, claimId] as const,
  parse: (claimId: string) => [...workspaceKeys.all, 'parse', claimId] as const,
}

// Hook to get workspace for a claim
export function useWorkspace(claimId: string | undefined) {
  return useQuery({
    queryKey: workspaceKeys.detail(claimId || ''),
    queryFn: () => workspaceApi.get(claimId!).then(res => res.data),
    enabled: !!claimId,
  })
}

// Hook to update workspace markdown
export function useUpdateWorkspace() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ claimId, markdown }: { claimId: string; markdown: string }) =>
      workspaceApi.update(claimId, { markdown }).then(res => res.data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: workspaceKeys.detail(variables.claimId) })
    },
  })
}

// Hook to run discovery
export function useDiscovery() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ claimId, options }: { claimId: string; options?: WorkspaceDiscoverRequest }) =>
      workspaceApi.discover(claimId, options).then(res => res.data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: workspaceKeys.detail(variables.claimId) })
    },
  })
}

// Hook to parse workspace markdown
export function useParseWorkspace(claimId: string | undefined) {
  return useQuery({
    queryKey: workspaceKeys.parse(claimId || ''),
    queryFn: () => workspaceApi.parse(claimId!).then(res => res.data),
    enabled: !!claimId,
  })
}

// Hook for workspace chat with streaming
export function useWorkspaceChat(claimId: string | undefined) {
  const queryClient = useQueryClient()
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const [error, setError] = useState<string | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  const sendMessage = useCallback(async (
    message: string,
    onWorkspaceUpdate?: (newMarkdown: string) => void
  ): Promise<{
    messageId: string
    content: string
    workspaceWasEdited: boolean
  }> => {
    if (!claimId) {
      throw new Error('No claim ID provided')
    }

    setIsStreaming(true)
    setStreamingContent('')
    setError(null)

    abortControllerRef.current = new AbortController()

    try {
      const response = await workspaceApi.chatStream(claimId, { message, stream: true })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(errorText || `HTTP ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('No response body')
      }

      const decoder = new TextDecoder()
      let content = ''
      let messageId = ''
      let workspaceWasEdited = false

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6)) as WorkspaceStreamChunk

              if (data.type === 'content' && data.content) {
                content += data.content
                setStreamingContent(content)
              } else if (data.type === 'workspace_update' && data.workspace_update) {
                onWorkspaceUpdate?.(data.workspace_update)
                workspaceWasEdited = true
              } else if (data.type === 'done') {
                messageId = data.message_id || ''
                workspaceWasEdited = data.workspace_was_edited || workspaceWasEdited
              } else if (data.type === 'error') {
                throw new Error(data.error || 'Unknown streaming error')
              }
            } catch (parseError) {
              // Ignore parse errors for incomplete chunks
            }
          }
        }
      }

      // Always invalidate workspace query to refresh messages
      // (even if workspace wasn't edited, the new messages need to be fetched)
      queryClient.invalidateQueries({ queryKey: workspaceKeys.detail(claimId) })

      return { messageId, content, workspaceWasEdited }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      setError(errorMessage)
      throw err
    } finally {
      setIsStreaming(false)
      abortControllerRef.current = null
    }
  }, [claimId, queryClient])

  const cancelStream = useCallback(() => {
    abortControllerRef.current?.abort()
    setIsStreaming(false)
  }, [])

  return {
    sendMessage,
    cancelStream,
    isStreaming,
    streamingContent,
    error,
  }
}

// Combined hook for managing workspace state
export function useWorkspaceState(claimId: string | undefined) {
  const { data: workspace, isLoading, refetch } = useWorkspace(claimId)
  const updateMutation = useUpdateWorkspace()
  const discoveryMutation = useDiscovery()
  const chat = useWorkspaceChat(claimId)

  const [localMarkdown, setLocalMarkdown] = useState<string | null>(null)

  // Sync local markdown with server when workspace loads
  const markdown = localMarkdown ?? workspace?.workspace_md ?? ''

  const updateMarkdown = useCallback((newMarkdown: string) => {
    setLocalMarkdown(newMarkdown)
  }, [])

  const saveMarkdown = useCallback(async () => {
    if (!claimId || localMarkdown === null) return
    await updateMutation.mutateAsync({ claimId, markdown: localMarkdown })
    setLocalMarkdown(null) // Reset local state after save
  }, [claimId, localMarkdown, updateMutation])

  const runDiscovery = useCallback(async (options?: WorkspaceDiscoverRequest) => {
    if (!claimId) return
    const result = await discoveryMutation.mutateAsync({ claimId, options })
    setLocalMarkdown(result.workspace_md)
    return result
  }, [claimId, discoveryMutation])

  const sendChatMessage = useCallback(async (message: string) => {
    const result = await chat.sendMessage(message, (newMarkdown) => {
      setLocalMarkdown(newMarkdown)
    })

    // Add message to optimistic UI
    return result
  }, [chat])

  const hasUnsavedChanges = localMarkdown !== null && localMarkdown !== workspace?.workspace_md

  return {
    workspace,
    markdown,
    messages: workspace?.messages ?? [],
    isLoading,
    hasUnsavedChanges,
    hasDocumentChanges: workspace?.has_document_changes ?? false,
    newDocumentCount: workspace?.new_document_count ?? 0,

    // Actions
    updateMarkdown,
    saveMarkdown,
    runDiscovery,
    sendChatMessage,
    refetch,

    // Chat state
    isStreaming: chat.isStreaming,
    streamingContent: chat.streamingContent,
    chatError: chat.error,

    // Mutation states
    isSaving: updateMutation.isPending,
    isDiscovering: discoveryMutation.isPending,
  }
}
