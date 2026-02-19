import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { customersApi } from '@/api/customers';
import { brandsApi } from '@/api/brands';
import { menuApi } from '@/api/menu';
import { ingestionApi } from '@/api/ingestion';
import { campaignsApi } from '@/api/campaigns';
import type { BulkCreateRequest } from '@/types/api';

// Query keys
export const queryKeys = {
  customers: {
    all: ['customers'] as const,
    list: (page: number) => [...queryKeys.customers.all, 'list', page] as const,
    detail: (id: string) => [...queryKeys.customers.all, 'detail', id] as const,
    preferences: (id: string) => [...queryKeys.customers.all, 'preferences', id] as const,
    recommendations: (id: string) => [...queryKeys.customers.all, 'recommendations', id] as const,
    orders: (id: string) => [...queryKeys.customers.all, 'orders', id] as const,
  },
  brands: {
    all: ['brands'] as const,
    list: () => [...queryKeys.brands.all, 'list'] as const,
    detail: (id: string) => [...queryKeys.brands.all, 'detail', id] as const,
  },
  menu: {
    all: ['menu'] as const,
    list: (params?: any) => [...queryKeys.menu.all, 'list', params] as const,
    detail: (id: string) => [...queryKeys.menu.all, 'detail', id] as const,
  },
  ingestion: {
    all: ['ingestion'] as const,
    jobs: (page: number) => [...queryKeys.ingestion.all, 'jobs', page] as const,
    job: (id: string) => [...queryKeys.ingestion.all, 'job', id] as const,
  },
  campaigns: {
    all: ['campaigns'] as const,
    list: (page: number) => [...queryKeys.campaigns.all, 'list', page] as const,
    detail: (id: string) => [...queryKeys.campaigns.all, 'detail', id] as const,
    recipients: (id: string, page: number) => [
      ...queryKeys.campaigns.all,
      'recipients',
      id,
      page,
    ] as const,
  },
};

// Customer hooks
export const useCustomers = (page = 1, pageSize = 25) => {
  return useQuery({
    queryKey: queryKeys.customers.list(page),
    queryFn: () => customersApi.list(page, pageSize),
  });
};

export const useCustomer = (id: string) => {
  return useQuery({
    queryKey: queryKeys.customers.detail(id),
    queryFn: () => customersApi.get(id),
    enabled: !!id,
  });
};

export const useCustomerPreferences = (id: string) => {
  return useQuery({
    queryKey: queryKeys.customers.preferences(id),
    queryFn: () => customersApi.getPreferences(id),
    enabled: !!id,
  });
};

export const useCustomerRecommendations = (id: string, limit = 5) => {
  return useQuery({
    queryKey: queryKeys.customers.recommendations(id),
    queryFn: () => customersApi.getRecommendations(id, limit),
    enabled: !!id,
  });
};

export const useCustomerOrders = (id: string, page = 1) => {
  return useQuery({
    queryKey: queryKeys.customers.orders(id),
    queryFn: () => customersApi.getOrders(id, page),
    enabled: !!id,
  });
};

// Brand hooks
export const useBrands = () => {
  return useQuery({
    queryKey: queryKeys.brands.list(),
    queryFn: () => brandsApi.list(),
  });
};

export const useBrand = (id: string) => {
  return useQuery({
    queryKey: queryKeys.brands.detail(id),
    queryFn: () => brandsApi.get(id),
    enabled: !!id,
  });
};

// Menu hooks
export const useMenuItems = (params?: any) => {
  return useQuery({
    queryKey: queryKeys.menu.list(params),
    queryFn: () => menuApi.list(params),
  });
};

export const useMenuItem = (id: string) => {
  return useQuery({
    queryKey: queryKeys.menu.detail(id),
    queryFn: () => menuApi.get(id),
    enabled: !!id,
  });
};

// Ingestion hooks
export const useIngestionJobs = (page = 1) => {
  return useQuery({
    queryKey: queryKeys.ingestion.jobs(page),
    queryFn: () => ingestionApi.listJobs(page),
  });
};

export const useIngestionJob = (id: string) => {
  return useQuery({
    queryKey: queryKeys.ingestion.job(id),
    queryFn: () => ingestionApi.getJob(id),
    enabled: !!id,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      // Poll every 2 seconds if processing
      return status === 'processing' ? 2000 : false;
    },
  });
};

// Campaign hooks
export const useCampaigns = (page = 1) => {
  return useQuery({
    queryKey: queryKeys.campaigns.list(page),
    queryFn: () => campaignsApi.list(page),
  });
};

export const useCampaign = (id: string) => {
  return useQuery({
    queryKey: queryKeys.campaigns.detail(id),
    queryFn: () => campaignsApi.get(id),
    enabled: !!id,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      // Poll every 3 seconds if executing
      return status === 'executing' ? 3000 : false;
    },
  });
};

export const useCampaignRecipients = (id: string, page = 1) => {
  return useQuery({
    queryKey: queryKeys.campaigns.recipients(id, page),
    queryFn: () => campaignsApi.listRecipients(id, page),
    enabled: !!id,
  });
};

// Mutation hooks
export const useUploadCSV = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ file, csvType }: { file: File; csvType: string }) =>
      ingestionApi.upload(file, csvType),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.ingestion.all });
    },
  });
};

export const useCreateCampaign = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: campaignsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.campaigns.all });
    },
  });
};

export const useExecuteCampaign = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => campaignsApi.execute(id),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.campaigns.detail(id) });
    },
  });
};

// PDF import hooks
export const useParsePDF = () => {
  return useMutation({
    mutationFn: ({ file, brandId }: { file: File; brandId: string }) =>
      menuApi.parsePdf(file, brandId),
  });
};

export const useBulkCreateMenuItems = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: BulkCreateRequest) => menuApi.bulkCreate(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.menu.all });
    },
  });
};
