import { createContext, useContext, useState, type ReactNode } from "react"
import { useNavigate } from "react-router"
import { brandsApi } from "@/api/brands"
import { menuApi } from "@/api/menu"
import { ingestionApi } from "@/api/ingestion"
import { useSettingsStore } from "@/stores/settings"
import { toast } from "sonner"
import { getErrorMessage } from "@/api/client"
import type { BrandFormData } from "@/lib/schemas/brandSchema"
import type { MenuUploadFormData } from "@/lib/schemas/menuUploadSchema"
import type { OrderUploadFormData } from "@/lib/schemas/orderUploadSchema"

interface OnboardingData {
  brand: BrandFormData | null
  menuUpload: MenuUploadFormData | null
  orderUpload: OrderUploadFormData | null
  parsedMenuItems?: any[]
}

interface OnboardingContextType {
  data: OnboardingData
  updateBrandData: (brand: BrandFormData) => void
  updateMenuUpload: (menuUpload: MenuUploadFormData) => void
  updateOrderUpload: (orderUpload: OrderUploadFormData) => void
  setParsedMenuItems: (items: any[]) => void
  submitOnboarding: () => Promise<void>
  isSubmitting: boolean
}

const OnboardingContext = createContext<OnboardingContextType | null>(null)

export function OnboardingProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate()
  const completeOnboarding = useSettingsStore((state) => state.completeOnboarding)

  const [data, setData] = useState<OnboardingData>({
    brand: null,
    menuUpload: null,
    orderUpload: null,
    parsedMenuItems: undefined,
  })

  const [isSubmitting, setIsSubmitting] = useState(false)

  const updateBrandData = (brand: BrandFormData) => {
    setData((prev) => ({ ...prev, brand }))
  }

  const updateMenuUpload = (menuUpload: MenuUploadFormData) => {
    setData((prev) => ({ ...prev, menuUpload }))
  }

  const updateOrderUpload = (orderUpload: OrderUploadFormData) => {
    setData((prev) => ({ ...prev, orderUpload }))
  }

  const setParsedMenuItems = (items: any[]) => {
    setData((prev) => ({ ...prev, parsedMenuItems: items }))
  }

  const submitOnboarding = async () => {
    setIsSubmitting(true)
    try {
      // Step 1: Create brand
      if (!data.brand) {
        throw new Error("Brand data is required")
      }

      const brand = await brandsApi.create({
        name: data.brand.name,
        cuisine_type: data.brand.cuisineType || undefined,
      })

      toast.success("Brand created successfully!")

      // Step 2: Parse PDF and upload menu if provided
      if (data.menuUpload?.uploadMethod === "pdf" && data.menuUpload.pdfFile) {
        const parseResult = await menuApi.parsePdf(data.menuUpload.pdfFile, brand.id)
        if (parseResult.items.length > 0) {
          await menuApi.bulkCreate({
            brand_id: brand.id,
            items: parseResult.items,
          })
          toast.success(`${parseResult.items.length} menu items imported!`)
        }
      }

      // Step 3: Upload orders if provided
      if (data.orderUpload?.uploadMethod === "csv" && data.orderUpload.csvFile) {
        await ingestionApi.upload(data.orderUpload.csvFile, "orders")
        toast.success("Orders uploaded successfully!")
      }

      // Mark onboarding complete
      completeOnboarding()

      // Navigate to dashboard
      navigate("/")
      toast.success("Welcome! Your account is ready.")
    } catch (error) {
      console.error("Onboarding error:", error)
      const errorMessage = getErrorMessage(error)
      toast.error(errorMessage)
      throw error
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <OnboardingContext.Provider
      value={{
        data,
        updateBrandData,
        updateMenuUpload,
        updateOrderUpload,
        setParsedMenuItems,
        submitOnboarding,
        isSubmitting,
      }}
    >
      {children}
    </OnboardingContext.Provider>
  )
}

export function useOnboarding() {
  const context = useContext(OnboardingContext)
  if (!context) {
    throw new Error("useOnboarding must be used within OnboardingProvider")
  }
  return context
}
