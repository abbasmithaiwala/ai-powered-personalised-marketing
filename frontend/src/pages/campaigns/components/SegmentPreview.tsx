import React, { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { customersApi } from '@/api/customers';
import { ArrowPathIcon } from '@/components/icons';
import type { SegmentFilters } from '@/types/api';

interface SegmentPreviewProps {
  filters: SegmentFilters;
}

export const SegmentPreview: React.FC<SegmentPreviewProps> = ({ filters }) => {
  const {
    data,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['segment-count', filters],
    queryFn: () => customersApi.getSegmentCount(filters),
    enabled: true,
  });

  // Refetch when filters change
  useEffect(() => {
    refetch();
  }, [filters, refetch]);

  return (
    <div className="bg-primary-50 border border-primary-200 rounded-lg p-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-primary-900">
            Estimated Audience
          </p>
          <p className="text-xs text-primary-700 mt-0.5">
            Customers matching your filters
          </p>
        </div>
        <div className="text-right">
          {isLoading ? (
            <div className="flex items-center justify-end">
              <ArrowPathIcon className="animate-spin h-5 w-5 text-primary-600" />
              <span className="ml-2 text-sm text-primary-700">Loading...</span>
            </div>
          ) : error ? (
            <p className="text-sm text-red-600">Error loading count</p>
          ) : (
            <>
              <p className="text-3xl font-bold text-primary-900">
                {data?.count.toLocaleString()}
              </p>
              <p className="text-xs text-primary-700">
                {data?.count === 1 ? 'customer' : 'customers'}
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
