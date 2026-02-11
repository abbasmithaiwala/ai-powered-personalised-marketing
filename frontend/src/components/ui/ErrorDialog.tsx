import React from 'react';
import { ExclamationTriangleIcon, XMarkIcon } from '@/components/icons';

interface ErrorDialogProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  message: string;
  details?: string;
}

export const ErrorDialog: React.FC<ErrorDialogProps> = ({
  isOpen,
  onClose,
  title = 'Error',
  message,
  details,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />
      
      {/* Dialog */}
      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="relative w-full max-w-md transform rounded-lg bg-white p-6 shadow-xl transition-all">
          {/* Close button */}
          <button
            onClick={onClose}
            className="absolute right-4 top-4 text-gray-400 hover:text-gray-500 transition-colors"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>

          {/* Error icon */}
          <div className="flex items-center justify-center w-12 h-12 mx-auto bg-red-100 rounded-full mb-4">
            <ExclamationTriangleIcon className="w-6 h-6 text-red-600" />
          </div>

          {/* Title */}
          <h2 className="text-xl font-bold text-center text-gray-900 mb-2">
            {title}
          </h2>

          {/* Message */}
          <p className="text-gray-600 text-center mb-6">
            {message}
          </p>

          {/* Details (optional) */}
          {details && (
            <details className="mb-6 bg-gray-50 rounded p-4">
              <summary className="cursor-pointer font-medium text-sm text-gray-700 mb-2">
                Error details
              </summary>
              <pre className="text-xs text-red-600 overflow-auto whitespace-pre-wrap break-words">
                {details}
              </pre>
            </details>
          )}

          {/* Action buttons */}
          <div className="flex justify-center">
            <button
              onClick={onClose}
              className="px-6 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};