// Create Matter page - Form to create a new legal matter/case

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { mattersApi } from '@/lib/api'
import { MATTER_TYPES, MATTER_STATUSES } from '@/types/matters'
import Input from '@/components/ui/Input'
import Button from '@/components/ui/Button'
import { ArrowLeft } from 'lucide-react'

const createMatterSchema = z.object({
  matter_number: z.string().min(1, 'Matter number is required'),
  client_name: z.string().min(1, 'Client name is required'),
  matter_type: z.string().min(1, 'Matter type is required'),
  matter_status: z.string().min(1, 'Status is required'),
  description: z.string().optional(),
  opened_date: z.string().min(1, 'Opened date is required'),
  closed_date: z.string().optional(),
})

type CreateMatterFormData = z.infer<typeof createMatterSchema>

export default function CreateMatterPage() {
  const navigate = useNavigate()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<CreateMatterFormData>({
    resolver: zodResolver(createMatterSchema),
    defaultValues: {
      matter_status: 'active',
      opened_date: new Date().toISOString().split('T')[0], // Today's date
    },
  })

  const onSubmit = async (data: CreateMatterFormData) => {
    try {
      setIsSubmitting(true)
      setError(null)

      // Remove closed_date if empty
      const submitData = {
        ...data,
        closed_date: data.closed_date || null,
        description: data.description || null,
      }

      const response = await mattersApi.create(submitData)

      // Navigate to the newly created matter
      navigate(`/matters/${response.data.id}`)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create matter')
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
            onClick={() => navigate('/matters')}
            className="flex items-center text-sm text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to Matters
          </button>
          <h1 className="text-3xl font-bold text-gray-900">Create New Matter</h1>
          <p className="mt-1 text-sm text-gray-600">
            Add a new legal matter or case to your system
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-800 rounded-md p-4">
            <p className="font-medium">Error creating matter</p>
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
              onClick={() => navigate('/matters')}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              isLoading={isSubmitting}
            >
              Create Matter
            </Button>
          </div>
        </form>
      </div>
    </DashboardLayout>
  )
}
