// BillablePage - Billable hours tracking and management

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { billableApi } from '@/lib/api'
import type { BillableSession, BillableSessionUpdate } from '@/types/billable'
import {
  Clock,
  Briefcase,
  Edit2,
  Trash2,
  RefreshCw,
  Check,
  X,
  MessageSquare,
} from 'lucide-react'
import Button from '@/components/ui/Button'

export default function BillablePage() {
  const queryClient = useQueryClient()
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editForm, setEditForm] = useState<BillableSessionUpdate>({})
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [includeExported, setIncludeExported] = useState(false)

  // Fetch billable sessions
  const { data, isLoading } = useQuery({
    queryKey: ['billable-sessions', includeExported],
    queryFn: async () => {
      const response = await billableApi.list({
        page_size: 100,
        include_exported: includeExported,
      })
      return response.data
    },
  })

  // Update session mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: BillableSessionUpdate }) =>
      billableApi.update(id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['billable-sessions'] })
      toast.success('Session updated')
      setEditingId(null)
      setEditForm({})
    },
    onError: () => {
      toast.error('Failed to update session')
    },
  })

  // Delete session mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => billableApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['billable-sessions'] })
      toast.success('Session deleted')
    },
    onError: () => {
      toast.error('Failed to delete session')
    },
  })

  // Regenerate description mutation
  const regenerateMutation = useMutation({
    mutationFn: (id: string) => billableApi.regenerateDescription(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['billable-sessions'] })
      toast.success('Description regenerated')
    },
    onError: () => {
      toast.error('Failed to regenerate description')
    },
  })

  // Export sessions mutation
  const exportMutation = useMutation({
    mutationFn: (ids: string[]) => billableApi.export(ids),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['billable-sessions'] })
      toast.success(`Marked ${response.data.exported_count} session(s) as billed`)
      setSelectedIds(new Set())
    },
    onError: () => {
      toast.error('Failed to mark sessions as billed')
    },
  })

  const sessions = data?.sessions || []
  const totalMinutes = data?.total_minutes || 0
  const totalHours = Math.floor(totalMinutes / 60)
  const remainingMinutes = totalMinutes % 60

  const formatDuration = (minutes?: number) => {
    if (!minutes) return '-'
    const h = Math.floor(minutes / 60)
    const m = minutes % 60
    if (h > 0) {
      return `${h}h ${m}m`
    }
    return `${m}m`
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-CA', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  const handleEdit = (session: BillableSession) => {
    setEditingId(session.id)
    setEditForm({
      description: session.description || session.ai_description || '',
      duration_minutes: session.duration_minutes,
      is_billable: session.is_billable,
    })
  }

  const handleSaveEdit = (id: string) => {
    updateMutation.mutate({ id, updates: editForm })
  }

  const handleToggleSelect = (id: string) => {
    const newSelected = new Set(selectedIds)
    if (newSelected.has(id)) {
      newSelected.delete(id)
    } else {
      newSelected.add(id)
    }
    setSelectedIds(newSelected)
  }

  const handleSelectAll = () => {
    if (selectedIds.size === sessions.filter((s) => !s.is_exported).length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(sessions.filter((s) => !s.is_exported).map((s) => s.id)))
    }
  }

  const handleExport = () => {
    if (selectedIds.size > 0) {
      exportMutation.mutate(Array.from(selectedIds))
    }
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Billable Hours</h1>
            <p className="mt-1 text-sm text-gray-500">
              Track time spent on AI-assisted legal research
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-2xl font-bold text-gray-900">
                {totalHours}h {remainingMinutes}m
              </div>
              <div className="text-sm text-gray-500">Total billable time</div>
            </div>
          </div>
        </div>

        {/* Filters and Actions */}
        <div className="flex items-center justify-between rounded-lg bg-white p-4 shadow">
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={includeExported}
                onChange={(e) => setIncludeExported(e.target.checked)}
                className="rounded border-gray-300"
              />
              <span className="text-sm text-gray-700">Show billed</span>
            </label>
          </div>
          <div className="flex items-center gap-2">
            {selectedIds.size > 0 && (
              <Button
                variant="primary"
                onClick={handleExport}
                disabled={exportMutation.isPending}
              >
                <Check className="mr-2 h-4 w-4" />
                Mark {selectedIds.size} as Billed
              </Button>
            )}
          </div>
        </div>

        {/* Sessions Table */}
        <div className="overflow-hidden rounded-lg bg-white shadow">
          {isLoading ? (
            <div className="flex items-center justify-center p-8">
              <div className="text-gray-500">Loading sessions...</div>
            </div>
          ) : sessions.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-12 text-center">
              <Clock className="h-12 w-12 text-gray-300" />
              <h3 className="mt-4 text-lg font-medium text-gray-900">No billable sessions</h3>
              <p className="mt-2 text-sm text-gray-500">
                Billable sessions are created from your chat conversations.
                <br />
                Start a chat, then click the "Track Time" button in the conversation header.
              </p>
            </div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="w-12 px-4 py-3">
                    <input
                      type="checkbox"
                      checked={
                        selectedIds.size > 0 &&
                        selectedIds.size === sessions.filter((s) => !s.is_exported).length
                      }
                      onChange={handleSelectAll}
                      className="rounded border-gray-300"
                    />
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Date
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Conversation
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Matter
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Description
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                    Duration
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
                    Status
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {sessions.map((session) => (
                  <tr
                    key={session.id}
                    className={session.is_exported ? 'bg-gray-50' : undefined}
                  >
                    <td className="px-4 py-4">
                      <input
                        type="checkbox"
                        checked={selectedIds.has(session.id)}
                        onChange={() => handleToggleSelect(session.id)}
                        disabled={session.is_exported}
                        className="rounded border-gray-300 disabled:opacity-50"
                      />
                    </td>
                    <td className="whitespace-nowrap px-4 py-4 text-sm text-gray-900">
                      {formatDate(session.started_at)}
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-2">
                        <MessageSquare className="h-4 w-4 text-gray-400" />
                        <span className="text-sm text-gray-900">
                          {session.conversation_title || 'Untitled conversation'}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      {session.matter_name ? (
                        <div className="flex items-center gap-1">
                          <Briefcase className="h-4 w-4 text-blue-500" />
                          <span className="text-sm text-gray-900">{session.matter_name}</span>
                        </div>
                      ) : (
                        <span className="text-sm text-gray-400">-</span>
                      )}
                    </td>
                    <td className="max-w-md px-4 py-4">
                      {editingId === session.id ? (
                        <textarea
                          value={editForm.description || ''}
                          onChange={(e) =>
                            setEditForm({ ...editForm, description: e.target.value })
                          }
                          rows={2}
                          className="w-full rounded border-gray-300 text-sm"
                        />
                      ) : (
                        <p className="line-clamp-2 text-sm text-gray-700">
                          {session.description || session.ai_description || '-'}
                        </p>
                      )}
                    </td>
                    <td className="whitespace-nowrap px-4 py-4 text-right">
                      {editingId === session.id ? (
                        <input
                          type="number"
                          value={editForm.duration_minutes || ''}
                          onChange={(e) =>
                            setEditForm({
                              ...editForm,
                              duration_minutes: parseInt(e.target.value) || undefined,
                            })
                          }
                          className="w-20 rounded border-gray-300 text-right text-sm"
                          min={1}
                        />
                      ) : (
                        <span className="text-sm font-medium text-gray-900">
                          {formatDuration(session.duration_minutes)}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-4 text-center">
                      {session.is_exported ? (
                        <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
                          Billed
                        </span>
                      ) : session.is_billable ? (
                        <span className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800">
                          Billable
                        </span>
                      ) : (
                        <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-800">
                          Non-billable
                        </span>
                      )}
                    </td>
                    <td className="whitespace-nowrap px-4 py-4 text-right">
                      {editingId === session.id ? (
                        <div className="flex justify-end gap-1">
                          <button
                            onClick={() => handleSaveEdit(session.id)}
                            disabled={updateMutation.isPending}
                            className="rounded p-1 text-green-600 hover:bg-green-50"
                            title="Save"
                          >
                            <Check className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => {
                              setEditingId(null)
                              setEditForm({})
                            }}
                            className="rounded p-1 text-gray-600 hover:bg-gray-100"
                            title="Cancel"
                          >
                            <X className="h-4 w-4" />
                          </button>
                        </div>
                      ) : (
                        <div className="flex justify-end gap-1">
                          {!session.is_exported && (
                            <>
                              <button
                                onClick={() => handleEdit(session)}
                                className="rounded p-1 text-gray-600 hover:bg-gray-100"
                                title="Edit"
                              >
                                <Edit2 className="h-4 w-4" />
                              </button>
                              <button
                                onClick={() => regenerateMutation.mutate(session.id)}
                                disabled={regenerateMutation.isPending}
                                className="rounded p-1 text-gray-600 hover:bg-gray-100"
                                title="Regenerate description"
                              >
                                <RefreshCw className="h-4 w-4" />
                              </button>
                              <button
                                onClick={() => {
                                  if (
                                    window.confirm(
                                      'Are you sure you want to delete this session?'
                                    )
                                  ) {
                                    deleteMutation.mutate(session.id)
                                  }
                                }}
                                disabled={deleteMutation.isPending}
                                className="rounded p-1 text-red-600 hover:bg-red-50"
                                title="Delete"
                              >
                                <Trash2 className="h-4 w-4" />
                              </button>
                            </>
                          )}
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </DashboardLayout>
  )
}
