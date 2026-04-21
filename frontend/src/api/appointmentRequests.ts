import { api } from './client'

export interface RequestItem {
  id: string
  sequence: number
  service_name: string
  preferred_provider_name: string
}

export interface AppointmentRequest {
  id: string
  status: 'new' | 'reviewed' | 'converted' | 'declined'
  desired_date: string
  desired_time_note: string | null
  special_note: string | null
  submitted_at: string
  staff_notes: string | null
  first_name: string
  last_name: string
  email: string
  items: RequestItem[]
}

export interface RequestItemIn {
  service_name: string
  preferred_provider_name: string
  sequence: number
}

export interface AppointmentRequestIn {
  desired_date: string
  desired_time_note?: string
  special_note?: string
  items: RequestItemIn[]
}

export function createRequest(body: AppointmentRequestIn): Promise<AppointmentRequest> {
  return api.post<AppointmentRequest>('/appointment-requests', body)
}

export function listMyRequests(): Promise<AppointmentRequest[]> {
  return api.get<AppointmentRequest[]>('/appointment-requests')
}

export function listAllRequests(status?: string): Promise<AppointmentRequest[]> {
  const qs = status ? `?status=${status}` : ''
  return api.get<AppointmentRequest[]>(`/appointment-requests${qs}`)
}

export function reviewRequest(
  id: string,
  body: { status: AppointmentRequest['status']; staff_notes?: string },
): Promise<AppointmentRequest> {
  return api.patch<AppointmentRequest>(`/appointment-requests/${id}`, body)
}
