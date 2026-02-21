import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { useNavigate } from "react-router"
import { Form } from "@/components/ui/form"
import { FormRadioGroup } from "@/components/forms/FormRadioGroup"
import { FileUploadZone } from "@/components/forms/FileUploadZone"
import { FormStep } from "@/components/onboarding/FormStep"
import { StepNavigation } from "@/components/onboarding/StepNavigation"
import { menuUploadSchema, type MenuUploadFormData } from "@/lib/schemas/menuUploadSchema"
import { useOnboarding } from "../OnboardingContext"

export default function MenuDataStep() {
  const navigate = useNavigate()
  const { updateMenuUpload } = useOnboarding()
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  const form = useForm<MenuUploadFormData>({
    resolver: zodResolver(menuUploadSchema),
    mode: "onChange",
    defaultValues: {
      uploadMethod: "skip",
    },
  })

  const uploadMethod = form.watch("uploadMethod")

  const handleFileSelect = (file: File) => {
    setSelectedFile(file)
    form.setValue("pdfFile", file, { shouldValidate: true })
  }

  const handleFileRemove = () => {
    setSelectedFile(null)
    form.setValue("pdfFile", undefined, { shouldValidate: true })
  }

  const onSubmit = async (data: MenuUploadFormData) => {
    updateMenuUpload(data)

    // Note: PDF parsing will happen during onboarding submission
    // after the brand is created, since parsePdf requires a brandId
    navigate("/onboarding/orders")
  }

  return (
    <FormStep
      title="Add your menu items"
      description="Upload a PDF menu or skip to add items manually later"
    >
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          <FormRadioGroup
            control={form.control}
            name="uploadMethod"
            label="How would you like to add your menu?"
            options={[
              {
                label: "Upload PDF Menu",
                value: "pdf",
                description: "We'll automatically extract menu items from your PDF",
              },
              {
                label: "Skip for now",
                value: "skip",
                description: "You can add menu items manually later from the dashboard",
              },
            ]}
          />

          {uploadMethod === "pdf" && (
            <FileUploadZone
              label="Menu PDF"
              description="Upload a PDF file (max 10MB)"
              accept={{ "application/pdf": [".pdf"] }}
              onDrop={handleFileSelect}
              selectedFile={selectedFile}
              onRemove={handleFileRemove}
            />
          )}

          <StepNavigation
            onBack={() => navigate("/onboarding/brand")}
            onNext={form.handleSubmit(onSubmit)}
            nextLabel="Continue"
            isLoading={form.formState.isSubmitting}
          />
        </form>
      </Form>
    </FormStep>
  )
}
