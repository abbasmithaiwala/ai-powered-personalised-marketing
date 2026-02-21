import React from 'react';
import type { ColumnDef } from '@tanstack/react-table';
import type { CampaignRecipient } from '@/types/api';
import { Badge } from '@/components/ui/Badge';
import { DataTable } from '@/components/ui/data-table';

interface RecipientTableProps {
  recipients: CampaignRecipient[];
}

export const RecipientTable: React.FC<RecipientTableProps> = ({ recipients }) => {
  const [expandedRows, setExpandedRows] = React.useState<Set<string>>(new Set());

  const toggleRow = (id: string) => {
    setExpandedRows((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const columns: ColumnDef<CampaignRecipient>[] = [
    {
      accessorKey: 'customer_id',
      header: 'Customer ID',
      cell: ({ row }) => {
        return (
          <div className="text-sm font-mono text-gray-900">
            {row.original.customer_id.substring(0, 8)}...
          </div>
        );
      },
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
          ? message.body.substring(0, 100) + (message.body.length > 100 ? '...' : '')
          : '-';
        return <div className="text-sm text-gray-500 max-w-md truncate">{bodyPreview}</div>;
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
              status === 'generated'
                ? 'success'
                : status === 'failed'
                ? 'danger'
                : 'warning'
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
        const message = row.original.generated_message;
        const isExpanded = expandedRows.has(row.original.id);
        if (!message) return null;
        return (
          <button
            onClick={(e) => {
              e.stopPropagation();
              toggleRow(row.original.id);
            }}
            className="text-primary-600 hover:text-primary-700 font-medium text-sm"
          >
            {isExpanded ? 'Hide' : 'View Full'}
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
    <div className="overflow-hidden border border-gray-200 rounded-lg">
      <DataTable
        columns={columns}
        data={recipients}
        showPagination={true}
        pageSize={10}
        emptyMessage="No recipients yet"
      />

      {/* Expanded details (rendered outside table) */}
      {recipients.map((recipient) => {
        const isExpanded = expandedRows.has(recipient.id);
        const message = recipient.generated_message;

        if (!isExpanded || !message) return null;

        return (
          <div key={recipient.id} className="px-6 py-4 bg-gray-50 border-t border-gray-200">
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-500 uppercase mb-1">
                  Subject
                </label>
                <p className="text-sm font-medium text-gray-900">{message.subject}</p>
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
          </div>
        );
      })}
    </div>
  );
};
