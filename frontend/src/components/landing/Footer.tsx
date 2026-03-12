import React from 'react'
import { Link } from 'react-router'

export const Footer: React.FC = () => {
  return (
    <footer className="w-full bg-gray-900 text-white py-16 px-4">
      <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-12">
        {/* Brand */}
        <div className="space-y-4">
          <h3 className="text-2xl font-bold tracking-tight">FlavorFlow</h3>
          <p className="text-sm text-gray-400 leading-relaxed">
            AI-powered personalized marketing for modern food brands.
          </p>
        </div>

        {/* Product */}
        <div className="space-y-4">
          <h4 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">Product</h4>
          <ul className="space-y-3">
            <li><a href="#features" className="text-sm text-gray-400 hover:text-white transition-colors">Features</a></li>
            <li><a href="#" className="text-sm text-gray-400 hover:text-white transition-colors">Pricing</a></li>
            <li><a href="#" className="text-sm text-gray-400 hover:text-white transition-colors">API</a></li>
          </ul>
        </div>

        {/* Company */}
        <div className="space-y-4">
          <h4 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">Company</h4>
          <ul className="space-y-3">
            <li><a href="#" className="text-sm text-gray-400 hover:text-white transition-colors">About</a></li>
            <li><a href="#" className="text-sm text-gray-400 hover:text-white transition-colors">Blog</a></li>
            <li><a href="#" className="text-sm text-gray-400 hover:text-white transition-colors">Careers</a></li>
          </ul>
        </div>

        {/* Legal */}
        <div className="space-y-4">
          <h4 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">Legal</h4>
          <ul className="space-y-3">
            <li><a href="#" className="text-sm text-gray-400 hover:text-white transition-colors">Privacy</a></li>
            <li><a href="#" className="text-sm text-gray-400 hover:text-white transition-colors">Terms</a></li>
            <li><a href="#" className="text-sm text-gray-400 hover:text-white transition-colors">Contact</a></li>
          </ul>
        </div>
      </div>

      <div className="max-w-6xl mx-auto mt-12 pt-8 border-t border-gray-800 text-center">
        <p className="text-sm text-gray-500">
          © {new Date().getFullYear()} FlavorFlow. All rights reserved.
        </p>
      </div>
    </footer>
  )
}
