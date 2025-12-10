// Edit Matter page - Form to edit an existing legal matter/case

import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import toast from 'react-hot-toast'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { mattersApi } from '@/lib/api'
import { Matter, MATTER_TYPES, MATTER_STATUSES } from '@/types/matters'
import Input from '@/components/ui/Input'
import Button from '@/components/ui/Button'
import { ArrowLeft } from 'lucide-react'

const editMatterSchema = z.object({
  matter_number: z.string().min(1, 'Matter number is required'),
  client_name: z.string().min(1, 'Client name is required'),
  matter_type: z.string().min(1, 'Matter type is required'),
  matter_status: z.string().min(1, 'Status is required'),
  description: z.string().optional(),
  opened_date: z.string().min(1, 'Opened date is required'),
  closed_date: z.string().optional(),
})

type EditMatterFormData = z.infer<typeof editMatterSchema>

export default function EditMatterPage() {
  const { matterId } = useParams<{ matterId: string }>()
  const navigate = useNavigate()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [matter, setMatter] = useState<Matter | null>(null)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<EditMatterFormData>({
    resolver: zodResolver(editMatterSchema),
  })

  useEffect(() => {
    if (matterId) {
      fetchMatter()
    }
  }, [matterId])

  const fetchMatter = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await mattersApi.get(matterId!)
      const matterData = response.data
      setMatter(matterData)

      // Pre-populate form with existing data
      reset({
        matter_number: matterData.matter_number,
        client_name: matterData.client_name,
        matter_type: matterData.matter_type,
        matter_status: matterData.matter_status,
        description: matterData.description || '',
        opened_date: matterData.opened_date.split('T')[0],
        closed_date: matterData.closed_date?.split('T')[0] || '',
      })
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load matter')
    } finally {
      setLoading(false)
    }
  }

  const onSubmit = async (data: EditMatterFormData) => {
    try {
      setIsSubmitting(true)
      setError(null)

      const submitData = {
        ...data,
        closed_date: data.closed_date || null,
        description: data.description || null,
      }

      await mattersApi.update(matterId!, submitData)

      toast.success('Matter updated successfully')
      navigate(`/matters/${matterId}`)
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to update matter'
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
            <span className="ml-3 text-gray-600">Loading matter...</span>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  if (error && !matter) {
    return (
      <DashboardLayout>
        <div className="max-w-3xl mx-auto p-6">
          <div className="bg-red-50 border border-red-200 text-red-800 rounded-md p-4">
            <p className="font-medium">Error loading matter</p>
            <p className="text-sm mt-1">{error}</p>
            <Button
              variant="secondary"
              onClick={() => navigate('/matters')}
              className="mt-4"
            >
              Back to Matters
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
            onClick={() => navigate(`/matters/${matterId}`)}
            className="flex items-center text-sm text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to Matter
          </button>
          <h1 className="text-3xl font-bold text-gray-900">Edit Matter</h1>
          <p className="mt-1 text-sm text-gray-600">
            Update the details for {matter?.client_name}
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-800 rounded-md p-4">
            <p className="font-medium">Error updating matter</p>
            <p className="text-sm mt-1">{error}</p>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="space-y-6">
            {/* Matter Number */}
            <Input
              label="Matter Number"
              type="text"
              placeholder="e.g., 2024-001"
              error={errors.matter_number?.message}
              helperText="Unique identifier for this matter"
              {...register('matter_number')}
            />

            {/* Client Name */}
            <Input
              label="Client Name"
              type="text"
              placeholder="e.g., John Doe"
              error={errors.client_name?.message}
              {...register('client_name')}
            />

            {/* Matter Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Matter Type
              </label>
              <select
                {...register('matter_type')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">Select a type...</option>
                {MATTER_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
              {errors.matter_type && (
                <p className="mt-1 text-sm text-red-600">{errors.matter_type.message}</p>
              )}
            </div>

            {/* Matter Status */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <select
                {...register('matter_status')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
              >
                {MATTER_STATUSES.map((status) => (
                  <option key={status} value={status}>
                    {status.charAt(0).toUpperCase() + status.slice(1).replace('_', ' ')}
                  </option>
                ))}
              </select>
              {errors.matter_status && (
                <p className="mt-1 text-sm text-red-600">{errors.matter_status.message}</p>
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
                placeholder="Brief description of the matter..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
              />
              {errors.description && (
                <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
              )}
            </div>

            {/* Dates */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Input
                label="Opened Date"
                type="date"
                error={errors.opened_date?.message}
                {...register('opened_date')}
              />

              <Input
                label="Closed Date"
                type="date"
                helperText="Leave empty if matter is still open"
                {...register('closed_date')}
              />
            </div>
          </div>

          {/* Actions */}
          <div className="mt-8 flex items-center justify-end gap-3">
            <Button
              type="button"
              variant="secondary"
              onClick={() => navigate(`/matters/${matterId}`)}
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
