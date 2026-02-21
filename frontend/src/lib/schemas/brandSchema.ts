import { z } from "zod"

export const brandSchema = z.object({
  name: z.string().min(2, "Brand name must be at least 2 characters"),
  description: z.string().optional(),
  cuisineType: z.string().optional(),
})

export type BrandFormData = z.infer<typeof brandSchema>
