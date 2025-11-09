// Document upload component with Quick Upload mode

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { documentsApi } from '@/lib/api'
import {
  QuickDocumentUpload,
  DOCUMENT_TYPES,
  CONFIDENTIALITY_LEVELS,
} from '@/types/documents'
import MatterSelector from './MatterSelector'
import { Upload, FileText, CheckCircle, AlertCircle, X } from 'lucide-react'

interface DocumentUploadProps {
  onSuccess?: () => void
  onCancel?: () => void
}

export default function DocumentUpload({ onSuccess, onCancel }: DocumentUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const [formData, setFormData] = useState<QuickDocumentUpload>({
    matter_id: '',
    document_type: '',
    document_title: '',
    document_date: new Date().toISOString().split('T')[0],
    confidentiality_level: 'standard_confidential',
  })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [uploadError, setUploadError] = useState<string | null>(null)

  const queryClient = useQueryClient()

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: async () => {
      if (!selectedFile) throw new Error('No file selected')

      const response = await documentsApi.upload(selectedFile, formData)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      setSelectedFile(null)
      setFormData({
        matter_id: '',
        document_type: '',
        document_title: '',
        document_date: new Date().toISOString().split('T')[0],
        confidentiality_level: 'standard_confidential',
      })
      setErrors({})
      setUploadError(null)
      onSuccess?.()
    },
    onError: (error: any) => {
      setUploadError(
        error.response?.data?.detail || 'Failed to upload document'
      )
    },
  })

  const handleFileSelect = (file: File) => {
    // Validate file size (50MB max)
    const maxSize = 50 * 1024 * 1024
    if (file.size > maxSize) {
      setUploadError('File size exceeds 50MB limit')
      return
    }

    // Validate file type
    const allowedTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain',
    ]
    if (!allowedTypes.includes(file.type)) {
      setUploadError('Unsupported file type. Please upload PDF, DOC, DOCX, or TXT files.')
      return
    }

    setSelectedFile(file)
    setUploadError(null)

    // Auto-fill document title from filename if empty
    if (!formData.document_title) {
      const titleFromFile = file.name.replace(/\.[^/.]+$/, '') // Remove extension
      setFormData({ ...formData, document_title: titleFromFile })
    }
  }

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0])
    }
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0])
    }
  }

  const validateForm = () => {
    const newErrors: Record<string, string> = {}

    if (!formData.matter_id) newErrors.matter_id = 'Matter is required'
    if (!formData.document_type) newErrors.document_type = 'Document type is required'
    if (!formData.document_title) newErrors.document_title = 'Document title is required'
    if (!formData.document_date) newErrors.document_date = 'Document date is required'
    if (!selectedFile) newErrors.file = 'Please select a file to upload'

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setUploadError(null)

    if (!validateForm()) return

    uploadMutation.mutate()
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* File upload area */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Document File <span className="text-red-500">*</span>
        </label>
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={`relative border-2 border-dashed rounded-lg p-6 text-center ${
            dragActive
              ? 'border-primary-500 bg-primary-50'
              : 'border-gray-300 hover:border-gray-400'
          } ${errors.file ? 'border-red-300 bg-red-50' : ''}`}
        >
          <input
            type="file"
            id="file-upload"
            className="sr-only"
            accept=".pdf,.doc,.docx,.txt"
            onChange={handleFileInput}
          />

          {!selectedFile ? (
            <label htmlFor="file-upload" className="cursor-pointer">
              <Upload className="mx-auto h-12 w-12 text-gray-400" />
              <p className="mt-2 text-sm text-gray-600">
                <span className="font-medium text-primary-600 hover:text-primary-500">
                  Click to upload
                </span>{' '}
                or drag and drop
              </p>
              <p className="mt-1 text-xs text-gray-500">
                PDF, DOC, DOCX, or TXT (max 50MB)
              </p>
            </label>
          ) : (
            <div className="flex items-center justify-center">
              <FileText className="h-8 w-8 text-primary-500" />
              <div className="ml-3 text-left">
                <p className="text-sm font-medium text-gray-900">
                  {selectedFile.name}
                </p>
                <p className="text-xs text-gray-500">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
              <button
                type="button"
                onClick={() => setSelectedFile(null)}
                className="ml-4 text-gray-400 hover:text-gray-500"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          )}
        </div>
        {errors.file && (
          <p className="mt-2 text-sm text-red-600 flex items-center">
            <AlertCircle className="h-4 w-4 mr-1" />
            {errors.file}
          </p>
        )}
      </div>

      {/* Matter selector */}
      <MatterSelector
        value={formData.matter_id}
        onChange={(matterId) =>
          setFormData({ ...formData, matter_id: matterId })
        }
        error={errors.matter_id}
      />

      {/* Document metadata fields */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Document Type <span className="text-red-500">*</span>
          </label>
          <select
            value={formData.document_type}
            onChange={(e) =>
              setFormData({ ...formData, document_type: e.target.value })
            }
            className={`block w-full rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm ${
              errors.document_type
                ? 'border-red-300 text-red-900 focus:ring-red-500 focus:border-red-500'
                : 'border-gray-300'
            }`}
          >
            <option value="">Select type...</option>
            {DOCUMENT_TYPES.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
          {errors.document_type && (
            <p className="mt-1 text-sm text-red-600">{errors.document_type}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Document Date <span className="text-red-500">*</span>
          </label>
          <input
            type="date"
            value={formData.document_date}
            onChange={(e) =>
              setFormData({ ...formData, document_date: e.target.value })
            }
            className={`block w-full rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm ${
              errors.document_date
                ? 'border-red-300 text-red-900 focus:ring-red-500 focus:border-red-500'
                : 'border-gray-300'
            }`}
          />
          {errors.document_date && (
            <p className="mt-1 text-sm text-red-600">{errors.document_date}</p>
          )}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Document Title <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={formData.document_title}
          onChange={(e) =>
            setFormData({ ...formData, document_title: e.target.value })
          }
          placeholder="e.g., Employment Contract - John Doe"
          className={`block w-full rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm ${
            errors.document_title
              ? 'border-red-300 text-red-900 focus:ring-red-500 focus:border-red-500'
              : 'border-gray-300'
          }`}
        />
        {errors.document_title && (
          <p className="mt-1 text-sm text-red-600">{errors.document_title}</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Confidentiality Level
        </label>
        <select
          value={formData.confidentiality_level}
          onChange={(e) =>
            setFormData({ ...formData, confidentiality_level: e.target.value })
          }
          className="block w-full rounded-md border-gray-300 shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
        >
          {CONFIDENTIALITY_LEVELS.map((level) => (
            <option key={level} value={level}>
              {level.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
            </option>
          ))}
        </select>
      </div>

      {/* Upload error */}
      {uploadError && (
        <div className="rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-700 flex items-center">
            <AlertCircle className="h-4 w-4 mr-2" />
            {uploadError}
          </p>
        </div>
      )}

      {/* Success message */}
      {uploadMutation.isSuccess && (
        <div className="rounded-md bg-green-50 p-4">
          <p className="text-sm text-green-700 flex items-center">
            <CheckCircle className="h-4 w-4 mr-2" />
            Document uploaded successfully! Processing will begin shortly.
          </p>
        </div>
      )}

      {/* Action buttons */}
      <div className="flex justify-end gap-3">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            disabled={uploadMutation.isPending}
            className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
          >
            Cancel
          </button>
        )}
        <button
          type="submit"
          disabled={uploadMutation.isPending || !selectedFile}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {uploadMutation.isPending ? (
            <>
              <svg
                className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              Uploading...
            </>
          ) : (
            <>
              <Upload className="h-4 w-4 mr-2" />
              Upload Document
            </>
          )}
        </button>
      </div>
    </form>
  )
}
