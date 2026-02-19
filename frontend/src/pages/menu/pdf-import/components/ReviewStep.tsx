import React, { useState } from 'react';
import { PlusIcon } from '@heroicons/react/20/solid';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/Button';
import { EditableItemsTable } from './EditableItemsTable';
import type { ParsedMenuItem } from '@/types/api';

interface ReviewStepProps {
  items: ParsedMenuItem[];
  brandName: string;
  filename: string;
  onItemsChange: (items: ParsedMenuItem[]) => void;
  onConfirm: () => void;
  onBack: () => void;
  isSubmitting: boolean;
}

const blankItem = (): ParsedMenuItem => ({
  name: '',
  description: null,
  category: null,
  cuisine_type: null,
  price: null,
  dietary_tags: [],
  flavor_tags: [],
});

export const ReviewStep: React.FC<ReviewStepProps> = ({
  items,
  brandName,
  filename,
  onItemsChange,
  onConfirm,
  onBack,
  isSubmitting,
}) => {
  const [confirmOpen, setConfirmOpen] = useState(false);

  const handleItemChange = (index: number, updated: ParsedMenuItem) => {
    const next = [...items];
    next[index] = updated;
    onItemsChange(next);
  };

  const handleItemDelete = (index: number) => {
    onItemsChange(items.filter((_, i) => i !== index));
  };

  const handleAddRow = () => {
    onItemsChange([...items, blankItem()]);
  };

  const validItems = items.filter((item) => item.name.trim().length > 0);

  return (
    <div className="space-y-4">
      {/* Summary bar */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="text-sm text-gray-600">
          <span className="font-semibold text-gray-900">{items.length}</span> items extracted
          from <span className="font-medium">{filename}</span>
          {brandName && (
            <>
              {' '}for <span className="font-medium">{brandName}</span>
            </>
          )}
        </div>
        <span className="text-xs text-gray-400">
          {validItems.length} valid (name required)
        </span>
      </div>

      {/* Editable table */}
      <div className="max-h-[50vh] overflow-y-auto rounded-xl border border-gray-200">
        <EditableItemsTable
          items={items}
          onItemChange={handleItemChange}
          onItemDelete={handleItemDelete}
        />
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between pt-2 flex-wrap gap-3 border-t border-gray-100">
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" onClick={onBack} disabled={isSubmitting}>
            ← Back
          </Button>
          <Button variant="ghost" size="sm" onClick={handleAddRow} disabled={isSubmitting}>
            <PlusIcon className="h-4 w-4 mr-1" />
            Add Row
          </Button>
        </div>

        <Button
          variant="ghost"
          onClick={() => setConfirmOpen(true)}
          disabled={validItems.length === 0 || isSubmitting}
          loading={isSubmitting}
        >
          Save {validItems.length} Item{validItems.length !== 1 ? 's' : ''}
        </Button>
      </div>

      {/* Confirm dialog */}
      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Save menu items?</DialogTitle>
            <DialogDescription>
              This will add <strong>{validItems.length} item{validItems.length !== 1 ? 's' : ''}</strong>
              {brandName && <> to <strong>{brandName}</strong></>} and generate vector embeddings for each.
              Items with an empty name will be skipped.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="secondary"
              onClick={() => setConfirmOpen(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              variant="secondary"
              onClick={() => {
                setConfirmOpen(false);
                onConfirm();
              }}
              loading={isSubmitting}
            >
              Confirm & Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};
