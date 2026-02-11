import React from 'react';
import { SegmentFilters } from '@/types/api';

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
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Campaign Details
        </h3>
        <div className="space-y-4">
          <div>
            <label
              htmlFor="name"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Campaign Name *
            </label>
            <input
              type="text"
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="e.g., Weekend Special Promotion"
              required
            />
          </div>

          <div>
            <label
              htmlFor="description"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Description
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              rows={3}
              placeholder="Internal notes about this campaign"
            />
          </div>

          <div>
            <label
              htmlFor="purpose"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Campaign Purpose *
            </label>
            <textarea
              id="purpose"
              value={purpose}
              onChange={(e) => setPurpose(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              rows={2}
              placeholder="e.g., Promote new menu items to vegetarian customers"
              required
            />
            <p className="mt-1 text-sm text-gray-500">
              This will be used to generate personalized messages
            </p>
          </div>
        </div>
      </div>

      {/* Segment Filters */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Target Audience
        </h3>
        <div className="space-y-4">
          {/* Last Order Date Range */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label
                htmlFor="last_order_after"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Last Order After
              </label>
              <input
                type="date"
                id="last_order_after"
                value={filters.last_order_after || ''}
                onChange={(e) =>
                  updateFilter('last_order_after', e.target.value || undefined)
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label
                htmlFor="last_order_before"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Last Order Before
              </label>
              <input
                type="date"
                id="last_order_before"
                value={filters.last_order_before || ''}
                onChange={(e) =>
                  updateFilter('last_order_before', e.target.value || undefined)
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          {/* Spend Range */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label
                htmlFor="total_spend_min"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Min Total Spend (£)
              </label>
              <input
                type="number"
                id="total_spend_min"
                value={filters.total_spend_min || ''}
                onChange={(e) =>
                  updateFilter(
                    'total_spend_min',
                    e.target.value ? parseFloat(e.target.value) : undefined
                  )
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                min="0"
                step="0.01"
              />
            </div>
            <div>
              <label
                htmlFor="total_spend_max"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Max Total Spend (£)
              </label>
              <input
                type="number"
                id="total_spend_max"
                value={filters.total_spend_max || ''}
                onChange={(e) =>
                  updateFilter(
                    'total_spend_max',
                    e.target.value ? parseFloat(e.target.value) : undefined
                  )
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                min="0"
                step="0.01"
              />
            </div>
          </div>

          {/* Min Orders */}
          <div>
            <label
              htmlFor="total_orders_min"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Minimum Orders
            </label>
            <input
              type="number"
              id="total_orders_min"
              value={filters.total_orders_min || ''}
              onChange={(e) =>
                updateFilter(
                  'total_orders_min',
                  e.target.value ? parseInt(e.target.value) : undefined
                )
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              min="0"
            />
          </div>

          {/* Cuisine Preference */}
          <div>
            <label
              htmlFor="favorite_cuisine"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Favorite Cuisine
            </label>
            <input
              type="text"
              id="favorite_cuisine"
              value={filters.favorite_cuisine || ''}
              onChange={(e) =>
                updateFilter('favorite_cuisine', e.target.value || undefined)
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="e.g., italian, thai, mexican"
            />
          </div>

          {/* Dietary Flag */}
          <div>
            <label
              htmlFor="dietary_flag"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Dietary Restriction
            </label>
            <select
              id="dietary_flag"
              value={filters.dietary_flag || ''}
              onChange={(e) =>
                updateFilter('dietary_flag', e.target.value || undefined)
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Any</option>
              <option value="vegetarian">Vegetarian</option>
              <option value="vegan">Vegan</option>
              <option value="halal">Halal</option>
              <option value="gluten_free">Gluten Free</option>
            </select>
          </div>

          {/* Order Frequency */}
          <div>
            <label
              htmlFor="order_frequency"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Order Frequency
            </label>
            <select
              id="order_frequency"
              value={filters.order_frequency || ''}
              onChange={(e) =>
                updateFilter(
                  'order_frequency',
                  e.target.value
                    ? (e.target.value as SegmentFilters['order_frequency'])
                    : undefined
                )
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Any</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
              <option value="occasional">Occasional</option>
            </select>
          </div>

          {/* City */}
          <div>
            <label
              htmlFor="city"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              City
            </label>
            <input
              type="text"
              id="city"
              value={filters.city || ''}
              onChange={(e) => updateFilter('city', e.target.value || undefined)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="e.g., London, Manchester"
            />
          </div>
        </div>
      </div>
    </div>
  );
};
