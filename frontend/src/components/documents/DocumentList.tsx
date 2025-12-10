// Document list component with filtering and actions

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { documentsApi, mattersApi } from '@/lib/api'
import { DocumentWithMatter } from '@/types/documents'
import {
  FileText,
  Download,
  Trash2,
  Search,
  Filter,
  Calendar,
  Building2,
  FileType,
  Clock,
  CheckCircle,
  AlertCircle,
  Pencil,
  X,
} from 'lucide-react'
import { DOCUMENT_TYPES, DOCUMENT_STATUSES, CONFIDENTIALITY_LEVELS } from '@/types/documents'
import toast from 'react-hot-toast'

interface DocumentListProps {
  matterId?: string
}

interface EditFormData {
  document_title: string
  document_type: string
  document_date: string
  document_status: string
  description: string
  confidentiality_level: string
}

export default function DocumentList({ matterId }: DocumentListProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedMatter, setSelectedMatter] = useState(matterId || '')
  const [selectedType, setSelectedType] = useState('')
  const [page, setPage] = useState(1)
  const pageSize = 20

  // Edit modal state
  const [editingDocument, setEditingDocument] = useState<DocumentWithMatter | null>(null)
  const [editForm, setEditForm] = useState<EditFormData>({
    document_title: '',
    document_type: '',
    document_date: '',
    document_status: '',
    description: '',
    confidentiality_level: '',
  })

  const queryClient = useQueryClient()

  // Fetch documents
  const { data: documentsResponse, isLoading } = useQuery({
    queryKey: ['documents', { matter_id: selectedMatter || undefined, page, document_type: selectedType || undefined }],
    queryFn: async () => {
      const params: any = { page, size: pageSize }
      if (selectedMatter) params.matter_id = selectedMatter
      if (selectedType) params.document_type = selectedType

      const response = await documentsApi.list(params)
      return response.data
    },
  })

  // Fetch matters for filter
  const { data: mattersResponse } = useQuery({
    queryKey: ['matters', 'active'],
    queryFn: async () => {
      const response = await mattersApi.list({ status: 'active' })
      return response.data
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (documentId: string) => documentsApi.delete(documentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })

  const handleDelete = async (documentId: string, documentTitle: string) => {
    if (confirm(`Are you sure you want to delete "${documentTitle}"? This action cannot be undone.`)) {
      deleteMutation.mutate(documentId)
    }
  }

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ documentId, data }: { documentId: string; data: Partial<EditFormData> }) =>
      documentsApi.update(documentId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      setEditingDocument(null)
      toast.success('Document updated successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update document')
    },
  })

  const handleEdit = (document: DocumentWithMatter) => {
    setEditingDocument(document)
    setEditForm({
      document_title: document.document_title,
      document_type: document.document_type,
      document_date: document.document_date.split('T')[0],
      document_status: document.document_status,
      description: document.description || '',
      confidentiality_level: document.confidentiality_level,
    })
  }

  const handleSaveEdit = () => {
    if (!editingDocument) return
    // Convert empty strings to null for optional fields
    const data = {
      ...editForm,
      description: editForm.description || null,
    }
    updateMutation.mutate({
      documentId: editingDocument.id,
      data,
    })
  }

  const handleDownload = async (documentId: string) => {
    try {
      const response = await documentsApi.download(documentId)
      const { download_url } = response.data
      window.open(download_url, '_blank')
    } catch (error) {
      console.error('Download failed:', error)
      alert('Failed to download document')
    }
  }

  const documents = documentsResponse?.documents || []
  const filteredDocuments = documents.filter((doc: DocumentWithMatter) =>
    doc.document_title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    doc.original_filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
    doc.client_name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const matters = mattersResponse?.matters || []

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'embedded':
      case 'events_extracted':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'processing':
        return <Clock className="h-4 w-4 text-blue-500 animate-spin" />
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-500" />
      default:
        return <Clock className="h-4 w-4 text-gray-400" />
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'embedded':
      case 'events_extracted':
        return 'Ready'
      case 'processing':
        return 'Processing...'
      case 'failed':
        return 'Processing failed'
      case 'chunked':
        return 'Indexing...'
      default:
        return 'Pending'
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="animate-pulse bg-gray-100 h-24 rounded-lg"></div>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="bg-white p-4 rounded-lg border border-gray-200 space-y-4">
        <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
          <Filter className="h-4 w-4" />
          Filters
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search documents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 block w-full rounded-md border-gray-300 shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            />
          </div>

          {/* Matter filter */}
          <div>
            <select
              value={selectedMatter}
              onChange={(e) => {
                setSelectedMatter(e.target.value)
                setPage(1)
              }}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            >
              <option value="">All matters</option>
              {matters.map((matter: any) => (
                <option key={matter.id} value={matter.id}>
                  {matter.matter_number} - {matter.client_name}
                </option>
              ))}
            </select>
          </div>

          {/* Type filter */}
          <div>
            <select
              value={selectedType}
              onChange={(e) => {
                setSelectedType(e.target.value)
                setPage(1)
              }}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            >
              <option value="">All types</option>
              <option value="Contract">Contract</option>
              <option value="Pleading">Pleading</option>
              <option value="Correspondence">Correspondence</option>
              <option value="Discovery">Discovery</option>
              <option value="Exhibit">Exhibit</option>
              <option value="Other">Other</option>
            </select>
          </div>
        </div>
      </div>

      {/* Document list */}
      {filteredDocuments.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
          <FileText className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No documents</h3>
          <p className="mt-1 text-sm text-gray-500">
            {searchTerm || selectedMatter || selectedType
              ? 'No documents match your filters'
              : 'Get started by uploading a document'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredDocuments.map((document: DocumentWithMatter) => (
            <div
              key={document.id}
              className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3 flex-1">
                  <div className="flex-shrink-0">
                    <FileText className="h-8 w-8 text-primary-500" />
                  </div>

                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-medium text-gray-900 truncate">
                      {document.document_title}
                    </h3>
                    <p className="text-xs text-gray-500 mt-1">
                      {document.original_filename} ({(document.file_size_bytes / 1024 / 1024).toFixed(2)} MB)
                    </p>

                    <div className="flex flex-wrap items-center gap-4 mt-2 text-xs text-gray-600">
                      <div className="flex items-center">
                        <Building2 className="h-3 w-3 mr-1" />
                        {document.matter_number} - {document.client_name}
                      </div>
                      <div className="flex items-center">
                        <FileType className="h-3 w-3 mr-1" />
                        {document.document_type}
                      </div>
                      <div className="flex items-center">
                        <Calendar className="h-3 w-3 mr-1" />
                        {new Date(document.document_date).toLocaleDateString()}
                      </div>
                      <div className="flex items-center">
                        {getStatusIcon(document.processing_status)}
                        <span className="ml-1">{getStatusText(document.processing_status)}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center space-x-2 ml-4">
                  <button
                    onClick={() => handleEdit(document)}
                    className="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-md transition-colors"
                    title="Edit"
                  >
                    <Pencil className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => handleDownload(document.id)}
                    className="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-md transition-colors"
                    title="Download"
                  >
                    <Download className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(document.id, document.document_title)}
                    disabled={deleteMutation.isPending}
                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors disabled:opacity-50"
                    title="Delete"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {documentsResponse && documentsResponse.pages > 1 && (
        <div className="flex items-center justify-between border-t border-gray-200 bg-white px-4 py-3 sm:px-6 rounded-lg">
          <div className="flex flex-1 justify-between sm:hidden">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="relative inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(Math.min(documentsResponse.pages, page + 1))}
              disabled={page === documentsResponse.pages}
              className="relative ml-3 inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              Next
            </button>
          </div>
          <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-gray-700">
                Showing page <span className="font-medium">{page}</span> of{' '}
                <span className="font-medium">{documentsResponse.pages}</span>
                {' '}({documentsResponse.total} total documents)
              </p>
            </div>
            <div>
              <nav className="isolate inline-flex -space-x-px rounded-md shadow-sm" aria-label="Pagination">
                <button
                  onClick={() => setPage(Math.max(1, page - 1))}
                  disabled={page === 1}
                  className="relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage(Math.min(documentsResponse.pages, page + 1))}
                  disabled={page === documentsResponse.pages}
                  className="relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50"
                >
                  Next
                </button>
              </nav>
            </div>
          </div>
        </div>
      )}

      {/* Edit Document Modal */}
      {editingDocument && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-lg w-full mx-4 shadow-xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Edit Document</h3>
              <button
                onClick={() => setEditingDocument(null)}
                className="p-1 text-gray-400 hover:text-gray-600 rounded"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              {/* Title */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Document Title
                </label>
                <input
                  type="text"
                  value={editForm.document_title}
                  onChange={(e) => setEditForm({ ...editForm, document_title: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                />
              </div>

              {/* Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Document Type
                </label>
                <select
                  value={editForm.document_type}
                  onChange={(e) => setEditForm({ ...editForm, document_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                >
                  {DOCUMENT_TYPES.map((type) => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </div>

              {/* Date */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Document Date
                </label>
                <input
                  type="date"
                  value={editForm.document_date}
                  onChange={(e) => setEditForm({ ...editForm, document_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                />
              </div>

              {/* Status */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Status
                </label>
                <select
                  value={editForm.document_status}
                  onChange={(e) => setEditForm({ ...editForm, document_status: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                >
                  {DOCUMENT_STATUSES.map((status) => (
                    <option key={status} value={status}>
                      {status.charAt(0).toUpperCase() + status.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              {/* Confidentiality */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Confidentiality Level
                </label>
                <select
                  value={editForm.confidentiality_level}
                  onChange={(e) => setEditForm({ ...editForm, confidentiality_level: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                >
                  {CONFIDENTIALITY_LEVELS.map((level) => (
                    <option key={level} value={level}>
                      {level.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                    </option>
                  ))}
                </select>
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={editForm.description}
                  onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                  placeholder="Optional description..."
                />
              </div>
            </div>

            {/* Actions */}
            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={() => setEditingDocument(null)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveEdit}
                disabled={updateMutation.isPending}
                className="px-4 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-md hover:bg-primary-700 disabled:opacity-50"
              >
                {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
