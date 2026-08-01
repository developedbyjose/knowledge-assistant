import { Loader2Icon } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

type Status = "queued" | "processing" | "ready" | "failed" | "active"

const statusStyles: Record<Status, string> = {
  queued: "bg-secondary text-secondary-foreground",
  processing: "border-border bg-background text-foreground",
  ready: "border-emerald-200 bg-emerald-50 text-emerald-700",
  failed: "bg-destructive/10 text-destructive",
  active: "border-primary/20 bg-primary/10 text-primary",
}

export function StatusBadge({
  status,
  children,
}: {
  status: Status
  children: React.ReactNode
}) {
  return (
    <Badge
      variant={status === "processing" ? "outline" : "secondary"}
      className={cn("capitalize", statusStyles[status])}
    >
      {status === "processing" ? (
        <Loader2Icon className="animate-spin" aria-hidden="true" />
      ) : null}
      {children}
    </Badge>
  )
}
