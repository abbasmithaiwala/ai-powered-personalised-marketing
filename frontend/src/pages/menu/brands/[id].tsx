import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { brandsApi } from '@/api/brands';
import { menuApi } from '@/api/menu';
import { Card, CardHeader, CardTitle, Badge, Button } from '@/components/ui';
import type { MenuItem } from '@/types/api';

export const BrandDetail = () => {
  const { id } = useParams<{ id: string }>();
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const { data: brand, isLoading: brandLoading } = useQuery({
    queryKey: ['brand', id],
    queryFn: () => brandsApi.get(id!),
    enabled: !!id,
  });

  const { data: itemsData, isLoading: itemsLoading } = useQuery({
    queryKey: ['menu-items', 'brand', id, page],
    queryFn: () => menuApi.list({ brandId: id, page, pageSize }),
    enabled: !!id,
  });

  if (brandLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (!brand) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">Brand not found</p>
        <Link to="/menu">
          <Button variant="secondary" className="mt-4">
            Back to Menu
          </Button>
        </Link>
      </div>
    );
  }

  const items = itemsData?.items || [];

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="flex items-center space-x-2 text-sm text-gray-600">
        <Link to="/menu" className="hover:text-gray-900">
          Menu Catalog
        </Link>
        <span>/</span>
        <span className="text-gray-900">{brand.name}</span>
      </nav>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold text-gray-900">{brand.name}</h1>
            {!brand.is_active && <Badge variant="gray">Inactive</Badge>}
          </div>
          {brand.cuisine_type && (
            <p className="mt-2 text-gray-600 capitalize">{brand.cuisine_type}</p>
          )}
        </div>
        <Link to="/menu/items">
          <Button variant="secondary">View All Items</Button>
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <div className="flex flex-col">
            <span className="text-sm font-medium text-gray-600">Total Items</span>
            <span className="mt-2 text-3xl font-bold text-gray-900">
              {itemsData?.total || 0}
            </span>
          </div>
        </Card>
        <Card>
          <div className="flex flex-col">
            <span className="text-sm font-medium text-gray-600">Available Items</span>
            <span className="mt-2 text-3xl font-bold text-gray-900">
              {items.filter((item) => item.is_available).length}
            </span>
          </div>
        </Card>
        <Card>
          <div className="flex flex-col">
            <span className="text-sm font-medium text-gray-600">Categories</span>
            <span className="mt-2 text-3xl font-bold text-gray-900">
              {new Set(items.map((item) => item.category).filter(Boolean)).size}
            </span>
          </div>
        </Card>
      </div>

      {/* Menu Items */}
      <Card>
        <CardHeader>
          <CardTitle>Menu Items</CardTitle>
        </CardHeader>

        {itemsLoading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse">
                <div className="h-20 bg-gray-200 rounded"></div>
              </div>
            ))}
          </div>
        ) : items.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-600">No menu items found for this brand.</p>
          </div>
        ) : (
          <>
            <div className="space-y-3">
              {items.map((item) => (
                <MenuItem key={item.id} item={item} />
              ))}
            </div>

            {/* Pagination */}
            {itemsData && itemsData.pages > 1 && (
              <div className="flex items-center justify-between mt-6 pt-6 border-t border-gray-200">
                <div className="text-sm text-gray-700">
                  Page {itemsData.page} of {itemsData.pages}
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1 || itemsLoading}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => setPage((p) => Math.min(itemsData.pages, p + 1))}
                    disabled={page === itemsData.pages || itemsLoading}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </Card>
    </div>
  );
};

interface MenuItemProps {
  item: MenuItem;
}

const MenuItem: React.FC<MenuItemProps> = ({ item }) => {
  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <h3 className="font-semibold text-gray-900">{item.name}</h3>
            {!item.is_available && (
              <Badge variant="gray" size="sm">
                Unavailable
              </Badge>
            )}
          </div>

          {item.description && (
            <p className="text-sm text-gray-600 mb-3">{item.description}</p>
          )}

          <div className="flex flex-wrap gap-2 mb-2">
            {item.category && (
              <Badge variant="blue" size="sm">
                {item.category}
              </Badge>
            )}
            {item.cuisine_type && (
              <Badge variant="gray" size="sm">
                {item.cuisine_type}
              </Badge>
            )}
            {item.dietary_tags.map((tag) => (
              <Badge key={tag} variant="green" size="sm">
                {tag}
              </Badge>
            ))}
          </div>

          {item.flavor_tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {item.flavor_tags.map((tag) => (
                <span
                  key={tag}
                  className="text-xs text-gray-500 bg-gray-50 px-2 py-1 rounded"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>

        {item.price !== null && (
          <div className="ml-4 text-right">
            <span className="text-lg font-bold text-gray-900">
              £{item.price.toFixed(2)}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
