import React, { ReactNode } from 'react'

interface FeatureCardProps {
  tag: string
  tagIcon: ReactNode
  title: string
  description: string
  imageUrl?: string
}

export const FeatureCard: React.FC<FeatureCardProps> = ({
  tag,
  tagIcon,
  title,
  description,
  imageUrl,
}) => {
  return (
    <div className="flex flex-col gap-8">
      {/* Image + Tag */}
      <div className="space-y-6">
        <div className="inline-flex items-center gap-1.5 px-2 py-1.5 bg-gray-900 rounded text-white">
          <span className="text-green-400">{tagIcon}</span>
          <span className="text-xs font-extrabold tracking-wide">{tag}</span>
        </div>

        {imageUrl ? (
          <div className="w-full h-40 rounded-lg overflow-hidden">
            <img
              src={imageUrl}
              alt={title}
              className="w-full h-full object-contain"
            />
          </div>
        ) : (
          <div className="w-full h-40 bg-gradient-to-br from-orange-100 to-amber-100 rounded-lg" />
        )}
      </div>

      {/* Content */}
      <div className="space-y-4">
        <h3 className="text-2xl font-medium text-gray-900 leading-tight tracking-tight">
          {title}
        </h3>
        <p className="text-sm text-gray-600 leading-relaxed">
          {description}
        </p>
      </div>
    </div>
  )
}
