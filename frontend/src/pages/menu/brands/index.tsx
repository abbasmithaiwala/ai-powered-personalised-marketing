import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { brandsApi } from '@/api/brands';
import { menuApi } from '@/api/menu';
import { Card, CardTitle } from '@/components/ui';
import { Button } from '@/components/ui';

export const BrandsList = () => {
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const { data: brandsData, isLoading: brandsLoading } = useQuery({
    queryKey: ['brands', page],
    queryFn: () => brandsApi.list({ page, pageSize }),
  });

  if (brandsLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Brands</h1>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse">
              <div className="h-32 bg-gray-200 rounded"></div>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  const brands = brandsData?.items || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Brands</h1>
          <p className="mt-2 text-gray-600">
            Browse and manage restaurant brands
          </p>
        </div>
        <Link to="/menu">
          <Button variant="secondary">Back to Menu</Button>
        </Link>
      </div>

      {/* Results Summary */}
      {brandsData && !brandsLoading && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-700">
            Showing {(page - 1) * pageSize + 1} to{' '}
            {Math.min(page * pageSize, brandsData.total)} of {brandsData.total} brands
          </p>
        </div>
      )}

      {/* Brand Cards */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          All Brands ({brandsData?.total || 0})
        </h2>
        {brandsLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <Card key={i} className="animate-pulse">
                <div className="h-32 bg-gray-200 rounded"></div>
              </Card>
            ))}
          </div>
        ) : brands.length === 0 ? (
          <Card>
            <div className="text-center py-12">
              <p className="text-gray-600">No brands found. Import order data to get started.</p>
            </div>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {brands.map((brand) => (
              <BrandCard key={brand.id} brand={brand} />
            ))}
          </div>
        )}
      </div>

      {/* Pagination */}
      {brandsData && brandsData.pages > 1 && (
        <div className="flex items-center justify-between bg-white rounded-lg shadow px-6 py-4">
          <div className="text-sm text-gray-700">
            Page {brandsData.page} of {brandsData.pages}
          </div>
          <div className="flex gap-2">
            <Button
              variant="secondary"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1 || brandsLoading}
            >
              Previous
            </Button>
            <Button
              variant="secondary"
              onClick={() => setPage((p) => Math.min(brandsData.pages, p + 1))}
              disabled={page === brandsData.pages || brandsLoading}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

interface BrandCardProps {
  brand: {
    id: string;
    name: string;
    cuisine_type: string | null;
    is_active: boolean;
  };
}

const BrandCard: React.FC<BrandCardProps> = ({ brand }) => {
  const { data: itemsData } = useQuery({
    queryKey: ['menu-items', 'brand', brand.id],
    queryFn: () => menuApi.list({ brandId: brand.id, pageSize: 1 }),
  });

  const itemCount = itemsData?.total || 0;

  return (
    <Link to={`/menu/brands/${brand.id}`}>
      <Card className="hover:shadow-lg transition-shadow cursor-pointer h-full">
        <div className="flex flex-col h-full">
          <div className="flex items-start justify-between mb-3">
            <CardTitle className="flex-1">{brand.name}</CardTitle>
            {!brand.is_active && (
              <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-600 rounded">
                Inactive
              </span>
            )}
          </div>

          {brand.cuisine_type && (
            <p className="text-sm text-gray-600 mb-4 capitalize">
              {brand.cuisine_type}
            </p>
          )}

          <div className="mt-auto pt-4 border-t border-gray-200">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Menu Items</span>
              <span className="font-semibold text-gray-900">{itemCount}</span>
            </div>
          </div>
        </div>
      </Card>
    </Link>
  );
};