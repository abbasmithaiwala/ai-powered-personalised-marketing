import { apiClient } from './client';
import type {
  Campaign,
  CampaignCreate,
  CampaignRecipient,
  PaginatedResponse,
} from '@/types/api';

export const campaignsApi = {
  // List campaigns
  list: async (page = 1, pageSize = 25) => {
    const response = await apiClient.get<PaginatedResponse<Campaign>>(
      `/campaigns?page=${page}&page_size=${pageSize}`
    );
    return response.data;
  },

  // Get campaign by ID
  get: async (id: string) => {
    const response = await apiClient.get<Campaign>(`/campaigns/${id}`);
    return response.data;
  },

  // Create campaign
  create: async (data: CampaignCreate) => {
    const response = await apiClient.post<Campaign>('/campaigns', data);
    return response.data;
  },

  // Update campaign
  update: async (id: string, data: Partial<CampaignCreate>) => {
    const response = await apiClient.put<Campaign>(`/campaigns/${id}`, data);
    return response.data;
  },

  // Preview campaign (generate 3 sample messages)
  preview: async (id: string) => {
    const response = await apiClient.post<{ recipients: CampaignRecipient[] }>(
      `/campaigns/${id}/preview`
    );
    return response.data;
  },

  // Execute campaign (generate all messages)
  execute: async (id: string) => {
    const response = await apiClient.post<Campaign>(`/campaigns/${id}/execute`);
    return response.data;
  },

  // List campaign recipients
  listRecipients: async (id: string, page = 1, pageSize = 25) => {
    const response = await apiClient.get<PaginatedResponse<CampaignRecipient>>(
      `/campaigns/${id}/recipients?page=${page}&page_size=${pageSize}`
    );
    return response.data;
  },
};
