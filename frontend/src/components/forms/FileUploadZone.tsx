import { useCallback } from "react"
import { useDropzone } from "react-dropzone"
import { DocumentIcon, XMarkIcon } from "@heroicons/react/24/outline"
import { cn } from "@/lib/utils"

interface FileUploadZoneProps {
  onDrop: (file: File) => void
  accept?: Record<string, string[]>
  maxSize?: number
  label: string
  description?: string
  selectedFile?: File | null
  onRemove?: () => void
  disabled?: boolean
}

export function FileUploadZone({
  onDrop,
  accept,
  maxSize = 10 * 1024 * 1024, // 10MB default
  label,
  description,
  selectedFile,
  onRemove,
  disabled = false,
}: FileUploadZoneProps) {
  const handleDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        onDrop(acceptedFiles[0])
      }
    },
    [onDrop]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: handleDrop,
    accept,
    maxSize,
    multiple: false,
    disabled,
  })

  if (selectedFile) {
    return (
      <div className="space-y-2">
        <label className="text-sm font-medium">{label}</label>
        <div className="flex items-center justify-between p-4 border rounded-lg bg-gray-50">
          <div className="flex items-center space-x-3">
            <DocumentIcon className="h-8 w-8 text-gray-400" />
            <div>
              <p className="text-sm font-medium">{selectedFile.name}</p>
              <p className="text-xs text-gray-500">
                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
          </div>
          {onRemove && !disabled && (
            <button
              type="button"
              onClick={onRemove}
              className="p-1 hover:bg-gray-200 rounded"
            >
              <XMarkIcon className="h-5 w-5 text-gray-500" />
            </button>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">{label}</label>
      <div
        {...getRootProps()}
        className={cn(
          "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
          isDragActive && "border-blue-500 bg-blue-50",
          !isDragActive && "border-gray-300 hover:border-gray-400",
          disabled && "opacity-50 cursor-not-allowed"
        )}
      >
        <input {...getInputProps()} />
        <DocumentIcon className="h-12 w-12 mx-auto text-gray-400 mb-4" />
        <p className="text-sm font-medium text-gray-700 mb-1">
          {isDragActive ? "Drop file here" : "Click to upload or drag and drop"}
        </p>
        {description && (
          <p className="text-xs text-gray-500">{description}</p>
        )}
      </div>
    </div>
  )
}
