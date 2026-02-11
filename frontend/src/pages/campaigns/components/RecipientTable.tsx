import React from 'react';
import { CampaignRecipient } from '@/types/api';
import { Badge } from '@/components/ui/Badge';

interface RecipientTableProps {
  recipients: CampaignRecipient[];
}

export const RecipientTable: React.FC<RecipientTableProps> = ({ recipients }) => {
  if (recipients.length === 0) {
    return (
      <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
        <p className="text-gray-500">No recipients yet</p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden border border-gray-200 rounded-lg">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Customer ID
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Subject
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Body Preview
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Status
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {recipients.map((recipient) => (
            <RecipientRow key={recipient.id} recipient={recipient} />
          ))}
        </tbody>
      </table>
    </div>
  );
};

const RecipientRow: React.FC<{ recipient: CampaignRecipient }> = ({
  recipient,
}) => {
  const [expanded, setExpanded] = React.useState(false);

  const message = recipient.generated_message;
  const bodyPreview = message?.body
    ? message.body.substring(0, 100) + (message.body.length > 100 ? '...' : '')
    : '-';

  return (
    <>
      <tr className="hover:bg-gray-50">
        <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
          {recipient.customer_id.substring(0, 8)}...
        </td>
        <td className="px-6 py-4 text-sm text-gray-900">
          {message?.subject || '-'}
        </td>
        <td className="px-6 py-4 text-sm text-gray-500 max-w-md truncate">
          {bodyPreview}
        </td>
        <td className="px-6 py-4 whitespace-nowrap">
          <Badge
            variant={
              recipient.status === 'generated'
                ? 'success'
                : recipient.status === 'failed'
                ? 'danger'
                : 'warning'
            }
          >
            {recipient.status}
          </Badge>
        </td>
        <td className="px-6 py-4 whitespace-nowrap text-sm">
          {message && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-primary-600 hover:text-primary-700 font-medium"
            >
              {expanded ? 'Hide' : 'View Full'}
            </button>
          )}
        </td>
      </tr>
      {expanded && message && (
        <tr>
          <td colSpan={5} className="px-6 py-4 bg-gray-50">
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-500 uppercase mb-1">
                  Subject
                </label>
                <p className="text-sm font-medium text-gray-900">
                  {message.subject}
                </p>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 uppercase mb-1">
                  Body
                </label>
                <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
                  {message.body}
                </p>
              </div>
              {recipient.error_message && (
                <div>
                  <label className="block text-xs font-medium text-red-500 uppercase mb-1">
                    Error
                  </label>
                  <p className="text-sm text-red-600">{recipient.error_message}</p>
                </div>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  );
};
