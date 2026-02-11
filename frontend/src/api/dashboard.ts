import { apiClient } from './client';
import type { DashboardMetrics } from '@/types/api';

export const dashboardApi = {
  // Get dashboard metrics
  getMetrics: async () => {
    const response = await apiClient.get<DashboardMetrics>('/dashboard/metrics');
    return response.data;
  },
};
