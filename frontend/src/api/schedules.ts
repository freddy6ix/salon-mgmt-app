import { api } from './client'

export interface ProviderWorkStatus {
  provider_id: string
  display_name: string
  booking_order: number
  is_working: boolean
  start_time: string | null  // "HH:MM"
  end_time: string | null
}

export interface DayHours {
  day_of_week: number  // 0=Mon … 6=Sun
  is_working: boolean
  start_time: string | null
  end_time: string | null
}

export interface ProviderWeeklyHours {
  provider_id: string
  display_name: string
  booking_order: number
  days: DayHours[]
}

export function getSchedule(date: string): Promise<ProviderWorkStatus[]> {
  return api.get<ProviderWorkStatus[]>(`/schedules?date=${date}`)
}

export function getWeeklySchedules(): Promise<ProviderWeeklyHours[]> {
  return api.get<ProviderWeeklyHours[]>('/schedules/weekly')
}

export function setWeeklySchedule(provider_id: string, days: DayHours[]): Promise<ProviderWeeklyHours> {
  return api.put<ProviderWeeklyHours>(`/schedules/weekly/${provider_id}`, { days })
}

export function setWorkingStatus(provider_id: string, date: string, is_working: boolean): Promise<ProviderWorkStatus> {
  return api.post<ProviderWorkStatus>('/schedules', { provider_id, date, is_working })
}
