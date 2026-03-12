import React, { useState } from 'react';
import { useBulkCreateMenuItems } from '@/hooks/useApi';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { UploadStep } from './components/UploadStep';
import { ReviewStep } from './components/ReviewStep';
import { DoneStep } from './components/DoneStep';
import type { BulkCreateResponse, ParsedMenuItem, PDFParseResponse } from '@/types/api';

type ImportStep = 'upload' | 'review' | 'done';

const STEPS: { key: ImportStep; label: string }[] = [
  { key: 'upload', label: 'Upload' },
  { key: 'review', label: 'Review' },
  { key: 'done', label: 'Done' },
];

export const PdfImportPage: React.FC = () => {
  const [step, setStep] = useState<ImportStep>('upload');
  const [brandId, setBrandId] = useState('');
  const [brandName, setBrandName] = useState('');
  const [filename, setFilename] = useState('');
  const [reviewItems, setReviewItems] = useState<ParsedMenuItem[]>([]);
  const [bulkResult, setBulkResult] = useState<BulkCreateResponse | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const bulkCreateMutation = useBulkCreateMenuItems();

  const handleParseSuccess = (
    data: PDFParseResponse,
    parsedBrandId: string,
    parsedBrandName: string
  ) => {
    setBrandId(parsedBrandId);
    setBrandName(parsedBrandName);
    setFilename(data.filename);
    // Filter out items with no name
    setReviewItems(data.items.filter((item) => item.name.trim().length > 0));
    setStep('review');
  };

  const handleConfirmSave = () => {
    setSubmitError(null);
    const validItems = reviewItems.filter((item) => item.name.trim().length > 0);
    bulkCreateMutation.mutate(
      { brand_id: brandId, items: validItems },
      {
        onSuccess: (result) => {
          setBulkResult(result);
          setStep('done');
        },
        onError: (err) => {
          setSubmitError((err as Error)?.message ?? 'Failed to save items. Please try again.');
        },
      }
    );
  };

  const handleReset = () => {
    setStep('upload');
    setBrandId('');
    setBrandName('');
    setFilename('');
    setReviewItems([]);
    setBulkResult(null);
    setSubmitError(null);
    bulkCreateMutation.reset();
  };

  const currentStepIndex = STEPS.findIndex((s) => s.key === step);

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">PDF Menu Import</h1>
        <p className="text-sm text-gray-500 mt-1">
          Upload a menu PDF, review the extracted items, then save them to your catalogue.
        </p>
      </div>

      {/* Step indicator */}
      <div className="flex items-center gap-0">
        {STEPS.map((s, i) => {
          const isCompleted = i < currentStepIndex;
          const isActive = i === currentStepIndex;
          return (
            <React.Fragment key={s.key}>
              <div className="flex items-center gap-2">
                <div
                  className={[
                    'w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold',
                    isCompleted
                      ? 'bg-green-500 text-white'
                      : isActive
                        ? 'bg-orange-500 text-white'
                        : 'bg-gray-200 text-gray-500',
                  ].join(' ')}
                >
                  {isCompleted ? '✓' : i + 1}
                </div>
                <span
                  className={[
                    'text-sm font-medium',
                    isActive ? 'text-gray-900' : 'text-gray-400',
                  ].join(' ')}
                >
                  {s.label}
                </span>
              </div>
              {i < STEPS.length - 1 && (
                <div
                  className={[
                    'flex-1 h-px mx-3',
                    i < currentStepIndex ? 'bg-green-400' : 'bg-gray-200',
                  ].join(' ')}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Submit error (shown in review step) */}
      {submitError && step === 'review' && (
        <Alert variant="destructive">
          <AlertDescription>{submitError}</AlertDescription>
        </Alert>
      )}

      {/* Step content */}
      <div className="bg-white rounded-2xl border border-gray-200 p-6">
        {step === 'upload' && <UploadStep onSuccess={handleParseSuccess} />}

        {step === 'review' && (
          <ReviewStep
            items={reviewItems}
            brandName={brandName}
            filename={filename}
            onItemsChange={setReviewItems}
            onConfirm={handleConfirmSave}
            onBack={() => setStep('upload')}
            isSubmitting={bulkCreateMutation.isPending}
          />
        )}

        {step === 'done' && bulkResult && (
          <DoneStep result={bulkResult} brandId={brandId} onReset={handleReset} />
        )}
      </div>
    </div>
  );
};
