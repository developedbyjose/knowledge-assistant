"use client"

import { useEffect, useRef, useState } from "react"
import {
  AlertCircleIcon,
  DownloadIcon,
  FileWarningIcon,
  Loader2Icon,
  RotateCwIcon,
  XIcon,
} from "lucide-react"

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  DocumentContent,
  RetrievalResult,
  downloadDocumentContent,
  fetchDocumentContent,
} from "@/lib/api"

const PDF_MIME_TYPE = "application/pdf"
const DOCX_MIME_TYPE =
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

type DocumentPreviewDialogProps = {
  open: boolean
  source: RetrievalResult | null
  onOpenChange: (open: boolean) => void
}

export function DocumentPreviewDialog({
  open,
  source,
  onOpenChange,
}: DocumentPreviewDialogProps) {
  if (!source) {
    return null
  }

  return (
    <DocumentPreviewDialogContent
      key={source.chunk_id}
      open={open}
      source={source}
      onOpenChange={onOpenChange}
    />
  )
}

function DocumentPreviewDialogContent({
  open,
  source,
  onOpenChange,
}: DocumentPreviewDialogProps & { source: RetrievalResult }) {
  const [content, setContent] = useState<DocumentContent | null>(null)
  const [objectUrl, setObjectUrl] = useState("")
  const [loadError, setLoadError] = useState<string | null>(null)
  const [renderError, setRenderError] = useState<string | null>(null)
  const [isRendering, setIsRendering] = useState(false)
  const [downloadError, setDownloadError] = useState<string | null>(null)
  const [isDownloading, setIsDownloading] = useState(false)
  const [loadAttempt, setLoadAttempt] = useState(0)
  const docxContainerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) {
      return
    }

    const controller = new AbortController()
    let createdObjectUrl = ""

    void fetchDocumentContent(source.document_id, {
      fallbackFilename: source.filename,
      signal: controller.signal,
    })
      .then((documentContent) => {
        if (controller.signal.aborted) {
          return
        }
        createdObjectUrl = URL.createObjectURL(documentContent.blob)
        setIsRendering(documentContent.mimeType === DOCX_MIME_TYPE)
        setContent(documentContent)
        setObjectUrl(createdObjectUrl)
      })
      .catch((caught: unknown) => {
        if (!controller.signal.aborted) {
          setLoadError(errorMessage(caught))
        }
      })

    return () => {
      controller.abort()
      if (createdObjectUrl) {
        URL.revokeObjectURL(createdObjectUrl)
      }
    }
  }, [loadAttempt, open, source])

  useEffect(() => {
    const container = docxContainerRef.current
    if (!open || !content || content.mimeType !== DOCX_MIME_TYPE || !container) {
      return
    }

    let active = true
    container.replaceChildren()

    void import("docx-preview")
      .then(({ renderAsync }) =>
        renderAsync(content.blob, container, undefined, {
          breakPages: true,
          renderAltChunks: false,
          renderComments: false,
          renderChanges: false,
        })
      )
      .then(() => {
        if (active) {
          setIsRendering(false)
        }
      })
      .catch((caught: unknown) => {
        if (active) {
          setIsRendering(false)
          setRenderError(errorMessage(caught, "This DOCX could not be rendered."))
        }
      })

    return () => {
      active = false
      container.replaceChildren()
    }
  }, [content, open])

  async function handleDownload() {
    if (!source) {
      return
    }

    setIsDownloading(true)
    setDownloadError(null)
    try {
      await downloadDocumentContent(source.document_id, source.filename)
    } catch (caught) {
      setDownloadError(errorMessage(caught, "The document could not be downloaded."))
    } finally {
      setIsDownloading(false)
    }
  }

  function handleRetry() {
    setContent(null)
    setObjectUrl("")
    setLoadError(null)
    setRenderError(null)
    setDownloadError(null)
    setLoadAttempt((value) => value + 1)
  }

  const pageLabel = source?.page_number ? `Page ${source.page_number}` : null
  const displayName = content?.filename ?? source?.filename ?? "Document preview"

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        showCloseButton={false}
        className="h-[100dvh] w-screen max-w-none gap-0 overflow-hidden rounded-none p-0 sm:h-[92vh] sm:w-[96vw] sm:max-w-[1400px] sm:rounded-lg"
      >
        <DialogHeader className="flex-row items-center justify-between gap-4 border-b p-4">
          <div className="min-w-0 space-y-1">
            <DialogTitle className="truncate">{displayName}</DialogTitle>
            <DialogDescription>
              {pageLabel ? `${pageLabel} · ` : ""}Original source document
            </DialogDescription>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <Button
              type="button"
              variant="outline"
              disabled={!content || isDownloading}
              onClick={() => void handleDownload()}
            >
              {isDownloading ? (
                <Loader2Icon className="size-4 animate-spin" />
              ) : (
                <DownloadIcon className="size-4" />
              )}
              Download
            </Button>
            <DialogClose render={<Button variant="ghost" size="icon" aria-label="Close preview" />}>
              <XIcon className="size-4" />
            </DialogClose>
          </div>
        </DialogHeader>

        <div className="relative min-h-0 flex-1 overflow-hidden bg-muted/40">
          {!content && !loadError ? (
            <PreviewStatus label="Loading document preview" />
          ) : loadError ? (
            <div className="flex h-full items-center justify-center p-6">
              <div className="w-full max-w-lg space-y-4">
                <Alert variant="destructive">
                  <AlertCircleIcon className="size-4" />
                  <AlertTitle>Preview unavailable</AlertTitle>
                  <AlertDescription>{loadError}</AlertDescription>
                </Alert>
                <Button type="button" variant="outline" onClick={handleRetry}>
                  <RotateCwIcon className="size-4" />
                  Retry
                </Button>
              </div>
            </div>
          ) : content?.mimeType === PDF_MIME_TYPE && objectUrl ? (
            <iframe
              title={`Preview of ${displayName}`}
              src={`${objectUrl}${source?.page_number ? `#page=${source.page_number}` : ""}`}
              className="h-full w-full border-0 bg-background"
            />
          ) : content?.mimeType === DOCX_MIME_TYPE ? (
            <div className="relative h-full overflow-auto p-4 sm:p-8">
              {isRendering ? (
                <div className="absolute inset-0 z-10 bg-muted/40">
                  <PreviewStatus label="Rendering DOCX preview" />
                </div>
              ) : null}
              {renderError ? (
                <div className="mx-auto max-w-lg">
                  <Alert variant="destructive">
                    <FileWarningIcon className="size-4" />
                    <AlertTitle>DOCX preview unavailable</AlertTitle>
                    <AlertDescription>
                      {renderError} You can still download the original file.
                    </AlertDescription>
                  </Alert>
                </div>
              ) : null}
              <div
                ref={docxContainerRef}
                className={renderError ? "hidden" : "mx-auto min-h-full max-w-fit"}
                aria-label={`Preview of ${displayName}`}
              />
            </div>
          ) : (
            <div className="flex h-full items-center justify-center p-6">
              <Alert className="max-w-lg">
                <FileWarningIcon className="size-4" />
                <AlertTitle>Preview not supported</AlertTitle>
                <AlertDescription>
                  This file type cannot be displayed here. You can still download the original file.
                </AlertDescription>
              </Alert>
            </div>
          )}
        </div>

        {downloadError ? (
          <div className="border-t bg-background px-4 py-3 text-sm text-destructive" role="alert">
            {downloadError}
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  )
}

function PreviewStatus({ label }: { label: string }) {
  return (
    <div className="flex h-full items-center justify-center" role="status">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2Icon className="size-4 animate-spin" />
        {label}
      </div>
    </div>
  )
}

function errorMessage(caught: unknown, fallback = "The document could not be loaded."): string {
  return caught instanceof Error ? caught.message : fallback
}
