import React from 'react';
import type { SegmentFilters } from '@/types/api';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface CampaignFormProps {
  name: string;
  setName: (value: string) => void;
  description: string;
  setDescription: (value: string) => void;
  purpose: string;
  setPurpose: (value: string) => void;
  filters: SegmentFilters;
  setFilters: (filters: SegmentFilters) => void;
}

export const CampaignForm: React.FC<CampaignFormProps> = ({
  name,
  setName,
  description,
  setDescription,
  purpose,
  setPurpose,
  filters,
  setFilters,
}) => {
  const updateFilter = <K extends keyof SegmentFilters>(
    key: K,
    value: SegmentFilters[K]
  ) => {
    setFilters({ ...filters, [key]: value });
  };

  return (
    <div className="space-y-6">
      {/* Campaign Details */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-6">
          Campaign Details
        </h3>
        <div className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="name">Campaign Name *</Label>
            <Input
              type="text"
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Weekend Special Promotion"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              placeholder="Internal notes about this campaign"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="purpose">Campaign Purpose *</Label>
            <Textarea
              id="purpose"
              value={purpose}
              onChange={(e) => setPurpose(e.target.value)}
              rows={2}
              placeholder="e.g., Promote new menu items to vegetarian customers"
              required
            />
            <p className="text-sm text-gray-500">
              This will be used to generate personalized messages
            </p>
          </div>
        </div>
      </div>

      {/* Segment Filters */}
      <div className="pt-6 border-t border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-6">
          Target Audience
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Last Order Date Range */}
          <div className="space-y-2">
            <Label htmlFor="last_order_after">Last Order After</Label>
            <Input
              type="date"
              id="last_order_after"
              value={filters.last_order_after || ''}
              onChange={(e) =>
                updateFilter('last_order_after', e.target.value || undefined)
              }
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="last_order_before">Last Order Before</Label>
            <Input
              type="date"
              id="last_order_before"
              value={filters.last_order_before || ''}
              onChange={(e) =>
                updateFilter('last_order_before', e.target.value || undefined)
              }
            />
          </div>

          {/* Spend Range */}
          <div className="space-y-2">
            <Label htmlFor="total_spend_min">Min Total Spend (₹)</Label>
            <Input
              type="number"
              id="total_spend_min"
              value={filters.total_spend_min || ''}
              onChange={(e) =>
                updateFilter(
                  'total_spend_min',
                  e.target.value ? parseFloat(e.target.value) : undefined
                )
              }
              min="0"
              step="0.01"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="total_spend_max">Max Total Spend (₹)</Label>
            <Input
              type="number"
              id="total_spend_max"
              value={filters.total_spend_max || ''}
              onChange={(e) =>
                updateFilter(
                  'total_spend_max',
                  e.target.value ? parseFloat(e.target.value) : undefined
                )
              }
              min="0"
              step="0.01"
            />
          </div>

          {/* Min Orders */}
          <div className="space-y-2">
            <Label htmlFor="total_orders_min">Minimum Orders</Label>
            <Input
              type="number"
              id="total_orders_min"
              value={filters.total_orders_min || ''}
              onChange={(e) =>
                updateFilter(
                  'total_orders_min',
                  e.target.value ? parseInt(e.target.value) : undefined
                )
              }
              min="0"
            />
          </div>

          {/* Cuisine Preference */}
          <div className="space-y-2">
            <Label htmlFor="favorite_cuisine">Favorite Cuisine</Label>
            <Input
              type="text"
              id="favorite_cuisine"
              value={filters.favorite_cuisine || ''}
              onChange={(e) =>
                updateFilter('favorite_cuisine', e.target.value || undefined)
              }
              placeholder="e.g., italian, thai, mexican"
            />
          </div>

          {/* Dietary Flag */}
          <div className="space-y-2">
            <Label htmlFor="dietary_flag">Dietary Restriction</Label>
            <Select
              value={filters.dietary_flag || ''}
              onValueChange={(val) => updateFilter('dietary_flag', val === 'none' ? undefined : val)}
            >
              <SelectTrigger id="dietary_flag" className="w-full">
                <SelectValue placeholder="Any" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">Any</SelectItem>
                <SelectItem value="vegetarian">Vegetarian</SelectItem>
                <SelectItem value="vegan">Vegan</SelectItem>
                <SelectItem value="halal">Halal</SelectItem>
                <SelectItem value="gluten_free">Gluten Free</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Order Frequency */}
          <div className="space-y-2">
            <Label htmlFor="order_frequency">Order Frequency</Label>
            <Select
              value={filters.order_frequency || ''}
              onValueChange={(val) =>
                updateFilter('order_frequency', val === 'none' ? undefined : val as SegmentFilters['order_frequency'])
              }
            >
              <SelectTrigger id="order_frequency" className="w-full">
                <SelectValue placeholder="Any" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">Any</SelectItem>
                <SelectItem value="daily">Daily</SelectItem>
                <SelectItem value="weekly">Weekly</SelectItem>
                <SelectItem value="monthly">Monthly</SelectItem>
                <SelectItem value="occasional">Occasional</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* City */}
          <div className="md:col-span-2 space-y-2">
            <Label htmlFor="city">City</Label>
            <Input
              type="text"
              id="city"
              value={filters.city || ''}
              onChange={(e) => updateFilter('city', e.target.value || undefined)}
              placeholder="e.g., London, Manchester"
            />
          </div>
        </div>
      </div>
    </div>
  );
};
