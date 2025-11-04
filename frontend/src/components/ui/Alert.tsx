// Alert component for notifications

import { HTMLAttributes, forwardRef } from 'react'
import { cn } from '@/utils/cn'
import { AlertCircle, CheckCircle, Info, XCircle } from 'lucide-react'

export interface AlertProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'info' | 'success' | 'warning' | 'error'
  title?: string
}

const Alert = forwardRef<HTMLDivElement, AlertProps>(
  ({ className, variant = 'info', title, children, ...props }, ref) => {
    const variants = {
      info: {
        container: 'bg-blue-50 border-blue-200 text-blue-800',
        icon: Info,
        iconColor: 'text-blue-600',
      },
      success: {
        container: 'bg-green-50 border-green-200 text-green-800',
        icon: CheckCircle,
        iconColor: 'text-green-600',
      },
      warning: {
        container: 'bg-yellow-50 border-yellow-200 text-yellow-800',
        icon: AlertCircle,
        iconColor: 'text-yellow-600',
      },
      error: {
        container: 'bg-red-50 border-red-200 text-red-800',
        icon: XCircle,
        iconColor: 'text-red-600',
      },
    }

    const { container, icon: Icon, iconColor } = variants[variant]

    return (
      <div
        ref={ref}
        className={cn(
          'rounded-md border px-4 py-3',
          container,
          className
        )}
        {...props}
      >
        <div className="flex">
          <Icon className={cn('h-5 w-5 flex-shrink-0', iconColor)} />
          <div className="ml-3">
            {title && (
              <h3 className="text-sm font-medium">{title}</h3>
            )}
            {children && (
              <div className={cn('text-sm', title && 'mt-2')}>
                {children}
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }
)

Alert.displayName = 'Alert'

export default Alert
