import React from 'react'
import { ArticleCard } from './ArticleCard'

export const ResourcesSection: React.FC = () => {
  const articles = [
    {
      title: "How real-time analytics can revolutionize your food marketing strategy",
      description: "In today's fast-paced food industry, manual marketing processes slow you down. Learn how AI-powered campaigns drive customer engagement.",
      gradient: "bg-gradient-to-br from-blue-500 to-blue-800",
    },
    {
      title: "Simplify and empower your customer engagement with AI",
      description: "Managing growing customer bases can be overwhelming. Read this guide to ensure personalized experiences at scale.",
      gradient: "bg-gradient-to-br from-sky-200 to-blue-500",
    },
    {
      title: "The importance of personalized recommendations for food brands",
      description: "Discover how food brands improve conversion rates by using AI-powered menu recommendations and reducing customer churn.",
      gradient: "bg-gradient-to-r from-blue-300 to-sky-200",
    },
  ]

  return (
    <section className="w-full bg-gray-50 py-24 px-4">
      <div className="max-w-6xl mx-auto space-y-16">
        <div className="text-center">
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900">
            Articles for You
          </h2>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {articles.map((article, idx) => (
            <ArticleCard key={idx} {...article} />
          ))}
        </div>
      </div>
    </section>
  )
}
