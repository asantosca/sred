// Claims page - List and manage SR&ED claims

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { mattersApi } from '@/lib/api'
import { Matter } from '@/types/matters'
import { Briefcase, Plus, Search, Filter } from 'lucide-react'
import Button from '@/components/ui/Button'

export default function ClaimsPage() {
  const navigate = useNavigate()
  const [claims, setClaims] = useState<Matter[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')

  // Fetch claims on mount
  useEffect(() => {
    fetchClaims()
  }, [])

  const fetchClaims = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await mattersApi.list()
      setClaims(response.data.matters)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load claims')
    } finally {
      setLoading(false)
    }
  }

  // Filter claims based on search and status
  const filteredClaims = claims.filter((claim) => {
    const matchesSearch =
      claim.client_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      claim.matter_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      claim.matter_type.toLowerCase().includes(searchTerm.toLowerCase())

    const matchesStatus =
      statusFilter === 'all' || claim.matter_status === statusFilter

    return matchesSearch && matchesStatus
  })

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800'
      case 'pending':
        return 'bg-yellow-100 text-yellow-800'
      case 'closed':
        return 'bg-gray-100 text-gray-800'
      case 'on_hold':
        return 'bg-orange-100 text-orange-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <DashboardLayout>
      <div className="p-6">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Claims</h1>
            <p className="mt-1 text-sm text-gray-600">
              Manage your SR&ED claims and projects
            </p>
          </div>
          <Button
            variant="primary"
            onClick={() => navigate('/matters/new')}
            icon={<Plus className="h-4 w-4" />}
          >
            New Claim
          </Button>
        </div>

        {/* Search and Filters */}
        <div className="mb-6 flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search claims by company, number, or project type..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="h-5 w-5 text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="border border-gray-300 rounded-md px-4 py-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="pending">Pending</option>
              <option value="on_hold">On Hold</option>
              <option value="closed">Closed</option>
            </select>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-800 rounded-md p-4">
            <p className="font-medium">Error loading claims</p>
            <p className="text-sm mt-1">{error}</p>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary-600 border-r-transparent"></div>
            <span className="ml-3 text-gray-600">Loading claims...</span>
          </div>
        )}

        {/* Claims Grid */}
        {!loading && !error && (
          <>
            {filteredClaims.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
                <Briefcase className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-4 text-lg font-medium text-gray-900">
                  {searchTerm || statusFilter !== 'all'
                    ? 'No claims found'
                    : 'No claims yet'}
                </h3>
                <p className="mt-2 text-sm text-gray-600">
                  {searchTerm || statusFilter !== 'all'
                    ? 'Try adjusting your search or filters'
                    : 'Get started by creating your first claim'}
                </p>
                {!searchTerm && statusFilter === 'all' && (
                  <Button
                    variant="primary"
                    onClick={() => navigate('/matters/new')}
                    className="mt-4"
                    icon={<Plus className="h-4 w-4" />}
                  >
                    Create Claim
                  </Button>
                )}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredClaims.map((claim) => (
                  <div
                    key={claim.id}
                    onClick={() => navigate(`/matters/${claim.id}`)}
                    className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow cursor-pointer"
                  >
                    {/* Claim Status Badge */}
                    <div className="flex items-start justify-between mb-4">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                          claim.matter_status
                        )}`}
                      >
                        {claim.matter_status}
                      </span>
                      <span className="text-xs text-gray-500">
                        {claim.matter_number}
                      </span>
                    </div>

                    {/* Company Name */}
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      {claim.client_name}
                    </h3>

                    {/* Project Type */}
                    <p className="text-sm text-gray-600 mb-4">
                      {claim.matter_type}
                    </p>

                    {/* Description (truncated) */}
                    {claim.description && (
                      <p className="text-sm text-gray-500 mb-4 line-clamp-2">
                        {claim.description}
                      </p>
                    )}

                    {/* Dates */}
                    <div className="flex items-center justify-between text-xs text-gray-500 pt-4 border-t border-gray-100">
                      <span>Opened {formatDate(claim.opened_date)}</span>
                      {claim.closed_date && (
                        <span>Closed {formatDate(claim.closed_date)}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Results Count */}
            {filteredClaims.length > 0 && (
              <div className="mt-6 text-center text-sm text-gray-600">
                Showing {filteredClaims.length} of {claims.length} claim
                {claims.length !== 1 ? 's' : ''}
              </div>
            )}
          </>
        )}
      </div>
    </DashboardLayout>
  )
}
