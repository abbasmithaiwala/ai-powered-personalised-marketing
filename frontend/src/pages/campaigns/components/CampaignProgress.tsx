import React from 'react';
import { Campaign } from '@/types/api';

interface CampaignProgressProps {
  campaign: Campaign;
}

export const CampaignProgress: React.FC<CampaignProgressProps> = ({
  campaign,
}) => {
  const { status, total_recipients, generated_count } = campaign;

  const percentage =
    total_recipients > 0 ? (generated_count / total_recipients) * 100 : 0;

  const getStatusColor = () => {
    switch (status) {
      case 'completed':
        return 'bg-green-600';
      case 'executing':
        return 'bg-primary-600';
      case 'failed':
        return 'bg-red-600';
      case 'ready':
        return 'bg-blue-600';
      case 'previewing':
        return 'bg-yellow-600';
      default:
        return 'bg-gray-400';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'draft':
        return 'Draft';
      case 'previewing':
        return 'Previewing';
      case 'ready':
        return 'Ready';
      case 'executing':
        return 'Generating Messages...';
      case 'completed':
        return 'Completed';
      case 'failed':
        return 'Failed';
      default:
        return status;
    }
  };

  return (
    <div className="space-y-3">
      {/* Status Badge */}
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-700">Campaign Status</span>
        <span
          className={`px-3 py-1 text-sm font-medium text-white rounded-full ${
            status === 'completed'
              ? 'bg-green-600'
              : status === 'executing'
              ? 'bg-primary-600'
              : status === 'failed'
              ? 'bg-red-600'
              : status === 'ready'
              ? 'bg-blue-600'
              : status === 'previewing'
              ? 'bg-yellow-600'
              : 'bg-gray-400'
          }`}
        >
          {getStatusText()}
        </span>
      </div>

      {/* Progress Bar */}
      {(status === 'executing' || status === 'completed' || status === 'failed') && (
        <div>
          <div className="flex items-center justify-between text-sm mb-1">
            <span className="text-gray-600">Progress</span>
            <span className="font-medium text-gray-900">
              {generated_count} / {total_recipients} messages
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div
              className={`h-2.5 rounded-full transition-all duration-300 ${getStatusColor()}`}
              style={{ width: `${percentage}%` }}
            />
          </div>
          <div className="flex items-center justify-between text-xs text-gray-500 mt-1">
            <span>{percentage.toFixed(1)}% complete</span>
            {status === 'executing' && (
              <span className="flex items-center">
                <svg
                  className="animate-spin h-3 w-3 mr-1"
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
                In progress
              </span>
            )}
          </div>
        </div>
      )}

      {/* Recipients Count */}
      {total_recipients > 0 && (
        <div className="pt-2 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Total Recipients</span>
            <span className="font-medium text-gray-900">
              {total_recipients.toLocaleString()}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
