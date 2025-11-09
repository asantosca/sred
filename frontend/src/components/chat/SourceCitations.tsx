// SourceCitations component - Displays document sources for AI responses

import { FileText, ExternalLink } from 'lucide-react'
import type { MessageSource } from '@/types/chat'

interface SourceCitationsProps {
  sources: MessageSource[]
  onViewDocument?: (documentId: string) => void
}

export default function SourceCitations({
  sources,
  onViewDocument,
}: SourceCitationsProps) {
  if (!sources || sources.length === 0) {
    return null
  }

  const formatSimilarity = (score: number) => {
    return `${(score * 100).toFixed(0)}% match`
  }

  return (
    <div className="mt-3 space-y-2">
      <div className="text-xs font-medium text-gray-500">Sources:</div>
      <div className="space-y-2">
        {sources.map((source, index) => (
          <div
            key={`${source.document_id}-${source.chunk_id}`}
            className="rounded-lg border border-gray-200 bg-gray-50 p-3 text-sm"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex min-w-0 flex-1 items-start gap-2">
                <FileText className="mt-0.5 h-4 w-4 flex-shrink-0 text-blue-600" />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900">
                      [{index + 1}] {source.document_title}
                    </span>
                    {source.page_number && (
                      <span className="text-xs text-gray-500">
                        (Page {source.page_number})
                      </span>
                    )}
                  </div>
                  <div className="mt-1 text-xs text-gray-600">
                    Matter: {source.matter_name}
                  </div>
                  {source.content && (
                    <div className="mt-2 max-h-20 overflow-hidden text-xs text-gray-700">
                      <div className="line-clamp-3">{source.content}</div>
                    </div>
                  )}
                  <div className="mt-2 flex items-center gap-3 text-xs text-gray-500">
                    <span>{formatSimilarity(source.similarity_score)}</span>
                    {onViewDocument && (
                      <button
                        onClick={() => onViewDocument(source.document_id)}
                        className="flex items-center gap-1 text-blue-600 hover:text-blue-700"
                      >
                        View document
                        <ExternalLink className="h-3 w-3" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
