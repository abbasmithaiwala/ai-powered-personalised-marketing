import React from 'react'
import { Link } from 'react-router'

export const CTASection: React.FC = () => {
  return (
    <section className="w-full bg-gradient-to-br from-orange-500 via-orange-600 to-amber-600 py-24 px-4">
      <div className="max-w-4xl mx-auto text-center space-y-8">
        <h2 className="text-4xl md:text-5xl font-bold text-white leading-tight">
          Ready to Transform Your
          <br />
          Customer Engagement?
        </h2>
        <p className="text-xl text-white/90 max-w-2xl mx-auto">
          Join food brands already using AI to create personalized campaigns
          that delight customers and drive revenue.
        </p>
        <div className="pt-4">
          <Link to="/onboarding">
            <button
              className="bg-white flex rounded-full font-medium mx-auto text-orange-600 hover:bg-gray-50 shadow-xl text-base px-8 py-4"
            >
              Start Free Trial Today
            </button>
          </Link>
        </div>
      </div>
    </section>
  )
}
