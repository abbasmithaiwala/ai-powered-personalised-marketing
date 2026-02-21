import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { useNavigate } from "react-router"
import { Form } from "@/components/ui/form"
import { FormInput } from "@/components/forms/FormInput"
import { FormTextarea } from "@/components/forms/FormTextarea"
import { FormStep } from "@/components/onboarding/FormStep"
import { StepNavigation } from "@/components/onboarding/StepNavigation"
import { brandSchema, type BrandFormData } from "@/lib/schemas/brandSchema"
import { useOnboarding } from "../OnboardingContext"

export default function BrandDetailsStep() {
  const navigate = useNavigate()
  const { updateBrandData } = useOnboarding()

  const form = useForm<BrandFormData>({
    resolver: zodResolver(brandSchema),
    mode: "onBlur",
    defaultValues: {
      name: "",
      description: "",
      cuisineType: "",
    },
  })

  const onSubmit = (data: BrandFormData) => {
    updateBrandData(data)
    navigate("/onboarding/menu")
  }

  return (
    <FormStep
      title="Tell us about your brand"
      description="We'll use this information to personalize your campaigns"
    >
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          <FormInput
            control={form.control}
            name="name"
            label="Brand Name"
            placeholder="e.g., Bella's Italian Kitchen"
          />

          <FormTextarea
            control={form.control}
            name="description"
            label="Description (Optional)"
            placeholder="Tell us about your brand, cuisine style, and what makes you unique"
            rows={3}
          />

          <FormInput
            control={form.control}
            name="cuisineType"
            label="Cuisine Type (Optional)"
            placeholder="e.g., Italian, Asian Fusion, American"
          />

          <StepNavigation
            onNext={form.handleSubmit(onSubmit)}
            canGoBack={false}
            nextLabel="Continue"
            isLoading={form.formState.isSubmitting}
          />
        </form>
      </Form>
    </FormStep>
  )
}
