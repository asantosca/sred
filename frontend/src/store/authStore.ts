// Auth store using Zustand for state management

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User, Company, AuthResponse } from '@/types/auth'
import { authApi } from '@/lib/api'

interface AuthState {
  user: User | null
  company: Company | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null

  // Actions
  setAuth: (data: AuthResponse) => void
  setTokens: (accessToken: string, refreshToken?: string) => void
  clearAuth: () => void
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
  setError: (error: string | null) => void
  setLoading: (loading: boolean) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      company: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      setAuth: (data: AuthResponse) => {
        const { user, company, token } = data

        // Store tokens in localStorage
        localStorage.setItem('access_token', token.access_token)
        if (token.refresh_token) {
          localStorage.setItem('refresh_token', token.refresh_token)
        }

        set({
          user,
          company,
          accessToken: token.access_token,
          refreshToken: token.refresh_token || null,
          isAuthenticated: true,
          error: null,
        })
      },

      setTokens: (accessToken: string, refreshToken?: string) => {
        localStorage.setItem('access_token', accessToken)
        if (refreshToken) {
          localStorage.setItem('refresh_token', refreshToken)
        }

        set({
          accessToken,
          refreshToken: refreshToken || get().refreshToken,
        })
      },

      clearAuth: () => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')

        set({
          user: null,
          company: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          error: null,
        })
      },

      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null })
        try {
          const response = await authApi.login({ email, password })
          get().setAuth(response.data)
        } catch (error: any) {
          const errorMessage =
            error.response?.data?.detail || 'Login failed. Please try again.'
          set({ error: errorMessage })
          throw error
        } finally {
          set({ isLoading: false })
        }
      },

      logout: async () => {
        const refreshToken = get().refreshToken
        if (refreshToken) {
          try {
            await authApi.logout(refreshToken)
          } catch (error) {
            // Ignore errors on logout - just clear local state
            console.error('Logout error:', error)
          }
        }
        get().clearAuth()
      },

      refreshUser: async () => {
        set({ isLoading: true, error: null })
        try {
          const response = await authApi.me()
          const { user, company, token } = response.data

          set({
            user,
            company,
            accessToken: token.access_token,
            isAuthenticated: true,
            error: null,
          })
        } catch (error: any) {
          const errorMessage =
            error.response?.data?.detail ||
            'Failed to refresh user data. Please log in again.'
          set({ error: errorMessage })
          get().clearAuth()
          throw error
        } finally {
          set({ isLoading: false })
        }
      },

      setError: (error: string | null) => set({ error }),
      setLoading: (loading: boolean) => set({ isLoading: loading }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        company: state.company,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)
