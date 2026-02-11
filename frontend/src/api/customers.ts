import { apiClient } from './client';
import type {
  Customer,
  CustomerPreference,
  PaginatedResponse,
  SegmentFilters,
  SegmentCountResponse,
  RecommendationResponse,
  Order,
} from '@/types/api';

export const customersApi = {
  // List customers with pagination
  list: async (page = 1, pageSize = 25) => {
    const response = await apiClient.get<PaginatedResponse<Customer>>(
      `/customers?page=${page}&page_size=${pageSize}`
    );
    return response.data;
  },

  // Get customer by ID
  get: async (id: string) => {
    const response = await apiClient.get<Customer>(`/customers/${id}`);
    return response.data;
  },

  // Get customer preferences
  getPreferences: async (id: string) => {
    const response = await apiClient.get<CustomerPreference>(`/customers/${id}/preferences`);
    return response.data;
  },

  // Get customer recommendations
  getRecommendations: async (id: string, limit = 5) => {
    const response = await apiClient.get<RecommendationResponse>(
      `/customers/${id}/recommendations?limit=${limit}`
    );
    return response.data;
  },

  // Get customer order history
  getOrders: async (id: string, page = 1, pageSize = 20) => {
    const response = await apiClient.get<PaginatedResponse<Order>>(
      `/customers/${id}/orders?page=${page}&page_size=${pageSize}`
    );
    return response.data;
  },

  // Recompute customer preferences
  recomputePreferences: async (id: string) => {
    const response = await apiClient.post<CustomerPreference>(
      `/customers/${id}/recompute-preferences`
    );
    return response.data;
  },

  // Search customers with filters
  search: async (filters: SegmentFilters, page = 1, pageSize = 25) => {
    const response = await apiClient.post<PaginatedResponse<Customer>>('/customers/search', {
      filters,
      page,
      page_size: pageSize,
    });
    return response.data;
  },

  // Get segment count
  getSegmentCount: async (filters: SegmentFilters) => {
    const response = await apiClient.post<SegmentCountResponse>('/customers/segment-count', {
      filters,
    });
    return response.data;
  },
};
