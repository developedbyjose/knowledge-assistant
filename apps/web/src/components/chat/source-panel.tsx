"use client"

import { FileTextIcon } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { AnswerCitation, RetrievalResult } from "@/lib/api"

type SourcePanelProps = {
  citations: AnswerCitation[]
  sourceChunks: RetrievalResult[]
}

export function SourcePanel({ citations, sourceChunks }: SourcePanelProps) {
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
                <div key={source.chunk_id} className="rounded-lg border p-3">
                  <div className="flex items-start gap-2">
                    <FileTextIcon className="mt-0.5 size-4 text-muted-foreground" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">{source.filename}</p>
                      <p className="text-xs text-muted-foreground">
                        Page {source.page_number ?? "unknown"} · Rank {source.rank} · Score{" "}
                        {source.similarity_score.toFixed(2)}
                      </p>
                    </div>
                    {cited ? <Badge variant="secondary">Cited</Badge> : null}
                  </div>
                  <p className="mt-3 max-h-32 overflow-hidden text-sm leading-6 text-muted-foreground">
                    {source.content}
                  </p>
                </div>
              )
            })
          )}
        </div>
      </ScrollArea>
    </aside>
  )
}
