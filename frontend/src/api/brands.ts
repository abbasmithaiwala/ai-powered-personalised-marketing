import { apiClient } from './client';
import type { Brand, BrandCreate, PaginatedResponse } from '@/types/api';

export const brandsApi = {
  // List all brands with pagination
  list: async (params?: {
    page?: number;
    pageSize?: number;
  }) => {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.append('page', String(params.page));
    if (params?.pageSize) queryParams.append('page_size', String(params.pageSize));

    const response = await apiClient.get<PaginatedResponse<Brand>>(
      `/brands?${queryParams.toString()}`
    );
    return response.data;
  },

  // Get brand by ID
  get: async (id: string) => {
    const response = await apiClient.get<Brand>(`/brands/${id}`);
    return response.data;
  },

  // Create brand
  create: async (data: BrandCreate) => {
    const response = await apiClient.post<Brand>('/brands', data);
    return response.data;
  },

  // Update brand
  update: async (id: string, data: Partial<BrandCreate>) => {
    const response = await apiClient.put<Brand>(`/brands/${id}`, data);
    return response.data;
  },

  // Delete brand (soft delete)
  delete: async (id: string) => {
    await apiClient.delete(`/brands/${id}`);
  },
};
