import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { campaignsApi } from '@/api/campaigns';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import type { Campaign } from '@/types/api';

export const Campaigns: React.FC = () => {
  const [page, setPage] = React.useState(1);
  const pageSize = 25;

  const { data, isLoading, error } = useQuery({
    queryKey: ['campaigns', page, pageSize],
    queryFn: () => campaignsApi.list(page, pageSize),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto" />
          <p className="mt-4 text-gray-600">Loading campaigns...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error loading campaigns</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Campaigns</h1>
          <p className="mt-1 text-gray-600">
            Create and manage marketing campaigns
          </p>
        </div>
        <Link to="/campaigns/new">
          <Button>Create Campaign</Button>
        </Link>
      </div>

      {/* Campaigns List */}
      {data && data.items.length > 0 ? (
        <div className="space-y-4">
          {data.items.map((campaign) => (
            <CampaignCard key={campaign.id} campaign={campaign} />
          ))}

          {/* Pagination */}
          {data.pages > 1 && (
            <div className="flex items-center justify-between border-t border-gray-200 bg-white px-4 py-3 sm:px-6 rounded-lg">
              <div className="flex flex-1 justify-between sm:hidden">
                <Button
                  variant="secondary"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  Previous
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
                  disabled={page === data.pages}
                >
                  Next
                </Button>
              </div>
              <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm text-gray-700">
                    Showing page <span className="font-medium">{page}</span> of{' '}
                    <span className="font-medium">{data.pages}</span> (
                    <span className="font-medium">{data.total}</span> total
                    campaigns)
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="secondary"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
                    disabled={page === data.pages}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      ) : (
        <Card className="text-center py-12">
          <div className="mx-auto w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mb-4">
            <svg
              className="w-12 h-12 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No campaigns yet
          </h3>
          <p className="text-gray-600 mb-6">
            Get started by creating your first marketing campaign
          </p>
          <Link to="/campaigns/new">
            <Button>Create Your First Campaign</Button>
          </Link>
        </Card>
      )}
    </div>
  );
};

const CampaignCard: React.FC<{ campaign: Campaign }> = ({ campaign }) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  };

  const getStatusBadgeVariant = (status: Campaign['status']) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'executing':
        return 'primary';
      case 'failed':
        return 'danger';
      case 'ready':
        return 'info';
      default:
        return 'default';
    }
  };

  const percentage =
    campaign.total_recipients > 0
      ? (campaign.generated_count / campaign.total_recipients) * 100
      : 0;

  return (
    <Link to={`/campaigns/${campaign.id}`}>
      <Card className="hover:shadow-md transition-shadow cursor-pointer">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h3 className="text-lg font-semibold text-gray-900">
                {campaign.name}
              </h3>
              <Badge variant={getStatusBadgeVariant(campaign.status)}>
                {campaign.status}
              </Badge>
            </div>
            {campaign.description && (
              <p className="text-sm text-gray-600 mb-3">{campaign.description}</p>
            )}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Recipients:</span>
                <span className="ml-2 font-medium text-gray-900">
                  {campaign.total_recipients.toLocaleString()}
                </span>
              </div>
              <div>
                <span className="text-gray-500">Generated:</span>
                <span className="ml-2 font-medium text-gray-900">
                  {campaign.generated_count.toLocaleString()}
                </span>
              </div>
              <div>
                <span className="text-gray-500">Created:</span>
                <span className="ml-2 font-medium text-gray-900">
                  {formatDate(campaign.created_at)}
                </span>
              </div>
              {campaign.status === 'executing' && (
                <div>
                  <span className="text-gray-500">Progress:</span>
                  <span className="ml-2 font-medium text-gray-900">
                    {percentage.toFixed(0)}%
                  </span>
                </div>
              )}
            </div>
            {campaign.status === 'executing' && (
              <div className="mt-3">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      </Card>
    </Link>
  );
};
