import { Button } from "@/components/ui/Button"
import { ArrowLeftIcon, ArrowRightIcon } from "@heroicons/react/24/outline"
import { Loader2Icon } from "lucide-react"

interface StepNavigationProps {
  onBack?: () => void
  onNext?: () => void
  canGoBack?: boolean
  canGoNext?: boolean
  nextLabel?: string
  isLoading?: boolean
}

export function StepNavigation({
  onBack,
  onNext,
  canGoBack = true,
  canGoNext = true,
  nextLabel = "Continue",
  isLoading = false,
}: StepNavigationProps) {
  return (
    <div className="flex items-center justify-between pt-6 border-t">
      {onBack && canGoBack ? (
        <Button
          type="button"
          variant="ghost"
          onClick={onBack}
          disabled={isLoading}
        >
          <ArrowLeftIcon className="h-4 w-4 mr-2" />
          Back
        </Button>
      ) : (
        <div />
      )}

      {onNext && canGoNext && (
        <Button
          type="button"
          onClick={onNext}
          disabled={isLoading}
        >
          {isLoading && <Loader2Icon className="h-4 w-4 mr-2 animate-spin" />}
          {nextLabel}
          {!isLoading && <ArrowRightIcon className="h-4 w-4 ml-2" />}
        </Button>
      )}
    </div>
  )
}
