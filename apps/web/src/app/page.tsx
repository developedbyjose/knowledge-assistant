"use client"

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react"
import Link from "next/link"
import {
  BookOpenIcon,
  DatabaseIcon,
  FileTextIcon,
  Loader2Icon,
  MessageSquareIcon,
  RefreshCwIcon,
  RotateCcwIcon,
  SearchIcon,
  Trash2Icon,
  UploadIcon,
} from "lucide-react"

import { StatusBadge } from "@/components/common/status-badge"
import { PageContainer } from "@/components/layout/page-container"
import { PageHeader } from "@/components/layout/page-header"
import { Badge } from "@/components/ui/badge"
import { Button, buttonVariants } from "@/components/ui/button"
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Textarea } from "@/components/ui/textarea"
import {
  KnowledgeDocument,
  KnowledgeBase,
  RetrievalResult,
  createKnowledgeBase,
  deleteKnowledgeBase,
  deleteDocument,
  listKnowledgeBases,
  listDocuments,
  reprocessDocument,
  retrieveChunks,
  uploadPdf,
} from "@/lib/api"
import { cn } from "@/lib/utils"

const MAX_UPLOAD_BYTES = 25 * 1024 * 1024

type BusyState =
  | "idle"
  | "loading"
  | "creating"
  | "uploading"
  | "retrieving"
  | "refreshing"
  | "deleting"
  | "deletingCollection"
  | "reprocessing"

export default function Home() {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([])
  const [selectedKnowledgeBaseId, setSelectedKnowledgeBaseId] = useState("")
  const [knowledgeBaseName, setKnowledgeBaseName] = useState("Retrieval Lab")
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([])
  const [file, setFile] = useState<File | null>(null)
  const [question, setQuestion] = useState("")
  const [results, setResults] = useState<RetrievalResult[]>([])
  const [hasRetrieved, setHasRetrieved] = useState(false)
  const [busyState, setBusyState] = useState<BusyState>("loading")
  const [activeDocumentId, setActiveDocumentId] = useState<string | null>(null)
  const [knowledgeBaseToDeleteId, setKnowledgeBaseToDeleteId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const selectedKnowledgeBase = useMemo(
    () => knowledgeBases.find((knowledgeBase) => knowledgeBase.id === selectedKnowledgeBaseId),
    [knowledgeBases, selectedKnowledgeBaseId]
  )

  const knowledgeBaseToDelete = useMemo(
    () => knowledgeBases.find((knowledgeBase) => knowledgeBase.id === knowledgeBaseToDeleteId),
    [knowledgeBases, knowledgeBaseToDeleteId]
  )

  const loadDocuments = useCallback(
    async (knowledgeBaseId: string) => {
      if (!knowledgeBaseId) {
        setDocuments([])
        return
      }

      const loaded = await listDocuments(knowledgeBaseId)
      setDocuments(loaded)
    },
    []
  )

  const refreshKnowledgeBases = useCallback(async () => {
    const refreshed = await listKnowledgeBases()
    setKnowledgeBases(refreshed)
    return refreshed
  }, [])

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

  useEffect(() => {
    let active = true

    async function loadSelectedDocuments() {
      if (!selectedKnowledgeBaseId) {
        setDocuments([])
        return
      }

      try {
        setBusyState((current) => (current === "idle" ? "refreshing" : current))
        setError(null)
        const loaded = await listDocuments(selectedKnowledgeBaseId)
        if (active) {
          setDocuments(loaded)
        }
      } catch (caught) {
        if (active) {
          setError(errorMessage(caught))
        }
      } finally {
        if (active) {
          setBusyState((current) => (current === "refreshing" ? "idle" : current))
        }
      }
    }

    loadSelectedDocuments()

    return () => {
      active = false
    }
  }, [selectedKnowledgeBaseId])

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
      setDocuments([])
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
    const validationError = validatePdf(file)
    if (validationError) {
      setError(validationError)
      return
    }

    try {
      setBusyState("uploading")
      setError(null)
      setResults([])
      setHasRetrieved(false)
      await uploadPdf(selectedKnowledgeBaseId, file)
      setFile(null)
      await Promise.all([refreshKnowledgeBases(), loadDocuments(selectedKnowledgeBaseId)])
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

  async function handleRefreshDocuments() {
    if (!selectedKnowledgeBaseId) {
      return
    }

    try {
      setBusyState("refreshing")
      setError(null)
      await Promise.all([refreshKnowledgeBases(), loadDocuments(selectedKnowledgeBaseId)])
    } catch (caught) {
      setError(errorMessage(caught))
    } finally {
      setBusyState("idle")
    }
  }

  async function handleDeleteDocument(documentId: string) {
    try {
      setBusyState("deleting")
      setActiveDocumentId(documentId)
      setError(null)
      await deleteDocument(documentId)
      await Promise.all([refreshKnowledgeBases(), loadDocuments(selectedKnowledgeBaseId)])
    } catch (caught) {
      setError(errorMessage(caught))
    } finally {
      setActiveDocumentId(null)
      setBusyState("idle")
    }
  }

  async function handleDeleteKnowledgeBase() {
    if (!knowledgeBaseToDelete) {
      return
    }

    try {
      setBusyState("deletingCollection")
      setError(null)
      setResults([])
      setHasRetrieved(false)
      await deleteKnowledgeBase(knowledgeBaseToDelete.id)

      const nextKnowledgeBases = knowledgeBases.filter(
        (knowledgeBase) => knowledgeBase.id !== knowledgeBaseToDelete.id
      )
      const nextSelectedKnowledgeBase =
        nextKnowledgeBases.find((knowledgeBase) => knowledgeBase.chunk_count > 0) ??
        nextKnowledgeBases[0]

      setKnowledgeBases(nextKnowledgeBases)
      setSelectedKnowledgeBaseId(nextSelectedKnowledgeBase?.id ?? "")
      setDocuments([])
      setKnowledgeBaseToDeleteId(null)

      if (nextSelectedKnowledgeBase) {
        await loadDocuments(nextSelectedKnowledgeBase.id)
      }
    } catch (caught) {
      setError(errorMessage(caught))
    } finally {
      setBusyState("idle")
    }
  }

  async function handleReprocessDocument(documentId: string) {
    try {
      setBusyState("reprocessing")
      setActiveDocumentId(documentId)
      setError(null)
      setResults([])
      setHasRetrieved(false)
      await reprocessDocument(documentId)
      await Promise.all([refreshKnowledgeBases(), loadDocuments(selectedKnowledgeBaseId)])
    } catch (caught) {
      setError(errorMessage(caught))
    } finally {
      setActiveDocumentId(null)
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
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="hidden sm:inline-flex">
                Retrieval only
              </Badge>
              <Link href="/chat" className={cn(buttonVariants())}>
                <MessageSquareIcon aria-hidden="true" />
                Chat
              </Link>
            </div>
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
                  <Select
                    value={selectedKnowledgeBaseId}
                    onValueChange={(value) => {
                      if (value === null) {
                        return
                      }
                      setSelectedKnowledgeBaseId(value)
                      setResults([])
                      setHasRetrieved(false)
                    }}
                    disabled={busyState === "loading" || knowledgeBases.length === 0}
                  >
                    <SelectTrigger id="knowledge-base">
                      <SelectValue placeholder="Select collection">
                        {(value) => {
                          const knowledgeBase = knowledgeBases.find(
                            (current) => current.id === value
                          )
                          return knowledgeBase
                            ? `${knowledgeBase.name} (${knowledgeBase.chunk_count} chunks)`
                            : "Select collection"
                        }}
                      </SelectValue>
                    </SelectTrigger>
                    <SelectContent>
                      {knowledgeBases.map((knowledgeBase) => (
                        <SelectItem key={knowledgeBase.id} value={knowledgeBase.id}>
                          {knowledgeBase.name} ({knowledgeBase.chunk_count} chunks)
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
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
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="break-words font-medium text-foreground">
                          {selectedKnowledgeBase.name}
                        </p>
                        <p>{selectedKnowledgeBase.embedding_model}</p>
                        <p>
                          {selectedKnowledgeBase.document_count} documents, {selectedKnowledgeBase.chunk_count} chunks
                        </p>
                      </div>
                      <Button
                        type="button"
                        variant="destructive"
                        size="sm"
                        className="shrink-0"
                        disabled={isBusy}
                        onClick={() => setKnowledgeBaseToDeleteId(selectedKnowledgeBase.id)}
                      >
                        {busyState === "deletingCollection" ? (
                          <Loader2Icon className="animate-spin" aria-hidden="true" />
                        ) : (
                          <Trash2Icon aria-hidden="true" />
                        )}
                        Delete
                      </Button>
                    </div>
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
                    onChange={(event) => {
                      const selected = event.target.files?.[0] ?? null
                      setFile(selected)
                      setError(selected ? validatePdf(selected) : null)
                    }}
                  />
                  {file ? (
                    <p className="text-xs text-muted-foreground">
                      {file.name} ({formatFileSize(file.size)})
                    </p>
                  ) : null}
                  <Button type="submit" className="w-full" disabled={isBusy || !file}>
                    {busyState === "uploading" ? (
                      <Loader2Icon className="animate-spin" aria-hidden="true" />
                    ) : (
                      <UploadIcon aria-hidden="true" />
                    )}
                    Upload and index
                  </Button>
                </form>
              </CardContent>
            </Card>
          </div>

          <section className="space-y-6">
            <Card className="rounded-lg shadow-none">
              <CardHeader className="border-b pb-4">
                <CardTitle>Documents</CardTitle>
                <CardDescription>PDFs stored locally and indexed for the selected collection.</CardDescription>
                <CardAction>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={handleRefreshDocuments}
                    disabled={isBusy || !selectedKnowledgeBaseId}
                  >
                    {busyState === "refreshing" ? (
                      <Loader2Icon className="animate-spin" aria-hidden="true" />
                    ) : (
                      <RefreshCwIcon aria-hidden="true" />
                    )}
                    Refresh
                  </Button>
                </CardAction>
              </CardHeader>
              <CardContent className="pt-4">
                {documents.length === 0 ? (
                  <div className="rounded-lg border border-dashed p-6 text-center">
                    <FileTextIcon className="mx-auto size-5 text-muted-foreground" aria-hidden="true" />
                    <p className="mt-2 text-sm font-medium">No documents in this knowledge base</p>
                    <p className="mt-1 text-sm text-muted-foreground">
                      Upload a text-based PDF to create chunks for retrieval.
                    </p>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>File</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Pages</TableHead>
                        <TableHead className="text-right">Chunks</TableHead>
                        <TableHead>Uploaded</TableHead>
                        <TableHead>Processed</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {documents.map((item) => (
                        <TableRow key={item.id}>
                          <TableCell className="max-w-[260px] whitespace-normal">
                            <div className="flex min-w-0 items-start gap-2">
                              <FileTextIcon className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
                              <div className="min-w-0">
                                <p className="break-words font-medium">{item.original_filename}</p>
                                {item.error_message ? (
                                  <p className="mt-1 line-clamp-2 text-xs leading-5 text-destructive">
                                    {item.error_message}
                                  </p>
                                ) : (
                                  <p className="mt-1 text-xs text-muted-foreground">{item.mime_type}</p>
                                )}
                              </div>
                            </div>
                          </TableCell>
                          <TableCell>
                            <StatusBadge status={documentStatus(item.status)}>{item.status}</StatusBadge>
                          </TableCell>
                          <TableCell className="text-right">{item.page_count ?? "-"}</TableCell>
                          <TableCell className="text-right">{item.chunk_count}</TableCell>
                          <TableCell>{formatDate(item.created_at)}</TableCell>
                          <TableCell>{formatDate(item.processed_at)}</TableCell>
                          <TableCell>
                            <div className="flex justify-end gap-2">
                              <Button
                                type="button"
                                variant="outline"
                                size="icon"
                                aria-label={`Reprocess ${item.original_filename}`}
                                onClick={() => handleReprocessDocument(item.id)}
                                disabled={isBusy}
                              >
                                {busyState === "reprocessing" && activeDocumentId === item.id ? (
                                  <Loader2Icon className="animate-spin" aria-hidden="true" />
                                ) : (
                                  <RotateCcwIcon aria-hidden="true" />
                                )}
                              </Button>
                              <Button
                                type="button"
                                variant="outline"
                                size="icon"
                                aria-label={`Delete ${item.original_filename}`}
                                onClick={() => handleDeleteDocument(item.id)}
                                disabled={isBusy}
                              >
                                {busyState === "deleting" && activeDocumentId === item.id ? (
                                  <Loader2Icon className="animate-spin" aria-hidden="true" />
                                ) : (
                                  <Trash2Icon aria-hidden="true" />
                                )}
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>

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
                        ? "This knowledge base has no indexed chunks yet. Upload a text-based PDF here, or choose a collection with chunks."
                        : "Upload a text-based PDF into this knowledge base, then submit a retrieval query."}
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

        <Dialog
          open={knowledgeBaseToDeleteId !== null}
          onOpenChange={(open) => {
            if (!open) {
              setKnowledgeBaseToDeleteId(null)
            }
          }}
        >
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Delete Collection</DialogTitle>
              <DialogDescription>
                This will permanently delete{" "}
                <span className="font-medium text-foreground">
                  {knowledgeBaseToDelete?.name ?? "this collection"}
                </span>{" "}
                and all of its documents and chunks.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <DialogClose render={<Button variant="outline" />}>Cancel</DialogClose>
              <Button
                variant="destructive"
                disabled={!knowledgeBaseToDelete || busyState === "deletingCollection"}
                onClick={() => void handleDeleteKnowledgeBase()}
              >
                {busyState === "deletingCollection" ? (
                  <Loader2Icon className="animate-spin" aria-hidden="true" />
                ) : (
                  <Trash2Icon aria-hidden="true" />
                )}
                Delete
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </PageContainer>
    </main>
  )
}

function errorMessage(caught: unknown) {
  return caught instanceof Error ? caught.message : "Something went wrong."
}

function validatePdf(file: File) {
  if (!file.name.toLowerCase().endsWith(".pdf")) {
    return "Choose a PDF file."
  }

  if (file.size === 0) {
    return "Uploaded PDF cannot be empty."
  }

  if (file.size > MAX_UPLOAD_BYTES) {
    return "Uploaded PDF must be 25 MB or smaller."
  }

  return null
}

function documentStatus(status: string) {
  if (status === "processed") {
    return "ready"
  }

  if (status === "processing") {
    return "processing"
  }

  if (status === "failed") {
    return "failed"
  }

  return "queued"
}

function formatDate(value: string | null) {
  if (!value) {
    return "-"
  }

  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value))
}

function formatFileSize(bytes: number) {
  if (bytes < 1024 * 1024) {
    return `${Math.max(1, Math.round(bytes / 1024))} KB`
  }

  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
