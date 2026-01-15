// Claim Detail page - View claim details and manage documents

import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { mattersApi, documentsApi, billableApi } from '@/lib/api'
import { Matter } from '@/types/matters'
import { ArrowLeft, Upload, FileText, Calendar, Briefcase, X, Trash2, AlertTriangle, MessageSquare, Clock, History, DollarSign, Pencil } from 'lucide-react'
import Button from '@/components/ui/Button'
import DocumentUpload from '@/components/documents/DocumentUpload'

export default function ClaimDetailPage() {
  const { matterId } = useParams<{ matterId: string }>()
  const navigate = useNavigate()

  const [claim, setClaim] = useState<Matter | null>(null)
  const [documents, setDocuments] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showUpload, setShowUpload] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState<string | null>(null)
  const [unbilledCount, setUnbilledCount] = useState<number>(0)

  useEffect(() => {
    if (matterId) {
      fetchClaimDetails()
      fetchClaimDocuments()
      fetchUnbilledCount()
    }
  }, [matterId])

  const fetchClaimDetails = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await mattersApi.get(matterId!)
      setClaim(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load claim details')
    } finally {
      setLoading(false)
    }
  }

  const fetchClaimDocuments = async () => {
    try {
      const response = await documentsApi.list({ matter_id: matterId })
      setDocuments(response.data.documents || [])
    } catch (err) {
      console.error('Failed to load documents:', err)
    }
  }

  const fetchUnbilledCount = async () => {
    try {
      const response = await billableApi.getUnbilled({ matter_id: matterId })
      setUnbilledCount(response.data.total_unbilled)
    } catch (err) {
      console.error('Failed to fetch unbilled count:', err)
    }
  }

  const handleUploadSuccess = () => {
    setShowUpload(false)
    fetchClaimDocuments()
  }

  const handleDeleteClaim = async () => {
    if (!matterId) return

    try {
      setDeleting(true)
      setDeleteError(null)
      await mattersApi.delete(matterId)
      navigate('/matters', { replace: true })
    } catch (err: any) {
      const errorDetail = err.response?.data?.detail || 'Failed to delete claim'
      setDeleteError(errorDetail)
      setDeleting(false)
    }
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
          <span className="ml-3 text-gray-600">Loading claim...</span>
        </div>
      </DashboardLayout>
    )
  }

  if (error || !claim) {
    return (
      <DashboardLayout>
        <div className="max-w-3xl mx-auto p-6">
          <div className="bg-red-50 border border-red-200 text-red-800 rounded-md p-4">
            <p className="font-medium">Error loading claim</p>
            <p className="text-sm mt-1">{error || 'Claim not found'}</p>
          </div>
          <Button
            variant="secondary"
            onClick={() => navigate('/matters')}
            className="mt-4"
            icon={<ArrowLeft className="h-4 w-4" />}
          >
            Back to Claims
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
            Back to Claims
          </button>

          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <h1 className="text-3xl font-bold text-gray-900">{claim.client_name}</h1>
                <span
                  className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(
                    claim.matter_status
                  )}`}
                >
                  {claim.matter_status}
                </span>
              </div>
              <p className="text-gray-600">{claim.matter_type}</p>
              <p className="text-sm text-gray-500 mt-1">Claim #{claim.matter_number}</p>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="primary"
                onClick={() => setShowUpload(!showUpload)}
                icon={showUpload ? <X className="h-4 w-4" /> : <Upload className="h-4 w-4" />}
              >
                {showUpload ? 'Cancel' : 'Upload Document'}
              </Button>

              {claim.user_can_edit && (
                <Button
                  variant="secondary"
                  onClick={() => navigate(`/matters/${matterId}/edit`)}
                  icon={<Pencil className="h-4 w-4" />}
                >
                  Edit
                </Button>
              )}

              {claim.user_can_delete && (
                <Button
                  variant="secondary"
                  onClick={() => setShowDeleteConfirm(true)}
                  icon={<Trash2 className="h-4 w-4" />}
                  className="text-red-600 hover:text-red-700 hover:bg-red-50"
                >
                  Delete
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* Delete Confirmation Modal */}
        {showDeleteConfirm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
              <div className="flex items-center gap-3 mb-4">
                <div className="flex-shrink-0 w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                  <AlertTriangle className="h-5 w-5 text-red-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900">Delete Claim</h3>
              </div>

              <p className="text-gray-600 mb-4">
                Are you sure you want to delete <strong>{claim.client_name}</strong> (Claim #{claim.matter_number})?
              </p>

              <p className="text-sm text-gray-500 mb-4">
                This will permanently delete all documents associated with this claim. This action cannot be undone.
              </p>

              {deleteError && (
                <div className="bg-red-50 border border-red-200 text-red-800 rounded-md p-3 mb-4 text-sm">
                  {deleteError}
                </div>
              )}

              <div className="flex justify-end gap-3">
                <Button
                  variant="secondary"
                  onClick={() => {
                    setShowDeleteConfirm(false)
                    setDeleteError(null)
                  }}
                  disabled={deleting}
                >
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  onClick={handleDeleteClaim}
                  disabled={deleting}
                  className="bg-red-600 hover:bg-red-700"
                >
                  {deleting ? 'Deleting...' : 'Delete Claim'}
                </Button>
              </div>
            </div>
          </div>
        )}

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

        {/* Claim Details */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          {/* Main Info */}
          <div className="lg:col-span-2 bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Claim Information</h2>

            <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <dt className="text-sm font-medium text-gray-500">Company Name</dt>
                <dd className="mt-1 text-sm text-gray-900">{claim.client_name}</dd>
              </div>

              <div>
                <dt className="text-sm font-medium text-gray-500">Claim Number</dt>
                <dd className="mt-1 text-sm text-gray-900">{claim.matter_number}</dd>
              </div>

              <div>
                <dt className="text-sm font-medium text-gray-500">Project Type</dt>
                <dd className="mt-1 text-sm text-gray-900">{claim.matter_type}</dd>
              </div>

              <div>
                <dt className="text-sm font-medium text-gray-500">Claim Status</dt>
                <dd className="mt-1">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                      claim.matter_status
                    )}`}
                  >
                    {claim.matter_status}
                  </span>
                </dd>
              </div>

              <div>
                <dt className="text-sm font-medium text-gray-500 flex items-center">
                  <Calendar className="h-4 w-4 mr-1" />
                  Opened Date
                </dt>
                <dd className="mt-1 text-sm text-gray-900">{formatDate(claim.opened_date)}</dd>
              </div>

              {claim.closed_date && (
                <div>
                  <dt className="text-sm font-medium text-gray-500 flex items-center">
                    <Calendar className="h-4 w-4 mr-1" />
                    Closed Date
                  </dt>
                  <dd className="mt-1 text-sm text-gray-900">{formatDate(claim.closed_date)}</dd>
                </div>
              )}
            </dl>

            {claim.description && (
              <div className="mt-6 pt-6 border-t border-gray-200">
                <dt className="text-sm font-medium text-gray-500 mb-2">Description</dt>
                <dd className="text-sm text-gray-900">{claim.description}</dd>
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

            {unbilledCount > 0 && (
              <div
                onClick={() => navigate(`/chat?matter=${matterId}&history=true`)}
                className="bg-amber-50 rounded-lg border border-amber-200 p-6 cursor-pointer hover:bg-amber-100 transition-colors"
              >
                <div className="flex items-center mb-2">
                  <DollarSign className="h-5 w-5 text-amber-600 mr-2" />
                  <h3 className="text-sm font-medium text-amber-700">Unbilled Work</h3>
                </div>
                <p className="text-3xl font-bold text-amber-900">{unbilledCount}</p>
                <p className="text-sm text-amber-700 mt-1">
                  Conversation{unbilledCount !== 1 ? 's' : ''} to review
                </p>
              </div>
            )}

            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-sm font-medium text-gray-500 mb-3">Quick Actions</h3>
              <div className="space-y-2">
                <button
                  onClick={() => navigate(`/chat?matter=${matterId}`)}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-primary-700 bg-primary-50 hover:bg-primary-100 rounded-md font-medium"
                >
                  <MessageSquare className="h-4 w-4" />
                  Chat about this Claim
                </button>
                <button
                  onClick={() => setShowUpload(true)}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-md"
                >
                  <Upload className="h-4 w-4" />
                  Upload Document
                </button>
                <button
                  onClick={() => navigate(`/documents?matter=${matterId}`)}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-md"
                >
                  <FileText className="h-4 w-4" />
                  View All Documents
                </button>
                <button
                  onClick={() => navigate(`/timeline?matter_id=${matterId}`)}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-md"
                >
                  <Calendar className="h-4 w-4" />
                  View Timeline
                </button>
                <button
                  onClick={() => navigate(`/chat?matter=${matterId}&history=true`)}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-md"
                >
                  <History className="h-4 w-4" />
                  Chat History
                </button>
                <button
                  onClick={() => navigate(`/billable?matter=${matterId}`)}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-md"
                >
                  <Clock className="h-4 w-4" />
                  Consulting Hours
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
