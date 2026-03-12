import React from 'react'

export const HowItWorksSection: React.FC = () => {
  return (
    <section id="how-it-works" className="w-full bg-white py-24 px-4">
      <div className="max-w-6xl mx-auto space-y-16">
        {/* Header */}
        <div className="text-center space-y-8">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-white border border-gray-200 rounded-full text-sm font-medium text-gray-700 shadow-sm">
            ✨ How It Works
          </div>

          <div className="max-w-3xl mx-auto space-y-6">
            <h2 className="text-4xl md:text-6xl font-bold text-gray-900 leading-tight">
              From setup to scale:
              <br />
              How AI campaigns work
            </h2>
            <p className="text-lg text-gray-600 leading-relaxed">
              This is how modern food brands launch, track, and scale AI-powered campaigns
              with unlimited customer reach and post-campaign analytics to refine engagement
              to perfection.
            </p>
          </div>
        </div>

        {/* Placeholder for workflow diagram/illustration */}
        <div className="w-full max-w-5xl mx-auto">
          <div className="aspect-video bg-gradient-to-br from-orange-50 to-amber-50 rounded-3xl border border-gray-200 flex items-center justify-center">
            <p className="text-gray-400 text-sm">Campaign Workflow Visualization</p>
          </div>
        </div>
      </div>
    </section>
  )
}
