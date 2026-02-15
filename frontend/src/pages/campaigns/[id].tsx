import React from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useParams, Link } from 'react-router-dom';
import { campaignsApi } from '@/api/campaigns';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { CampaignProgress } from './components/CampaignProgress';
import { RecipientTable } from './components/RecipientTable';
import { ArrowPathIcon } from '@/components/icons';
import { useSettingsStore } from '@/stores/settings';

export const CampaignDetail: React.FC = () => {
  const { llm } = useSettingsStore();
  const { id } = useParams<{ id: string }>();
  const [recipientPage, setRecipientPage] = React.useState(1);
  const recipientPageSize = 25;
  const [showPreviewSuccess, setShowPreviewSuccess] = React.useState(false);

  // Auto-refresh when campaign is executing
  const {
    data: campaign,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['campaign', id],
    queryFn: () => campaignsApi.get(id!),
    enabled: !!id,
    refetchInterval: (query) => {
      // Auto-refresh every 3 seconds when executing
      return query.state.data?.status === 'executing' ? 3000 : false;
    },
  });

  const {
    data: recipientsData,
    isLoading: recipientsLoading,
    refetch: refetchRecipients,
  } = useQuery({
    queryKey: ['campaign-recipients', id, recipientPage, recipientPageSize],
    queryFn: () => campaignsApi.listRecipients(id!, recipientPage, recipientPageSize),
    enabled: !!id,
    refetchInterval: () => {
      // Auto-refresh recipients when campaign is executing or previewing
      return campaign?.status === 'executing' || campaign?.status === 'previewing' ? 3000 : false;
    },
  });

  const previewMutation = useMutation({
    mutationFn: () => campaignsApi.preview(id!, { provider: llm.provider, model: llm.model }),
    onSuccess: async () => {
      setShowPreviewSuccess(true);
      // Refetch campaign and recipients data
      await refetch();
      // Small delay to ensure backend has updated
      setTimeout(async () => {
        await refetchRecipients();
      }, 500);
      // Auto-hide success message after 5 seconds
      setTimeout(() => setShowPreviewSuccess(false), 5000);
    },
  });

  const executeMutation = useMutation({
    mutationFn: () => campaignsApi.execute(id!, { provider: llm.provider, model: llm.model }),
    onSuccess: () => {
      refetch();
      refetchRecipients();
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <ArrowPathIcon className="w-12 h-12 text-gray-400 animate-spin mx-auto" />
          <p className="mt-4 text-gray-600">Loading campaign...</p>
        </div>
      </div>
    );
  }

  if (error || !campaign) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error loading campaign</p>
      </div>
    );
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const canPreview = campaign.status === 'draft' || campaign.status === 'ready';
  const canExecute = campaign.status === 'draft' || campaign.status === 'ready';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <Link
              to="/campaigns"
              className="text-gray-500 hover:text-gray-700"
            >
              ← Back to Campaigns
            </Link>
          </div>
          <h1 className="text-3xl font-bold text-gray-900">{campaign.name}</h1>
          {campaign.description && (
            <p className="mt-1 text-gray-600">{campaign.description}</p>
          )}
        </div>
      </div>

      {/* Campaign Info & Progress */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Campaign Details */}
        <Card padding="lg">
          <CardHeader>
            <CardTitle>Campaign Details</CardTitle>
          </CardHeader>
          <div className="space-y-3">
            {campaign.purpose && (
              <div>
                <label className="block text-sm font-medium text-gray-500 mb-1">
                  Purpose
                </label>
                <p className="text-sm text-gray-900">{campaign.purpose}</p>
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">
                Created
              </label>
              <p className="text-sm text-gray-900">
                {formatDate(campaign.created_at)}
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">
                Last Updated
              </label>
              <p className="text-sm text-gray-900">
                {formatDate(campaign.updated_at)}
              </p>
            </div>
          </div>
        </Card>

        {/* Progress */}
        <Card padding="lg">
          <CardHeader>
            <CardTitle>Progress</CardTitle>
          </CardHeader>
          <CampaignProgress campaign={campaign} />
        </Card>
      </div>

      {/* Segment Filters */}
      <Card padding="lg">
        <CardHeader>
          <CardTitle>Target Audience Filters</CardTitle>
        </CardHeader>
        <div className="grid md:grid-cols-2 gap-4 text-sm">
          {Object.entries(campaign.segment_filters).map(([key, value]) => {
            if (value === undefined || value === null || value === '') return null;
            return (
              <div key={key} className="flex items-center justify-between py-2 border-b border-gray-100">
                <span className="text-gray-500 capitalize">
                  {key.replace(/_/g, ' ')}:
                </span>
                <span className="font-medium text-gray-900">
                  {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                </span>
              </div>
            );
          })}
          {Object.keys(campaign.segment_filters).length === 0 && (
            <p className="text-gray-500 col-span-2">No filters applied (all customers)</p>
          )}
        </div>
      </Card>

      {/* Actions */}
      {(canPreview || canExecute) && (
        <Card padding="lg">
          <CardHeader>
            <CardTitle>Campaign Actions</CardTitle>
            <p className="text-sm text-gray-600 mt-1">
              Preview sample messages or execute the full campaign
            </p>
          </CardHeader>
          <div className="flex items-center gap-4 flex-wrap">
            {canPreview && (
              <Button
                variant="secondary"
                onClick={() => previewMutation.mutate()}
                loading={previewMutation.isPending}
                disabled={executeMutation.isPending}
                className="flex-1 sm:flex-none min-w-[200px]"
              >
                {previewMutation.isPending ? 'Generating Preview...' : 'Preview Messages (3 samples)'}
              </Button>
            )}
            {canExecute && (
              <Button
                onClick={() => {
                  if (
                    confirm(
                      `Generate messages for ${campaign.total_recipients} recipients? This may take several minutes.`
                    )
                  ) {
                    executeMutation.mutate();
                  }
                }}
                loading={executeMutation.isPending}
                disabled={previewMutation.isPending}
                className="flex-1 sm:flex-none min-w-[200px]"
              >
                {executeMutation.isPending ? 'Executing...' : 'Execute Campaign'}
              </Button>
            )}
          </div>
          {showPreviewSuccess && (
            <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-green-800 font-medium">✓ Preview messages generated successfully!</p>
              <p className="text-sm text-green-700 mt-1">
                Check the Recipients & Messages section below to see the previews.
              </p>
            </div>
          )}
          {previewMutation.isError && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-800">Error generating preview. Please try again.</p>
            </div>
          )}
          {executeMutation.isError && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-800">Error executing campaign. Please try again.</p>
            </div>
          )}
        </Card>
      )}

      {/* Recipients */}
      <Card padding="lg">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <CardTitle>Recipients & Messages</CardTitle>
              <p className="text-sm text-gray-600 mt-1">
                {campaign.status === 'draft' && 'Preview or execute the campaign to generate messages'}
                {campaign.status === 'ready' && 'Preview generated! Execute to generate all messages'}
                {campaign.status === 'previewing' && 'Generating preview messages...'}
                {campaign.status === 'executing' && 'Generating messages for all recipients...'}
                {campaign.status === 'completed' && 'All messages have been generated'}
              </p>
            </div>
            <div className="flex items-center gap-2">
              {campaign.total_recipients > 0 && (
                <Badge variant="default">
                  {campaign.total_recipients.toLocaleString()} total
                </Badge>
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  refetch();
                  refetchRecipients();
                }}
                disabled={recipientsLoading}
              >
                <ArrowPathIcon className={`w-4 h-4 ${recipientsLoading ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </div>
        </CardHeader>
        {recipientsLoading ? (
          <div className="text-center py-8">
            <ArrowPathIcon className="w-8 h-8 text-gray-400 animate-spin mx-auto" />
            <p className="mt-2 text-gray-600">Loading recipients...</p>
          </div>
        ) : recipientsData && recipientsData.items.length > 0 ? (
          <>
            <RecipientTable recipients={recipientsData.items} />
            {/* Pagination */}
            {recipientsData.pages > 1 && (
              <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200">
                <div>
                  <p className="text-sm text-gray-700">
                    Showing page <span className="font-medium">{recipientPage}</span> of{' '}
                    <span className="font-medium">{recipientsData.pages}</span>
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => setRecipientPage((p) => Math.max(1, p - 1))}
                    disabled={recipientPage === 1}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() =>
                      setRecipientPage((p) => Math.min(recipientsData.pages, p + 1))
                    }
                    disabled={recipientPage === recipientsData.pages}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </>
        ) : campaign.total_recipients > 0 ? (
          <div className="text-center py-8 bg-gray-50 rounded-lg border border-gray-200">
            <p className="text-gray-600 font-medium">No messages generated yet</p>
            <p className="text-sm text-gray-500 mt-1">
              Click "Preview Messages" above to see 3 sample messages
            </p>
          </div>
        ) : (
          <div className="text-center py-8 bg-gray-50 rounded-lg border border-gray-200">
            <p className="text-gray-600 font-medium">No recipients found</p>
            <p className="text-sm text-gray-500 mt-1">
              Adjust your segment filters to include more customers
            </p>
          </div>
        )}
      </Card>
    </div>
  );
};
