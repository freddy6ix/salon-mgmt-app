import { api } from './client'

export interface TimeBlock {
  id: string
  provider_id: string
  start_time: string  // ISO without timezone
  duration_minutes: number
  note: string | null
}

export interface TimeBlockIn {
  provider_id: string
  start_time: string
  duration_minutes: number
  note?: string | null
}

export interface TimeBlockPatch {
  provider_id?: string
  start_time?: string
  duration_minutes?: number
  note?: string | null
}

export function listTimeBlocks(date: string): Promise<TimeBlock[]> {
  return api.get<TimeBlock[]>(`/time-blocks?date=${date}`)
}

export function createTimeBlock(body: TimeBlockIn): Promise<TimeBlock> {
  return api.post<TimeBlock>('/time-blocks', body)
}

export function updateTimeBlock(id: string, body: TimeBlockPatch): Promise<TimeBlock> {
  return api.patch<TimeBlock>(`/time-blocks/${id}`, body)
}

export function deleteTimeBlock(id: string): Promise<void> {
  return api.delete<void>(`/time-blocks/${id}`)
}
