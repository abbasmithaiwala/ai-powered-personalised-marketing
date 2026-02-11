import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Card, CardHeader, CardTitle, Badge } from '@/components/ui';
import { ingestionApi } from '@/api/ingestion';
import { formatRelativeTime } from '@/utils/formatting';
import type { IngestionJob } from '@/types/api';

const getStatusColor = (status: IngestionJob['status']) => {
  switch (status) {
    case 'completed':
      return 'success';
    case 'failed':
      return 'error';
    case 'processing':
      return 'warning';
    default:
      return 'default';
  }
};

export const RecentImports: React.FC = () => {
  const { data, isLoading } = useQuery({
    queryKey: ['recent-imports'],
    queryFn: () => ingestionApi.listJobs(1, 5),
  });

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Data Imports</CardTitle>
        </CardHeader>
        <div className="space-y-3 animate-pulse">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center justify-between p-3 border-b border-gray-100">
              <div className="flex-1">
                <div className="h-4 bg-gray-200 rounded w-1/3 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-1/4"></div>
              </div>
              <div className="h-6 w-20 bg-gray-200 rounded"></div>
            </div>
          ))}
        </div>
      </Card>
    );
  }

  if (!data || data.items.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Data Imports</CardTitle>
        </CardHeader>
        <div className="text-center py-8">
          <p className="text-gray-500">No imports yet</p>
          <Link
            to="/import"
            className="text-primary-600 hover:text-primary-700 font-medium mt-2 inline-block"
          >
            Upload your first CSV
          </Link>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Recent Data Imports</CardTitle>
          <Link
            to="/import"
            className="text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            View all
          </Link>
        </div>
      </CardHeader>
      <div className="space-y-3">
        {data.items.map((job) => (
          <div
            key={job.id}
            className="flex items-center justify-between p-3 hover:bg-gray-50 transition-colors border-b border-gray-100 last:border-0"
          >
            <div className="flex-1">
              <p className="font-medium text-gray-900">{job.filename}</p>
              <p className="text-sm text-gray-500">
                {formatRelativeTime(job.created_at)} •{' '}
                {job.processed_rows ? `${job.processed_rows.toLocaleString()} rows` : 'Processing...'}
              </p>
            </div>
            <Badge variant={getStatusColor(job.status)}>
              {job.status}
            </Badge>
          </div>
        ))}
      </div>
    </Card>
  );
};
