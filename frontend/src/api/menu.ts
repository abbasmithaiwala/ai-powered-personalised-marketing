import { apiClient } from './client';
import type {
  MenuItem,
  MenuItemCreate,
  PaginatedResponse,
  PDFParseResponse,
  BulkCreateRequest,
  BulkCreateResponse,
} from '@/types/api';

export const menuApi = {
  // List menu items with filters
  list: async (params?: {
    brandId?: string;
    category?: string;
    cuisine?: string;
    dietaryTag?: string;
    page?: number;
    pageSize?: number;
  }) => {
    const queryParams = new URLSearchParams();
    if (params?.brandId) queryParams.append('brand_id', params.brandId);
    if (params?.category) queryParams.append('category', params.category);
    if (params?.cuisine) queryParams.append('cuisine', params.cuisine);
    if (params?.dietaryTag) queryParams.append('dietary_tag', params.dietaryTag);
    if (params?.page) queryParams.append('page', String(params.page));
    if (params?.pageSize) queryParams.append('page_size', String(params.pageSize));

    const response = await apiClient.get<PaginatedResponse<MenuItem>>(
      `/menu-items?${queryParams.toString()}`
    );
    return response.data;
  },

  // Get menu item by ID
  get: async (id: string) => {
    const response = await apiClient.get<MenuItem>(`/menu-items/${id}`);
    return response.data;
  },

  // Create menu item
  create: async (data: MenuItemCreate) => {
    const response = await apiClient.post<MenuItem>('/menu-items', data);
    return response.data;
  },

  // Update menu item
  update: async (id: string, data: Partial<MenuItemCreate>) => {
    const response = await apiClient.put<MenuItem>(`/menu-items/${id}`, data);
    return response.data;
  },

  // Delete menu item (soft delete)
  delete: async (id: string) => {
    await apiClient.delete(`/menu-items/${id}`);
  },

  // Parse a PDF menu via OCR (multipart/form-data — no DB write)
  parsePdf: async (file: File, brandId: string): Promise<PDFParseResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('brand_id', brandId);
    const response = await apiClient.post<PDFParseResponse>(
      '/menu-items/parse-pdf',
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 120000 }
    );
    return response.data;
  },

  // Bulk create items from the reviewed OCR-parsed list
  bulkCreate: async (data: BulkCreateRequest): Promise<BulkCreateResponse> => {
    const response = await apiClient.post<BulkCreateResponse>(
      '/menu-items/bulk-create',
      data,
      { timeout: 60000 }
    );
    return response.data;
  },
};
