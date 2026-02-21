import React from 'react';
import type { ColumnDef } from '@tanstack/react-table';
import { Card, CardHeader, CardTitle, Badge } from '@/components/ui';
import type { IngestionJob } from '@/types/api';
import { formatDate, formatNumber } from '@/utils/formatting';
import { DataTable } from '@/components/ui/data-table';

interface ImportHistoryProps {
  jobs: IngestionJob[];
  loading?: boolean;
}

export const ImportHistory: React.FC<ImportHistoryProps> = ({ jobs, loading = false }) => {
  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'success' | 'error' | 'warning' | 'gray' | 'blue'> = {
      completed: 'success',
      failed: 'error',
      processing: 'blue',
      pending: 'warning',
    };
    return <Badge variant={variants[status] || 'gray'}>{status.toUpperCase()}</Badge>;
  };

  const calculateProgress = (job: IngestionJob) => {
    if (!job.total_rows || job.total_rows === 0) return 0;
    return Math.round(((job.processed_rows || 0) / job.total_rows) * 100);
  };

  const columns: ColumnDef<IngestionJob>[] = [
    {
      accessorKey: 'filename',
      header: 'Filename',
      cell: ({ row }) => {
        const job = row.original;
        return (
          <div>
            <div className="text-sm font-medium text-gray-900">{job.filename}</div>
            <div className="text-xs text-gray-500">{job.csv_type}</div>
          </div>
        );
      },
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => getStatusBadge(row.original.status),
    },
    {
      accessorKey: 'progress',
      header: 'Progress',
      cell: ({ row }) => {
        const job = row.original;
        if (job.status === 'processing' || job.status === 'completed') {
          const progress = calculateProgress(job);
          return (
            <div className="flex items-center space-x-2">
              <div className="flex-1 bg-gray-200 rounded-full h-2 max-w-[100px]">
                <div
                  className={`h-2 rounded-full ${
                    job.status === 'completed' ? 'bg-green-500' : 'bg-blue-500'
                  }`}
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
              <span className="text-xs text-gray-600">{progress}%</span>
            </div>
          );
        }
        return <span className="text-xs text-gray-500">-</span>;
      },
    },
    {
      accessorKey: 'rows',
      header: 'Rows',
      cell: ({ row }) => {
        const job = row.original;
        if (job.total_rows !== null) {
          return (
            <div className="text-sm text-gray-900">
              <div>
                {formatNumber(job.processed_rows || 0)} / {formatNumber(job.total_rows)}
              </div>
              {job.failed_rows && job.failed_rows > 0 && (
                <div className="text-xs text-red-600">
                  {formatNumber(job.failed_rows)} failed
                </div>
              )}
            </div>
          );
        }
        return <span className="text-sm text-gray-500">-</span>;
      },
    },
    {
      accessorKey: 'created_at',
      header: 'Date',
      cell: ({ row }) => {
        return (
          <div className="text-sm text-gray-500">{formatDate(row.original.created_at)}</div>
        );
      },
    },
  ];

  if (jobs.length === 0 && !loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Import History</CardTitle>
        </CardHeader>
        <div className="p-6 text-center text-gray-500">No import history yet</div>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Import History</CardTitle>
      </CardHeader>
      <div className="p-6">
        <DataTable
          columns={columns}
          data={jobs}
          isLoading={loading}
          emptyMessage="No import history yet"
          showPagination={true}
          pageSize={10}
        />
      </div>
    </Card>
  );
};
