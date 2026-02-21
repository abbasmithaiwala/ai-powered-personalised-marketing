import { Link } from "react-router"
import { Card } from "@/components/ui/Card"
import type { LucideIcon } from "lucide-react"

interface QuickActionProps {
  icon: LucideIcon
  label: string
  href: string
}

export function QuickAction({ icon: Icon, label, href }: QuickActionProps) {
  return (
    <Link to={href}>
      <Card className="p-6 hover:shadow-md transition-shadow cursor-pointer border-2 hover:border-orange-500">
        <div className="flex items-center space-x-4">
          <div className="p-3 bg-orange-100 rounded-lg">
            <Icon className="h-6 w-6 text-orange-600" />
          </div>
          <span className="font-medium text-gray-900">{label}</span>
        </div>
      </Card>
    </Link>
  )
}
