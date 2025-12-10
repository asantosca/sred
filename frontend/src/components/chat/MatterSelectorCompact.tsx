// Compact matter selector for chat - shows as a dropdown above the message input

import { useQuery } from '@tanstack/react-query'
import { mattersApi } from '@/lib/api'
import { Briefcase, X } from 'lucide-react'
import type { Matter } from '@/types/documents'

interface MatterSelectorCompactProps {
  value: string | null
  onChange: (matterId: string | null) => void
  disabled?: boolean
}

export default function MatterSelectorCompact({
  value,
  onChange,
  disabled = false,
}: MatterSelectorCompactProps) {
  // Fetch matters list
  const { data: mattersResponse, isLoading } = useQuery({
    queryKey: ['matters', 'active'],
    queryFn: async () => {
      const response = await mattersApi.list({ status: 'active' })
      return response.data
    },
  })

  const matters = mattersResponse?.matters || []

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 px-4 py-2 text-sm text-gray-500">
        <Briefcase className="h-4 w-4 animate-pulse" />
        <span>Loading matters...</span>
      </div>
    )
  }

  if (matters.length === 0) {
    return null
  }

  return (
    <div className="flex items-center gap-2 border-b border-gray-200 bg-gray-50 px-4 py-2">
      <Briefcase className="h-4 w-4 text-gray-500" />
      <select
        value={value || ''}
        onChange={(e) => onChange(e.target.value || null)}
        disabled={disabled}
        className="flex-1 rounded border-gray-300 bg-white py-1 text-sm focus:border-blue-500 focus:ring-blue-500 disabled:bg-gray-100"
      >
        <option value="">AI Discovery (general assistance)</option>
        {matters.map((matter: Matter) => (
          <option key={matter.id} value={matter.id}>
            {matter.matter_number} - {matter.client_name}
          </option>
        ))}
      </select>
      {value && (
        <button
          type="button"
          onClick={() => onChange(null)}
          disabled={disabled}
          className="rounded p-1 text-gray-400 hover:bg-gray-200 hover:text-gray-600 disabled:opacity-50"
          title="Switch to AI Discovery"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  )
}
