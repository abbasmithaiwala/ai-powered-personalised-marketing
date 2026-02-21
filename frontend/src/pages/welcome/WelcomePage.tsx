import { Link } from "react-router"
import { Button } from "@/components/ui/Button"
import { SparklesIcon } from "@heroicons/react/24/outline"

export default function WelcomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-amber-50 flex items-center justify-center p-4">
      <div className="max-w-2xl mx-auto text-center space-y-8">
        {/* Logo/Icon */}
        <div className="flex justify-center">
          <div className="p-4 bg-orange-500 rounded-2xl">
            <SparklesIcon className="h-16 w-16 text-white" />
          </div>
        </div>

        {/* Heading */}
        <div className="space-y-4">
          <h1 className="text-5xl font-bold text-gray-900">
            AI-Powered Marketing
          </h1>
          <p className="text-xl text-gray-600 max-w-lg mx-auto">
            Create personalized campaigns that delight your customers with intelligent
            recommendations and targeted messaging.
          </p>
        </div>

        {/* CTA */}
        <div className="pt-4">
          <Link to="/onboarding">
            <Button size="lg" className="text-lg px-8">
              Get Started
            </Button>
          </Link>
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 pt-8 text-left">
          <div className="p-4">
            <div className="text-orange-600 font-semibold mb-2">Smart Recommendations</div>
            <p className="text-sm text-gray-600">
              AI analyzes customer preferences to suggest perfect menu items
            </p>
          </div>
          <div className="p-4">
            <div className="text-orange-600 font-semibold mb-2">Personalized Messages</div>
            <p className="text-sm text-gray-600">
              Generate custom marketing copy for each customer segment
            </p>
          </div>
          <div className="p-4">
            <div className="text-orange-600 font-semibold mb-2">Easy Setup</div>
            <p className="text-sm text-gray-600">
              Import your menu and customer data in minutes
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
