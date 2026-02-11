import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { customersApi } from '@/api/customers';
import { CustomerTable } from './components/CustomerTable';
import { CustomerFilters } from './components/CustomerFilters';
import { Button } from '@/components/ui';
import type { SegmentFilters } from '@/types/api';

export const Customers = () => {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<SegmentFilters>({});
  const [isFiltering, setIsFiltering] = useState(false);
  const pageSize = 25;

  // Use search API if filters are active, otherwise use list API
  const { data, isLoading, error } = useQuery({
    queryKey: ['customers', page, filters, isFiltering],
    queryFn: () => {
      if (isFiltering && Object.keys(filters).length > 0) {
        return customersApi.search(filters, page, pageSize);
      }
      return customersApi.list(page, pageSize);
    },
  });

  const handleFilterChange = (newFilters: SegmentFilters) => {
    setFilters(newFilters);
    setIsFiltering(Object.keys(newFilters).length > 0);
    setPage(1); // Reset to first page when filters change
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Customers</h1>
          <p className="mt-2 text-gray-600">
            Browse and manage customer profiles, preferences, and order history
          </p>
        </div>
      </div>

      {/* Filters */}
      <CustomerFilters onFilterChange={handleFilterChange} />

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Failed to load customers. Please try again.</p>
        </div>
      )}

      {/* Results Summary */}
      {data && !isLoading && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-700">
            Showing {(page - 1) * pageSize + 1} to{' '}
            {Math.min(page * pageSize, data.total)} of {data.total} customers
          </p>
          {isFiltering && (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                setFilters({});
                setIsFiltering(false);
                setPage(1);
              }}
            >
              Clear Filters
            </Button>
          )}
        </div>
      )}

      {/* Table */}
      <CustomerTable customers={data?.items || []} isLoading={isLoading} />

      {/* Pagination */}
      {data && data.pages > 1 && (
        <div className="flex items-center justify-between bg-white rounded-lg shadow px-6 py-4">
          <div className="text-sm text-gray-700">
            Page {data.page} of {data.pages}
          </div>
          <div className="flex gap-2">
            <Button
              variant="secondary"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1 || isLoading}
            >
              Previous
            </Button>
            <Button
              variant="secondary"
              onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
              disabled={page === data.pages || isLoading}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
