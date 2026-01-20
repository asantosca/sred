// WorkspaceEditor - Markdown editor with edit/preview/split modes

import { useState, useEffect, useRef, useCallback } from 'react'
import { Edit3, Eye, Columns, Save, RotateCcw } from 'lucide-react'
import Button from '@/components/ui/Button'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface WorkspaceEditorProps {
  markdown: string
  onChange: (markdown: string) => void
  onSave: () => void
  onDiscard: () => void
  hasUnsavedChanges: boolean
  isSaving: boolean
}

type ViewMode = 'edit' | 'preview' | 'split'

export default function WorkspaceEditor({
  markdown,
  onChange,
  onSave,
  onDiscard,
  hasUnsavedChanges,
  isSaving,
}: WorkspaceEditorProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('split')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const previewRef = useRef<HTMLDivElement>(null)

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }, [markdown])

  // Sync scroll between editor and preview in split mode
  const handleEditorScroll = useCallback(() => {
    if (viewMode !== 'split' || !textareaRef.current || !previewRef.current) return
    const scrollRatio = textareaRef.current.scrollTop / (textareaRef.current.scrollHeight - textareaRef.current.clientHeight)
    previewRef.current.scrollTop = scrollRatio * (previewRef.current.scrollHeight - previewRef.current.clientHeight)
  }, [viewMode])

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center space-x-2">
          <div className="flex bg-gray-200 rounded-md p-0.5">
            <button
              onClick={() => setViewMode('edit')}
              className={`px-3 py-1 text-sm rounded ${viewMode === 'edit' ? 'bg-white shadow text-gray-900' : 'text-gray-600 hover:text-gray-900'}`}
            >
              <Edit3 className="h-4 w-4 inline mr-1" />
              Edit
            </button>
            <button
              onClick={() => setViewMode('preview')}
              className={`px-3 py-1 text-sm rounded ${viewMode === 'preview' ? 'bg-white shadow text-gray-900' : 'text-gray-600 hover:text-gray-900'}`}
            >
              <Eye className="h-4 w-4 inline mr-1" />
              Preview
            </button>
            <button
              onClick={() => setViewMode('split')}
              className={`px-3 py-1 text-sm rounded ${viewMode === 'split' ? 'bg-white shadow text-gray-900' : 'text-gray-600 hover:text-gray-900'}`}
            >
              <Columns className="h-4 w-4 inline mr-1" />
              Split
            </button>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {hasUnsavedChanges && (
            <>
              <Button
                variant="secondary"
                size="sm"
                onClick={onDiscard}
                icon={<RotateCcw className="h-4 w-4" />}
              >
                Discard
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={onSave}
                isLoading={isSaving}
                icon={<Save className="h-4 w-4" />}
              >
                Save
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Editor/Preview Content */}
      <div className="flex-1 overflow-hidden flex">
        {/* Editor */}
        {(viewMode === 'edit' || viewMode === 'split') && (
          <div className={`${viewMode === 'split' ? 'w-1/2 border-r border-gray-200' : 'w-full'} overflow-auto`}>
            <textarea
              ref={textareaRef}
              value={markdown}
              onChange={(e) => onChange(e.target.value)}
              onScroll={handleEditorScroll}
              className="w-full h-full min-h-full p-4 font-mono text-sm resize-none border-0 focus:outline-none focus:ring-0"
              placeholder="Project workspace content will appear here after running discovery from the Claim page."
              spellCheck={false}
            />
          </div>
        )}

        {/* Preview */}
        {(viewMode === 'preview' || viewMode === 'split') && (
          <div
            ref={previewRef}
            className={`${viewMode === 'split' ? 'w-1/2' : 'w-full'} overflow-auto p-4`}
          >
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  // Custom rendering for document links
                  a: ({ href, children }) => {
                    if (href?.startsWith('doc:')) {
                      const docId = href.slice(4)
                      return (
                        <a
                          href={`/documents/${docId}`}
                          className="text-blue-600 hover:text-blue-800 hover:underline"
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          {children}
                        </a>
                      )
                    }
                    return <a href={href} className="text-blue-600 hover:underline">{children}</a>
                  },
                  // Style project headers
                  h2: ({ children }) => (
                    <h2 className="text-xl font-semibold mt-6 mb-3 pb-2 border-b border-gray-200">
                      {children}
                    </h2>
                  ),
                  h3: ({ children }) => (
                    <h3 className="text-lg font-medium mt-4 mb-2 text-gray-700">
                      {children}
                    </h3>
                  ),
                  // Style code blocks
                  code: ({ className, children }) => {
                    if (className?.includes('language-')) {
                      return (
                        <code className="block bg-gray-100 p-3 rounded text-sm overflow-x-auto">
                          {children}
                        </code>
                      )
                    }
                    return <code className="bg-gray-100 px-1 py-0.5 rounded text-sm">{children}</code>
                  },
                  // Style lists
                  ul: ({ children }) => (
                    <ul className="list-disc pl-5 space-y-1">{children}</ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="list-decimal pl-5 space-y-1">{children}</ol>
                  ),
                }}
              >
                {markdown || '*No content yet.*'}
              </ReactMarkdown>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
