import React from 'react';
import type { ColumnDef } from '@tanstack/react-table';
import type { CampaignRecipient } from '@/types/api';
import { Badge } from '@/components/ui/Badge';
import { DataTable } from '@/components/ui/data-table';

interface RecipientTableProps {
  recipients: CampaignRecipient[];
}

interface MessageModalProps {
  recipient: CampaignRecipient;
  onClose: () => void;
}

const MessageModal: React.FC<MessageModalProps> = ({ recipient, onClose }) => {
  const message = recipient.generated_message;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between px-6 py-4 border-b border-gray-200">
          <div>
            <p className="font-semibold text-gray-900">
              {recipient.customer_name || 'Message'}
            </p>
            {recipient.customer_email && (
              <p className="text-sm text-gray-500 mt-0.5">To: {recipient.customer_email}</p>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl leading-none ml-4"
          >
            ✕
          </button>
        </div>

        <div className="px-6 py-4 space-y-4">
          {message ? (
            <>
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                  Subject
                </label>
                <p className="text-sm font-medium text-gray-900 bg-gray-50 rounded-lg px-3 py-2">
                  {message.subject}
                </p>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                  Body
                </label>
                <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed bg-gray-50 rounded-lg px-3 py-2">
                  {message.body}
                </p>
              </div>
            </>
          ) : (
            recipient.error_message && (
              <div>
                <label className="block text-xs font-semibold text-red-500 uppercase tracking-wide mb-1">
                  Error
                </label>
                <p className="text-sm text-red-600">{recipient.error_message}</p>
              </div>
            )
          )}
        </div>
      </div>
    </div>
  );
};

export const RecipientTable: React.FC<RecipientTableProps> = ({ recipients }) => {
  const [selectedRecipient, setSelectedRecipient] = React.useState<CampaignRecipient | null>(null);

  const columns: ColumnDef<CampaignRecipient>[] = [
    {
      accessorKey: 'customer_name',
      header: 'Customer',
      cell: ({ row }) => (
        <div>
          <div className="text-sm font-medium text-gray-900">
            {row.original.customer_name || (
              <span className="font-mono text-gray-500">
                {row.original.customer_id.substring(0, 8)}...
              </span>
            )}
          </div>
          {row.original.customer_email && (
            <div className="text-xs text-gray-500">{row.original.customer_email}</div>
          )}
        </div>
      ),
    },
    {
      accessorKey: 'subject',
      header: 'Subject',
      cell: ({ row }) => {
        const message = row.original.generated_message;
        return <div className="text-sm text-gray-900">{message?.subject || '-'}</div>;
      },
    },
    {
      accessorKey: 'body_preview',
      header: 'Body Preview',
      cell: ({ row }) => {
        const message = row.original.generated_message;
        const bodyPreview = message?.body
          ? message.body.substring(0, 80) + (message.body.length > 80 ? '...' : '')
          : '-';
        return <div className="text-sm text-gray-500 max-w-xs truncate">{bodyPreview}</div>;
      },
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => {
        const status = row.original.status;
        return (
          <Badge
            variant={
              status === 'generated' ? 'success' : status === 'failed' ? 'danger' : 'warning'
            }
          >
            {status}
          </Badge>
        );
      },
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => {
        const hasContent = row.original.generated_message || row.original.error_message;
        if (!hasContent) return null;
        return (
          <button
            onClick={(e) => {
              e.stopPropagation();
              setSelectedRecipient(row.original);
            }}
            className="text-primary-600 hover:text-primary-700 font-medium text-sm"
          >
            View Full
          </button>
        );
      },
    },
  ];

  if (recipients.length === 0) {
    return (
      <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
        <p className="text-gray-500">No recipients yet</p>
      </div>
    );
  }

  return (
    <>
      <div className="overflow-hidden border border-gray-200 rounded-lg">
        <DataTable
          columns={columns}
          data={recipients}
          showPagination={true}
          pageSize={10}
          emptyMessage="No recipients yet"
        />
      </div>

      {selectedRecipient && (
        <MessageModal
          recipient={selectedRecipient}
          onClose={() => setSelectedRecipient(null)}
        />
      )}
    </>
  );
};
