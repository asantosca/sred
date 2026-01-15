// Dashboard home page

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import Card, { CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { FileText, MessageSquare, HardDrive, AlertCircle, Sparkles, RefreshCw, Calendar, ChevronRight, Briefcase, DollarSign } from 'lucide-react'
import { usageApi, briefingApi, timelineApi, billableApi, BriefingResponse } from '@/lib/api'
import type { DocumentEventWithContext } from '@/types/timeline'

interface UsageSummary {
  overall_health: string
  plan_tier: string
  health_details: {
    documents: {
      status: string
      current: number
      limit: number
      percentage: number
    }
    storage: {
      status: string
      current_bytes?: number
      current_mb: number
      limit_mb: number
      percentage: number
    }
    ai_queries: {
      status: string
      current: number
      limit: number
      percentage: number
    }
  }
  recommendations?: string[]
}

export default function DashboardPage() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [usageSummary, setUsageSummary] = useState<UsageSummary | null>(null)
  const [briefing, setBriefing] = useState<BriefingResponse | null>(null)
  const [upcomingEvents, setUpcomingEvents] = useState<DocumentEventWithContext[]>([])
  const [unbilledData, setUnbilledData] = useState<{
    total_unbilled: number
    by_matter: Array<{ matter_id: string; matter_name: string; unbilled_count: number }>
  } | null>(null)
  const [loading, setLoading] = useState(true)
  const [briefingLoading, setBriefingLoading] = useState(true)
  const [briefingError, setBriefingError] = useState<string | null>(null)
  const [eventsLoading, setEventsLoading] = useState(true)
  const [unbilledLoading, setUnbilledLoading] = useState(true)

  useEffect(() => {
    const fetchUsage = async () => {
      try {
        const response = await usageApi.getSummary()
        setUsageSummary(response.data)
      } catch (error) {
        console.error('Failed to fetch usage data:', error)
      } finally {
        setLoading(false)
      }
    }

    const fetchBriefing = async () => {
      try {
        setBriefingLoading(true)
        setBriefingError(null)
        const response = await briefingApi.getToday()
        setBriefing(response.data)
      } catch (error: any) {
        console.error('Failed to fetch briefing:', error)
        setBriefingError(error.response?.data?.detail || 'Failed to load briefing')
      } finally {
        setBriefingLoading(false)
      }
    }

    const fetchUpcomingEvents = async () => {
      try {
        setEventsLoading(true)
        const today = new Date().toISOString().split('T')[0]
        const response = await timelineApi.list({
          date_from: today,
          page: 1,
          page_size: 5,
        })
        setUpcomingEvents(response.data.events)
      } catch (error) {
        console.error('Failed to fetch upcoming events:', error)
      } finally {
        setEventsLoading(false)
      }
    }

    const fetchUnbilled = async () => {
      try {
        setUnbilledLoading(true)
        const response = await billableApi.getUnbilled()
        setUnbilledData(response.data)
      } catch (error) {
        console.error('Failed to fetch unbilled data:', error)
      } finally {
        setUnbilledLoading(false)
      }
    }

    fetchUsage()
    fetchBriefing()
    fetchUpcomingEvents()
    fetchUnbilled()
  }, [])

  const handleRegenerateBriefing = async () => {
    try {
      setBriefingLoading(true)
      setBriefingError(null)
      const response = await briefingApi.getToday(true)
      setBriefing(response.data)
    } catch (error: any) {
      console.error('Failed to regenerate briefing:', error)
      setBriefingError(error.response?.data?.detail || 'Failed to regenerate briefing')
    } finally {
      setBriefingLoading(false)
    }
  }

  const getHealthColor = (health: string) => {
    switch (health) {
      case 'healthy':
        return { text: 'text-green-600', bg: 'bg-green-100', bar: 'bg-green-500' }
      case 'caution':
        return { text: 'text-yellow-600', bg: 'bg-yellow-100', bar: 'bg-yellow-500' }
      case 'warning':
        return { text: 'text-orange-600', bg: 'bg-orange-100', bar: 'bg-orange-500' }
      case 'critical':
        return { text: 'text-red-600', bg: 'bg-red-100', bar: 'bg-red-500' }
      default:
        return { text: 'text-gray-600', bg: 'bg-gray-100', bar: 'bg-gray-500' }
    }
  }

  const formatLimit = (limit: number) => {
    return limit === -1 ? 'Unlimited' : limit.toLocaleString()
  }

  const formatStorageLimit = (limit: number) => {
    if (limit === -1) return 'Unlimited'
    return `${limit.toLocaleString()} MB`
  }

  // Simple markdown-like rendering for briefing content
  const renderBriefingContent = (content: string) => {
    const lines = content.split('\n')
    return lines.map((line, index) => {
      // Headers
      if (line.startsWith('## ')) {
        return <h2 key={index} className="text-xl font-semibold text-gray-900 mt-4 mb-2">{line.slice(3)}</h2>
      }
      if (line.startsWith('### ')) {
        return <h3 key={index} className="text-lg font-medium text-gray-800 mt-3 mb-1">{line.slice(4)}</h3>
      }
      // Bullet points
      if (line.startsWith('- ') || line.startsWith('* ')) {
        const text = line.slice(2)
        return (
          <li key={index} className="ml-4 text-sm text-gray-700">
            {renderInlineFormatting(text)}
          </li>
        )
      }
      // Empty lines
      if (line.trim() === '') {
        return <div key={index} className="h-2" />
      }
      // Regular paragraphs
      return <p key={index} className="text-sm text-gray-700 mb-2">{renderInlineFormatting(line)}</p>
    })
  }

  // Handle bold text
  const renderInlineFormatting = (text: string) => {
    const parts = text.split(/(\*\*[^*]+\*\*)/g)
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} className="font-semibold">{part.slice(2, -2)}</strong>
      }
      return part
    })
  }

  return (
    <DashboardLayout>
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">
            Welcome back, {user?.first_name || user?.email}!
          </h1>
          <p className="mt-1 text-sm text-gray-600">
            Here's what's happening with your SR&ED claims today
          </p>
        </div>

        {/* Overall Health Status */}
        {!loading && usageSummary && usageSummary.overall_health !== 'healthy' && (
          <div className={`mb-6 rounded-lg p-4 ${
            usageSummary.overall_health === 'critical' ? 'bg-red-50 border border-red-200' :
            usageSummary.overall_health === 'warning' ? 'bg-orange-50 border border-orange-200' :
            'bg-yellow-50 border border-yellow-200'
          }`}>
            <div className="flex items-start">
              <AlertCircle className={`h-5 w-5 mt-0.5 ${
                usageSummary.overall_health === 'critical' ? 'text-red-600' :
                usageSummary.overall_health === 'warning' ? 'text-orange-600' :
                'text-yellow-600'
              }`} />
              <div className="ml-3">
                <h3 className={`text-sm font-medium ${
                  usageSummary.overall_health === 'critical' ? 'text-red-800' :
                  usageSummary.overall_health === 'warning' ? 'text-orange-800' :
                  'text-yellow-800'
                }`}>
                  {usageSummary.overall_health === 'critical' ? 'Critical Usage Alert' :
                   usageSummary.overall_health === 'warning' ? 'Usage Warning' :
                   'Usage Caution'}
                </h3>
                <p className={`mt-1 text-sm ${
                  usageSummary.overall_health === 'critical' ? 'text-red-700' :
                  usageSummary.overall_health === 'warning' ? 'text-orange-700' :
                  'text-yellow-700'
                }`}>
                  You're approaching your plan limits. Consider upgrading to avoid service interruption.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Usage Stats Grid */}
        <div className="mb-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {loading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <Card key={i}>
                <CardContent className="p-6">
                  <div className="animate-pulse">
                    <div className="h-12 bg-gray-200 rounded mb-2"></div>
                    <div className="h-4 bg-gray-200 rounded"></div>
                  </div>
                </CardContent>
              </Card>
            ))
          ) : usageSummary?.health_details ? (
            <>
              {/* Documents */}
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-3">
                    <div className={`rounded-lg p-3 ${getHealthColor(usageSummary.health_details.documents.status).bg}`}>
                      <FileText className={`h-6 w-6 ${getHealthColor(usageSummary.health_details.documents.status).text}`} />
                    </div>
                  </div>
                  <p className="text-sm font-medium text-gray-600">Documents</p>
                  <p className="text-2xl font-semibold text-gray-900 mt-1">
                    {usageSummary.health_details.documents.current.toLocaleString()}
                    <span className="text-sm text-gray-500 font-normal">
                      {' / '}{formatLimit(usageSummary.health_details.documents.limit)}
                    </span>
                  </p>
                  {usageSummary.health_details.documents.limit !== -1 && (
                    <div className="mt-3">
                      <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                        <span>{usageSummary.health_details.documents.percentage.toFixed(0)}% used</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${getHealthColor(usageSummary.health_details.documents.status).bar}`}
                          style={{ width: `${Math.min(usageSummary.health_details.documents.percentage, 100)}%` }}
                        />
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Storage */}
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-3">
                    <div className={`rounded-lg p-3 ${getHealthColor(usageSummary.health_details.storage.status).bg}`}>
                      <HardDrive className={`h-6 w-6 ${getHealthColor(usageSummary.health_details.storage.status).text}`} />
                    </div>
                  </div>
                  <p className="text-sm font-medium text-gray-600">Storage</p>
                  <p className="text-2xl font-semibold text-gray-900 mt-1">
                    {usageSummary.health_details.storage.current_mb.toFixed(1)} MB
                    <span className="text-sm text-gray-500 font-normal">
                      {' / '}{formatStorageLimit(usageSummary.health_details.storage.limit_mb)}
                    </span>
                  </p>
                  {usageSummary.health_details.storage.limit_mb !== -1 && (
                    <div className="mt-3">
                      <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                        <span>{usageSummary.health_details.storage.percentage.toFixed(0)}% used</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${getHealthColor(usageSummary.health_details.storage.status).bar}`}
                          style={{ width: `${Math.min(usageSummary.health_details.storage.percentage, 100)}%` }}
                        />
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* AI Queries */}
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-3">
                    <div className={`rounded-lg p-3 ${getHealthColor(usageSummary.health_details.ai_queries.status).bg}`}>
                      <MessageSquare className={`h-6 w-6 ${getHealthColor(usageSummary.health_details.ai_queries.status).text}`} />
                    </div>
                  </div>
                  <p className="text-sm font-medium text-gray-600">AI Queries (Monthly)</p>
                  <p className="text-2xl font-semibold text-gray-900 mt-1">
                    {usageSummary.health_details.ai_queries.current.toLocaleString()}
                    <span className="text-sm text-gray-500 font-normal">
                      {' / '}{formatLimit(usageSummary.health_details.ai_queries.limit)}
                    </span>
                  </p>
                  {usageSummary.health_details.ai_queries.limit !== -1 && (
                    <div className="mt-3">
                      <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                        <span>{usageSummary.health_details.ai_queries.percentage.toFixed(0)}% used</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${getHealthColor(usageSummary.health_details.ai_queries.status).bar}`}
                          style={{ width: `${Math.min(usageSummary.health_details.ai_queries.percentage, 100)}%` }}
                        />
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </>
          ) : null}
        </div>

        {/* Unbilled Work Alert */}
        {!unbilledLoading && unbilledData && unbilledData.total_unbilled > 0 && (
          <div className="mb-8">
            <Card className="border-amber-200 bg-amber-50">
              <CardContent className="p-4">
                <div className="flex items-start gap-4">
                  <div className="rounded-full bg-amber-100 p-2">
                    <DollarSign className="h-5 w-5 text-amber-600" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-medium text-amber-900">
                      {unbilledData.total_unbilled} Unbilled Conversation{unbilledData.total_unbilled !== 1 ? 's' : ''}
                    </h3>
                    <p className="text-sm text-amber-700 mt-1">
                      You have claim-related conversations that haven't been billed yet.
                    </p>
                    {unbilledData.by_matter.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {unbilledData.by_matter.slice(0, 5).map((matter) => (
                          <button
                            key={matter.matter_id}
                            onClick={() => navigate(`/chat?matter=${matter.matter_id}&history=true`)}
                            className="inline-flex items-center gap-1.5 rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800 hover:bg-amber-200 transition-colors"
                          >
                            <Briefcase className="h-3 w-3" />
                            {matter.matter_name.split(' - ')[1] || matter.matter_name}
                            <span className="rounded-full bg-amber-200 px-1.5 text-amber-900">
                              {matter.unbilled_count}
                            </span>
                          </button>
                        ))}
                        {unbilledData.by_matter.length > 5 && (
                          <span className="text-xs text-amber-600 self-center">
                            +{unbilledData.by_matter.length - 5} more
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                  <button
                    onClick={() => navigate('/billable')}
                    className="flex items-center gap-1 text-sm text-amber-700 hover:text-amber-900 font-medium"
                  >
                    Review
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Two column layout for briefing and timeline */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily Briefing */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-purple-600" />
                <CardTitle>Daily Briefing</CardTitle>
              </div>
              <button
                onClick={handleRegenerateBriefing}
                disabled={briefingLoading}
                className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 disabled:opacity-50"
                title="Regenerate briefing"
              >
                <RefreshCw className={`h-4 w-4 ${briefingLoading ? 'animate-spin' : ''}`} />
                {briefingLoading ? 'Generating...' : 'Refresh'}
              </button>
            </div>
            <CardDescription>
              AI-generated insights based on your claims and activity
            </CardDescription>
          </CardHeader>
          <CardContent>
            {briefingLoading ? (
              <div className="space-y-3">
                <div className="animate-pulse">
                  <div className="h-6 bg-gray-200 rounded w-3/4 mb-3"></div>
                  <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
                  <div className="h-4 bg-gray-200 rounded w-5/6 mb-2"></div>
                  <div className="h-4 bg-gray-200 rounded w-4/6 mb-4"></div>
                  <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
                  <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                </div>
                <p className="text-xs text-gray-500 mt-4">
                  Generating your personalized briefing...
                </p>
              </div>
            ) : briefingError ? (
              <div className="text-center py-8">
                <AlertCircle className="mx-auto h-10 w-10 text-red-400 mb-2" />
                <p className="text-sm text-red-600">{briefingError}</p>
                <button
                  onClick={handleRegenerateBriefing}
                  className="mt-3 text-sm text-primary-600 hover:text-primary-700"
                >
                  Try again
                </button>
              </div>
            ) : briefing ? (
              <div className="prose prose-sm max-w-none">
                {renderBriefingContent(briefing.content)}
                {briefing.is_fresh && (
                  <p className="text-xs text-gray-400 mt-4 pt-2 border-t">
                    Just generated for you
                  </p>
                )}
              </div>
            ) : null}
          </CardContent>
        </Card>

        {/* Upcoming Events */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Calendar className="h-5 w-5 text-blue-600" />
                <CardTitle>Upcoming Events</CardTitle>
              </div>
              <button
                onClick={() => navigate('/timeline')}
                className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
              >
                View all
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
            <CardDescription>
              Key dates and deadlines from your documents
            </CardDescription>
          </CardHeader>
          <CardContent>
            {eventsLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="animate-pulse flex items-start gap-3">
                    <div className="h-10 w-10 bg-gray-200 rounded-lg" />
                    <div className="flex-1">
                      <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
                      <div className="h-3 bg-gray-200 rounded w-1/2" />
                    </div>
                  </div>
                ))}
              </div>
            ) : upcomingEvents.length === 0 ? (
              <div className="text-center py-6">
                <Calendar className="mx-auto h-10 w-10 text-gray-300 mb-2" />
                <p className="text-sm text-gray-500">No upcoming events</p>
                <p className="text-xs text-gray-400 mt-1">
                  Events will appear here once documents are processed
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {upcomingEvents.map((event) => (
                  <div
                    key={event.id}
                    className="flex items-start gap-3 p-3 rounded-lg border border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={() => navigate(`/timeline?date_from=${event.event_date}`)}
                  >
                    <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-blue-100 flex flex-col items-center justify-center">
                      <span className="text-xs font-medium text-blue-600">
                        {new Date(event.event_date).toLocaleDateString('en-CA', { month: 'short' })}
                      </span>
                      <span className="text-sm font-bold text-blue-700">
                        {new Date(event.event_date).getDate()}
                      </span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-900 line-clamp-2">
                        {event.event_description}
                      </p>
                      <div className="mt-1 flex items-center gap-2 text-xs text-gray-500">
                        {event.matter_number && (
                          <span className="inline-flex items-center gap-1">
                            <Briefcase className="h-3 w-3" />
                            {event.matter_number}
                          </span>
                        )}
                        <span className="inline-flex items-center gap-1">
                          <FileText className="h-3 w-3" />
                          {event.document_title || event.document_filename}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
        </div>
      </div>
    </DashboardLayout>
  )
}
