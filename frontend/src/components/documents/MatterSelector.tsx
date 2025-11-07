// Matter selector with create new matter functionality

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { mattersApi } from '@/lib/api'
import { Matter, MatterCreate, MATTER_STATUSES } from '@/types/documents'
import { Plus, Check, AlertCircle } from 'lucide-react'

interface MatterSelectorProps {
  value: string | null
  onChange: (matterId: string) => void
  error?: string
}

export default function MatterSelector({ value, onChange, error }: MatterSelectorProps) {
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [createFormData, setCreateFormData] = useState<MatterCreate>({
    matter_number: '',
    client_name: '',
    matter_type: '',
    matter_status: 'active',
    description: '',
    opened_date: new Date().toISOString().split('T')[0],
  })
  const [createError, setCreateError] = useState<string | null>(null)

  const queryClient = useQueryClient()

  // Fetch matters list
  const { data: mattersResponse, isLoading } = useQuery({
    queryKey: ['matters', 'active'],
    queryFn: async () => {
      const response = await mattersApi.list({ status: 'active' })
      return response.data
    },
  })

  const matters = mattersResponse?.matters || []

  // Create matter mutation
  const createMutation = useMutation({
    mutationFn: (data: MatterCreate) => mattersApi.create(data),
    onSuccess: (response) => {
      const newMatter = response.data
      queryClient.invalidateQueries({ queryKey: ['matters'] })
      onChange(newMatter.id)
      setShowCreateForm(false)
      setCreateFormData({
        matter_number: '',
        client_name: '',
        matter_type: '',
        matter_status: 'active',
        description: '',
        opened_date: new Date().toISOString().split('T')[0],
      })
      setCreateError(null)
    },
    onError: (error: any) => {
      setCreateError(
        error.response?.data?.detail || 'Failed to create matter'
      )
    },
  })

  const handleCreateSubmit = () => {
    // Validate required fields
    if (!createFormData.matter_number || !createFormData.client_name || !createFormData.matter_type || !createFormData.opened_date) {
      setCreateError('Please fill in all required fields')
      return
    }

    setCreateError(null)
    createMutation.mutate(createFormData)
  }

  if (isLoading) {
    return (
      <div className="animate-pulse">
        <div className="h-10 bg-gray-200 rounded-md"></div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Matter selector */}
      {!showCreateForm && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Matter <span className="text-red-500">*</span>
          </label>
          <div className="flex gap-2">
            <select
              value={value || ''}
              onChange={(e) => onChange(e.target.value)}
              className={`flex-1 block w-full rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm ${
                error
                  ? 'border-red-300 text-red-900 focus:ring-red-500 focus:border-red-500'
                  : 'border-gray-300'
              }`}
            >
              <option value="">Select a matter...</option>
              {matters.map((matter: Matter) => (
                <option key={matter.id} value={matter.id}>
                  {matter.matter_number} - {matter.client_name}
                </option>
              ))}
            </select>
            <button
              type="button"
              onClick={() => setShowCreateForm(true)}
              className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              title="Create new matter"
            >
              <Plus className="h-4 w-4" />
            </button>
          </div>
          {error && (
            <p className="mt-2 text-sm text-red-600 flex items-center">
              <AlertCircle className="h-4 w-4 mr-1" />
              {error}
            </p>
          )}
        </div>
      )}

      {/* Create new matter form */}
      {showCreateForm && (
        <div className="border border-gray-300 rounded-md p-4 bg-gray-50">
          <h3 className="text-sm font-medium text-gray-900 mb-4">
            Create New Matter
          </h3>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Matter Number <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={createFormData.matter_number}
                  onChange={(e) =>
                    setCreateFormData({
                      ...createFormData,
                      matter_number: e.target.value,
                    })
                  }
                  placeholder="e.g., 2024-001"
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Client Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={createFormData.client_name}
                  onChange={(e) =>
                    setCreateFormData({
                      ...createFormData,
                      client_name: e.target.value,
                    })
                  }
                  placeholder="e.g., John Doe"
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Matter Type <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={createFormData.matter_type}
                  onChange={(e) =>
                    setCreateFormData({
                      ...createFormData,
                      matter_type: e.target.value,
                    })
                  }
                  placeholder="e.g., Personal Injury, Contract Dispute"
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Opened Date <span className="text-red-500">*</span>
                </label>
                <input
                  type="date"
                  required
                  value={createFormData.opened_date}
                  onChange={(e) =>
                    setCreateFormData({
                      ...createFormData,
                      opened_date: e.target.value,
                    })
                  }
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Matter Description
              </label>
              <textarea
                value={createFormData.description || ''}
                onChange={(e) =>
                  setCreateFormData({
                    ...createFormData,
                    description: e.target.value,
                  })
                }
                placeholder="Brief description of the matter (optional)"
                rows={3}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              />
            </div>

            {createError && (
              <div className="rounded-md bg-red-50 p-4">
                <p className="text-sm text-red-700 flex items-center">
                  <AlertCircle className="h-4 w-4 mr-2" />
                  {createError}
                </p>
              </div>
            )}

            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => {
                  setShowCreateForm(false)
                  setCreateError(null)
                }}
                disabled={createMutation.isPending}
                className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleCreateSubmit}
                disabled={createMutation.isPending}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
              >
                {createMutation.isPending ? (
                  'Creating...'
                ) : (
                  <>
                    <Check className="h-4 w-4 mr-2" />
                    Create Matter
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
