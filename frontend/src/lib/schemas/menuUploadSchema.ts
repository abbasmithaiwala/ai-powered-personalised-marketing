import { z } from "zod"

export const menuUploadSchema = z.object({
  uploadMethod: z.enum(["pdf", "skip"]),
  pdfFile: z.instanceof(File).optional()
}).refine(
  (data) => data.uploadMethod !== "pdf" || data.pdfFile,
  { message: "PDF file required when upload method is PDF", path: ["pdfFile"] }
)

export type MenuUploadFormData = z.infer<typeof menuUploadSchema>
