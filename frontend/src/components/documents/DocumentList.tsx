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
} from 'lucide-react'

interface DocumentListProps {
  matterId?: string
}

export default function DocumentList({ matterId }: DocumentListProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedMatter, setSelectedMatter] = useState(matterId || '')
  const [selectedType, setSelectedType] = useState('')
  const [page, setPage] = useState(1)
  const pageSize = 20

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
        return 'Ready for search'
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
    </div>
  )
}
