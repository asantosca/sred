// Edit Claim page - Form to edit an existing SR&ED claim

import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import toast from 'react-hot-toast'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { claimsApi } from '@/lib/api'
import { Claim, CLAIM_STATUSES } from '@/types/claims'
import Input from '@/components/ui/Input'
import Button from '@/components/ui/Button'
import { ArrowLeft } from 'lucide-react'

// SR&ED project types
const PROJECT_TYPES = [
  'Software Development',
  'Manufacturing Process',
  'Product Design',
  'Chemical/Biological',
  'Engineering',
  'Other',
] as const

// SR&ED filing deadline is 18 months from fiscal year end
const SRED_FILING_DEADLINE_MONTHS = 18

const editClaimSchema = z.object({
  claim_number: z.string().min(1, 'Claim number is required'),
  company_name: z.string().min(1, 'Company name is required'),
  project_type: z.string().min(1, 'Project type is required'),
  claim_status: z.string().min(1, 'Status is required'),
  description: z.string().optional(),
  opened_date: z.string().min(1, 'Opened date is required'),
  closed_date: z.string().optional(),
  fiscal_year_end: z.string().min(1, 'Fiscal year end is required'),
  // Project context fields (for AI guidance in T661 generation)
  project_title: z.string().optional(),
  project_objective: z.string().optional(),
  technology_focus: z.string().optional(),
}).refine(
  (data) => {
    if (!data.fiscal_year_end) return true
    const fiscalEnd = new Date(data.fiscal_year_end)
    const today = new Date()
    today.setHours(0, 0, 0, 0) // Compare dates only
    return fiscalEnd <= today
  },
  {
    message: 'Fiscal year end cannot be in the future (claims are for completed fiscal years)',
    path: ['fiscal_year_end'],
  }
).refine(
  (data) => {
    if (!data.fiscal_year_end || !data.opened_date) return true
    const fiscalEnd = new Date(data.fiscal_year_end)
    const opened = new Date(data.opened_date)
    return opened >= fiscalEnd
  },
  {
    message: 'Opened date must be on or after the fiscal year end (claims are for completed fiscal years)',
    path: ['opened_date'],
  }
).refine(
  (data) => {
    if (!data.fiscal_year_end || !data.opened_date) return true
    const fiscalEnd = new Date(data.fiscal_year_end)
    const opened = new Date(data.opened_date)
    // Calculate 18 months from fiscal year end
    const deadline = new Date(fiscalEnd)
    deadline.setMonth(deadline.getMonth() + SRED_FILING_DEADLINE_MONTHS)
    return opened <= deadline
  },
  {
    message: `Opened date must be within ${SRED_FILING_DEADLINE_MONTHS} months of fiscal year end (CRA filing deadline)`,
    path: ['opened_date'],
  }
)

type EditClaimFormData = z.infer<typeof editClaimSchema>

export default function EditClaimPage() {
  const { claimId } = useParams<{ claimId: string }>()
  const navigate = useNavigate()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [claim, setClaim] = useState<Claim | null>(null)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<EditClaimFormData>({
    resolver: zodResolver(editClaimSchema),
  })

  useEffect(() => {
    if (claimId) {
      fetchClaim()
    }
  }, [claimId])

  const fetchClaim = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await claimsApi.get(claimId!)
      const claimData = response.data
      setClaim(claimData)

      // Pre-populate form with existing data
      reset({
        claim_number: claimData.claim_number,
        company_name: claimData.company_name,
        project_type: claimData.project_type,
        claim_status: claimData.claim_status,
        description: claimData.description || '',
        opened_date: claimData.opened_date.split('T')[0],
        closed_date: claimData.closed_date?.split('T')[0] || '',
        fiscal_year_end: claimData.fiscal_year_end?.split('T')[0] || '',
        project_title: claimData.project_title || '',
        project_objective: claimData.project_objective || '',
        technology_focus: claimData.technology_focus || '',
      })
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load claim')
    } finally {
      setLoading(false)
    }
  }

  const onSubmit = async (data: EditClaimFormData) => {
    try {
      setIsSubmitting(true)
      setError(null)

      const submitData = {
        ...data,
        closed_date: data.closed_date || null,
        description: data.description || null,
        fiscal_year_end: data.fiscal_year_end || null,
        project_title: data.project_title || null,
        project_objective: data.project_objective || null,
        technology_focus: data.technology_focus || null,
      }

      await claimsApi.update(claimId!, submitData)

      toast.success('Claim updated successfully')
      navigate(`/claims/${claimId}`)
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to update claim'
      setError(errorMessage)
      toast.error(errorMessage)
    } finally {
      setIsSubmitting(false)
    }
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="max-w-3xl mx-auto p-6">
          <div className="flex items-center justify-center py-12">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary-600 border-r-transparent"></div>
            <span className="ml-3 text-gray-600">Loading claim...</span>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  if (error && !claim) {
    return (
      <DashboardLayout>
        <div className="max-w-3xl mx-auto p-6">
          <div className="bg-red-50 border border-red-200 text-red-800 rounded-md p-4">
            <p className="font-medium">Error loading claim</p>
            <p className="text-sm mt-1">{error}</p>
            <Button
              variant="secondary"
              onClick={() => navigate('/claims')}
              className="mt-4"
            >
              Back to Claims
            </Button>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="max-w-3xl mx-auto p-6">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate(`/claims/${claimId}`)}
            className="flex items-center text-sm text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to Claim
          </button>
          <h1 className="text-3xl font-bold text-gray-900">Edit Claim</h1>
          <p className="mt-1 text-sm text-gray-600">
            Update the details for {claim?.company_name}
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-800 rounded-md p-4">
            <p className="font-medium">Error updating claim</p>
            <p className="text-sm mt-1">{error}</p>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="space-y-6">
            {/* Claim Number */}
            <Input
              label="Claim Number"
              type="text"
              placeholder="e.g., 2024-001"
              error={errors.claim_number?.message}
              helperText="Unique identifier for this claim"
              {...register('claim_number')}
            />

            {/* Company Name */}
            <Input
              label="Company Name"
              type="text"
              placeholder="e.g., Acme Corp"
              error={errors.company_name?.message}
              {...register('company_name')}
            />

            {/* Project Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Project Type
              </label>
              <select
                {...register('project_type')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">Select a type...</option>
                {PROJECT_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
              {errors.project_type && (
                <p className="mt-1 text-sm text-red-600">{errors.project_type.message}</p>
              )}
            </div>

            {/* Claim Status */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <select
                {...register('claim_status')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
              >
                {CLAIM_STATUSES.map((status) => (
                  <option key={status} value={status}>
                    {status.charAt(0).toUpperCase() + status.slice(1).replace('_', ' ')}
                  </option>
                ))}
              </select>
              {errors.claim_status && (
                <p className="mt-1 text-sm text-red-600">{errors.claim_status.message}</p>
              )}
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
                <span className="text-gray-500 font-normal ml-1">(Optional)</span>
              </label>
              <textarea
                {...register('description')}
                rows={4}
                placeholder="Brief description of the claim..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
              />
              {errors.description && (
                <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
              )}
            </div>

            {/* Project Context Section - for AI Guidance */}
            <div className="border-t border-gray-200 pt-6 mt-6">
              <h3 className="text-lg font-medium text-gray-900 mb-1">Project Context</h3>
              <p className="text-sm text-gray-500 mb-4">
                These fields help the AI focus on the specific R&D project when generating T661 drafts from your documents.
              </p>

              <div className="space-y-4">
                <Input
                  label="Project Title"
                  type="text"
                  placeholder="e.g., ML-Based Fraud Detection Algorithm"
                  helperText="Short name for the specific R&D project"
                  {...register('project_title')}
                />

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Project Objective
                    <span className="text-gray-500 font-normal ml-1">(Optional)</span>
                  </label>
                  <textarea
                    {...register('project_objective')}
                    rows={2}
                    placeholder="e.g., Develop a neural network that reduces false positives in transaction fraud detection by 40%"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                  />
                  <p className="mt-1 text-sm text-gray-500">1-2 sentences describing the technical goal</p>
                </div>

                <Input
                  label="Technology Focus"
                  type="text"
                  placeholder="e.g., Machine learning, anomaly detection, real-time processing"
                  helperText="Specific technology area and keywords to help AI filter relevant content"
                  {...register('technology_focus')}
                />
              </div>
            </div>

            {/* Fiscal Year End - Critical for SR&ED */}
            <Input
              label="Fiscal Year End"
              type="date"
              error={errors.fiscal_year_end?.message}
              helperText="The end of the company's fiscal year for this SR&ED claim (determines eligible work period)"
              {...register('fiscal_year_end')}
            />

            {/* Administrative Dates */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Input
                label="Opened Date"
                type="date"
                error={errors.opened_date?.message}
                helperText="When you started working on this claim"
                {...register('opened_date')}
              />

              <Input
                label="Closed Date"
                type="date"
                helperText="Leave empty if claim is still open"
                {...register('closed_date')}
              />
            </div>
          </div>

          {/* Actions */}
          <div className="mt-8 flex items-center justify-end gap-3">
            <Button
              type="button"
              variant="secondary"
              onClick={() => navigate(`/claims/${claimId}`)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              isLoading={isSubmitting}
              disabled={!isDirty}
            >
              Save Changes
            </Button>
          </div>
        </form>
      </div>
    </DashboardLayout>
  )
}
