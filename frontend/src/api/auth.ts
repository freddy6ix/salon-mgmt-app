import { api, setToken } from './client'

export interface MeResponse {
  id: string
  email: string
  role: string
  tenant_id: string
}

export async function login(email: string, password: string): Promise<MeResponse> {
  const { access_token } = await api.post<{ access_token: string }>('/auth/login', {
    email,
    password,
  })
  setToken(access_token)
  return api.get<MeResponse>('/auth/me')
}

export function getMe(): Promise<MeResponse> {
  return api.get<MeResponse>('/auth/me')
}
