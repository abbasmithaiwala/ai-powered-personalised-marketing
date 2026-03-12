import React from 'react'

interface TopBannerProps {
  text: string
  icon?: string
}

export const TopBanner: React.FC<TopBannerProps> = ({ text, icon = "🚀" }) => {
  return (
    <div className="w-full bg-orange-900 text-white py-2.5 px-4">
      <div className="max-w-7xl mx-auto text-center">
        <p className="text-sm font-medium">
          {icon} {text}
        </p>
      </div>
    </div>
  )
}
