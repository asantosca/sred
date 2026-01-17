// Dashboard Layout with navigation and user menu

import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import Button from '@/components/ui/Button'
import HelpDeskModal from '@/components/help/HelpDeskModal'
import {
  Menu,
  X,
  Home,
  FileText,
  MessageSquare,
  Users,
  Settings,
  LogOut,
  User,
  Briefcase,
  Clock,
  Calendar,
  HelpCircle,
} from 'lucide-react'

interface DashboardLayoutProps {
  children: React.ReactNode
}

const MARKETING_URL = import.meta.env.VITE_MARKETING_URL || 'http://localhost:3001'

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const { user, company, logout } = useAuthStore()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [helpOpen, setHelpOpen] = useState(false)

  const handleLogout = async () => {
    await logout()
    // Redirect to marketing site after logout
    window.location.href = MARKETING_URL
  }

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: Home },
    { name: 'Claims', href: '/claims', icon: Briefcase },
    { name: 'Documents', href: '/documents', icon: FileText },
    { name: 'Project Timeline', href: '/timeline', icon: Calendar },
    { name: 'Chat', href: '/chat', icon: MessageSquare },
    { name: 'Consulting Hours', href: '/billable', icon: Clock },
    { name: 'Users', href: '/users', icon: Users, adminOnly: true },
    { name: 'Settings', href: '/settings', icon: Settings },
  ]

  const filteredNavigation = navigation.filter(
    (item) => !item.adminOnly || user?.is_admin
  )

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar for mobile */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div
            className="fixed inset-0 bg-gray-600 bg-opacity-75"
            onClick={() => setSidebarOpen(false)}
          />
          <nav className="fixed inset-y-0 left-0 flex w-64 flex-col bg-white">
            <div className="flex h-16 items-center justify-between px-4">
              <span className="text-xl font-bold text-gray-900">PwC SR&ED Intelligence</span>
              <button
                onClick={() => setSidebarOpen(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                <X className="h-6 w-6" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto">
              {filteredNavigation.map((item) => (
                <Link
                  key={item.name}
                  to={item.href}
                  className="flex items-center px-4 py-3 text-gray-700 hover:bg-gray-100"
                  onClick={() => setSidebarOpen(false)}
                >
                  <item.icon className="mr-3 h-5 w-5" />
                  {item.name}
                </Link>
              ))}
            </div>
          </nav>
        </div>
      )}

      {/* Sidebar for desktop */}
      <div className="hidden lg:flex lg:w-64 lg:flex-col">
        <div className="flex flex-col flex-1 border-r border-gray-200 bg-white">
          <div className="flex h-16 items-center border-b border-gray-200 px-4">
            <span className="text-xl font-bold text-gray-900">PwC SR&ED Intelligence</span>
          </div>
          <nav className="flex-1 space-y-1 px-2 py-4">
            {filteredNavigation.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                className="group flex items-center rounded-md px-2 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 hover:text-gray-900"
              >
                <item.icon className="mr-3 h-5 w-5 flex-shrink-0 text-gray-400 group-hover:text-gray-500" />
                {item.name}
              </Link>
            ))}
          </nav>
        </div>
      </div>

      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top bar */}
        <header className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-4 lg:px-6">
          <button
            onClick={() => setSidebarOpen(true)}
            className="text-gray-500 hover:text-gray-700 lg:hidden"
          >
            <Menu className="h-6 w-6" />
          </button>

          <div className="flex items-center space-x-4">
            {/* Company name */}
            <div className="hidden text-sm text-gray-600 sm:block">
              {company?.name}
            </div>

            {/* Help button */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setHelpOpen(true)}
              title="Help & Support"
            >
              <HelpCircle className="h-5 w-5" />
            </Button>

            {/* User menu */}
            <div className="flex items-center space-x-2">
              <Link to="/profile">
                <Button variant="ghost" size="sm">
                  <User className="mr-2 h-4 w-4" />
                  {user?.first_name || user?.email}
                </Button>
              </Link>

              <Button variant="ghost" size="sm" onClick={handleLogout}>
                <LogOut className="mr-2 h-4 w-4" />
                Logout
              </Button>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>

      {/* Help Desk Modal */}
      <HelpDeskModal isOpen={helpOpen} onClose={() => setHelpOpen(false)} />
    </div>
  )
}
