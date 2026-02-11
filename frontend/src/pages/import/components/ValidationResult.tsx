import React from 'react';
import { Card, CardHeader, CardTitle, Badge } from '@/components/ui';

interface ValidationResultProps {
  filename: string;
  totalRows: number;
  validationSummary: any;
  onStartImport: () => void;
  onCancel: () => void;
  loading?: boolean;
}

export const ValidationResult: React.FC<ValidationResultProps> = ({
  filename,
  totalRows,
  validationSummary,
  onStartImport,
  onCancel,
  loading = false,
}) => {
  const hasErrors = validationSummary?.errors && validationSummary.errors.length > 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Validation Result</CardTitle>
      </CardHeader>
      <div className="p-6 space-y-4">
        {/* File Info */}
        <div className="bg-gray-50 rounded-lg p-4 space-y-2">
          <div className="flex justify-between">
            <span className="text-sm font-medium text-gray-700">Filename:</span>
            <span className="text-sm text-gray-900">{filename}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm font-medium text-gray-700">Total Rows:</span>
            <span className="text-sm text-gray-900">{totalRows.toLocaleString()}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-gray-700">Status:</span>
            {hasErrors ? (
              <Badge variant="error">Has Errors</Badge>
            ) : (
              <Badge variant="success">Valid</Badge>
            )}
          </div>
        </div>

        {/* Column Mapping */}
        {validationSummary?.column_mapping && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Column Mapping:</h4>
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="grid grid-cols-2 gap-2 text-xs">
                {Object.entries(validationSummary.column_mapping).map(([key, value]) => (
                  <div key={key} className="flex justify-between">
                    <span className="text-gray-600">{key}:</span>
                    <span className="text-gray-900 font-medium">{value as string}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Validation Errors */}
        {hasErrors && (
          <div>
            <h4 className="text-sm font-medium text-red-700 mb-2">
              Validation Errors ({validationSummary.errors.length}):
            </h4>
            <div className="bg-red-50 rounded-lg p-3 max-h-48 overflow-y-auto">
              <table className="min-w-full text-xs">
                <thead>
                  <tr className="text-left text-red-800">
                    <th className="px-2 py-1">Row</th>
                    <th className="px-2 py-1">Field</th>
                    <th className="px-2 py-1">Error</th>
                  </tr>
                </thead>
                <tbody className="text-red-900">
                  {validationSummary.errors.slice(0, 20).map((error: any, idx: number) => (
                    <tr key={idx} className="border-t border-red-100">
                      <td className="px-2 py-1">{error.row}</td>
                      <td className="px-2 py-1 font-medium">{error.field}</td>
                      <td className="px-2 py-1">{error.error}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {validationSummary.errors.length > 20 && (
                <p className="text-xs text-red-600 mt-2 text-center">
                  ... and {validationSummary.errors.length - 20} more errors
                </p>
              )}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex justify-end space-x-3 pt-4 border-t">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
            disabled={loading}
          >
            Cancel
          </button>
          <button
            onClick={onStartImport}
            disabled={hasErrors || loading}
            className={`
              px-4 py-2 text-sm font-medium text-white rounded-md
              focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500
              ${
                hasErrors || loading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-primary-600 hover:bg-primary-700'
              }
            `}
          >
            {loading ? (
              <span className="flex items-center">
                <svg
                  className="animate-spin -ml-1 mr-2 h-4 w-4"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Starting Import...
              </span>
            ) : (
              'Start Import'
            )}
          </button>
        </div>
      </div>
    </Card>
  );
};
