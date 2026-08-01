"use client"

import { FormEvent, useEffect, useMemo, useState } from "react"
import {
  BookOpenIcon,
  CheckCircle2Icon,
  DatabaseIcon,
  FileTextIcon,
  Loader2Icon,
  SearchIcon,
  UploadIcon,
} from "lucide-react"

import { StatusBadge } from "@/components/common/status-badge"
import { PageContainer } from "@/components/layout/page-container"
import { PageHeader } from "@/components/layout/page-header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import {
  KnowledgeBase,
  RetrievalResult,
  UploadedDocument,
  createKnowledgeBase,
  listKnowledgeBases,
  retrieveChunks,
  uploadPdf,
} from "@/lib/api"

type BusyState = "idle" | "loading" | "creating" | "uploading" | "retrieving"

export default function Home() {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([])
  const [selectedKnowledgeBaseId, setSelectedKnowledgeBaseId] = useState("")
  const [knowledgeBaseName, setKnowledgeBaseName] = useState("Retrieval Lab")
  const [document, setDocument] = useState<UploadedDocument | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [question, setQuestion] = useState("")
  const [results, setResults] = useState<RetrievalResult[]>([])
  const [hasRetrieved, setHasRetrieved] = useState(false)
  const [busyState, setBusyState] = useState<BusyState>("loading")
  const [error, setError] = useState<string | null>(null)

  const selectedKnowledgeBase = useMemo(
    () => knowledgeBases.find((knowledgeBase) => knowledgeBase.id === selectedKnowledgeBaseId),
    [knowledgeBases, selectedKnowledgeBaseId]
  )

  useEffect(() => {
    let active = true

    async function loadKnowledgeBases() {
      try {
        setBusyState("loading")
        const existing = await listKnowledgeBases()
        if (!active) {
          return
        }

        if (existing.length > 0) {
          setKnowledgeBases(existing)
          setSelectedKnowledgeBaseId(
            existing.find((knowledgeBase) => knowledgeBase.chunk_count > 0)?.id ?? existing[0].id
          )
          return
        }

        const created = await createKnowledgeBase({
          name: "Retrieval Lab",
          description: "Default workspace for validating PDF chunk retrieval.",
        })
        if (!active) {
          return
        }
        setKnowledgeBases([created])
        setSelectedKnowledgeBaseId(created.id)
      } catch (caught) {
        setError(errorMessage(caught))
      } finally {
        if (active) {
          setBusyState("idle")
        }
      }
    }

    loadKnowledgeBases()

    return () => {
      active = false
    }
  }, [])

  async function handleCreateKnowledgeBase(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!knowledgeBaseName.trim()) {
      setError("Enter a knowledge base name.")
      return
    }

    try {
      setBusyState("creating")
      setError(null)
      const created = await createKnowledgeBase({
        name: knowledgeBaseName.trim(),
        description: "PDF retrieval validation workspace.",
      })
      setKnowledgeBases((current) => [created, ...current])
      setSelectedKnowledgeBaseId(created.id)
      setKnowledgeBaseName("")
      setDocument(null)
      setResults([])
      setHasRetrieved(false)
    } catch (caught) {
      setError(errorMessage(caught))
    } finally {
      setBusyState("idle")
    }
  }

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!selectedKnowledgeBaseId || !file) {
      setError("Choose a knowledge base and a PDF file.")
      return
    }

    try {
      setBusyState("uploading")
      setError(null)
      setResults([])
      setHasRetrieved(false)
      const uploaded = await uploadPdf(selectedKnowledgeBaseId, file)
      setDocument(uploaded)
      const refreshed = await listKnowledgeBases()
      setKnowledgeBases(refreshed)
    } catch (caught) {
      setError(errorMessage(caught))
    } finally {
      setBusyState("idle")
    }
  }

  async function handleRetrieve(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!selectedKnowledgeBaseId || !question.trim()) {
      setError("Choose a knowledge base and enter a question.")
      return
    }

    try {
      setBusyState("retrieving")
      setError(null)
      const retrieved = await retrieveChunks(selectedKnowledgeBaseId, question.trim(), 5)
      setResults(retrieved.results)
      setHasRetrieved(true)
    } catch (caught) {
      setError(errorMessage(caught))
    } finally {
      setBusyState("idle")
    }
  }

  const isBusy = busyState !== "idle"

  return (
    <main className="min-h-screen bg-background text-foreground">
      <PageContainer size="wide">
        <PageHeader
          title="Retrieval Lab"
          description="Upload one PDF, index its chunks, and verify the top five retrieval matches before connecting an LLM."
          actions={
            <Badge variant="outline" className="hidden sm:inline-flex">
              Retrieval only
            </Badge>
          }
        />

        {error ? (
          <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        ) : null}

        <section className="grid gap-6 xl:grid-cols-[380px_minmax(0,1fr)]">
          <div className="space-y-6">
            <Card className="rounded-lg shadow-none">
              <CardHeader className="border-b pb-4">
                <CardTitle>Knowledge base</CardTitle>
                <CardDescription>Select the retrieval collection for this run.</CardDescription>
                <CardAction>
                  <DatabaseIcon className="size-4 text-muted-foreground" aria-hidden="true" />
                </CardAction>
              </CardHeader>
              <CardContent className="space-y-4 pt-4">
                <div className="space-y-2">
                  <label htmlFor="knowledge-base" className="text-sm font-medium">
                    Active collection
                  </label>
                  <select
                    id="knowledge-base"
                    value={selectedKnowledgeBaseId}
                    onChange={(event) => {
                      setSelectedKnowledgeBaseId(event.target.value)
                      setDocument(null)
                      setResults([])
                      setHasRetrieved(false)
                    }}
                    className="h-9 w-full rounded-md border bg-background px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
                    disabled={busyState === "loading"}
                  >
                    {knowledgeBases.map((knowledgeBase) => (
                      <option key={knowledgeBase.id} value={knowledgeBase.id}>
                        {knowledgeBase.name} ({knowledgeBase.chunk_count} chunks)
                      </option>
                    ))}
                  </select>
                </div>

                <form className="space-y-3" onSubmit={handleCreateKnowledgeBase}>
                  <label htmlFor="new-knowledge-base" className="text-sm font-medium">
                    Create another collection
                  </label>
                  <div className="flex gap-2">
                    <Input
                      id="new-knowledge-base"
                      value={knowledgeBaseName}
                      onChange={(event) => setKnowledgeBaseName(event.target.value)}
                      placeholder="Knowledge base name"
                    />
                    <Button type="submit" disabled={isBusy}>
                      {busyState === "creating" ? (
                        <Loader2Icon className="animate-spin" aria-hidden="true" />
                      ) : null}
                      Create
                    </Button>
                  </div>
                </form>

                {selectedKnowledgeBase ? (
                  <div className="rounded-lg border bg-muted/30 p-3 text-xs leading-5 text-muted-foreground">
                    <p className="font-medium text-foreground">{selectedKnowledgeBase.name}</p>
                    <p>{selectedKnowledgeBase.embedding_model}</p>
                    <p>
                      {selectedKnowledgeBase.document_count} documents, {selectedKnowledgeBase.chunk_count} chunks
                    </p>
                  </div>
                ) : null}
              </CardContent>
            </Card>

            <Card className="rounded-lg shadow-none">
              <CardHeader className="border-b pb-4">
                <CardTitle>PDF upload</CardTitle>
                <CardDescription>Processing runs synchronously for this first slice.</CardDescription>
                <CardAction>
                  <UploadIcon className="size-4 text-muted-foreground" aria-hidden="true" />
                </CardAction>
              </CardHeader>
              <CardContent className="space-y-4 pt-4">
                <form className="space-y-3" onSubmit={handleUpload}>
                  <label htmlFor="pdf-file" className="text-sm font-medium">
                    PDF file
                  </label>
                  <Input
                    id="pdf-file"
                    type="file"
                    accept="application/pdf,.pdf"
                    onChange={(event) => setFile(event.target.files?.[0] ?? null)}
                  />
                  <Button type="submit" className="w-full" disabled={isBusy || !file}>
                    {busyState === "uploading" ? (
                      <Loader2Icon className="animate-spin" aria-hidden="true" />
                    ) : (
                      <UploadIcon aria-hidden="true" />
                    )}
                    Upload and index
                  </Button>
                </form>

                {document ? (
                  <div className="space-y-3 rounded-lg border p-3">
                    <div className="flex items-start gap-2">
                      <FileTextIcon className="mt-0.5 size-4 text-muted-foreground" aria-hidden="true" />
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium">{document.original_filename}</p>
                        <p className="text-xs text-muted-foreground">
                          {document.chunk_count} chunks
                          {document.page_count ? ` across ${document.page_count} pages` : ""}
                        </p>
                      </div>
                      <StatusBadge status={document.status === "processed" ? "ready" : "failed"}>
                        {document.status}
                      </StatusBadge>
                    </div>
                    {document.error_message ? (
                      <p className="text-xs leading-5 text-destructive">{document.error_message}</p>
                    ) : (
                      <div className="flex items-center gap-2 text-xs text-emerald-700">
                        <CheckCircle2Icon className="size-4" aria-hidden="true" />
                        Stored in pgvector and ready for retrieval.
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
                    No indexed PDF yet.
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          <section className="space-y-6">
            <Card className="rounded-lg shadow-none">
              <CardHeader className="border-b pb-4">
                <CardTitle>Question</CardTitle>
                <CardDescription>The response below is retrieved evidence, not an LLM answer.</CardDescription>
                <CardAction>
                  <SearchIcon className="size-4 text-muted-foreground" aria-hidden="true" />
                </CardAction>
              </CardHeader>
              <CardContent className="space-y-4 pt-4">
                <form className="space-y-3" onSubmit={handleRetrieve}>
                  <label htmlFor="question" className="text-sm font-medium">
                    Retrieval query
                  </label>
                  <Textarea
                    id="question"
                    value={question}
                    onChange={(event) => setQuestion(event.target.value)}
                    placeholder="Ask a question that should be answered by the uploaded PDF"
                    rows={4}
                  />
                  <Button type="submit" disabled={isBusy || !question.trim()}>
                    {busyState === "retrieving" ? (
                      <Loader2Icon className="animate-spin" aria-hidden="true" />
                    ) : (
                      <SearchIcon aria-hidden="true" />
                    )}
                    Retrieve five chunks
                  </Button>
                </form>
              </CardContent>
            </Card>

            <Card className="rounded-lg shadow-none">
              <CardHeader className="border-b pb-4">
                <CardTitle>Retrieved chunks</CardTitle>
                <CardDescription>Top five pgvector matches ordered by cosine similarity.</CardDescription>
                <CardAction>
                  <Badge variant="outline">{results.length}/5</Badge>
                </CardAction>
              </CardHeader>
              <CardContent className="space-y-3 pt-4">
                {results.length === 0 ? (
                  <div className="rounded-lg border border-dashed p-6 text-center">
                    <BookOpenIcon className="mx-auto size-5 text-muted-foreground" aria-hidden="true" />
                    <p className="mt-2 text-sm font-medium">
                      {hasRetrieved ? "No chunks returned" : "No retrieved chunks yet"}
                    </p>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {hasRetrieved
                        ? "This selected knowledge base has no indexed chunks yet. Upload a text-based PDF here, or choose a collection with chunks."
                        : "Upload a text-based PDF, then submit a retrieval query."}
                    </p>
                  </div>
                ) : (
                  <>
                    {results.map((result) => (
                      <article key={result.chunk_id} className="rounded-lg border p-4">
                        <div className="mb-3 flex flex-wrap items-center gap-2">
                          <Badge variant="secondary">Rank {result.rank}</Badge>
                          <span className="text-xs text-muted-foreground">
                            Score {result.similarity_score.toFixed(3)}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {result.filename}
                            {result.page_number ? `, page ${result.page_number}` : ""}
                          </span>
                          <span className="ml-auto text-xs text-muted-foreground">
                            Chunk {result.chunk_index}
                          </span>
                        </div>
                        <p className="text-sm leading-6">{result.content}</p>
                      </article>
                    ))}
                    {Array.from({ length: Math.max(0, 5 - results.length) }).map((_, index) => (
                      <div key={`empty-${index}`} className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
                        No additional match returned for slot {results.length + index + 1}.
                      </div>
                    ))}
                  </>
                )}
              </CardContent>
            </Card>
          </section>
        </section>
      </PageContainer>
    </main>
  )
}

function errorMessage(caught: unknown) {
  return caught instanceof Error ? caught.message : "Something went wrong."
}
