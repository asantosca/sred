// Documents page with upload and management

import { useState } from 'react'
import DashboardLayout from '@/components/layout/DashboardLayout'
import DocumentUpload from '@/components/documents/DocumentUpload'
import DocumentList from '@/components/documents/DocumentList'
import { Upload, FileText, X } from 'lucide-react'

export default function DocumentsPage() {
  const [showUpload, setShowUpload] = useState(false)

  return (
    <DashboardLayout>
      <div className="p-6">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Documents</h1>
            <p className="mt-1 text-sm text-gray-600">
              Upload and manage your legal documents
            </p>
          </div>
          <button
            onClick={() => setShowUpload(!showUpload)}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            {showUpload ? (
              <>
                <X className="h-4 w-4 mr-2" />
                Cancel Upload
              </>
            ) : (
              <>
                <Upload className="h-4 w-4 mr-2" />
                Upload Document
              </>
            )}
          </button>
        </div>

        {/* Upload form */}
        {showUpload && (
          <div className="mb-6 bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
            <div className="flex items-center mb-4">
              <FileText className="h-5 w-5 text-primary-500 mr-2" />
              <h2 className="text-lg font-medium text-gray-900">
                Quick Upload
              </h2>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Upload a document with minimal required information. Takes about 60 seconds.
            </p>
            <DocumentUpload
              onSuccess={() => setShowUpload(false)}
              onCancel={() => setShowUpload(false)}
            />
          </div>
        )}

        {/* Document list */}
        <DocumentList />
      </div>
    </DashboardLayout>
  )
}
