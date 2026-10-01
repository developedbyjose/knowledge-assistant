"use client"

import { FileTextIcon } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { AnswerCitation, RetrievalResult } from "@/lib/api"

type SourcePanelProps = {
  citations: AnswerCitation[]
  sourceChunks: RetrievalResult[]
  onPreviewSource: (source: RetrievalResult, trigger: HTMLButtonElement) => void
}

export function SourcePanel({ citations, sourceChunks, onPreviewSource }: SourcePanelProps) {
  return (
    <aside className="flex min-h-0 flex-col border-l bg-background">
      <div className="border-b p-4">
        <h2 className="text-sm font-medium">Sources</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Evidence used for the latest assistant response.
        </p>
      </div>
      <ScrollArea className="min-h-0 flex-1">
        <div className="space-y-3 p-4">
          {sourceChunks.length === 0 ? (
            <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
              No source evidence is attached to this response.
            </div>
          ) : (
            sourceChunks.map((source) => {
              const cited = citations.some((citation) => citation.chunk_id === source.chunk_id)
              return (
                <button
                  key={source.chunk_id}
                  type="button"
                  onClick={(event) => onPreviewSource(source, event.currentTarget)}
                  className="w-full rounded-lg border p-3 text-left outline-none transition-colors hover:bg-muted/60 focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
                  aria-label={`Preview ${source.filename}${source.page_number ? `, page ${source.page_number}` : ""}`}
                >
                  <div className="flex items-start gap-2">
                    <FileTextIcon className="mt-0.5 size-4 text-muted-foreground" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">{source.filename}</p>
                      <p className="text-xs text-muted-foreground">
                        {source.page_number !== null ? `Page ${source.page_number} · ` : ""}
                        Rank {source.rank} · Score {source.similarity_score.toFixed(2)}
                      </p>
                    </div>
                    {cited ? <Badge variant="secondary">Cited</Badge> : null}
                  </div>
                  <p className="mt-3 max-h-32 overflow-hidden text-sm leading-6 text-muted-foreground">
                    {source.content}
                  </p>
                </button>
              )
            })
          )}
        </div>
      </ScrollArea>
    </aside>
  )
}
