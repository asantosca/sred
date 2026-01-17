// Compact claim selector for chat - shows as a dropdown above the message input

import { useQuery } from '@tanstack/react-query'
import { claimsApi } from '@/lib/api'
import { Briefcase, X } from 'lucide-react'
import type { Claim } from '@/types/claims'

interface ClaimSelectorCompactProps {
  value: string | null
  onChange: (claimId: string | null) => void
  disabled?: boolean
}

export default function ClaimSelectorCompact({
  value,
  onChange,
  disabled = false,
}: ClaimSelectorCompactProps) {
  // Fetch claims list (all statuses for chat context)
  const { data: claimsResponse, isLoading } = useQuery({
    queryKey: ['claims', 'all'],
    queryFn: async () => {
      const response = await claimsApi.list({})
      return response.data
    },
  })

  const claims = claimsResponse?.claims || []

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 px-4 py-2 text-sm text-gray-500">
        <Briefcase className="h-4 w-4 animate-pulse" />
        <span>Loading claims...</span>
      </div>
    )
  }

  if (claims.length === 0) {
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
        {claims.map((claim: Claim) => (
          <option key={claim.id} value={claim.id}>
            {claim.claim_number} - {claim.company_name}
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
