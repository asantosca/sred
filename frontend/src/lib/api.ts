// API client with axios and auth interceptors

import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import type {
  AuthResponse,
  LoginRequest,
  RegistrationRequest,
  RegistrationResponse,
  PasswordResetRequest,
  PasswordResetConfirm,
  PasswordChange,
  UserProfileUpdate,
  AvatarUploadResponse,
  RefreshTokenRequest,
  Token,
} from '@/types/auth'

// Create axios instance
const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean
    }

    // If error is 401 and we haven't retried yet, try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const { data } = await axios.post<Token>('/api/v1/auth/refresh', {
            refresh_token: refreshToken,
          })

          // Update tokens in localStorage
          localStorage.setItem('access_token', data.access_token)
          if (data.refresh_token) {
            localStorage.setItem('refresh_token', data.refresh_token)
          }

          // Retry original request with new token
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${data.access_token}`
          }
          return api(originalRequest)
        } catch (refreshError) {
          // Refresh failed, clear tokens and redirect to login
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
          return Promise.reject(refreshError)
        }
      }
    }

    return Promise.reject(error)
  }
)

// Auth API endpoints
export const authApi = {
  // Login
  login: (data: LoginRequest) =>
    api.post<AuthResponse>('/auth/login', data),

  // Register new company
  register: (data: RegistrationRequest) =>
    api.post<RegistrationResponse>('/auth/register', data),

  // Get current user
  me: () => api.get<AuthResponse>('/auth/me'),

  // Logout
  logout: (refresh_token: string) =>
    api.post('/auth/logout', { refresh_token }),

  // Refresh token
  refresh: (data: RefreshTokenRequest) =>
    api.post<Token>('/auth/refresh', data),

  // Password reset request
  requestPasswordReset: (data: PasswordResetRequest) =>
    api.post('/auth/password-reset/request', data),

  // Verify password reset token
  verifyPasswordResetToken: (token: string) =>
    api.get(`/auth/password-reset/verify?token=${token}`),

  // Confirm password reset
  confirmPasswordReset: (data: PasswordResetConfirm) =>
    api.post<AuthResponse>('/auth/password-reset/confirm', data),

  // Verify email confirmation token
  verifyEmailConfirmationToken: (token: string) =>
    api.get(`/auth/confirm-email/verify?token=${token}`),

  // Confirm email (activate account)
  confirmEmail: (token: string) =>
    api.get<AuthResponse>(`/auth/confirm-email?token=${token}`),

  // Change password
  changePassword: (data: PasswordChange) =>
    api.post('/auth/change-password', data),
}

// User API endpoints
export const userApi = {
  // Get my profile
  getMyProfile: () => api.get('/users/me'),

  // Update my profile
  updateMyProfile: (data: UserProfileUpdate) =>
    api.patch('/users/me', data),

  // Upload avatar
  uploadAvatar: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post<AvatarUploadResponse>('/users/me/avatar', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },
}

export default api
