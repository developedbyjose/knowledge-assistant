import * as React from "react"

import { cn } from "@/lib/utils"

type PageContainerProps = React.ComponentProps<"main"> & {
  size?: "default" | "wide"
}

export function PageContainer({
  className,
  size = "default",
  ...props
}: PageContainerProps) {
  return (
    <main
      className={cn(
        "mx-auto flex w-full flex-1 flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8",
        size === "default" ? "max-w-7xl" : "max-w-none",
        className
      )}
      {...props}
    />
  )
}
