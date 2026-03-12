import React from 'react';
import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { campaignsApi } from '@/api/campaigns';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { CampaignForm } from './components/CampaignForm';
import { SegmentPreview } from './components/SegmentPreview';
import { MessagePreviewCard } from './components/MessagePreviewCard';
import type { SegmentFilters, CampaignRecipient } from '@/types/api';
import { useSettingsStore } from '@/stores/settings';

export const NewCampaign: React.FC = () => {
  const { llm } = useSettingsStore();
  const navigate = useNavigate();
  const [name, setName] = React.useState('');
  const [description, setDescription] = React.useState('');
  const [purpose, setPurpose] = React.useState('');
  const [filters, setFilters] = React.useState<SegmentFilters>({});
  const [previewRecipients, setPreviewRecipients] = React.useState<
    CampaignRecipient[]
  >([]);
  const [showPreview, setShowPreview] = React.useState(false);

  const createMutation = useMutation({
    mutationFn: () =>
      campaignsApi.create({
        name,
        description: description || undefined,
        purpose: purpose || undefined,
        segment_filters: filters,
      }),
    onSuccess: (data) => {
      navigate(`/campaigns/${data.id}`);
    },
  });

  const previewMutation = useMutation({
    mutationFn: async () => {
      // First create a draft campaign
      const campaign = await campaignsApi.create({
        name: name || 'Draft Preview',
        description: description || undefined,
        purpose: purpose || undefined,
        segment_filters: filters,
      });
      // Then generate preview
      const preview = await campaignsApi.preview(campaign.id, { provider: llm.provider, model: llm.model });
      return { campaign, preview };
    },
    onSuccess: ({ campaign, preview }) => {
      console.log('✓ Preview generated successfully');
      console.log('Campaign:', campaign);
      console.log('Preview data:', preview);

      // The API returns { recipients: [...] }
      const recipients = preview.recipients || [];
      console.log(`Found ${recipients.length} preview recipients`);

      if (recipients.length > 0) {
        setPreviewRecipients(recipients);
        setShowPreview(true);
      } else {
        console.warn('No recipients in preview response');
      }
    },
    onError: (error) => {
      console.error('Preview generation failed:', error);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !purpose) {
      alert('Please fill in campaign name and purpose');
      return;
    }
    createMutation.mutate();
  };

  const handlePreview = () => {
    if (!name || !purpose) {
      alert('Please fill in campaign name and purpose');
      return;
    }
    previewMutation.mutate();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Create Campaign</h1>
          <p className="mt-1 text-gray-600">
            Design a personalized marketing campaign
          </p>
        </div>
        <Button variant="ghost" onClick={() => navigate('/campaigns')}>
          Cancel
        </Button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Campaign Form */}
        <Card>
          <CardContent className="pt-6">
            <CampaignForm
              name={name}
              setName={setName}
              description={description}
              setDescription={setDescription}
              purpose={purpose}
              setPurpose={setPurpose}
              filters={filters}
              setFilters={setFilters}
            />
          </CardContent>
        </Card>

        {/* Segment Preview */}
        <SegmentPreview filters={filters} />

        {/* Preview Loading State */}
        {previewMutation.isPending && (
          <Card>
            <CardContent className="pt-6">
              <div className="text-center py-8">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                <p className="mt-4 text-gray-600 font-medium">Generating preview messages...</p>
                <p className="text-sm text-gray-500 mt-1">This may take a few moments</p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Preview Success Message */}
        {previewMutation.isSuccess && !previewMutation.isPending && previewRecipients.length === 0 && (
          <Card>
            <CardContent className="pt-6">
              <div className="text-center py-8">
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 inline-block">
                  <p className="text-yellow-800 font-medium">⚠️ No preview messages generated</p>
                  <p className="text-sm text-yellow-700 mt-1">
                    Check the console for details or try again
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Preview Messages Section */}
        {showPreview && previewRecipients.length > 0 && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Message Previews</CardTitle>
                  <p className="text-sm text-gray-600 mt-1">
                    Here are {previewRecipients.length} sample message{previewRecipients.length > 1 ? 's' : ''} generated for your campaign
                  </p>
                </div>
                <div className="bg-green-50 border border-green-200 rounded-full px-3 py-1">
                  <span className="text-sm font-medium text-green-800">✓ Generated</span>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {previewRecipients.map((recipient) => (
                  <MessagePreviewCard
                    key={recipient.id}
                    recipient={recipient}
                  />
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Action Buttons */}
        <div className="flex items-center justify-between gap-4 pt-6 border-t border-gray-200">
          <Button
            type="button"
            variant="secondary"
            onClick={handlePreview}
            loading={previewMutation.isPending}
            disabled={!name || !purpose || createMutation.isPending}
            className="flex-1 sm:flex-none"
          >
            {previewMutation.isPending ? 'Generating...' : 'Preview Messages'}
          </Button>
          <Button
            type="submit"
            loading={createMutation.isPending}
            disabled={!name || !purpose || previewMutation.isPending}
            className="flex-1 sm:flex-none"
          >
            {createMutation.isPending ? 'Creating...' : 'Create Campaign'}
          </Button>
        </div>

        {createMutation.isError && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">
              Error creating campaign. Please try again.
            </p>
          </div>
        )}

        {previewMutation.isSuccess && previewRecipients.length > 0 && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <p className="text-green-800 font-medium">
              ✓ Preview messages generated successfully! Scroll down to see them.
            </p>
          </div>
        )}

        {previewMutation.isError && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800 font-medium">
              Error generating preview. Please try again.
            </p>
            <p className="text-sm text-red-600 mt-1">
              Check the browser console for more details.
            </p>
          </div>
        )}
      </form>
    </div>
  );
};
