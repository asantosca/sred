// FeedbackModal.tsx - Modal for collecting detailed feedback on AI responses

import { useState } from 'react'
import { X } from 'lucide-react'
import { chatApi } from '@/lib/api'

interface FeedbackModalProps {
  isOpen: boolean
  onClose: () => void
  messageId: string
  rating: -1 | 1  // -1 for thumbs down, 1 for thumbs up
  onSuccess?: () => void
}

const NEGATIVE_CATEGORIES = [
  { value: 'incorrect', label: 'Answer was incorrect', description: 'The information provided was factually wrong' },
  { value: 'irrelevant', label: "Answer wasn't relevant", description: 'The response didn\'t address my question' },
  { value: 'wrong_question', label: 'I asked the wrong question', description: 'My question was poorly formed or unclear' },
  { value: 'not_detailed', label: 'Not enough detail', description: 'The answer was too brief or lacked specifics' },
  { value: 'no_documents', label: "Couldn't find documents", description: 'Relevant documents weren\'t found or cited' },
] as const

type FeedbackCategory = typeof NEGATIVE_CATEGORIES[number]['value']

export function FeedbackModal({ isOpen, onClose, messageId, rating, onSuccess }: FeedbackModalProps) {
  const [selectedCategory, setSelectedCategory] = useState<FeedbackCategory | null>(null)
  const [feedbackText, setFeedbackText] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async () => {
    setIsSubmitting(true)
    setError(null)

    try {
      await chatApi.submitFeedback(messageId, {
        rating,
        feedback_category: rating === -1 && selectedCategory ? selectedCategory : undefined,
        feedback_text: feedbackText || undefined,
      })

      onSuccess?.()
      onClose()
    } catch (err) {
      setError('Failed to submit feedback. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = () => {
    setSelectedCategory(null)
    setFeedbackText('')
    setError(null)
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {rating === 1 ? 'Thank you!' : 'Help us improve'}
          </h3>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-500 dark:hover:text-gray-300"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4">
          {rating === 1 ? (
            // Positive feedback - just optional text
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                We're glad this response was helpful! Want to tell us what you liked?
              </p>
              <textarea
                value={feedbackText}
                onChange={(e) => setFeedbackText(e.target.value)}
                placeholder="What made this response helpful? (optional)"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md
                         bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                         focus:ring-2 focus:ring-blue-500 focus:border-transparent
                         placeholder:text-gray-400 dark:placeholder:text-gray-500"
                rows={3}
              />
            </div>
          ) : (
            // Negative feedback - category selection + optional text
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                What went wrong with this response?
              </p>

              {/* Category selection */}
              <div className="space-y-2 mb-4">
                {NEGATIVE_CATEGORIES.map((category) => (
                  <label
                    key={category.value}
                    className={`flex items-start p-3 rounded-lg border cursor-pointer transition-colors
                      ${selectedCategory === category.value
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'
                      }`}
                  >
                    <input
                      type="radio"
                      name="feedback-category"
                      value={category.value}
                      checked={selectedCategory === category.value}
                      onChange={() => setSelectedCategory(category.value)}
                      className="sr-only"
                    />
                    <div>
                      <div className="font-medium text-gray-900 dark:text-white text-sm">
                        {category.label}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                        {category.description}
                      </div>
                    </div>
                  </label>
                ))}
              </div>

              {/* Additional comments */}
              <textarea
                value={feedbackText}
                onChange={(e) => setFeedbackText(e.target.value)}
                placeholder="Any additional details? (optional)"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md
                         bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                         focus:ring-2 focus:ring-blue-500 focus:border-transparent
                         placeholder:text-gray-400 dark:placeholder:text-gray-500"
                rows={2}
              />
            </div>
          )}

          {/* Error message */}
          {error && (
            <p className="mt-2 text-sm text-red-600 dark:text-red-400">
              {error}
            </p>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 p-4 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={handleClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300
                     hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md"
          >
            Skip
          </button>
          <button
            onClick={handleSubmit}
            disabled={isSubmitting || (rating === -1 && !selectedCategory)}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600
                     hover:bg-blue-700 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? 'Submitting...' : 'Submit feedback'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default FeedbackModal
