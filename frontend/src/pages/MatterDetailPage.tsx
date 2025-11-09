// Matter Detail page - View matter details and manage documents

import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { mattersApi, documentsApi } from '@/lib/api'
import { Matter } from '@/types/matters'
import { ArrowLeft, Upload, FileText, Calendar, Briefcase, X } from 'lucide-react'
import Button from '@/components/ui/Button'
import DocumentUpload from '@/components/documents/DocumentUpload'

export default function MatterDetailPage() {
  const { matterId } = useParams<{ matterId: string }>()
  const navigate = useNavigate()

  const [matter, setMatter] = useState<Matter | null>(null)
  const [documents, setDocuments] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showUpload, setShowUpload] = useState(false)

  useEffect(() => {
    if (matterId) {
      fetchMatterDetails()
      fetchMatterDocuments()
    }
  }, [matterId])

  const fetchMatterDetails = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await mattersApi.get(matterId!)
      setMatter(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load matter details')
    } finally {
      setLoading(false)
    }
  }

  const fetchMatterDocuments = async () => {
    try {
      const response = await documentsApi.list({ matter_id: matterId })
      setDocuments(response.data.documents || [])
    } catch (err) {
      console.error('Failed to load documents:', err)
    }
  }

  const handleUploadSuccess = () => {
    setShowUpload(false)
    fetchMatterDocuments()
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
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

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary-600 border-r-transparent"></div>
          <span className="ml-3 text-gray-600">Loading matter...</span>
        </div>
      </DashboardLayout>
    )
  }

  if (error || !matter) {
    return (
      <DashboardLayout>
        <div className="max-w-3xl mx-auto p-6">
          <div className="bg-red-50 border border-red-200 text-red-800 rounded-md p-4">
            <p className="font-medium">Error loading matter</p>
            <p className="text-sm mt-1">{error || 'Matter not found'}</p>
          </div>
          <Button
            variant="secondary"
            onClick={() => navigate('/matters')}
            className="mt-4"
            icon={<ArrowLeft className="h-4 w-4" />}
          >
            Back to Matters
          </Button>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="p-6">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate('/matters')}
            className="flex items-center text-sm text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to Matters
          </button>

          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <h1 className="text-3xl font-bold text-gray-900">{matter.client_name}</h1>
                <span
                  className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(
                    matter.matter_status
                  )}`}
                >
                  {matter.matter_status}
                </span>
              </div>
              <p className="text-gray-600">{matter.matter_type}</p>
              <p className="text-sm text-gray-500 mt-1">Matter #{matter.matter_number}</p>
            </div>

            <Button
              variant="primary"
              onClick={() => setShowUpload(!showUpload)}
              icon={showUpload ? <X className="h-4 w-4" /> : <Upload className="h-4 w-4" />}
            >
              {showUpload ? 'Cancel' : 'Upload Document'}
            </Button>
          </div>
        </div>

        {/* Upload Section */}
        {showUpload && (
          <div className="mb-6 bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
            <div className="flex items-center mb-4">
              <FileText className="h-5 w-5 text-primary-500 mr-2" />
              <h2 className="text-lg font-medium text-gray-900">
                Quick Upload
              </h2>
            </div>
            <DocumentUpload
              matterId={matterId}
              onSuccess={handleUploadSuccess}
            />
          </div>
        )}

        {/* Matter Details */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          {/* Main Info */}
          <div className="lg:col-span-2 bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Matter Information</h2>

            <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <dt className="text-sm font-medium text-gray-500">Client Name</dt>
                <dd className="mt-1 text-sm text-gray-900">{matter.client_name}</dd>
              </div>

              <div>
                <dt className="text-sm font-medium text-gray-500">Matter Number</dt>
                <dd className="mt-1 text-sm text-gray-900">{matter.matter_number}</dd>
              </div>

              <div>
                <dt className="text-sm font-medium text-gray-500">Matter Type</dt>
                <dd className="mt-1 text-sm text-gray-900">{matter.matter_type}</dd>
              </div>

              <div>
                <dt className="text-sm font-medium text-gray-500">Status</dt>
                <dd className="mt-1">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                      matter.matter_status
                    )}`}
                  >
                    {matter.matter_status}
                  </span>
                </dd>
              </div>

              <div>
                <dt className="text-sm font-medium text-gray-500 flex items-center">
                  <Calendar className="h-4 w-4 mr-1" />
                  Opened Date
                </dt>
                <dd className="mt-1 text-sm text-gray-900">{formatDate(matter.opened_date)}</dd>
              </div>

              {matter.closed_date && (
                <div>
                  <dt className="text-sm font-medium text-gray-500 flex items-center">
                    <Calendar className="h-4 w-4 mr-1" />
                    Closed Date
                  </dt>
                  <dd className="mt-1 text-sm text-gray-900">{formatDate(matter.closed_date)}</dd>
                </div>
              )}
            </dl>

            {matter.description && (
              <div className="mt-6 pt-6 border-t border-gray-200">
                <dt className="text-sm font-medium text-gray-500 mb-2">Description</dt>
                <dd className="text-sm text-gray-900">{matter.description}</dd>
              </div>
            )}
          </div>

          {/* Quick Stats */}
          <div className="space-y-6">
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="flex items-center mb-2">
                <Briefcase className="h-5 w-5 text-gray-400 mr-2" />
                <h3 className="text-sm font-medium text-gray-500">Documents</h3>
              </div>
              <p className="text-3xl font-bold text-gray-900">{documents.length}</p>
              <p className="text-sm text-gray-600 mt-1">Total documents</p>
            </div>

            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-sm font-medium text-gray-500 mb-3">Quick Actions</h3>
              <div className="space-y-2">
                <button
                  onClick={() => setShowUpload(true)}
                  className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-md"
                >
                  Upload Document
                </button>
                <button
                  onClick={() => navigate(`/documents?matter=${matterId}`)}
                  className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-md"
                >
                  View All Documents
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Documents List */}
        <div className="bg-white rounded-lg border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Recent Documents</h2>
          </div>

          {documents.length === 0 ? (
            <div className="p-12 text-center">
              <FileText className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-4 text-lg font-medium text-gray-900">No documents yet</h3>
              <p className="mt-2 text-sm text-gray-600">
                Upload your first document to get started
              </p>
              <Button
                variant="primary"
                onClick={() => setShowUpload(true)}
                className="mt-4"
                icon={<Upload className="h-4 w-4" />}
              >
                Upload Document
              </Button>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {documents.slice(0, 10).map((doc) => (
                <div key={doc.id} className="p-4 hover:bg-gray-50 cursor-pointer">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center flex-1 min-w-0">
                      <FileText className="h-5 w-5 text-gray-400 mr-3 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {doc.document_title}
                        </p>
                        <p className="text-sm text-gray-500">
                          {doc.document_type} · {formatDate(doc.created_at)}
                        </p>
                      </div>
                    </div>
                    <span className="text-xs text-gray-500 ml-4">
                      {(doc.file_size_bytes / 1024 / 1024).toFixed(2)} MB
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {documents.length > 10 && (
            <div className="p-4 border-t border-gray-200 text-center">
              <Button
                variant="secondary"
                onClick={() => navigate(`/documents?matter=${matterId}`)}
              >
                View All {documents.length} Documents
              </Button>
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  )
}
