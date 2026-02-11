import { useState } from 'react';
import { Card, Button } from '@/components/ui';
import type { Brand } from '@/types/api';

interface FilterState {
  brandId?: string;
  category?: string;
  cuisine?: string;
  dietaryTag?: string;
}

interface MenuItemFiltersProps {
  brands: Brand[];
  filters: FilterState;
  onFilterChange: (filters: FilterState) => void;
}

export const MenuItemFilters: React.FC<MenuItemFiltersProps> = ({
  brands,
  filters,
  onFilterChange,
}) => {
  const [localFilters, setLocalFilters] = useState<FilterState>(filters);

  const handleApply = () => {
    // Remove empty filter values
    const cleanFilters = Object.fromEntries(
      Object.entries(localFilters).filter(([_, value]) => value !== '')
    );
    onFilterChange(cleanFilters);
  };

  const handleClear = () => {
    setLocalFilters({});
    onFilterChange({});
  };

  const commonCategories = [
    'mains',
    'starters',
    'desserts',
    'drinks',
    'sides',
    'snacks',
  ];

  const commonCuisines = [
    'italian',
    'thai',
    'indian',
    'chinese',
    'japanese',
    'mexican',
    'american',
    'mediterranean',
  ];

  const dietaryTags = [
    'vegetarian',
    'vegan',
    'gluten-free',
    'dairy-free',
    'halal',
    'kosher',
  ];

  return (
    <Card>
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Filters</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Brand Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Brand
            </label>
            <select
              value={localFilters.brandId || ''}
              onChange={(e) =>
                setLocalFilters({ ...localFilters, brandId: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">All Brands</option>
              {brands.map((brand) => (
                <option key={brand.id} value={brand.id}>
                  {brand.name}
                </option>
              ))}
            </select>
          </div>

          {/* Category Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Category
            </label>
            <select
              value={localFilters.category || ''}
              onChange={(e) =>
                setLocalFilters({ ...localFilters, category: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">All Categories</option>
              {commonCategories.map((category) => (
                <option key={category} value={category}>
                  {category.charAt(0).toUpperCase() + category.slice(1)}
                </option>
              ))}
            </select>
          </div>

          {/* Cuisine Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Cuisine
            </label>
            <select
              value={localFilters.cuisine || ''}
              onChange={(e) =>
                setLocalFilters({ ...localFilters, cuisine: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">All Cuisines</option>
              {commonCuisines.map((cuisine) => (
                <option key={cuisine} value={cuisine}>
                  {cuisine.charAt(0).toUpperCase() + cuisine.slice(1)}
                </option>
              ))}
            </select>
          </div>

          {/* Dietary Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Dietary
            </label>
            <select
              value={localFilters.dietaryTag || ''}
              onChange={(e) =>
                setLocalFilters({ ...localFilters, dietaryTag: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">All Dietary Options</option>
              {dietaryTags.map((tag) => (
                <option key={tag} value={tag}>
                  {tag
                    .split('-')
                    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
                    .join(' ')}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex gap-2">
          <Button onClick={handleApply}>Apply Filters</Button>
          <Button variant="secondary" onClick={handleClear}>
            Clear All
          </Button>
        </div>
      </div>
    </Card>
  );
};
