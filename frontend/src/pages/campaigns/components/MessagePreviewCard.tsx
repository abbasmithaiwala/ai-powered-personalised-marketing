import React from 'react';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
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
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-base">Sample Message</CardTitle>
            {customerEmail && (
              <p className="text-sm text-gray-500 mt-1">To: {customerEmail}</p>
            )}
          </div>
          <span
            className={`px-2 py-1 text-xs font-medium rounded-full ${
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
      </CardHeader>

      <div className="space-y-4">
        {/* Subject Line */}
        <div>
          <label className="block text-xs font-medium text-gray-500 uppercase mb-1">
            Subject
          </label>
          <div className="bg-gray-50 border border-gray-200 rounded px-3 py-2">
            <p className="text-sm font-medium text-gray-900">{message.subject}</p>
          </div>
        </div>

        {/* Email Body */}
        <div>
          <label className="block text-xs font-medium text-gray-500 uppercase mb-1">
            Body
          </label>
          <div className="bg-gray-50 border border-gray-200 rounded px-3 py-2">
            <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
              {message.body}
            </p>
          </div>
        </div>

        {/* Character/Word Counts */}
        <div className="flex items-center justify-between text-xs text-gray-500 pt-2 border-t border-gray-200">
          <span>Subject: {message.subject.length} chars</span>
          <span>Body: {message.body.split(/\s+/).length} words</span>
        </div>
      </div>
    </Card>
  );
};
