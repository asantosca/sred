// TimelinePage - Document event timeline view

import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useSearchParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { timelineApi, mattersApi } from '@/lib/api'
import type { DocumentEventWithContext, ConfidenceLevel } from '@/types/timeline'
import type { Matter } from '@/types/documents'
import {
  Calendar,
  FileText,
  Briefcase,
  AlertCircle,
  CheckCircle,
  HelpCircle,
  ChevronLeft,
  ChevronRight,
  Filter,
  Edit2,
  Trash2,
  Eye,
} from 'lucide-react'
import Button from '@/components/ui/Button'

export default function TimelinePage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [searchParams] = useSearchParams()

  // Initialize matter filter from URL params
  const initialMatterId = searchParams.get('matter_id') || ''

  // Filters
  const [matterId, setMatterId] = useState<string>(initialMatterId)
  const [dateFrom, setDateFrom] = useState<string>('')
  const [dateTo, setDateTo] = useState<string>('')
  const [confidence, setConfidence] = useState<ConfidenceLevel | ''>('')
  const [page, setPage] = useState(1)
  const pageSize = 50

  // Update matter filter if URL param changes
  useEffect(() => {
    const urlMatterId = searchParams.get('matter_id') || ''
    if (urlMatterId !== matterId) {
      setMatterId(urlMatterId)
      setPage(1)
    }
  }, [searchParams])

  // Fetch matters for filter dropdown
  const { data: mattersData } = useQuery({
    queryKey: ['matters', 'active'],
    queryFn: async () => {
      const response = await mattersApi.list({ status: 'active' })
      return response.data
    },
  })

  // Fetch timeline events
  const { data, isLoading, error } = useQuery({
    queryKey: ['timeline', matterId, dateFrom, dateTo, confidence, page],
    queryFn: async () => {
      const response = await timelineApi.list({
        matter_id: matterId || undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        confidence: confidence || undefined,
        page,
        page_size: pageSize,
      })
      return response.data
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (eventId: string) => timelineApi.delete(eventId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['timeline'] })
      toast.success('Event deleted')
    },
    onError: () => {
      toast.error('Failed to delete event')
    },
  })

  const events = data?.events || []
  const total = data?.total || 0
  const hasMore = data?.has_more || false
  const matters = mattersData?.matters || []

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-CA', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  const getConfidenceIcon = (conf: ConfidenceLevel) => {
    switch (conf) {
      case 'high':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'medium':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />
      case 'low':
        return <HelpCircle className="h-4 w-4 text-red-500" />
    }
  }

  const getConfidenceBadge = (conf: ConfidenceLevel) => {
    const colors = {
      high: 'bg-green-100 text-green-800',
      medium: 'bg-yellow-100 text-yellow-800',
      low: 'bg-red-100 text-red-800',
    }
    return (
      <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${colors[conf]}`}>
        {getConfidenceIcon(conf)}
        {conf}
      </span>
    )
  }

  const getPrecisionLabel = (precision: string) => {
    switch (precision) {
      case 'day':
        return 'Exact date'
      case 'month':
        return 'Month only'
      case 'year':
        return 'Year only'
      case 'unknown':
        return 'Inferred'
      default:
        return precision
    }
  }

  const handleViewDocument = (documentId: string) => {
    navigate(`/documents?id=${documentId}`)
  }

  // Group events by date for visual timeline
  const groupedEvents: Record<string, DocumentEventWithContext[]> = {}
  events.forEach((event) => {
    const dateKey = event.event_date
    if (!groupedEvents[dateKey]) {
      groupedEvents[dateKey] = []
    }
    groupedEvents[dateKey].push(event)
  })

  const sortedDates = Object.keys(groupedEvents).sort()

  return (
    <DashboardLayout>
      <div className="mx-auto max-w-6xl p-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Project Timeline</h1>
          <p className="mt-1 text-sm text-gray-500">
            Chronological view of R&D milestones extracted from your documents
          </p>
        </div>

        {/* Filters */}
        <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4">
          <div className="flex items-center gap-2 mb-3">
            <Filter className="h-4 w-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-700">Filters</span>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {/* Claim filter */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Claim
              </label>
              <select
                value={matterId}
                onChange={(e) => {
                  setMatterId(e.target.value)
                  setPage(1)
                }}
                className="w-full rounded-md border-gray-300 text-sm focus:border-blue-500 focus:ring-blue-500"
              >
                <option value="">All claims</option>
                {matters.map((matter: Matter) => (
                  <option key={matter.id} value={matter.id}>
                    {matter.matter_number} - {matter.client_name}
                  </option>
                ))}
              </select>
            </div>

            {/* Date from */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                From date
              </label>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => {
                  setDateFrom(e.target.value)
                  setPage(1)
                }}
                className="w-full rounded-md border-gray-300 text-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>

            {/* Date to */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                To date
              </label>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => {
                  setDateTo(e.target.value)
                  setPage(1)
                }}
                className="w-full rounded-md border-gray-300 text-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>

            {/* Confidence filter */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Confidence
              </label>
              <select
                value={confidence}
                onChange={(e) => {
                  setConfidence(e.target.value as ConfidenceLevel | '')
                  setPage(1)
                }}
                className="w-full rounded-md border-gray-300 text-sm focus:border-blue-500 focus:ring-blue-500"
              >
                <option value="">All confidence levels</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
          </div>
        </div>

        {/* Results count */}
        <div className="mb-4 text-sm text-gray-600">
          {total} event{total !== 1 ? 's' : ''} found
        </div>

        {/* Timeline */}
        {isLoading ? (
          <div className="text-center py-12">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600" />
            <p className="mt-2 text-sm text-gray-500">Loading events...</p>
          </div>
        ) : error ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
            <AlertCircle className="mx-auto h-8 w-8 text-red-500" />
            <p className="mt-2 text-red-700">Failed to load timeline</p>
          </div>
        ) : events.length === 0 ? (
          <div className="rounded-lg border border-gray-200 bg-white p-12 text-center">
            <Calendar className="mx-auto h-12 w-12 text-gray-300" />
            <h3 className="mt-4 text-lg font-medium text-gray-900">No events found</h3>
            <p className="mt-2 text-sm text-gray-500">
              Events will appear here once documents are processed.
              {matterId && ' Try clearing the claim filter to see all events.'}
            </p>
          </div>
        ) : (
          <div className="relative">
            {/* Timeline line */}
            <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />

            {/* Events grouped by date */}
            {sortedDates.map((dateKey) => (
              <div key={dateKey} className="relative mb-8">
                {/* Date marker */}
                <div className="flex items-center mb-4">
                  <div className="absolute left-0 w-9 h-9 rounded-full bg-blue-600 flex items-center justify-center">
                    <Calendar className="h-5 w-5 text-white" />
                  </div>
                  <div className="ml-14 text-lg font-semibold text-gray-900">
                    {formatDate(dateKey)}
                  </div>
                </div>

                {/* Events for this date */}
                <div className="ml-14 space-y-3">
                  {groupedEvents[dateKey].map((event) => (
                    <div
                      key={event.id}
                      className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <p className="text-gray-900">{event.event_description}</p>

                          {/* Metadata row */}
                          <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-gray-500">
                            {/* Document */}
                            <button
                              onClick={() => handleViewDocument(event.document_id)}
                              className="inline-flex items-center gap-1 hover:text-blue-600"
                            >
                              <FileText className="h-3 w-3" />
                              {event.document_title || event.document_filename}
                            </button>

                            {/* Matter */}
                            {event.matter_name && (
                              <span className="inline-flex items-center gap-1">
                                <Briefcase className="h-3 w-3" />
                                {event.matter_number} - {event.matter_name}
                              </span>
                            )}

                            {/* Date precision */}
                            <span className="text-gray-400">
                              {getPrecisionLabel(event.date_precision)}
                            </span>

                            {/* Raw date text */}
                            {event.raw_date_text && (
                              <span className="italic text-gray-400">
                                "{event.raw_date_text}"
                              </span>
                            )}
                          </div>

                          {/* User notes */}
                          {event.user_notes && (
                            <p className="mt-2 text-sm text-gray-600 bg-gray-50 p-2 rounded">
                              Note: {event.user_notes}
                            </p>
                          )}
                        </div>

                        {/* Right side: confidence badge and actions */}
                        <div className="flex flex-col items-end gap-2">
                          {getConfidenceBadge(event.confidence)}

                          {/* Source indicator */}
                          {event.is_user_created && (
                            <span className="text-xs text-blue-600">User created</span>
                          )}
                          {event.is_user_modified && !event.is_user_created && (
                            <span className="text-xs text-blue-600">User edited</span>
                          )}

                          {/* Actions */}
                          <div className="flex items-center gap-1">
                            <button
                              onClick={() => handleViewDocument(event.document_id)}
                              className="p-1 text-gray-400 hover:text-blue-600 rounded"
                              title="View document"
                            >
                              <Eye className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => deleteMutation.mutate(event.id)}
                              className="p-1 text-gray-400 hover:text-red-600 rounded"
                              title="Delete event"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {total > pageSize && (
          <div className="mt-6 flex items-center justify-between border-t border-gray-200 pt-4">
            <div className="text-sm text-gray-500">
              Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, total)} of {total}
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setPage(page - 1)}
                disabled={page === 1}
              >
                <ChevronLeft className="h-4 w-4" />
                Previous
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setPage(page + 1)}
                disabled={!hasMore}
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}
