import type { ReactNode } from "react"

interface FormStepProps {
  title: string
  description?: string
  children: ReactNode
}

export function FormStep({ title, description, children }: FormStepProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-4xl font-eb-garamond text-gray-900">{title}</h2>
        {description && (
          <p className="mt-2 text-sm text-gray-600">{description}</p>
        )}
      </div>
      {children}
    </div>
  )
}
