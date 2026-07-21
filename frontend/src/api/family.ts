import http from '@/api/http'
import type {
  ApiResponse,
  CreateFamilyPayload,
  FamilyAccessPayload,
  FamilyMember,
  FamilyProfile,
  JoinFamilyPayload,
} from '@/types/api'

export async function createFamily(payload: CreateFamilyPayload): Promise<FamilyAccessPayload> {
  const { data } = await http.post<ApiResponse<FamilyAccessPayload>>('/families', payload)
  return data.data
}

export async function joinFamily(payload: JoinFamilyPayload): Promise<FamilyAccessPayload> {
  const { data } = await http.post<ApiResponse<FamilyAccessPayload>>('/families/join', payload)
  return data.data
}

export async function fetchCurrentFamily(): Promise<FamilyProfile> {
  const { data } = await http.get<ApiResponse<FamilyProfile>>('/families/current')
  return data.data
}

export async function fetchCurrentFamilyMembers(): Promise<FamilyMember[]> {
  const { data } = await http.get<ApiResponse<FamilyMember[]>>('/families/current/members')
  return data.data
}
