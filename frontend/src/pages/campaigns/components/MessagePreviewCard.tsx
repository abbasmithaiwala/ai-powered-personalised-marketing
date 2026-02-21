import React from 'react';
import { Card } from '@/components/ui/Card';
import type { CampaignRecipient } from '@/types/api';

interface MessagePreviewCardProps {
  recipient: CampaignRecipient;
  customerEmail?: string;
}

export const MessagePreviewCard: React.FC<MessagePreviewCardProps> = ({
  recipient,
  customerEmail,
}) => {
  const message = recipient.generated_message;
  const displayEmail = customerEmail || recipient.customer_email;
  const displayName = recipient.customer_name;

  if (!message) {
    return (
      <Card className="bg-gray-50">
        <div className="text-center py-8">
          <p className="text-gray-500">No message generated</p>
          {recipient.error_message && (
            <p className="text-sm text-red-600 mt-2">{recipient.error_message}</p>
          )}
        </div>
      </Card>
    );
  }

  return (
    <Card padding="lg">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between pb-3 border-b border-gray-200">
          <div className="flex-1">
            <h4 className="text-base font-semibold text-gray-900">
              {displayName ? `Message for ${displayName}` : 'Sample Message'}
            </h4>
            {displayEmail && (
              <p className="text-sm text-gray-500 mt-1">To: {displayEmail}</p>
            )}
          </div>
          <span
            className={`px-3 py-1 text-xs font-medium rounded-full ${
              recipient.status === 'generated'
                ? 'bg-green-100 text-green-800'
                : recipient.status === 'failed'
                ? 'bg-red-100 text-red-800'
                : 'bg-yellow-100 text-yellow-800'
            }`}
          >
            {recipient.status}
          </span>
        </div>

        {/* Subject Line */}
        <div>
          <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
            Subject Line
          </label>
          <div className="bg-gray-50 border border-gray-200 rounded-lg px-4 py-3">
            <p className="text-sm font-medium text-gray-900">{message.subject}</p>
          </div>
        </div>

        {/* Email Body */}
        <div>
          <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
            Message Body
          </label>
          <div className="bg-gray-50 border border-gray-200 rounded-lg px-4 py-3">
            <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
              {message.body}
            </p>
          </div>
        </div>

        {/* Character/Word Counts */}
        <div className="flex items-center justify-between text-xs text-gray-500 pt-3 border-t border-gray-200">
          <span className="flex items-center gap-1">
            <span className="font-medium">Subject:</span>
            <span>{message.subject.length} characters</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="font-medium">Body:</span>
            <span>{message.body.split(/\s+/).length} words</span>
          </span>
        </div>
      </div>
    </Card>
  );
};
