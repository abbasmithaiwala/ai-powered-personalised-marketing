import React from 'react'
import { FeatureCard } from './FeatureCard'
import {
  BoltIcon,
  ArrowPathIcon,
  GlobeAltIcon,
  CubeIcon,
} from '@heroicons/react/24/outline'

export const FeaturesGrid: React.FC = () => {
  const features = [
    {
      tag: "AI-POWERED",
      tagIcon: <BoltIcon className="h-3 w-3" />,
      title: "Intelligent Recommendations",
      description: "AI analyzes customer order history and preferences to suggest perfect menu items, creating personalized experiences that drive engagement.",
      imageUrl: "/feat1.png",
    },
    {
      tag: "AUTO-SCALING",
      tagIcon: <ArrowPathIcon className="h-3 w-3" />,
      title: "Automated Campaigns",
      description: "Deploy high-volume personalized campaigns instantly. Our system scales to thousands of customers with zero manual effort or configuration.",
      imageUrl: "/feat2.png",
    },
    {
      tag: "MULTI-CHANNEL",
      tagIcon: <GlobeAltIcon className="h-3 w-3" />,
      title: "Reach Every Customer",
      description: "Send targeted messages across email, SMS, and push notifications. Connect with customers on their preferred channels at the perfect time.",
      imageUrl: "/feat3.png",
    },
    {
      tag: "SEAMLESS",
      tagIcon: <CubeIcon className="h-3 w-3" />,
      title: "Easy Integration",
      description: "Import your menu and customer data in minutes. Integrate with your existing tools via powerful APIs and webhooks for custom workflows.",
      imageUrl: "/feat4.png",
    },
  ]

  return (
    <section id="features" className="w-full bg-white py-24 px-4">
      <div className="max-w-6xl mx-auto space-y-16">
        {/* Header */}
        <div className="text-center space-y-4 max-w-2xl mx-auto">
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900">
            Next-Generation Marketing
          </h2>
          <p className="text-lg text-gray-900 font-medium">
            No manual work, customer limits, or technical complexity.
          </p>
        </div>

        {/* Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, idx) => (
            <FeatureCard key={idx} {...feature} />
          ))}
        </div>
      </div>
    </section>
  )
}
