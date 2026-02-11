import { apiClient } from './client';
import type { IngestionJob, IngestionUploadResponse, PaginatedResponse } from '@/types/api';

export const ingestionApi = {
  // Upload CSV file
  upload: async (file: File, csvType: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('csv_type', csvType);

    const response = await apiClient.post<IngestionUploadResponse>(
      '/ingestion/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  // List ingestion jobs
  listJobs: async (page = 1, pageSize = 10) => {
    const response = await apiClient.get<PaginatedResponse<IngestionJob>>(
      `/ingestion/jobs?page=${page}&page_size=${pageSize}`
    );
    return response.data;
  },

  // Get job by ID
  getJob: async (jobId: string) => {
    const response = await apiClient.get<IngestionJob>(`/ingestion/jobs/${jobId}`);
    return response.data;
  },
};
