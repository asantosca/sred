// Create Claim page - Form to create a new SR&ED claim

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import toast from 'react-hot-toast'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { claimsApi } from '@/lib/api'
import { CLAIM_STATUSES } from '@/types/claims'
import Input from '@/components/ui/Input'
import Button from '@/components/ui/Button'
import { ArrowLeft } from 'lucide-react'

// SR&ED project types
const SRED_PROJECT_TYPES = [
  'Software Development',
  'Manufacturing Process',
  'Product Design',
  'Chemical/Biological',
  'Engineering',
  'Other',
]

// SR&ED filing deadline is 18 months from fiscal year end
const SRED_FILING_DEADLINE_MONTHS = 18

const createClaimSchema = z.object({
  claim_number: z.string().min(1, 'Claim number is required'),
  company_name: z.string().min(1, 'Company name is required'),
  project_type: z.string().min(1, 'Project type is required'),
  claim_status: z.string().min(1, 'Status is required'),
  description: z.string().optional(),
  opened_date: z.string().min(1, 'Opened date is required'),
  closed_date: z.string().optional(),
  fiscal_year_end: z.string().min(1, 'Fiscal year end is required'),
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

type CreateClaimFormData = z.infer<typeof createClaimSchema>

export default function CreateClaimPage() {
  const navigate = useNavigate()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<CreateClaimFormData>({
    resolver: zodResolver(createClaimSchema),
    defaultValues: {
      claim_status: 'draft',
      opened_date: new Date().toISOString().split('T')[0], // Today's date
    },
  })

  const onSubmit = async (data: CreateClaimFormData) => {
    try {
      setIsSubmitting(true)
      setError(null)

      // Remove empty optional fields
      const submitData = {
        ...data,
        closed_date: data.closed_date || null,
        description: data.description || null,
        fiscal_year_end: data.fiscal_year_end || null,
      }

      const response = await claimsApi.create(submitData)

      toast.success('Claim created successfully')
      // Navigate to the newly created claim
      navigate(`/claims/${response.data.id}`)
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to create claim'
      setError(errorMessage)
      toast.error(errorMessage)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <DashboardLayout>
      <div className="max-w-3xl mx-auto p-6">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate('/claims')}
            className="flex items-center text-sm text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to Claims
          </button>
          <h1 className="text-3xl font-bold text-gray-900">Create New Claim</h1>
          <p className="mt-1 text-sm text-gray-600">
            Add a new SR&ED claim to your system
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-800 rounded-md p-4">
            <p className="font-medium">Error creating claim</p>
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
                {SRED_PROJECT_TYPES.map((type) => (
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
              onClick={() => navigate('/claims')}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              isLoading={isSubmitting}
            >
              Create Claim
            </Button>
          </div>
        </form>
      </div>
    </DashboardLayout>
  )
}
