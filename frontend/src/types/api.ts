export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

export interface UserProfile {
  id: number
  username: string
  nickname: string
  is_active: boolean
  created_at: string
}

export interface AuthTokens {
  access_token: string
  token_type: string
  expires_at: string
}

export interface AuthPayload {
  user: UserProfile
  tokens: AuthTokens
}

export interface LoginPayload {
  username: string
  password: string
}

export interface RegisterPayload extends LoginPayload {
  nickname?: string
}

export interface UpdateProfilePayload {
  nickname: string
}

export interface CreateFamilyPayload {
  name: string
  description?: string
}

export interface JoinFamilyPayload {
  invite_code: string
}

export interface FamilyMember {
  id: number
  family_id: number
  user_id: number
  role: 'owner' | 'member'
  joined_at: string
  user: UserProfile
}

export interface FamilyProfile {
  id: number
  name: string
  description: string | null
  cover_url: string | null
  invite_code: string
  owner_id: number
  max_members: number
  created_at: string
  updated_at: string
  members: FamilyMember[]
}

export interface FamilyAccessPayload {
  family: FamilyProfile
  needs_onboarding: boolean
}

export interface HealthCheckData {
  app_name: string
  environment: string
  status: 'ok' | 'degraded'
  database: {
    status: 'up' | 'down'
    host: string
    name: string
  }
}
