// Dashboard home page

import { useEffect, useState } from 'react'
import { useAuthStore } from '@/store/authStore'
import Card, { CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { FileText, MessageSquare, HardDrive, AlertCircle } from 'lucide-react'
import { usageApi } from '@/lib/api'

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
  const [usageSummary, setUsageSummary] = useState<UsageSummary | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchUsage = async () => {
      try {
        const response = await usageApi.getSummary()
        console.log('Usage API response:', response.data)
        setUsageSummary(response.data)
      } catch (error) {
        console.error('Failed to fetch usage data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchUsage()
  }, [])

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
    if (limit >= 1024) return `${(limit / 1024).toFixed(0)} GB`
    return `${limit} MB`
  }

  return (
    <DashboardLayout>
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">
            Welcome back, {user?.first_name || user?.email}!
          </h1>
          <p className="mt-1 text-sm text-gray-600">
            Here's what's happening with your legal documents today
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

        {/* Getting Started */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Getting Started</CardTitle>
              <CardDescription>
                Quick actions to help you get up and running
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-start">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100 text-primary-600">
                    1
                  </div>
                  <div className="ml-4">
                    <h4 className="text-sm font-medium text-gray-900">
                      Upload your first document
                    </h4>
                    <p className="mt-1 text-sm text-gray-600">
                      Start by uploading a PDF, Word, or Excel document
                    </p>
                  </div>
                </div>

                <div className="flex items-start">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100 text-primary-600">
                    2
                  </div>
                  <div className="ml-4">
                    <h4 className="text-sm font-medium text-gray-900">
                      Chat with your documents
                    </h4>
                    <p className="mt-1 text-sm text-gray-600">
                      Use AI to ask questions and get instant answers
                    </p>
                  </div>
                </div>

                <div className="flex items-start">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100 text-primary-600">
                    3
                  </div>
                  <div className="ml-4">
                    <h4 className="text-sm font-medium text-gray-900">
                      Invite your team
                    </h4>
                    <p className="mt-1 text-sm text-gray-600">
                      Collaborate with colleagues on your documents
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
              <CardDescription>
                Your latest document interactions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-gray-500">
                <FileText className="mx-auto h-12 w-12 text-gray-400" />
                <p className="mt-2 text-sm">No activity yet</p>
                <p className="mt-1 text-xs">
                  Upload a document to get started
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  )
}
