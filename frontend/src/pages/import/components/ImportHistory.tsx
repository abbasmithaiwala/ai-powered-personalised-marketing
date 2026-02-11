import React from 'react';
import { Card, CardHeader, CardTitle, Badge } from '@/components/ui';
import type { IngestionJob } from '@/types/api';
import { formatDate, formatNumber } from '@/utils/formatting';

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

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Import History</CardTitle>
        </CardHeader>
        <div className="p-6">
          <div className="animate-pulse space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </Card>
    );
  }

  if (jobs.length === 0) {
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
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Filename
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Progress
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Rows
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Date
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {jobs.map((job) => (
              <tr key={job.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">{job.filename}</div>
                  <div className="text-xs text-gray-500">{job.csv_type}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">{getStatusBadge(job.status)}</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {job.status === 'processing' || job.status === 'completed' ? (
                    <div className="flex items-center space-x-2">
                      <div className="flex-1 bg-gray-200 rounded-full h-2 max-w-[100px]">
                        <div
                          className={`h-2 rounded-full ${
                            job.status === 'completed' ? 'bg-green-500' : 'bg-blue-500'
                          }`}
                          style={{ width: `${calculateProgress(job)}%` }}
                        ></div>
                      </div>
                      <span className="text-xs text-gray-600">{calculateProgress(job)}%</span>
                    </div>
                  ) : (
                    <span className="text-xs text-gray-500">-</span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {job.total_rows !== null ? (
                    <div>
                      <div>
                        {formatNumber(job.processed_rows || 0)} /{' '}
                        {formatNumber(job.total_rows)}
                      </div>
                      {job.failed_rows && job.failed_rows > 0 && (
                        <div className="text-xs text-red-600">
                          {formatNumber(job.failed_rows)} failed
                        </div>
                      )}
                    </div>
                  ) : (
                    '-'
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatDate(job.created_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
};
