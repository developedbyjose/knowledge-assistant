import * as React from "react"

const MOBILE_BREAKPOINT = 768
const QUERY = `(max-width: ${MOBILE_BREAKPOINT - 1}px)`

export function useIsMobile() {
  return React.useSyncExternalStore(subscribeToMobile, getMobileSnapshot, () => false)
}

function subscribeToMobile(onStoreChange: () => void) {
  const mql = window.matchMedia(QUERY)

  mql.addEventListener("change", onStoreChange)

  return () => mql.removeEventListener("change", onStoreChange)
}

function getMobileSnapshot() {
  return window.matchMedia(QUERY).matches
}
