import React from 'react'
import { Link } from 'react-router'
import { Header } from '@/components/landing/Header'

export const Hero: React.FC = () => {
  return (
    <div className="w-full">

      <section
        className="w-full relative px-4 pb-20 md:pb-32 overflow-hidden"
        style={{
          background: `
          url('/hero_bg.webp')
        `,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        }}
      >
        <Header />
        <div className="max-w-4xl pt-32 mx-auto text-center space-y-8 relative z-10">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-white border border-gray-200 rounded-full text-sm font-medium text-gray-700 shadow-sm">
            ✨ Built to handle millions of customer campaigns
          </div>

          {/* Headline */}
          <h1 className="text-5xl md:text-7xl font-bold text-gray-900 leading-tight tracking-tight">
            AI-Powered Marketing
            <br />
            for Food Brands
          </h1>

          {/* Subheadline */}
          <p className="text-lg md:text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
            Automate personalized campaigns that delight your customers with intelligent
            recommendations and AI-generated messaging tailored to their tastes.
          </p>

          {/* CTA */}
          <div className="pt-4">
            <Link to="/onboarding">
              <button className="text-base flex rounded-full mx-auto font-medium bg-orange-500 hover:bg-orange-600/90 text-white px-8 py-4 shadow-lg hover:shadow-xl transition-shadow">
                Start with Free Trial
              </button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}
