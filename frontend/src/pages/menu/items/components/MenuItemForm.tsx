import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { menuApi } from '@/api/menu';
import { Card, Button } from '@/components/ui';
import type { MenuItem, MenuItemCreate, Brand } from '@/types/api';

interface MenuItemFormProps {
  brands: Brand[];
  item?: MenuItem;
  onSuccess?: () => void;
  onCancel?: () => void;
}

export const MenuItemForm: React.FC<MenuItemFormProps> = ({
  brands,
  item,
  onSuccess,
  onCancel,
}) => {
  const queryClient = useQueryClient();
  const isEdit = !!item;

  const [formData, setFormData] = useState<MenuItemCreate>({
    brand_id: item?.brand_id || '',
    name: item?.name || '',
    description: item?.description || '',
    category: item?.category || '',
    cuisine_type: item?.cuisine_type || '',
    price: item?.price || undefined,
    dietary_tags: item?.dietary_tags || [],
    flavor_tags: item?.flavor_tags || [],
    is_available: item?.is_available ?? true,
  });

  const [dietaryInput, setDietaryInput] = useState('');
  const [flavorInput, setFlavorInput] = useState('');
  const [error, setError] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: (data: MenuItemCreate) => menuApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['menu-items'] });
      onSuccess?.();
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to create menu item');
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: Partial<MenuItemCreate>) => menuApi.update(item!.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['menu-items'] });
      queryClient.invalidateQueries({ queryKey: ['menu-item', item!.id] });
      onSuccess?.();
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to update menu item');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!formData.brand_id || !formData.name) {
      setError('Brand and name are required');
      return;
    }

    if (isEdit) {
      updateMutation.mutate(formData);
    } else {
      createMutation.mutate(formData);
    }
  };

  const addDietaryTag = () => {
    const tags = formData.dietary_tags || [];
    if (dietaryInput.trim() && !tags.includes(dietaryInput.trim())) {
      setFormData({
        ...formData,
        dietary_tags: [...tags, dietaryInput.trim()],
      });
      setDietaryInput('');
    }
  };

  const removeDietaryTag = (tag: string) => {
    setFormData({
      ...formData,
      dietary_tags: (formData.dietary_tags || []).filter((t) => t !== tag),
    });
  };

  const addFlavorTag = () => {
    const tags = formData.flavor_tags || [];
    if (flavorInput.trim() && !tags.includes(flavorInput.trim())) {
      setFormData({
        ...formData,
        flavor_tags: [...tags, flavorInput.trim()],
      });
      setFlavorInput('');
    }
  };

  const removeFlavorTag = (tag: string) => {
    setFormData({
      ...formData,
      flavor_tags: (formData.flavor_tags || []).filter((t) => t !== tag),
    });
  };

  const isLoading = createMutation.isPending || updateMutation.isPending;

  return (
    <Card>
      <form onSubmit={handleSubmit} className="space-y-6">
        <h3 className="text-lg font-semibold text-gray-900">
          {isEdit ? 'Edit Menu Item' : 'Create Menu Item'}
        </h3>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        )}

        {/* Basic Information */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Brand *
            </label>
            <select
              value={formData.brand_id}
              onChange={(e) => setFormData({ ...formData, brand_id: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              required
              disabled={isEdit}
            >
              <option value="">Select a brand</option>
              {brands.map((brand) => (
                <option key={brand.id} value={brand.id}>
                  {brand.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Item Name *
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Category
              </label>
              <input
                type="text"
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="e.g., mains, desserts"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Cuisine Type
              </label>
              <input
                type="text"
                value={formData.cuisine_type}
                onChange={(e) =>
                  setFormData({ ...formData, cuisine_type: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="e.g., italian, thai"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Price (₹)
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={formData.price || ''}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    price: e.target.value ? parseFloat(e.target.value) : undefined,
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="0.00"
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_available"
              checked={formData.is_available}
              onChange={(e) =>
                setFormData({ ...formData, is_available: e.target.checked })
              }
              className="w-4 h-4 text-primary-600 rounded focus:ring-2 focus:ring-primary-500"
            />
            <label htmlFor="is_available" className="text-sm font-medium text-gray-700">
              Available for ordering
            </label>
          </div>
        </div>

        {/* Dietary Tags */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Dietary Tags
          </label>
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              value={dietaryInput}
              onChange={(e) => setDietaryInput(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  addDietaryTag();
                }
              }}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="e.g., vegetarian, vegan, gluten-free"
            />
            <Button type="button" onClick={addDietaryTag} variant="secondary">
              Add
            </Button>
          </div>
          {(formData.dietary_tags?.length ?? 0) > 0 && (
            <div className="flex flex-wrap gap-2">
              {formData.dietary_tags?.map((tag) => (
                <span
                  key={tag}
                  className="inline-flex items-center gap-1 px-3 py-1 bg-green-100 text-green-800 text-sm rounded-full"
                >
                  {tag}
                  <button
                    type="button"
                    onClick={() => removeDietaryTag(tag)}
                    className="hover:text-green-900"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Flavor Tags */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Flavor Tags
          </label>
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              value={flavorInput}
              onChange={(e) => setFlavorInput(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  addFlavorTag();
                }
              }}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="e.g., spicy, sweet, savory"
            />
            <Button type="button" onClick={addFlavorTag} variant="secondary">
              Add
            </Button>
          </div>
          {(formData.flavor_tags?.length ?? 0) > 0 && (
            <div className="flex flex-wrap gap-2">
              {formData.flavor_tags?.map((tag) => (
                <span
                  key={tag}
                  className="inline-flex items-center gap-1 px-3 py-1 bg-gray-100 text-gray-800 text-sm rounded-full"
                >
                  {tag}
                  <button
                    type="button"
                    onClick={() => removeFlavorTag(tag)}
                    className="hover:text-gray-900"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-3 pt-4 border-t border-gray-200">
          <Button type="submit" disabled={isLoading}>
            {isLoading ? 'Saving...' : isEdit ? 'Update Item' : 'Create Item'}
          </Button>
          {onCancel && (
            <Button type="button" variant="secondary" onClick={onCancel}>
              Cancel
            </Button>
          )}
        </div>

        {isEdit && (
          <p className="text-sm text-gray-600">
            Saving this item will trigger AI embedding generation in the background.
          </p>
        )}
      </form>
    </Card>
  );
};
