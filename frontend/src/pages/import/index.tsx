import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardHeader, CardTitle, Badge } from '@/components/ui';
import { CSVDropzone } from './components/CSVDropzone';
import { ValidationResult } from './components/ValidationResult';
import { ImportHistory } from './components/ImportHistory';
import { ingestionApi } from '@/api/ingestion';
import type { IngestionUploadResponse, IngestionJob } from '@/types/api';

type UploadStage = 'select' | 'validate' | 'import' | 'complete';

export const Import: React.FC = () => {
  const queryClient = useQueryClient();
  const [stage, setStage] = useState<UploadStage>('select');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [csvType, setCsvType] = useState('orders');
  const [uploadResponse, setUploadResponse] = useState<IngestionUploadResponse | null>(null);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [pollingInterval, setPollingInterval] = useState<number | null>(null);

  // Fetch import history
  const { data: historyData, isLoading: historyLoading } = useQuery({
    queryKey: ['ingestion-jobs'],
    queryFn: () => ingestionApi.listJobs(1, 10),
  });

  // Poll current job status
  const { data: currentJob } = useQuery({
    queryKey: ['ingestion-job', currentJobId],
    queryFn: () => ingestionApi.getJob(currentJobId!),
    enabled: !!currentJobId && stage === 'import',
    refetchInterval: pollingInterval || false,
  });

  // Upload mutation (for validation)
  const uploadMutation = useMutation({
    mutationFn: (file: File) => ingestionApi.upload(file, csvType),
    onSuccess: (data) => {
      setUploadResponse(data);
      setStage('validate');
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || 'Upload failed. Please try again.');
      setStage('select');
    },
  });

  // Start import (using the same upload response job_id)
  const startImport = () => {
    if (uploadResponse) {
      setCurrentJobId(uploadResponse.job_id);
      setStage('import');
      setPollingInterval(2000); // Poll every 2 seconds
    }
  };

  // Handle file selection
  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    uploadMutation.mutate(file);
  };

  // Cancel and reset
  const handleCancel = () => {
    setStage('select');
    setSelectedFile(null);
    setUploadResponse(null);
    setCurrentJobId(null);
    setPollingInterval(null);
  };

  // Monitor job completion
  useEffect(() => {
    if (currentJob && (currentJob.status === 'completed' || currentJob.status === 'failed')) {
      setPollingInterval(null);
      setStage('complete');
      // Refresh history
      queryClient.invalidateQueries({ queryKey: ['ingestion-jobs'] });
    }
  }, [currentJob, queryClient]);

  const renderStage = () => {
    switch (stage) {
      case 'select':
        return (
          <Card>
            <CardHeader>
              <CardTitle>Upload CSV File</CardTitle>
            </CardHeader>
            <div className="p-6 space-y-4">
              {/* CSV Type Selector */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  CSV Type
                </label>
                <select
                  value={csvType}
                  onChange={(e) => setCsvType(e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                  disabled={uploadMutation.isPending}
                >
                  <option value="orders">Orders</option>
                </select>
                <p className="mt-1 text-xs text-gray-500">
                  Select the type of CSV file you're uploading
                </p>
              </div>

              {/* Dropzone */}
              <CSVDropzone
                onFileSelect={handleFileSelect}
                disabled={uploadMutation.isPending}
              />

              {uploadMutation.isPending && (
                <div className="flex items-center justify-center space-x-2 text-primary-600">
                  <svg
                    className="animate-spin h-5 w-5"
                    xmlns="http://www.w3.org/2000/svg"
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
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  <span>Validating file...</span>
                </div>
              )}
            </div>
          </Card>
        );

      case 'validate':
        return uploadResponse ? (
          <ValidationResult
            filename={selectedFile?.name || 'Unknown'}
            totalRows={uploadResponse.total_rows}
            validationSummary={uploadResponse.validation_summary}
            onStartImport={startImport}
            onCancel={handleCancel}
          />
        ) : null;

      case 'import':
        return (
          <Card>
            <CardHeader>
              <CardTitle>Import in Progress</CardTitle>
            </CardHeader>
            <div className="p-6 space-y-4">
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
                  <svg
                    className="animate-spin h-8 w-8 text-blue-600"
                    xmlns="http://www.w3.org/2000/svg"
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
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Processing your import</h3>
                <p className="text-sm text-gray-500 mb-6">
                  This may take a few moments. Please don't close this page.
                </p>
              </div>

              {currentJob && (
                <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-700">Status:</span>
                    <Badge variant="blue">{currentJob.status.toUpperCase()}</Badge>
                  </div>
                  {currentJob.total_rows && (
                    <>
                      <div className="flex justify-between">
                        <span className="text-sm font-medium text-gray-700">Progress:</span>
                        <span className="text-sm text-gray-900">
                          {currentJob.processed_rows || 0} / {currentJob.total_rows}
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                          style={{
                            width: `${
                              currentJob.total_rows > 0
                                ? ((currentJob.processed_rows || 0) / currentJob.total_rows) * 100
                                : 0
                            }%`,
                          }}
                        ></div>
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>
          </Card>
        );

      case 'complete':
        return (
          <Card>
            <CardHeader>
              <CardTitle>Import Complete</CardTitle>
            </CardHeader>
            <div className="p-6 space-y-4">
              {currentJob && (
                <>
                  {currentJob.status === 'completed' ? (
                    <div className="text-center">
                      <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
                        <svg
                          className="w-8 h-8 text-green-600"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M5 13l4 4L19 7"
                          />
                        </svg>
                      </div>
                      <h3 className="text-lg font-medium text-gray-900 mb-2">
                        Import successful!
                      </h3>
                      <p className="text-sm text-gray-500 mb-6">
                        Your data has been imported successfully.
                      </p>
                    </div>
                  ) : (
                    <div className="text-center">
                      <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mb-4">
                        <svg
                          className="w-8 h-8 text-red-600"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M6 18L18 6M6 6l12 12"
                          />
                        </svg>
                      </div>
                      <h3 className="text-lg font-medium text-gray-900 mb-2">Import failed</h3>
                      <p className="text-sm text-gray-500 mb-6">
                        There was an error processing your import.
                      </p>
                    </div>
                  )}

                  {/* Summary */}
                  <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm font-medium text-gray-700">Total Rows:</span>
                      <span className="text-sm text-gray-900">
                        {currentJob.total_rows?.toLocaleString() || 0}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm font-medium text-gray-700">Processed:</span>
                      <span className="text-sm text-gray-900">
                        {currentJob.processed_rows?.toLocaleString() || 0}
                      </span>
                    </div>
                    {currentJob.failed_rows && currentJob.failed_rows > 0 && (
                      <div className="flex justify-between">
                        <span className="text-sm font-medium text-gray-700">Failed:</span>
                        <span className="text-sm text-red-600">
                          {currentJob.failed_rows.toLocaleString()}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Result Summary */}
                  {currentJob.result_summary && (
                    <div className="bg-blue-50 rounded-lg p-4">
                      <h4 className="text-sm font-medium text-blue-900 mb-2">Summary:</h4>
                      <pre className="text-xs text-blue-800 whitespace-pre-wrap">
                        {JSON.stringify(currentJob.result_summary, null, 2)}
                      </pre>
                    </div>
                  )}

                  <div className="flex justify-center pt-4">
                    <button
                      onClick={handleCancel}
                      className="px-6 py-2 text-sm font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                    >
                      Upload Another File
                    </button>
                  </div>
                </>
              )}
            </div>
          </Card>
        );
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Data Import</h1>
        <p className="mt-2 text-sm text-gray-600">
          Upload CSV files to import customer orders and menu items
        </p>
      </div>

      {renderStage()}

      {/* Import History */}
      {stage === 'select' && (
        <ImportHistory jobs={historyData?.items || []} loading={historyLoading} />
      )}
    </div>
  );
};
