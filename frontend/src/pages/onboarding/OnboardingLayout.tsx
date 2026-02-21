import { Outlet, useLocation, Navigate } from "react-router"
import { OnboardingProvider } from "./OnboardingContext"
import { ImagePanel } from "@/components/onboarding/ImagePanel"
import { Progress } from "@/components/ui/progress"

const stepImages: Record<string, { url: string; alt: string }> = {
  brand: {
    url: "https://images.unsplash.com/photo-1634489236139-dd3eb0e217f2?q=80&w=987&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    // url: "https://images.unsplash.com/photo-1766622308785-53c25e0653cb?q=80&w=987&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    alt: "Chef in restaurant kitchen",
  },
  menu: {
    url: "https://images.unsplash.com/photo-1582557678431-d3b30ea0be05?q=80&w=927&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    alt: "Delicious food dishes",
  },
  orders: {
    url: "https://images.unsplash.com/photo-1769766319375-1c384e4355d6?q=80&w=1018&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    alt: "Happy restaurant customers",
  },
  confirm: {
    url: "https://images.unsplash.com/photo-1508424757105-b6d5ad9329d0?q=80&w=1035&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    alt: "Analytics dashboard",
  },
}

const steps = ["brand", "menu", "orders", "confirm"]

export default function OnboardingLayout() {
  const location = useLocation()
  const currentPath = location.pathname.split("/").pop() || "brand"

  // If at /onboarding root, redirect to first step
  if (location.pathname === "/onboarding") {
    return <Navigate to="/onboarding/brand" replace />
  }

  const currentStepIndex = steps.indexOf(currentPath)
  const progressValue = ((currentStepIndex + 1) / steps.length) * 100

  const currentImage = stepImages[currentPath] || stepImages.brand

  return (
    <OnboardingProvider>
      <div className="flex flex-col lg:flex-row min-h-screen">
        {/* Left Column: Form */}
        <div className="w-full lg:w-3/5 bg-white">
          <div className="p-6 lg:p-12 max-w-xl mx-auto">
            {/* Progress Indicator */}
            <div className="mb-8">
              <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
                <span>Step {currentStepIndex + 1} of {steps.length}</span>
                <span>{Math.round(progressValue)}%</span>
              </div>
              <Progress value={progressValue} className="h-2" />
            </div>

            {/* Form Content */}
            <Outlet />
          </div>
        </div>

        {/* Right Column: Image (hidden on mobile) */}
        <div className="hidden lg:block lg:w-3/5 bg-gray-100">
          <ImagePanel imageUrl={currentImage.url} alt={currentImage.alt} />
        </div>
      </div>
    </OnboardingProvider>
  )
}
