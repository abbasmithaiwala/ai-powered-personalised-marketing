import React from 'react'

interface ArticleCardProps {
  title: string
  description: string
  gradient: string
}

export const ArticleCard: React.FC<ArticleCardProps> = ({ title, description, gradient }) => {
  return (
    <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden hover:shadow-lg transition-shadow">
      <div className={`w-full h-52 ${gradient}`} />
      <div className="p-6 space-y-4">
        <h3 className="text-lg font-bold text-gray-900 leading-snug">
          {title}
        </h3>
        <p className="text-sm text-gray-600 leading-relaxed">
          {description}
        </p>
        <a href="#" className="inline-block text-sm font-semibold text-blue-600 hover:text-blue-700">
          Read More →
        </a>
      </div>
    </div>
  )
}
