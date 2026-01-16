// T661DraftModal.tsx - Modal for generating and editing T661 form drafts

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { X, FileText, RefreshCw, Copy, Check, ChevronDown, ChevronUp, AlertTriangle } from 'lucide-react'
import { t661Api, T661Draft, T661SectionDraft, T661StreamlineResponse } from '@/lib/api'

interface T661DraftModalProps {
  isOpen: boolean
  onClose: () => void
  claimId: string
  companyName: string
  claimNumber: string
}

// Section tab keys (aligned with CRA T661 box numbers)
const SECTION_KEYS = ['box242', 'box244', 'box246'] as const
type SectionKey = typeof SECTION_KEYS[number]

const SECTION_LABELS: Record<SectionKey, string> = {
  box242: 'Box 242: Uncertainties',
  box244: 'Box 244: Work Performed',
  box246: 'Box 246: Advancements',
}

// Evidence strength indicator component
function EvidenceStrengthIndicator({ strength }: { strength: string }) {
  const levels = ['insufficient', 'weak', 'moderate', 'strong']
  const currentLevel = levels.indexOf(strength)

  const getColor = (index: number) => {
    if (index > currentLevel) return 'bg-gray-200'
    switch (strength) {
      case 'strong': return 'bg-green-500'
      case 'moderate': return 'bg-yellow-500'
      case 'weak': return 'bg-orange-500'
      default: return 'bg-red-500'
    }
  }

  return (
    <div className="flex items-center gap-1">
      <span className="text-xs text-gray-500 mr-1">Evidence:</span>
      {[0, 1, 2, 3].map((i) => (
        <div
          key={i}
          className={`w-2 h-2 rounded-full ${getColor(i)}`}
        />
      ))}
      <span className="text-xs text-gray-600 ml-1 capitalize">{strength}</span>
    </div>
  )
}

// Word count indicator component
function WordCountIndicator({ current, limit }: { current: number; limit: number }) {
  const percentage = (current / limit) * 100
  const isOver = current > limit
  const isClose = percentage >= 90 && !isOver

  let colorClass = 'text-green-600'
  let bgClass = 'bg-green-100'
  if (isOver) {
    colorClass = 'text-red-600'
    bgClass = 'bg-red-100'
  } else if (isClose) {
    colorClass = 'text-yellow-600'
    bgClass = 'bg-yellow-100'
  }

  return (
    <div className={`px-2 py-1 rounded text-sm font-medium ${colorClass} ${bgClass}`}>
      {current}/{limit} words
      {isOver && <span className="ml-1">({current - limit} over)</span>}
    </div>
  )
}

export function T661DraftModal({
  isOpen,
  onClose,
  claimId,
  companyName,
  claimNumber,
}: T661DraftModalProps) {
  const [activeSection, setActiveSection] = useState<SectionKey>('box242')
  const [draft, setDraft] = useState<T661Draft | null>(null)
  const [editedSections, setEditedSections] = useState<Record<string, string>>({})
  const [showSources, setShowSources] = useState(true)
  const [copiedSection, setCopiedSection] = useState<string | null>(null)

  // Generate draft mutation
  const generateMutation = useMutation({
    mutationFn: () => t661Api.generateDraft(claimId),
    onSuccess: (response) => {
      if (response.data.success && response.data.draft) {
        setDraft(response.data.draft)
        setEditedSections({})
      }
    },
  })

  // Streamline section mutation
  const streamlineMutation = useMutation({
    mutationFn: (section: string) => {
      const currentContent = editedSections[section] ||
        draft?.sections.find(s => s.section === section)?.draft_content || ''
      return t661Api.streamlineSection(claimId, {
        section,
        current_content: currentContent,
        preserve_citations: true,
      })
    },
    onSuccess: (response: { data: T661StreamlineResponse }) => {
      const { section, streamlined_content } = response.data
      setEditedSections(prev => ({
        ...prev,
        [section]: streamlined_content,
      }))
    },
  })

  const handleCopy = async (section: string, content: string) => {
    await navigator.clipboard.writeText(content)
    setCopiedSection(section)
    setTimeout(() => setCopiedSection(null), 2000)
  }

  const handleReset = (section: string) => {
    setEditedSections(prev => {
      const { [section]: _, ...rest } = prev
      return rest
    })
  }

  const getCurrentSection = (): T661SectionDraft | undefined => {
    return draft?.sections.find(s => s.section === activeSection)
  }

  const getCurrentContent = (): string => {
    const section = getCurrentSection()
    return editedSections[activeSection] || section?.draft_content || ''
  }

  const countWords = (text: string): number => {
    return text.replace(/\[\d+\]/g, '').split(/\s+/).filter(Boolean).length
  }

  if (!isOpen) return null

  const currentSection = getCurrentSection()
  const currentContent = getCurrentContent()
  const currentWordCount = countWords(currentContent)
  const wordLimit = currentSection?.word_limit || 350
  const isEdited = !!editedSections[activeSection]

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-5xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <FileText className="w-6 h-6 text-blue-600" />
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                T661 Draft - {companyName}
              </h2>
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <span>Claim: {claimNumber}</span>
                {draft?.fiscal_year_start && draft?.fiscal_year_end && (
                  <>
                    <span className="text-gray-300">|</span>
                    <span>
                      Fiscal Year: {new Date(draft.fiscal_year_start).toLocaleDateString('en-CA', { year: 'numeric', month: 'short', day: 'numeric' })} to {new Date(draft.fiscal_year_end).toLocaleDateString('en-CA', { year: 'numeric', month: 'short', day: 'numeric' })}
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden flex flex-col">
          {!draft ? (
            // Generate prompt
            <div className="flex-1 flex flex-col items-center justify-center p-8">
              <FileText className="w-16 h-16 text-gray-300 mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Generate T661 Draft
              </h3>
              <p className="text-gray-600 text-center max-w-md mb-6">
                Analyze project documents and generate draft responses for CRA Form T661 sections.
                The AI will cite sources from your uploaded documents.
              </p>
              <button
                onClick={() => generateMutation.mutate()}
                disabled={generateMutation.isPending}
                className="inline-flex items-center px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {generateMutation.isPending ? (
                  <>
                    <RefreshCw className="w-5 h-5 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <FileText className="w-5 h-5 mr-2" />
                    Generate Draft
                  </>
                )}
              </button>
              {generateMutation.isError && (
                <p className="mt-4 text-red-600 text-sm">
                  Failed to generate draft. Please try again.
                </p>
              )}
            </div>
          ) : (
            <>
              {/* Section tabs */}
              <div className="flex border-b border-gray-200">
                {SECTION_KEYS.map((key) => {
                  const section = draft.sections.find(s => s.section === key)
                  const isActive = activeSection === key
                  return (
                    <button
                      key={key}
                      onClick={() => setActiveSection(key)}
                      className={`flex-1 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                        isActive
                          ? 'border-blue-600 text-blue-600 bg-blue-50'
                          : 'border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex items-center justify-center gap-2">
                        <span>{SECTION_LABELS[key]}</span>
                        {section?.is_over_limit && (
                          <AlertTriangle className="w-4 h-4 text-red-500" />
                        )}
                      </div>
                    </button>
                  )
                })}
              </div>

              {/* Section content */}
              {currentSection && (
                <div className="flex-1 overflow-auto p-4">
                  {/* Section header with metrics */}
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-4">
                      <WordCountIndicator current={currentWordCount} limit={wordLimit} />
                      <EvidenceStrengthIndicator strength={currentSection.evidence_strength} />
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => streamlineMutation.mutate(activeSection)}
                        disabled={streamlineMutation.isPending || currentWordCount <= wordLimit}
                        className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-blue-600 bg-blue-50 rounded hover:bg-blue-100 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {streamlineMutation.isPending ? (
                          <>
                            <RefreshCw className="w-4 h-4 mr-1.5 animate-spin" />
                            Streamlining...
                          </>
                        ) : (
                          'Streamline'
                        )}
                      </button>
                      {isEdited && (
                        <button
                          onClick={() => handleReset(activeSection)}
                          className="px-3 py-1.5 text-sm font-medium text-gray-600 bg-gray-100 rounded hover:bg-gray-200"
                        >
                          Reset
                        </button>
                      )}
                      <button
                        onClick={() => handleCopy(activeSection, currentContent)}
                        className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-gray-600 bg-gray-100 rounded hover:bg-gray-200"
                      >
                        {copiedSection === activeSection ? (
                          <>
                            <Check className="w-4 h-4 mr-1.5 text-green-600" />
                            Copied!
                          </>
                        ) : (
                          <>
                            <Copy className="w-4 h-4 mr-1.5" />
                            Copy
                          </>
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Content text area */}
                  <div className="mb-4">
                    <textarea
                      value={currentContent}
                      onChange={(e) => setEditedSections(prev => ({
                        ...prev,
                        [activeSection]: e.target.value,
                      }))}
                      className="w-full h-64 p-4 border border-gray-300 rounded-lg text-sm font-mono resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>

                  {/* Confidence notes */}
                  {currentSection.confidence_notes && (
                    <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <p className="text-sm text-yellow-800">
                        <AlertTriangle className="w-4 h-4 inline-block mr-1.5" />
                        {currentSection.confidence_notes}
                      </p>
                    </div>
                  )}

                  {/* Sources section */}
                  {currentSection.sources.length > 0 && (
                    <div className="border border-gray-200 rounded-lg">
                      <button
                        onClick={() => setShowSources(!showSources)}
                        className="w-full flex items-center justify-between p-3 text-sm font-medium text-gray-700 hover:bg-gray-50"
                      >
                        <span>Sources ({currentSection.sources.length})</span>
                        {showSources ? (
                          <ChevronUp className="w-4 h-4" />
                        ) : (
                          <ChevronDown className="w-4 h-4" />
                        )}
                      </button>
                      {showSources && (
                        <div className="border-t border-gray-200 p-3 space-y-3">
                          {currentSection.sources.map((source) => (
                            <div key={source.citation_id} className="text-sm">
                              <div className="font-medium text-gray-900">
                                [{source.citation_id}] {source.document_title}
                                {source.page_number && (
                                  <span className="text-gray-500 ml-1">
                                    (p.{source.page_number})
                                  </span>
                                )}
                              </div>
                              <p className="text-gray-600 mt-1 pl-4 border-l-2 border-gray-200 italic">
                                "{source.excerpt}"
                              </p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t border-gray-200 bg-gray-50">
          <div className="text-sm text-gray-500">
            {draft && (
              <>
                {draft.documents_analyzed} documents analyzed
                {' | '}
                Completeness: {Math.round(draft.overall_completeness * 100)}%
              </>
            )}
          </div>
          <div className="flex items-center gap-3">
            {draft && (
              <button
                onClick={() => generateMutation.mutate()}
                disabled={generateMutation.isPending}
                className="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${generateMutation.isPending ? 'animate-spin' : ''}`} />
                Regenerate
              </button>
            )}
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default T661DraftModal
