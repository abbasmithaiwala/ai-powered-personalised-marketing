import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { menuApi } from '@/api/menu';
import { brandsApi } from '@/api/brands';
import { Card, Button } from '@/components/ui';
import { MenuItemCard } from './components/MenuItemCard';
import { MenuItemFilters } from './components/MenuItemFilters';

interface FilterState {
  brandId?: string;
  category?: string;
  cuisine?: string;
  dietaryTag?: string;
}

export const MenuItems = () => {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<FilterState>({});
  const pageSize = 20;

  const { data: itemsData, isLoading: itemsLoading } = useQuery({
    queryKey: ['menu-items', page, filters],
    queryFn: () => menuApi.list({ ...filters, page, pageSize }),
  });

  const { data: brandsData } = useQuery({
    queryKey: ['brands'],
    queryFn: () => brandsApi.list(),
  });

  const handleFilterChange = (newFilters: FilterState) => {
    setFilters(newFilters);
    setPage(1);
  };

  const clearFilters = () => {
    setFilters({});
    setPage(1);
  };

  const hasActiveFilters = Object.keys(filters).length > 0;
  const items = itemsData?.items || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Menu Items</h1>
          <p className="mt-2 text-gray-600">
            Browse and filter all menu items across brands
          </p>
        </div>
        <Link to="/menu">
          <Button variant="secondary">Back to Menu</Button>
        </Link>
      </div>

      {/* Filters */}
      <MenuItemFilters
        brands={brandsData?.items || []}
        filters={filters}
        onFilterChange={handleFilterChange}
      />

      {/* Results Summary */}
      {itemsData && !itemsLoading && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-700">
            Showing {(page - 1) * pageSize + 1} to{' '}
            {Math.min(page * pageSize, itemsData.total)} of {itemsData.total} items
          </p>
          {hasActiveFilters && (
            <Button variant="secondary" size="sm" onClick={clearFilters}>
              Clear Filters
            </Button>
          )}
        </div>
      )}

      {/* Items Grid */}
      {itemsLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Card key={i} className="animate-pulse">
              <div className="h-48 bg-gray-200 rounded"></div>
            </Card>
          ))}
        </div>
      ) : items.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <p className="text-gray-600">
              {hasActiveFilters
                ? 'No items match your filters. Try adjusting your search.'
                : 'No menu items found. Import order data to get started.'}
            </p>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {items.map((item) => (
            <MenuItemCard
              key={item.id}
              item={item}
              brandName={
                brandsData?.items.find((b) => b.id === item.brand_id)?.name ||
                'Unknown Brand'
              }
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {itemsData && itemsData.pages > 1 && (
        <div className="flex items-center justify-between bg-white rounded-lg shadow px-6 py-4">
          <div className="text-sm text-gray-700">
            Page {itemsData.page} of {itemsData.pages}
          </div>
          <div className="flex gap-2">
            <Button
              variant="secondary"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1 || itemsLoading}
            >
              Previous
            </Button>
            <Button
              variant="secondary"
              onClick={() => setPage((p) => Math.min(itemsData.pages, p + 1))}
              disabled={page === itemsData.pages || itemsLoading}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
