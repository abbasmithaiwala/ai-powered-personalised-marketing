import React from 'react'
import { Link } from 'react-router'

export const Header: React.FC = () => {
  return (
    <header className="px-8 py-6 rounded-lg w-full top-0 z-50">
      <div className="max-w-6xl mx-auto flex items-center justify-between rounded-full bg-white p-4">
        {/* Logo */}
        <Link to="/" className="text-2xl font-bold text-gray-900 tracking-tight">
          FlavorFlow
        </Link>

        {/* Navigation */}
        <nav className="hidden md:flex items-center gap-8">
          <a href="#features" className="text-sm font-medium text-gray-900 hover:text-orange-600 transition-colors">
            Features
          </a>
          <a href="#impact" className="text-sm font-medium text-gray-900 hover:text-orange-600 transition-colors">
            Impact
          </a>
          <a href="#how-it-works" className="text-sm font-medium text-gray-900 hover:text-orange-600 transition-colors">
            How It Works
          </a>
        </nav>

        {/* CTA */}
        <div className="flex items-center gap-6">
          <Link to="/onboarding" className="hidden md:block text-sm font-medium text-gray-900 hover:text-orange-600 transition-colors">
            Login
          </Link>
          <Link to="/onboarding">
            <button className="shadow-sm rounded-full bg-orange-500 hover:bg-orange-600/90 text-white font-medium px-6 py-2">
              Get Started Free
            </button>
          </Link>
        </div>
      </div>
    </header>
  )
}
