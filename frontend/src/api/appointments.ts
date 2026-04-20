import { api } from './client'

export interface ServiceSummary {
  id: string
  service_code: string
  name: string
  duration_minutes: number
  processing_offset_minutes: number
  processing_duration_minutes: number
}

export interface ProviderSummary {
  id: string
  display_name: string
  provider_type: 'stylist' | 'colourist' | 'dualist'
}

export interface ClientSummary {
  id: string
  first_name: string
  last_name: string
  cell_phone: string | null
  special_instructions: string | null
}

export interface AppointmentItem {
  id: string
  service: ServiceSummary
  provider: ProviderSummary
  second_provider: ProviderSummary | null
  sequence: number
  start_time: string
  duration_minutes: number
  duration_override_minutes: number | null
  price: number
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled'
  notes: string | null
}

export interface Appointment {
  id: string
  appointment_date: string
  status: 'confirmed' | 'in_progress' | 'completed' | 'cancelled' | 'no_show'
  source: string
  notes: string | null
  client: ClientSummary
  items: AppointmentItem[]
}

export function listAppointments(date: string): Promise<Appointment[]> {
  return api.get<Appointment[]>(`/appointments?date=${date}`)
}

export function getAppointment(id: string): Promise<Appointment> {
  return api.get<Appointment>(`/appointments/${id}`)
}

export function updateAppointmentStatus(
  id: string,
  status: Appointment['status'],
): Promise<Appointment> {
  return api.patch<Appointment>(`/appointments/${id}/status`, { status })
}
