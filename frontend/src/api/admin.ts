import { api } from './client'

export interface AdminUser {
  id: string
  email: string
  role: 'super_admin' | 'tenant_admin' | 'staff' | 'guest'
  is_active: boolean
  client_name: string | null
}

export function listUsers(): Promise<AdminUser[]> {
  return api.get<AdminUser[]>('/admin/users')
}

export function createUser(data: {
  email: string
  role: string
  send_welcome: boolean
}): Promise<AdminUser> {
  return api.post<AdminUser>('/admin/users', data)
}

export function updateUser(
  id: string,
  data: { role?: string; is_active?: boolean },
): Promise<AdminUser> {
  return api.patch<AdminUser>(`/admin/users/${id}`, data)
}

export function deleteUser(id: string): Promise<void> {
  return api.delete<void>(`/admin/users/${id}`)
}

export function sendWelcomeEmail(id: string): Promise<void> {
  return api.post<void>(`/admin/users/${id}/send-welcome`, {})
}
