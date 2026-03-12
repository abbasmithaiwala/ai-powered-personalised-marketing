import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/Button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { SegmentFilters } from '@/types/api';

interface CustomerFiltersProps {
  onFilterChange: (filters: SegmentFilters) => void;
}

export const CustomerFilters = ({ onFilterChange }: CustomerFiltersProps) => {
  const [filters, setFilters] = useState<SegmentFilters>({});

  const handleApply = () => {
    onFilterChange(filters);
  };

  const handleClear = () => {
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
        {/* Search Term */}
        <div className="lg:col-span-3">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Search
          </label>
          <Input
            type="text"
            placeholder="Search by name, email, or ID..."
            value={filters.search || ''}
            onChange={(e) => updateFilter('search', e.target.value)}
            className="text-sm"
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
            className="text-sm"
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
            className="text-sm"
          />
        </div>

        {/* Dietary Flag */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Dietary Preference
          </label>
          <Select
            value={filters.dietary_flag || 'all'}
            onValueChange={(value) => updateFilter('dietary_flag', value === 'all' ? undefined : value)}
          >
            <SelectTrigger className="text-sm w-full">
              <SelectValue placeholder="All" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="vegetarian">Vegetarian</SelectItem>
              <SelectItem value="vegan">Vegan</SelectItem>
              <SelectItem value="halal">Halal</SelectItem>
              <SelectItem value="gluten_free">Gluten Free</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Order Frequency */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Order Frequency
          </label>
          <Select
            value={filters.order_frequency || 'all'}
            onValueChange={(value) => updateFilter('order_frequency', value === 'all' ? undefined : (value as SegmentFilters['order_frequency']))}
          >
            <SelectTrigger className="text-sm w-full">
              <SelectValue placeholder="All" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="daily">Daily</SelectItem>
              <SelectItem value="weekly">Weekly</SelectItem>
              <SelectItem value="monthly">Monthly</SelectItem>
              <SelectItem value="occasional">Occasional</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Min Orders */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Min Orders
          </label>
          <Input
            type="number"
            placeholder="e.g., 5"
            min={0}
            value={filters.total_orders_min?.toString() || ''}
            onChange={(e) =>
              updateFilter('total_orders_min', e.target.value ? parseInt(e.target.value) : undefined)
            }
            className="text-sm"
            />
        </div>

        {/* Min Spend */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Min Total Spend (₹)
          </label>
          <Input
            type="number"
            placeholder="e.g., 100"
            min={0}
            step={0.01}
            value={filters.total_spend_min?.toString() || ''}
            onChange={(e) =>
              updateFilter('total_spend_min', e.target.value ? parseFloat(e.target.value) : undefined)
            }
            className="text-sm"
            />
        </div>
      </div>

      <div className="mt-4 flex justify-end">
        <Button onClick={handleApply}>Apply Filters</Button>
      </div>
    </div>
  );
};
