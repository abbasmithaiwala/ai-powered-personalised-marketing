import { z } from "zod"

export const orderUploadSchema = z.object({
  uploadMethod: z.enum(["csv", "skip"]),
  csvFile: z.instanceof(File).optional()
}).refine(
  (data) => data.uploadMethod !== "csv" || data.csvFile,
  { message: "CSV file required when upload method is CSV", path: ["csvFile"] }
)

export type OrderUploadFormData = z.infer<typeof orderUploadSchema>
