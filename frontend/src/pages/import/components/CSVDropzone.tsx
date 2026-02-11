import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { CloudArrowUpIcon } from '@/components/icons';

interface CSVDropzoneProps {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
  onError?: (title: string, message: string) => void;
}

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

export const CSVDropzone: React.FC<CSVDropzoneProps> = ({ onFileSelect, disabled = false, onError }) => {
  const onDrop = useCallback(
    (acceptedFiles: File[], rejectedFiles: any[]) => {
      if (rejectedFiles.length > 0) {
        const rejection = rejectedFiles[0];
        if (rejection.errors.some((e: any) => e.code === 'file-too-large')) {
          if (onError) {
            onError('File Too Large', 'File is too large. Maximum size is 50MB.');
          } else {
            alert('File is too large. Maximum size is 50MB.');
          }
        } else if (rejection.errors.some((e: any) => e.code === 'file-invalid-type')) {
          if (onError) {
            onError('Invalid File Type', 'Invalid file type. Please upload a CSV file.');
          } else {
            alert('Invalid file type. Please upload a CSV file.');
          }
        }
        return;
      }

      if (acceptedFiles.length > 0) {
        onFileSelect(acceptedFiles[0]);
      }
    },
    [onFileSelect, onError]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
    },
    maxSize: MAX_FILE_SIZE,
    multiple: false,
    disabled,
  });

  return (
    <div
      {...getRootProps()}
      className={`
        border-2 border-dashed rounded-lg p-12 text-center cursor-pointer
        transition-colors duration-200
        ${isDragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-primary-400'}
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
      `}
    >
      <input {...getInputProps()} />
      <div className="flex flex-col items-center space-y-4">
        <CloudArrowUpIcon
          className={`w-16 h-16 ${isDragActive ? 'text-primary-500' : 'text-gray-400'}`}
        />
        {isDragActive ? (
          <p className="text-lg font-medium text-primary-600">Drop the CSV file here...</p>
        ) : (
          <>
            <p className="text-lg font-medium text-gray-700">
              Drag and drop a CSV file here, or click to browse
            </p>
            <p className="text-sm text-gray-500">Maximum file size: 50MB</p>
          </>
        )}
      </div>
    </div>
  );
};
