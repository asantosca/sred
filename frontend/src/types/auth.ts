// Frontend types matching backend schemas

export interface User {
  id: string
  email: string
  first_name: string | null
  last_name: string | null
  avatar_url: string | null
  is_active: boolean
  is_admin: boolean
  company_id: string
  created_at: string
  last_active: string | null
}

export interface Company {
  id: string
  name: string
  plan_tier: string
  subscription_status: string
  created_at: string
}

export interface Token {
  access_token: string
  token_type: string
  expires_in: number
  refresh_token?: string
}

export interface AuthResponse {
  user: User
  company: Company
  token: Token
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegistrationRequest {
  company_name: string
  admin_email: string
  admin_password: string
  admin_first_name?: string
  admin_last_name?: string
  plan_tier?: string
}

export interface RegistrationResponse {
  user: User
  company: Company
  message: string
  token: string
}

export interface PasswordResetRequest {
  email: string
}

export interface PasswordResetConfirm {
  token: string
  new_password: string
}

export interface PasswordChange {
  current_password: string
  new_password: string
}

export interface UserProfileUpdate {
  first_name?: string
  last_name?: string
}

export interface AvatarUploadResponse {
  avatar_url: string
  message: string
}

export interface RefreshTokenRequest {
  refresh_token: string
}

export interface ApiError {
  detail: string
}
