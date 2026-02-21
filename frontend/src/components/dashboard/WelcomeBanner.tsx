import { Link } from "react-router"
import { XMarkIcon } from "@heroicons/react/24/outline"
import { Button } from "@/components/ui/Button"
import { Card } from "@/components/ui/Card"
import { useSettingsStore } from "@/stores/settings"

export function WelcomeBanner() {
  const dismissWelcomeBanner = useSettingsStore((state) => state.dismissWelcomeBanner)

  return (
    <Card className="bg-gradient-to-r from-orange-50 to-amber-50 border-orange-200">
      <div className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Welcome to AI-Powered Marketing! 🎉
            </h3>
            <p className="text-gray-700 mb-4">
              Your account is set up and ready to go. Start by creating your first campaign
              or importing more data to unlock powerful personalized recommendations.
            </p>
            <div className="flex flex-wrap gap-3">
              <Link to="/campaigns/new">
                <Button size="sm">Create Campaign</Button>
              </Link>
              <Link to="/menu/pdf-import">
                <Button variant="ghost" size="sm">Import Menu</Button>
              </Link>
              <Link to="/import">
                <Button variant="ghost" size="sm">Import Orders</Button>
              </Link>
            </div>
          </div>
          <button
            onClick={dismissWelcomeBanner}
            className="ml-4 p-1 hover:bg-orange-100 rounded"
            aria-label="Dismiss"
          >
            <XMarkIcon className="h-5 w-5 text-gray-500" />
          </button>
        </div>
      </div>
    </Card>
  )
}
