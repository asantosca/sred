// MatterSuggestionBanner - Displays when AI detects a query may relate to a claim

import { Briefcase, X } from 'lucide-react'
import Button from '@/components/ui/Button'
import type { MatterSuggestion } from '@/types/chat'

interface MatterSuggestionBannerProps {
  suggestion: MatterSuggestion
  onAccept: () => void
  onDismiss: () => void
  loading?: boolean
}

export default function MatterSuggestionBanner({
  suggestion,
  onAccept,
  onDismiss,
  loading = false,
}: MatterSuggestionBannerProps) {
  const confidencePercent = Math.round(suggestion.similarity * 100)

  return (
    <div className="mx-4 my-2 rounded-lg border border-blue-200 bg-blue-50 p-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 rounded-full bg-blue-100 p-1.5">
            <Briefcase className="h-4 w-4 text-blue-600" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-blue-900">
              This may relate to claim: {suggestion.matter_name}
            </p>
            <p className="mt-0.5 text-xs text-blue-700">
              Matched "{suggestion.matched_document}" ({confidencePercent}% confidence)
            </p>
            <p className="mt-1 text-xs text-blue-600">
              Link this conversation to enable document search for future messages.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="primary"
            onClick={onAccept}
            disabled={loading}
          >
            {loading ? 'Linking...' : 'Link to Claim'}
          </Button>
          <button
            type="button"
            onClick={onDismiss}
            className="rounded p-1 text-blue-400 hover:bg-blue-100 hover:text-blue-600"
            title="Dismiss"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
