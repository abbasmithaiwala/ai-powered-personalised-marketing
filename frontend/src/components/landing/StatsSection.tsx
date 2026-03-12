import React from 'react'
import { CodeBracketIcon, ArrowTrendingUpIcon, PhoneXMarkIcon, CalendarIcon } from '@heroicons/react/24/outline'

interface StatCardProps {
  company: string
  value: string
  icon: React.ReactNode
  description: string
}

const StatCard: React.FC<StatCardProps> = ({ company, value, icon, description }) => {
  return (
    <div className="flex flex-col gap-3">
      <p className="text-sm font-semibold text-gray-500 tracking-wide">{company}</p>
      <p className="text-5xl md:text-6xl font-medium text-gray-900 tracking-tight">{value}</p>
      <div className="flex items-start gap-2">
        <span className="text-gray-500 mt-0.5">{icon}</span>
        <p className="text-sm text-gray-600 leading-snug">{description}</p>
      </div>
    </div>
  )
}

export const StatsSection: React.FC = () => {
  const stats = [
    {
      company: "FRESH BITES",
      value: "94.2%",
      icon: <CodeBracketIcon className="h-4 w-4" />,
      description: "Message open rate with personalized content",
    },
    {
      company: "TASTY TREATS",
      value: "23%",
      icon: <ArrowTrendingUpIcon className="h-4 w-4" />,
      description: "Increase in repeat orders",
    },
    {
      company: "GOURMET CO",
      value: "87%",
      icon: <PhoneXMarkIcon className="h-4 w-4" />,
      description: "Customer engagement improvement",
    },
    {
      company: "ARTISAN EATS",
      value: "£45k",
      icon: <CalendarIcon className="h-4 w-4" />,
      description: "Additional monthly revenue",
    },
  ]

  return (
    <section id="impact" className="w-full bg-gray-100 py-24 px-4">
      <div className="max-w-6xl mx-auto flex flex-col min-h-[600px]">
        <h2 className="text-5xl md:text-6xl font-bold text-gray-900 leading-tight tracking-tight mb-16">
          Real Impact on
          <br />
          Food Brands
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-12 lg:gap-8 mb-auto">
          {stats.map((stat, idx) => (
            <StatCard key={idx} {...stat} />
          ))}
        </div>

        {/* Mini chart visualization */}
        <div className="flex items-end gap-4 h-48 justify-end mt-16">
          {[60, 100, 150, 190, 240].map((height, idx) => (
            <div
              key={idx}
              className="w-1 bg-gray-900"
              style={{ height: `${height}px`, opacity: 0.3 + idx * 0.15 }}
            />
          ))}
        </div>
      </div>
    </section>
  )
}
