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

// ── Email config ──────────────────────────────────────────────────────────────

export interface EmailConfig {
  is_configured: boolean
  smtp_host: string
  smtp_port: number
  smtp_username: string
  smtp_password_set: boolean
  smtp_use_tls: boolean
  from_address: string
}

export function getEmailConfig(): Promise<EmailConfig> {
  return api.get<EmailConfig>('/admin/email-config')
}

export function saveEmailConfig(data: {
  smtp_host: string
  smtp_port: number
  smtp_username: string
  smtp_password?: string
  smtp_use_tls: boolean
  from_address: string
}): Promise<EmailConfig> {
  return api.put<EmailConfig>('/admin/email-config', data)
}

export function testEmailConfig(to: string): Promise<void> {
  return api.post<void>('/admin/email-config/test', { to })
}
