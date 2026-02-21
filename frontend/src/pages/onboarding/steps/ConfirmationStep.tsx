import { useNavigate } from "react-router"
import { Button } from "@/components/ui/Button"
import { FormStep } from "@/components/onboarding/FormStep"
import { useOnboarding } from "../OnboardingContext"
import {
  CheckCircleIcon,
  DocumentIcon,
  ShoppingCartIcon,
} from "@heroicons/react/24/outline"

export default function ConfirmationStep() {
  const navigate = useNavigate()
  const { data, submitOnboarding, isSubmitting } = useOnboarding()

  const handleComplete = async () => {
    try {
      await submitOnboarding()
    } catch (error) {
      // Error is already handled in OnboardingContext with toast
      // Just prevent the uncaught promise error
    }
  }

  return (
    <FormStep
      title="You're all set!"
      description="Here's what we've configured for your account"
    >
      <div className="space-y-6">
        {/* Summary Cards */}
        <div className="space-y-4">
          {/* Brand */}
          <div className="flex items-start space-x-4 p-4 bg-green-50 border border-green-200 rounded-lg">
            <CheckCircleIcon className="h-6 w-6 text-green-600 flex-shrink-0 mt-0.5" />
            <div>
              <div className="font-medium text-gray-900">Brand Created</div>
              <div className="text-sm text-gray-600 mt-1">
                {data.brand?.name}
              </div>
              {data.brand?.description && (
                <div className="text-sm text-gray-500 mt-1">
                  {data.brand.description}
                </div>
              )}
            </div>
          </div>

          {/* Menu */}
          <div
            className={`flex items-start space-x-4 p-4 rounded-lg ${
              data.parsedMenuItems && data.parsedMenuItems.length > 0
                ? "bg-green-50 border border-green-200"
                : "bg-gray-50 border border-gray-200"
            }`}
          >
            <DocumentIcon
              className={`h-6 w-6 flex-shrink-0 mt-0.5 ${
                data.parsedMenuItems && data.parsedMenuItems.length > 0
                  ? "text-green-600"
                  : "text-gray-400"
              }`}
            />
            <div>
              <div className="font-medium text-gray-900">Menu Items</div>
              <div className="text-sm text-gray-600 mt-1">
                {data.parsedMenuItems && data.parsedMenuItems.length > 0
                  ? `${data.parsedMenuItems.length} items ready to import`
                  : "No menu items added - you can add them later"}
              </div>
            </div>
          </div>

          {/* Orders */}
          <div
            className={`flex items-start space-x-4 p-4 rounded-lg ${
              data.orderUpload?.uploadMethod === "csv"
                ? "bg-green-50 border border-green-200"
                : "bg-gray-50 border border-gray-200"
            }`}
          >
            <ShoppingCartIcon
              className={`h-6 w-6 flex-shrink-0 mt-0.5 ${
                data.orderUpload?.uploadMethod === "csv"
                  ? "text-green-600"
                  : "text-gray-400"
              }`}
            />
            <div>
              <div className="font-medium text-gray-900">Customer Orders</div>
              <div className="text-sm text-gray-600 mt-1">
                {data.orderUpload?.uploadMethod === "csv"
                  ? `CSV file ready to import (${data.orderUpload.csvFile?.name})`
                  : "No orders added - you can import them later"}
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between pt-6 border-t">
          <Button
            type="button"
            variant="ghost"
            onClick={() => navigate("/onboarding/orders")}
            disabled={isSubmitting}
          >
            Back
          </Button>

          <Button
            onClick={handleComplete}
            disabled={isSubmitting}
            size="lg"
          >
            {isSubmitting ? "Setting up..." : "Go to Dashboard"}
          </Button>
        </div>
      </div>
    </FormStep>
  )
}
