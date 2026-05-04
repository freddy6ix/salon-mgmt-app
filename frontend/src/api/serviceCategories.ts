import { api } from './client'

export interface ServiceCategory {
  id: string
  name: string
  display_order: number
  is_active: boolean
  translations?: Record<string, { name?: string | null }>
}

export interface ServiceCategoryIn {
  name: string
  display_order?: number
  is_active?: boolean
  translations?: Record<string, { name?: string | null }>
}

export type ServiceCategoryPatch = Partial<ServiceCategoryIn>

export function listServiceCategories(): Promise<ServiceCategory[]> {
  return api.get<ServiceCategory[]>('/service-categories')
}

export function getServiceCategory(id: string): Promise<ServiceCategory> {
  return api.get<ServiceCategory>(`/service-categories/${id}`)
}

export function createServiceCategory(body: ServiceCategoryIn): Promise<ServiceCategory> {
  return api.post<ServiceCategory>('/service-categories', body)
}

export function updateServiceCategory(id: string, body: ServiceCategoryPatch): Promise<ServiceCategory> {
  return api.patch<ServiceCategory>(`/service-categories/${id}`, body)
}
