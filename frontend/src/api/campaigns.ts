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
  preview: async (id: string, llmConfig?: { provider: string; model?: string }) => {
    const response = await apiClient.post<{
      campaign_id: string;
      sample_messages: CampaignRecipient[];
      estimated_audience_size: number;
    }>(
      `/campaigns/${id}/preview`,
      {
        sample_size: 3,
        llm_provider: llmConfig?.provider,
        llm_model: llmConfig?.model,
      }
    );
    // Transform the response to match expected format
    return {
      recipients: response.data.sample_messages || [],
      campaign_id: response.data.campaign_id,
      estimated_audience_size: response.data.estimated_audience_size,
    };
  },

  // Execute campaign (generate all messages)
  execute: async (id: string, llmConfig?: { provider: string; model?: string }) => {
    let url = `/campaigns/${id}/execute`;
    if (llmConfig) {
      const params = new URLSearchParams();
      if (llmConfig.provider) params.append('llm_provider', llmConfig.provider);
      if (llmConfig.model) params.append('llm_model', llmConfig.model);
      url += `?${params.toString()}`;
    }
    const response = await apiClient.post<Campaign>(url);
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
