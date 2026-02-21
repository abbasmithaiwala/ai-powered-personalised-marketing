import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { useNavigate } from "react-router"
import { Form } from "@/components/ui/form"
import { FormRadioGroup } from "@/components/forms/FormRadioGroup"
import { FileUploadZone } from "@/components/forms/FileUploadZone"
import { FormStep } from "@/components/onboarding/FormStep"
import { StepNavigation } from "@/components/onboarding/StepNavigation"
import { orderUploadSchema, type OrderUploadFormData } from "@/lib/schemas/orderUploadSchema"
import { useOnboarding } from "../OnboardingContext"

export default function OrderDataStep() {
  const navigate = useNavigate()
  const { updateOrderUpload } = useOnboarding()
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  const form = useForm<OrderUploadFormData>({
    resolver: zodResolver(orderUploadSchema),
    mode: "onChange",
    defaultValues: {
      uploadMethod: "skip",
    },
  })

  const uploadMethod = form.watch("uploadMethod")

  const handleFileSelect = (file: File) => {
    setSelectedFile(file)
    form.setValue("csvFile", file, { shouldValidate: true })
  }

  const handleFileRemove = () => {
    setSelectedFile(null)
    form.setValue("csvFile", undefined, { shouldValidate: true })
  }

  const onSubmit = (data: OrderUploadFormData) => {
    updateOrderUpload(data)
    navigate("/onboarding/confirm")
  }

  return (
    <FormStep
      title="Import customer orders"
      description="Upload order history to enable personalized recommendations"
    >
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          <FormRadioGroup
            control={form.control}
            name="uploadMethod"
            label="How would you like to add order data?"
            options={[
              {
                label: "Upload CSV File",
                value: "csv",
                description: "Import order history from a CSV file",
              },
              {
                label: "Skip for now",
                value: "skip",
                description: "You can import orders later from the dashboard",
              },
            ]}
          />

          {uploadMethod === "csv" && (
            <FileUploadZone
              label="Orders CSV"
              description="CSV with columns: customer_id, customer_name, email, order_date, item_name, quantity, price"
              accept={{ "text/csv": [".csv"] }}
              onDrop={handleFileSelect}
              selectedFile={selectedFile}
              onRemove={handleFileRemove}
            />
          )}

          <StepNavigation
            onBack={() => navigate("/onboarding/menu")}
            onNext={form.handleSubmit(onSubmit)}
            nextLabel="Continue"
            isLoading={form.formState.isSubmitting}
          />
        </form>
      </Form>
    </FormStep>
  )
}
