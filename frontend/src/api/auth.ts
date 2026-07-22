import http from '@/api/http'
import type {
  ApiResponse,
  AuthPayload,
  LoginPayload,
  RegisterPayload,
  UpdateProfilePayload,
  UserProfile,
} from '@/types/api'

export async function login(payload: LoginPayload): Promise<AuthPayload> {
  const { data } = await http.post<ApiResponse<AuthPayload>>('/auth/login', payload)
  return data.data
}

export async function register(payload: RegisterPayload): Promise<AuthPayload> {
  const { data } = await http.post<ApiResponse<AuthPayload>>('/auth/register', payload)
  return data.data
}

export async function fetchCurrentUser(): Promise<UserProfile> {
  const { data } = await http.get<ApiResponse<UserProfile>>('/auth/me')
  return data.data
}

export async function updateProfile(payload: UpdateProfilePayload): Promise<UserProfile> {
  const { data } = await http.patch<ApiResponse<UserProfile>>('/auth/me', payload)
  return data.data
}
