import React from 'react'
import { XMarkIcon, CheckIcon } from '@heroicons/react/24/outline'

export const ComparisonSection: React.FC = () => {
  const beforePoints = [
    "Manual campaign creation taking hours per customer segment",
    "Generic messages resulting in low engagement rates",
    "Overwhelmed team managing spreadsheets and email lists",
  ]

  const afterPoints = [
    "AI-generated campaigns launched in seconds with personalized content",
    "3x higher engagement through intelligent recommendations",
    "Team freed up to focus on strategy and customer relationships",
  ]

  return (
    <section className="w-full bg-white py-24 px-4">
      <div className="max-w-6xl mx-auto space-y-16">
        <div className="text-center">
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900">
            Experience the Difference
          </h2>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Before Card */}
          <div className="bg-gray-50 border border-gray-200 rounded-3xl p-12 space-y-10">
            <div className="space-y-3">
              <h3 className="text-3xl font-bold text-gray-900">Before FlavorFlow</h3>
              <p className="text-base text-gray-600 font-medium">
                Manual operations holding you back
              </p>
            </div>
            <div className="space-y-6">
              {beforePoints.map((point, idx) => (
                <div key={idx} className="flex items-start gap-4">
                  <XMarkIcon className="h-6 w-6 text-red-500 flex-shrink-0 mt-0.5" />
                  <p className="text-lg text-gray-700 leading-relaxed">{point}</p>
                </div>
              ))}
            </div>
          </div>

          {/* After Card */}
          <div className="bg-gradient-to-br from-blue-400 via-blue-500 to-blue-300 rounded-3xl p-12 space-y-10">
            <div className="space-y-3">
              <h3 className="text-3xl font-bold text-white">After FlavorFlow</h3>
              <p className="text-base text-white/80 font-medium">
                Automated, scalable, and intelligent
              </p>
            </div>
            <div className="space-y-6">
              {afterPoints.map((point, idx) => (
                <div key={idx} className="flex items-start gap-4">
                  <CheckIcon className="h-6 w-6 text-white flex-shrink-0 mt-0.5" />
                  <p className="text-lg text-white leading-relaxed">{point}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
