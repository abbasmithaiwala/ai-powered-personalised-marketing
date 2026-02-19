import React, { useRef, useState, type DragEvent, type ChangeEvent } from 'react';
import { DocumentArrowUpIcon } from '@heroicons/react/24/outline';

interface PDFDropzoneProps {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
  selectedFile?: File | null;
}

export const PDFDropzone: React.FC<PDFDropzoneProps> = ({
  onFileSelect,
  disabled = false,
  selectedFile,
}) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFile = (file: File) => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      return;
    }
    onFileSelect(file);
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (!disabled) setIsDragging(true);
  };

  const handleDragLeave = () => setIsDragging(false);

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (disabled) return;
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    // Reset so same file can be re-selected
    e.target.value = '';
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => !disabled && inputRef.current?.click()}
      className={[
        'border-2 border-dashed rounded-xl p-10 flex flex-col items-center justify-center gap-3',
        'cursor-pointer transition-colors select-none',
        isDragging
          ? 'border-primary-500 bg-primary-50'
          : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50',
        disabled ? 'opacity-50 cursor-not-allowed pointer-events-none' : '',
      ]
        .filter(Boolean)
        .join(' ')}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,application/pdf"
        className="hidden"
        onChange={handleChange}
        disabled={disabled}
      />
      <DocumentArrowUpIcon className="h-10 w-10 text-gray-400" />
      {selectedFile ? (
        <div className="text-center">
          <p className="text-sm font-medium text-gray-900">{selectedFile.name}</p>
          <p className="text-xs text-gray-500 mt-0.5">
            {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB — click to change
          </p>
        </div>
      ) : (
        <div className="text-center">
          <p className="text-sm font-medium text-gray-700">
            Drop your menu PDF here, or <span className="text-primary-600">browse</span>
          </p>
          <p className="text-xs text-gray-500 mt-0.5">PDF only, max 20 MB</p>
        </div>
      )}
    </div>
  );
};
