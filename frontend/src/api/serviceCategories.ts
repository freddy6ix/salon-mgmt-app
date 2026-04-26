import { api } from './client'

export interface ServiceCategory {
  id: string
  name: string
  display_order: number
  is_active: boolean
}

export interface ServiceCategoryIn {
  name: string
  display_order?: number
  is_active?: boolean
}

export type ServiceCategoryPatch = Partial<ServiceCategoryIn>

export function listServiceCategories(): Promise<ServiceCategory[]> {
  return api.get<ServiceCategory[]>('/service-categories')
}

export function createServiceCategory(body: ServiceCategoryIn): Promise<ServiceCategory> {
  return api.post<ServiceCategory>('/service-categories', body)
}

export function updateServiceCategory(id: string, body: ServiceCategoryPatch): Promise<ServiceCategory> {
  return api.patch<ServiceCategory>(`/service-categories/${id}`, body)
}
