// WorkspacePage - Split view for project discovery workspace

import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Download, AlertCircle } from 'lucide-react'
import DashboardLayout from '@/components/layout/DashboardLayout'
import Button from '@/components/ui/Button'
import WorkspaceEditor from '@/components/workspace/WorkspaceEditor'
import WorkspaceChat from '@/components/workspace/WorkspaceChat'
import { useWorkspaceState } from '@/hooks/useWorkspace'
import { claimsApi } from '@/lib/api'
import type { Claim } from '@/types/claims'

export default function WorkspacePage() {
  const { claimId } = useParams<{ claimId: string }>()
  const navigate = useNavigate()

  const [claim, setClaim] = useState<Claim | null>(null)
  const [claimLoading, setClaimLoading] = useState(true)
  const [claimError, setClaimError] = useState<string | null>(null)

  const {
    workspace,
    markdown,
    messages,
    isLoading,
    hasUnsavedChanges,
    updateMarkdown,
    saveMarkdown,
    sendChatMessage,
    isStreaming,
    streamingContent,
    chatError,
    isSaving,
  } = useWorkspaceState(claimId)

  // Fetch claim details
  useEffect(() => {
    if (!claimId) return

    const fetchClaim = async () => {
      try {
        setClaimLoading(true)
        setClaimError(null)
        const response = await claimsApi.get(claimId)
        setClaim(response.data)
      } catch (err: any) {
        setClaimError(err.response?.data?.detail || 'Failed to load claim')
      } finally {
        setClaimLoading(false)
      }
    }

    fetchClaim()
  }, [claimId])

  // Handle discard changes
  const handleDiscard = () => {
    if (workspace?.workspace_md !== undefined) {
      updateMarkdown(workspace.workspace_md)
    }
  }

  // Handle export
  const handleExport = () => {
    const blob = new Blob([markdown], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${claim?.company_name || 'workspace'}-projects.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  // Loading state
  if (claimLoading || isLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-purple-600 border-r-transparent"></div>
          <span className="ml-3 text-gray-600">Loading workspace...</span>
        </div>
      </DashboardLayout>
    )
  }

  // Error state
  if (claimError) {
    return (
      <DashboardLayout>
        <div className="max-w-3xl mx-auto p-6">
          <div className="bg-red-50 border border-red-200 text-red-800 rounded-md p-4">
            <div className="flex items-start">
              <AlertCircle className="h-5 w-5 mr-2 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium">Error loading workspace</p>
                <p className="text-sm mt-1">{claimError}</p>
              </div>
            </div>
          </div>
          <Button
            variant="secondary"
            onClick={() => navigate(-1)}
            className="mt-4"
            icon={<ArrowLeft className="h-4 w-4" />}
          >
            Go Back
          </Button>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="h-[calc(100vh-4rem)] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-white">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate(`/claims/${claimId}`)}
              className="flex items-center text-sm text-gray-600 hover:text-gray-900"
            >
              <ArrowLeft className="h-4 w-4 mr-1" />
              Back to Claim
            </button>
            <div className="h-4 w-px bg-gray-300" />
            <div>
              <h1 className="text-lg font-semibold text-gray-900">
                Project Workspace
              </h1>
              <p className="text-sm text-gray-500">
                {claim?.company_name} - FY {claim?.fiscal_year_end ? new Date(claim.fiscal_year_end).getFullYear() : 'N/A'}
              </p>
            </div>
          </div>
          <Button
            variant="secondary"
            size="sm"
            onClick={handleExport}
            icon={<Download className="h-4 w-4" />}
            disabled={!markdown}
          >
            Export
          </Button>
        </div>

        {/* Split View */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left: Markdown Editor (60%) */}
          <div className="w-3/5 border-r border-gray-200">
            <WorkspaceEditor
              markdown={markdown}
              onChange={updateMarkdown}
              onSave={saveMarkdown}
              onDiscard={handleDiscard}
              hasUnsavedChanges={hasUnsavedChanges}
              isSaving={isSaving}
            />
          </div>

          {/* Right: Chat Panel (40%) */}
          <div className="w-2/5">
            <WorkspaceChat
              messages={messages}
              onSendMessage={sendChatMessage}
              isStreaming={isStreaming}
              streamingContent={streamingContent}
              error={chatError}
            />
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
