import React from 'react';
import { CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import type { BulkCreateResponse } from '@/types/api';

interface DoneStepProps {
  result: BulkCreateResponse;
  brandId: string;
  onReset: () => void;
}

export const DoneStep: React.FC<DoneStepProps> = ({ result, brandId, onReset }) => {
  const allFailed = result.created === 0;

  return (
    <div className="max-w-md mx-auto text-center space-y-6 py-8">
      {allFailed ? (
        <ExclamationTriangleIcon className="h-16 w-16 text-yellow-500 mx-auto" />
      ) : (
        <CheckCircleIcon className="h-16 w-16 text-green-500 mx-auto" />
      )}

      <div>
        <h2 className="text-xl font-semibold text-gray-900">
          {allFailed ? 'No items saved' : 'Import complete!'}
        </h2>
        <p className="text-gray-600 mt-1">
          {result.created > 0 && (
            <>
              <span className="font-medium text-green-700">{result.created}</span> item
              {result.created !== 1 ? 's' : ''} saved successfully.
            </>
          )}
          {result.failed > 0 && (
            <>
              {result.created > 0 && ' '}
              <span className="font-medium text-yellow-700">{result.failed}</span> item
              {result.failed !== 1 ? 's' : ''} failed.
            </>
          )}
        </p>
        {result.created > 0 && (
          <p className="text-sm text-gray-500 mt-1">
            Vector embeddings are being generated in the background.
          </p>
        )}
      </div>

      <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
        <Button variant="secondary" onClick={onReset}>
          Import Another PDF
        </Button>
        {result.created > 0 && (
          <Link to={`/menu/items?brand_id=${brandId}`}>
            <Button variant="secondary">View Menu Items →</Button>
          </Link>
        )}
      </div>
    </div>
  );
};
