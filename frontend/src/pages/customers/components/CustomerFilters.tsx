import { useState } from 'react';
import { Input, Button } from '@/components/ui';
import type { SegmentFilters } from '@/types/api';

interface CustomerFiltersProps {
  onFilterChange: (filters: SegmentFilters) => void;
}

export const CustomerFilters = ({ onFilterChange }: CustomerFiltersProps) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState<SegmentFilters>({});

  const handleSearch = () => {
    onFilterChange(filters);
  };

  const handleClear = () => {
    setSearchTerm('');
    setFilters({});
    onFilterChange({});
  };

  const updateFilter = <K extends keyof SegmentFilters>(
    key: K,
    value: SegmentFilters[K]
  ) => {
    const newFilters = { ...filters };
    if (value === '' || value === undefined) {
      delete newFilters[key];
    } else {
      newFilters[key] = value;
    }
    setFilters(newFilters);
  };

  return (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Filters</h3>
        <Button variant="secondary" size="sm" onClick={handleClear}>
          Clear All
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Search */}
        <div className="lg:col-span-3">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Search
          </label>
          <Input
            type="text"
            placeholder="Search by name, email, or ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        {/* City */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            City
          </label>
          <Input
            type="text"
            placeholder="e.g., London"
            value={filters.city || ''}
            onChange={(e) => updateFilter('city', e.target.value)}
          />
        </div>

        {/* Cuisine */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Favorite Cuisine
          </label>
          <Input
            type="text"
            placeholder="e.g., Italian"
            value={filters.favorite_cuisine || ''}
            onChange={(e) => updateFilter('favorite_cuisine', e.target.value)}
          />
        </div>

        {/* Dietary Flag */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Dietary Preference
          </label>
          <select
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={filters.dietary_flag || ''}
            onChange={(e) => updateFilter('dietary_flag', e.target.value)}
          >
            <option value="">All</option>
            <option value="vegetarian">Vegetarian</option>
            <option value="vegan">Vegan</option>
            <option value="halal">Halal</option>
            <option value="gluten_free">Gluten Free</option>
          </select>
        </div>

        {/* Order Frequency */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Order Frequency
          </label>
          <select
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={filters.order_frequency || ''}
            onChange={(e) =>
              updateFilter('order_frequency', e.target.value as SegmentFilters['order_frequency'])
            }
          >
            <option value="">All</option>
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
            <option value="occasional">Occasional</option>
          </select>
        </div>

        {/* Min Orders */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Min Orders
          </label>
          <Input
            type="number"
            placeholder="e.g., 5"
            min="0"
            value={filters.total_orders_min || ''}
            onChange={(e) =>
              updateFilter('total_orders_min', e.target.value ? parseInt(e.target.value) : undefined)
            }
          />
        </div>

        {/* Min Spend */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Min Total Spend (£)
          </label>
          <Input
            type="number"
            placeholder="e.g., 100"
            min="0"
            step="0.01"
            value={filters.total_spend_min || ''}
            onChange={(e) =>
              updateFilter('total_spend_min', e.target.value ? parseFloat(e.target.value) : undefined)
            }
          />
        </div>
      </div>

      <div className="mt-4 flex justify-end">
        <Button onClick={handleSearch}>Apply Filters</Button>
      </div>
    </div>
  );
};
