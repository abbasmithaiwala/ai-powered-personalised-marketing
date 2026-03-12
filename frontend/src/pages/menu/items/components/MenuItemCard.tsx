import { Link } from 'react-router-dom';
import { Card, Badge } from '@/components/ui';
import type { MenuItem } from '@/types/api';

interface MenuItemCardProps {
  item: MenuItem;
  brandName: string;
}

export const MenuItemCard: React.FC<MenuItemCardProps> = ({ item, brandName }) => {
  return (
    <Card className="hover:shadow-lg transition-shadow h-full">
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <h3 className="font-semibold text-gray-900 mb-1">{item.name}</h3>
            <Link
              to={`/menu/brands/${item.brand_id}`}
              className="text-sm text-primary-600 hover:text-primary-700"
            >
              {brandName}
            </Link>
          </div>
          {!item.is_available && (
            <Badge variant="gray" size="sm">
              Unavailable
            </Badge>
          )}
        </div>

        {/* Description */}
        {item.description && (
          <p className="text-sm text-gray-600 mb-3 line-clamp-2">
            {item.description}
          </p>
        )}

        {/* Tags */}
        <div className="flex flex-wrap gap-2 mb-3">
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
          {item.dietary_tags?.slice(0, 2).map((tag) => (
            <Badge key={tag} variant="green" size="sm">
              {tag}
            </Badge>
          ))}
          {item.dietary_tags && item.dietary_tags.length > 2 && (
            <Badge variant="green" size="sm">
              +{item.dietary_tags.length - 2}
            </Badge>
          )}
        </div>

        {/* Flavor Tags */}
        {item.flavor_tags && item.flavor_tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {item.flavor_tags?.slice(0, 3).map((tag) => (
              <span
                key={tag}
                className="text-xs text-gray-500 bg-gray-50 px-2 py-1 rounded"
              >
                {tag}
              </span>
            ))}
            {item.flavor_tags && item.flavor_tags.length > 3 && (
              <span className="text-xs text-gray-500 bg-gray-50 px-2 py-1 rounded">
                +{item.flavor_tags.length - 3}
              </span>
            )}
          </div>
        )}

        {/* Price - Push to bottom */}
        <div className="mt-auto pt-3 border-t border-gray-200">
          {item.price !== null && item.price !== undefined ? (
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Price</span>
              <span className="text-lg font-bold text-gray-900">
                ₹{(typeof item.price === 'number' ? item.price : parseFloat(item.price)).toFixed(2)}
              </span>
            </div>
          ) : (
            <div className="text-sm text-gray-500">Price not set</div>
          )}
        </div>

        {/* Embedding Status */}
        {item.embedding_id && (
          <div className="mt-2 flex items-center gap-1 text-xs text-green-600">
            <span className="inline-block w-2 h-2 bg-green-500 rounded-full"></span>
            AI Embedded
          </div>
        )}
      </div>
    </Card>
  );
};
