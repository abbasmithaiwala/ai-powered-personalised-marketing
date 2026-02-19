import React from 'react';
import { TrashIcon } from '@heroicons/react/20/solid';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { TagEditor } from './TagEditor';
import type { ParsedMenuItem } from '@/types/api';

interface EditableItemsTableProps {
  items: ParsedMenuItem[];
  onItemChange: (index: number, updated: ParsedMenuItem) => void;
  onItemDelete: (index: number) => void;
}

const cellInputClass =
  'w-full bg-transparent outline-none text-sm placeholder:text-gray-400 focus:ring-1 focus:ring-primary-400 rounded px-1 py-0.5';

export const EditableItemsTable: React.FC<EditableItemsTableProps> = ({
  items,
  onItemChange,
  onItemDelete,
}) => {
  const update = (index: number, field: keyof ParsedMenuItem, value: unknown) => {
    onItemChange(index, { ...items[index], [field]: value });
  };

  if (items.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500 text-sm border border-dashed rounded-xl">
        No items. Click "Add Row" to add one manually.
      </div>
    );
  }

  return (
    <div className="overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow className="bg-gray-50 sticky top-0 z-10">
            <TableHead className="w-[180px]">Name *</TableHead>
            <TableHead className="w-[200px]">Description</TableHead>
            <TableHead className="w-[110px]">Category</TableHead>
            <TableHead className="w-[110px]">Cuisine</TableHead>
            <TableHead className="w-[80px]">Price (£)</TableHead>
            <TableHead className="w-[150px]">Dietary Tags</TableHead>
            <TableHead className="w-[150px]">Flavor Tags</TableHead>
            <TableHead className="w-[40px]" />
          </TableRow>
        </TableHeader>
        <TableBody>
          {items.map((item, i) => (
            <TableRow key={i} className="align-top">
              {/* Name */}
              <TableCell>
                <input
                  className={cellInputClass}
                  value={item.name}
                  onChange={(e) => update(i, 'name', e.target.value)}
                  placeholder="Item name"
                />
              </TableCell>

              {/* Description */}
              <TableCell>
                <input
                  className={cellInputClass}
                  value={item.description ?? ''}
                  onChange={(e) =>
                    update(i, 'description', e.target.value || null)
                  }
                  placeholder="Description"
                />
              </TableCell>

              {/* Category */}
              <TableCell>
                <input
                  className={cellInputClass}
                  value={item.category ?? ''}
                  onChange={(e) =>
                    update(i, 'category', e.target.value || null)
                  }
                  placeholder="e.g. Mains"
                />
              </TableCell>

              {/* Cuisine type */}
              <TableCell>
                <input
                  className={cellInputClass}
                  value={item.cuisine_type ?? ''}
                  onChange={(e) =>
                    update(i, 'cuisine_type', e.target.value || null)
                  }
                  placeholder="e.g. Italian"
                />
              </TableCell>

              {/* Price */}
              <TableCell>
                <input
                  type="number"
                  min={0}
                  step={0.01}
                  className={cellInputClass}
                  value={item.price ?? ''}
                  onChange={(e) =>
                    update(
                      i,
                      'price',
                      e.target.value === '' ? null : parseFloat(e.target.value)
                    )
                  }
                  placeholder="0.00"
                />
              </TableCell>

              {/* Dietary tags */}
              <TableCell className="whitespace-normal">
                <TagEditor
                  tags={item.dietary_tags}
                  onChange={(tags) => update(i, 'dietary_tags', tags)}
                  placeholder="e.g. vegan"
                />
              </TableCell>

              {/* Flavor tags */}
              <TableCell className="whitespace-normal">
                <TagEditor
                  tags={item.flavor_tags}
                  onChange={(tags) => update(i, 'flavor_tags', tags)}
                  placeholder="e.g. spicy"
                />
              </TableCell>

              {/* Delete */}
              <TableCell>
                <button
                  type="button"
                  onClick={() => onItemDelete(i)}
                  className="p-1 text-gray-400 hover:text-red-500 rounded transition-colors"
                  title="Remove row"
                >
                  <TrashIcon className="h-4 w-4" />
                </button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};
