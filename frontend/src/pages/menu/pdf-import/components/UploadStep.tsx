import React, { useState } from 'react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/Button';
import { useBrands, useParsePDF } from '@/hooks/useApi';
import { PDFDropzone } from './PDFDropzone';
import type { PDFParseResponse } from '@/types/api';

interface UploadStepProps {
  onSuccess: (data: PDFParseResponse, brandId: string, brandName: string) => void;
}

export const UploadStep: React.FC<UploadStepProps> = ({ onSuccess }) => {
  const [selectedBrandId, setSelectedBrandId] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const { data: brandsData } = useBrands();
  const parseMutation = useParsePDF();

  const brands = brandsData?.items ?? [];

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    // Auto-trigger parse if brand already selected
    if (selectedBrandId) {
      triggerParse(file, selectedBrandId);
    }
  };

  const triggerParse = (file: File, brandId: string) => {
    parseMutation.mutate(
      { file, brandId },
      {
        onSuccess: (data) => {
          const brand = brands.find((b) => b.id === brandId);
          onSuccess(data, brandId, brand?.name ?? '');
        },
      }
    );
  };

  const handleParseClick = () => {
    if (!selectedFile || !selectedBrandId) return;
    triggerParse(selectedFile, selectedBrandId);
  };

  const errorMessage = parseMutation.isError
    ? (parseMutation.error as Error)?.message ?? 'Failed to parse PDF. Please try again.'
    : null;

  return (
    <div className="max-w-xl mx-auto space-y-6">
      {/* Brand selector */}
      <div className="space-y-1.5">
        <label className="text-sm font-medium text-gray-700">Brand</label>
        <Select
          value={selectedBrandId}
          onValueChange={setSelectedBrandId}
          disabled={parseMutation.isPending}
        >
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Select a brand..." />
          </SelectTrigger>
          <SelectContent>
            {brands.map((brand) => (
              <SelectItem key={brand.id} value={brand.id}>
                {brand.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* PDF dropzone */}
      <div className="space-y-1.5">
        <label className="text-sm font-medium text-gray-700">Menu PDF</label>
        <PDFDropzone
          onFileSelect={handleFileSelect}
          disabled={parseMutation.isPending}
          selectedFile={selectedFile}
        />
      </div>

      {/* Error */}
      {errorMessage && (
        <Alert variant="destructive">
          <AlertDescription>{errorMessage}</AlertDescription>
        </Alert>
      )}

      {/* Parse button (shown when brand + file selected but no auto-trigger happened) */}
      {selectedFile && selectedBrandId && !parseMutation.isPending && (
        <Button
          variant="primary"
          fullWidth
          onClick={handleParseClick}
          loading={parseMutation.isPending}
        >
          Extract Menu Items
        </Button>
      )}

      {/* Loading state */}
      {parseMutation.isPending && (
        <div className="flex items-center justify-center gap-3 py-4 text-sm text-gray-600">
          <svg
            className="animate-spin h-5 w-5 text-primary-600"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8v8H4z"
            />
          </svg>
          Extracting menu items with Mistral OCR...
        </div>
      )}
    </div>
  );
};
