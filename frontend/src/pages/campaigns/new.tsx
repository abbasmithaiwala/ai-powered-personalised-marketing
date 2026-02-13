import React from 'react';
import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { campaignsApi } from '@/api/campaigns';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
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
    onSuccess: ({ preview }) => {
      setPreviewRecipients(preview?.recipients || []);
      setShowPreview(true);
      // Update the form to use the created campaign's ID
      // (in a real app, you might want to navigate to the campaign detail page)
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
    <div className="max-w-4xl mx-auto space-y-6">
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
        <Card padding="lg">
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
        </Card>

        {/* Segment Preview */}
        <SegmentPreview filters={filters} />

        {/* Preview Messages Section */}
        {showPreview && previewRecipients.length > 0 && (
          <Card padding="lg">
            <CardHeader>
              <CardTitle>Message Previews</CardTitle>
              <p className="text-sm text-gray-600 mt-1">
                Here are 3 sample messages generated for your campaign
              </p>
            </CardHeader>
            <div className="grid gap-4 md:grid-cols-1">
              {previewRecipients?.map((recipient) => (
                <MessagePreviewCard
                  key={recipient.id}
                  recipient={recipient}
                />
              ))}
            </div>
          </Card>
        )}

        {/* Action Buttons */}
        <div className="flex items-center gap-4">
          <Button
            type="button"
            variant="secondary"
            onClick={handlePreview}
            loading={previewMutation.isPending}
            disabled={!name || !purpose || createMutation.isPending}
          >
            Preview Messages
          </Button>
          <Button
            type="submit"
            loading={createMutation.isPending}
            disabled={!name || !purpose || previewMutation.isPending}
          >
            Create Campaign
          </Button>
        </div>

        {createMutation.isError && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">
              Error creating campaign. Please try again.
            </p>
          </div>
        )}

        {previewMutation.isError && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">
              Error generating preview. Please try again.
            </p>
          </div>
        )}
      </form>
    </div>
  );
};
