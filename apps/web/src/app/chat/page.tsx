"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import {
  AlertCircleIcon,
  BotIcon,
  MessageSquareIcon,
  PlusIcon,
  RefreshCwIcon,
  ThumbsDownIcon,
  ThumbsUpIcon,
  Trash2Icon,
  UserIcon,
} from "lucide-react"

import { ChatComposer } from "@/components/chat/chat-composer"
import { SourcePanel } from "@/components/chat/source-panel"
import { DocumentPreviewDialog } from "@/components/documents/document-preview-dialog"
import { PageContainer } from "@/components/layout/page-container"
import { PageHeader } from "@/components/layout/page-header"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import {
  AnswerCitation,
  Conversation,
  ConversationMessage,
  FeedbackRating,
  KnowledgeBase,
  RetrievalResult,
  createConversation,
  deleteConversation,
  listConversations,
  listKnowledgeBases,
  recordMessageFeedback,
  streamConversationMessage,
} from "@/lib/api"
import { cn } from "@/lib/utils"
import { AuthGate } from "@/features/auth/auth-gate"

type BusyState = "loading" | "idle" | "creating" | "sending" | "refreshing"

type SourceState = {
  citations: AnswerCitation[]
  sourceChunks: RetrievalResult[]
}

const EMPTY_SOURCES: SourceState = {
  citations: [],
  sourceChunks: [],
}

function ChatPageContent() {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([])
  const [selectedKnowledgeBaseId, setSelectedKnowledgeBaseId] = useState("")
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [selectedConversationId, setSelectedConversationId] = useState("")
  const [selectedSourceMessageId, setSelectedSourceMessageId] = useState("")
  const [pendingFeedbackMessageId, setPendingFeedbackMessageId] = useState("")
  const [busyState, setBusyState] = useState<BusyState>("loading")
  const [error, setError] = useState<string | null>(null)
  const [conversationToDeleteId, setConversationToDeleteId] = useState<string | null>(null)
  const [previewSource, setPreviewSource] = useState<RetrievalResult | null>(null)
  const [previewTrigger, setPreviewTrigger] = useState<HTMLButtonElement | null>(null)

  const selectedConversation = useMemo(
    () => conversations.find((conversation) => conversation.id === selectedConversationId),
    [conversations, selectedConversationId]
  )

  const visibleConversations = useMemo(
    () =>
      conversations.filter(
        (conversation) => conversation.knowledge_base_id === selectedKnowledgeBaseId
      ),
    [conversations, selectedKnowledgeBaseId]
  )

  const conversationToDelete = useMemo(
    () => conversations.find((conversation) => conversation.id === conversationToDeleteId),
    [conversations, conversationToDeleteId]
  )

  const selectedSourceMessage = useMemo(() => {
    const assistantMessages =
      selectedConversation?.messages.filter((message) => message.role === "assistant") ?? []
    return (
      assistantMessages.find((message) => message.id === selectedSourceMessageId) ??
      latestAssistantMessageWithSources(assistantMessages) ??
      assistantMessages.at(-1)
    )
  }, [selectedConversation, selectedSourceMessageId])

  const selectedSources = useMemo<SourceState>(
    () =>
      selectedSourceMessage
        ? {
            citations: selectedSourceMessage.citations ?? [],
            sourceChunks: selectedSourceMessage.source_chunks ?? [],
          }
        : EMPTY_SOURCES,
    [selectedSourceMessage]
  )

  const loadData = useCallback(async () => {
    setBusyState((current) => (current === "idle" ? "refreshing" : "loading"))
    setError(null)

    try {
      const bases = (await listKnowledgeBases()).filter((knowledgeBase) => knowledgeBase.is_active)

      const chats = await listConversations()
      const selectedBaseId = selectedKnowledgeBaseId || bases[0]?.id || ""
      const selectedChat =
        chats.find((conversation) => conversation.id === selectedConversationId) ??
        chats.find((conversation) => conversation.knowledge_base_id === selectedBaseId)

      setKnowledgeBases(bases)
      setSelectedKnowledgeBaseId(selectedBaseId)
      setConversations(chats)
      setSelectedConversationId(selectedChat?.id ?? "")
      setSelectedSourceMessageId("")
    } catch (caught) {
      setError(errorMessage(caught))
    } finally {
      setBusyState("idle")
    }
  }, [selectedConversationId, selectedKnowledgeBaseId])

  useEffect(() => {
    let active = true

    async function loadInitialData() {
      try {
        const bases = (await listKnowledgeBases()).filter((knowledgeBase) => knowledgeBase.is_active)
        const chats = await listConversations()
        if (!active) {
          return
        }

        const selectedBaseId = bases[0]?.id ?? ""
        const selectedChat = chats.find(
          (conversation) => conversation.knowledge_base_id === selectedBaseId
        )

        setKnowledgeBases(bases)
        setSelectedKnowledgeBaseId(selectedBaseId)
        setConversations(chats)
        setSelectedConversationId(selectedChat?.id ?? "")
        setSelectedSourceMessageId("")
      } catch (caught) {
        if (active) {
          setError(errorMessage(caught))
        }
      } finally {
        if (active) {
          setBusyState("idle")
        }
      }
    }

    void loadInitialData()

    return () => {
      active = false
    }
  }, [])

  async function handleNewChat() {
    if (!selectedKnowledgeBaseId) {
      return
    }

    try {
      setBusyState("creating")
      setError(null)
      const created = await createConversation({
        knowledge_base_id: selectedKnowledgeBaseId,
        title: "New chat",
      })
      setConversations((current) => [created, ...current])
      setSelectedConversationId(created.id)
      setSelectedSourceMessageId("")
    } catch (caught) {
      setError(errorMessage(caught))
    } finally {
      setBusyState("idle")
    }
  }

  async function handleDeleteConversation(conversationId: string) {
    const conversation = conversations.find((current) => current.id === conversationId)
    if (!conversation || isSending) {
      return
    }

    try {
      setBusyState("refreshing")
      setError(null)
      await deleteConversation(conversationId)
      const nextConversations = conversations.filter((current) => current.id !== conversationId)
      const nextSelectedConversation = nextConversations.find(
        (current) => current.knowledge_base_id === selectedKnowledgeBaseId
      )

      setConversations(nextConversations)
      setSelectedConversationId(nextSelectedConversation?.id ?? "")
      setSelectedSourceMessageId("")
      setConversationToDeleteId(null)
    } catch (caught) {
      setError(errorMessage(caught))
    } finally {
      setBusyState("idle")
    }
  }

  async function handleSend(content: string) {
    if (!selectedKnowledgeBaseId) {
      setError("Choose a knowledge base before sending a message.")
      return
    }

    setBusyState("sending")
    setError(null)
    setSelectedSourceMessageId("")

    const activeConversation = await ensureConversation(content)
    if (!activeConversation) {
      setBusyState("idle")
      return
    }

    const pendingUserMessage = createOptimisticMessage("user", content, activeConversation.id)
    const pendingAssistantMessage = createOptimisticMessage("assistant", "", activeConversation.id)
    let pendingUserMessageId = pendingUserMessage.id
    let pendingAssistantId = pendingAssistantMessage.id

    setConversations((current) =>
      upsertConversationMessage(current, activeConversation.id, pendingUserMessage)
    )
    setConversations((current) =>
      upsertConversationMessage(current, activeConversation.id, pendingAssistantMessage)
    )

    try {
      await streamConversationMessage(activeConversation.id, content, (event) => {
        if (event.event === "message_start") {
          setConversations((current) =>
            replaceMessageById(
              current,
              activeConversation.id,
              pendingUserMessageId,
              event.data.user_message
            )
          )
          pendingUserMessageId = event.data.user_message.id
        }

        if (event.event === "token") {
          setConversations((current) =>
            updateMessageContent(
              current,
              activeConversation.id,
              pendingAssistantId,
              event.data.content
            )
          )
        }

        if (event.event === "sources") {
          setConversations((current) =>
            setMessageSources(
              current,
              activeConversation.id,
              pendingAssistantId,
              event.data.citations,
              event.data.source_chunks
            )
          )
          setSelectedSourceMessageId(pendingAssistantId)
        }

        if (event.event === "message_done") {
          pendingAssistantId = event.data.assistant_message.id
          setConversations((current) =>
            replaceConversation(current, event.data.conversation)
          )
          setSelectedSourceMessageId(event.data.assistant_message.id)
        }

        if (event.event === "error") {
          setError(event.data.detail)
          if (pendingAssistantId) {
            setConversations((current) =>
              setMessageContent(
                current,
                activeConversation.id,
                pendingAssistantId,
                `Response failed: ${event.data.detail}`
              )
            )
          }
        }
      })
    } catch (caught) {
      setError(errorMessage(caught))
      setConversations((current) =>
        setMessageContent(
          current,
          activeConversation.id,
          pendingAssistantId,
          `Response failed: ${errorMessage(caught)}`
        )
      )
    } finally {
      setBusyState("idle")
    }
  }

  async function handleFeedback(message: ConversationMessage, rating: FeedbackRating) {
    if (message.id.startsWith("pending-")) {
      return
    }

    const previousRating = message.feedback_rating
    setPendingFeedbackMessageId(message.id)
    setError(null)
    setConversations((current) =>
      setMessageFeedback(current, message.conversation_id, message.id, rating)
    )

    try {
      await recordMessageFeedback(message.id, rating)
    } catch (caught) {
      setConversations((current) =>
        setMessageFeedback(current, message.conversation_id, message.id, previousRating)
      )
      setError(errorMessage(caught))
    } finally {
      setPendingFeedbackMessageId("")
    }
  }

  async function ensureConversation(firstMessage: string): Promise<Conversation | null> {
    if (selectedConversation) {
      return selectedConversation
    }

    try {
      const created = await createConversation({
        knowledge_base_id: selectedKnowledgeBaseId,
        title: firstMessage.slice(0, 80),
      })
      setConversations((current) => [created, ...current])
      setSelectedConversationId(created.id)
      return created
    } catch (caught) {
      setError(errorMessage(caught))
      return null
    }
  }

  const isBusy = busyState !== "idle"
  const isSending = busyState === "sending"

  return (
    <PageContainer size="wide" className="h-[calc(100vh-3.5rem)] min-h-[calc(100vh-3.5rem)] gap-4 py-4">
      <PageHeader
        title="Chat"
        description="Ask grounded questions against indexed knowledge base documents."
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="icon"
              aria-label="Refresh chat data"
              onClick={() => void loadData()}
              disabled={isBusy}
            >
              <RefreshCwIcon className={cn("size-4", busyState === "refreshing" && "animate-spin")} />
            </Button>
            <Button onClick={handleNewChat} disabled={!selectedKnowledgeBaseId || isBusy}>
              <PlusIcon className="size-4" />
              New chat
            </Button>
          </div>
        }
      />

      {error ? (
        <Alert variant="destructive">
          <AlertCircleIcon className="size-4" />
          <AlertTitle>Chat request failed</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      <div className="grid min-h-0 flex-1 grid-cols-1 overflow-hidden rounded-lg border bg-background lg:grid-cols-[260px_minmax(0,1fr)_340px]">
        <aside className="flex min-h-0 flex-col border-b lg:border-r lg:border-b-0">
          <div className="space-y-2 border-b p-4">
            <label htmlFor="knowledge-base" className="text-sm font-medium">
              Knowledge base
            </label>
            <Select
              value={selectedKnowledgeBaseId}
              onValueChange={(value) => {
                if (value === null) {
                  return
                }

                setSelectedKnowledgeBaseId(value)
                const nextConversation = conversations.find(
                  (conversation) => conversation.knowledge_base_id === value
                )
                setSelectedConversationId(nextConversation?.id ?? "")
                setSelectedSourceMessageId("")
              }}
              disabled={busyState === "loading" || knowledgeBases.length === 0}
            >
              <SelectTrigger id="knowledge-base" className="h-10">
                <SelectValue placeholder="Select knowledge base">
                  {(value) =>
                    knowledgeBases.find((knowledgeBase) => knowledgeBase.id === value)?.name ??
                    "Select knowledge base"
                  }
                </SelectValue>
              </SelectTrigger>
              <SelectContent>
                {knowledgeBases.map((knowledgeBase) => (
                  <SelectItem key={knowledgeBase.id} value={knowledgeBase.id}>
                    {knowledgeBase.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <ScrollArea className="min-h-0 flex-1">
            <div className="space-y-2 p-3">
              {busyState === "loading" ? (
                <>
                  <Skeleton className="h-16 w-full" />
                  <Skeleton className="h-16 w-full" />
                </>
              ) : visibleConversations.length === 0 ? (
                <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
                  No conversations yet.
                </div>
              ) : (
                visibleConversations.map((conversation) => (
                  <div
                    key={conversation.id}
                    className={cn(
                      "group flex items-start gap-2 rounded-lg border p-2 transition-colors hover:bg-muted",
                      conversation.id === selectedConversationId && "border-primary bg-muted"
                    )}
                  >
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedConversationId(conversation.id)
                        setSelectedSourceMessageId("")
                      }}
                      className="min-w-0 flex-1 rounded-md px-1 py-1 text-left text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    >
                      <span className="block truncate font-medium">{conversation.title}</span>
                      <span className="mt-1 block text-xs text-muted-foreground">
                        {conversation.messages.length} messages
                      </span>
                    </button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      aria-label={`Delete ${conversation.title}`}
                      className="size-8 shrink-0 text-muted-foreground hover:text-destructive"
                      disabled={isSending}
                      onClick={() => setConversationToDeleteId(conversation.id)}
                    >
                      <Trash2Icon className="size-4" />
                    </Button>
                  </div>
                ))
              )}
            </div>
          </ScrollArea>
        </aside>

        <section className="flex min-h-0 flex-col">
          <div className="flex items-center justify-between border-b px-4 py-3">
            <div className="min-w-0">
              <h2 className="truncate text-sm font-medium">
                {selectedConversation?.title ?? "New grounded chat"}
              </h2>
              <p className="text-xs text-muted-foreground">
                Responses are limited to retrieved document context.
              </p>
            </div>
            <Badge variant="outline">SSE</Badge>
          </div>

          <ScrollArea className="min-h-0 flex-1">
            <div className="mx-auto flex w-full max-w-3xl flex-col gap-4 p-4">
              {knowledgeBases.length === 0 ? (
                <div className="flex min-h-80 flex-col items-center justify-center rounded-lg border border-dashed p-8 text-center">
                  <MessageSquareIcon className="size-8 text-muted-foreground" />
                  <h3 className="mt-3 text-lg font-semibold">No knowledge base is available</h3>
                  <p className="mt-2 max-w-md text-sm leading-6 text-muted-foreground">
                    Contact an administrator to activate a knowledge base before starting a chat.
                  </p>
                </div>
              ) : !selectedConversation || selectedConversation.messages.length === 0 ? (
                <div className="flex min-h-80 flex-col items-center justify-center rounded-lg border border-dashed p-8 text-center">
                  <MessageSquareIcon className="size-8 text-muted-foreground" />
                  <h3 className="mt-3 text-lg font-semibold">Start a grounded conversation</h3>
                  <p className="mt-2 max-w-md text-sm leading-6 text-muted-foreground">
                    Ask a question after uploading processed documents to the selected knowledge base.
                  </p>
                </div>
              ) : (
                selectedConversation.messages.map((message) => (
                  <MessageBubble
                    key={message.id}
                    message={message}
                    isSourceSelected={message.id === selectedSourceMessage?.id}
                    isFeedbackPending={message.id === pendingFeedbackMessageId}
                    onSelectSources={() => setSelectedSourceMessageId(message.id)}
                    onFeedback={(rating) => void handleFeedback(message, rating)}
                  />
                ))
              )}
            </div>
          </ScrollArea>

          <ChatComposer
            disabled={!selectedKnowledgeBaseId}
            isSending={isSending}
            onSend={handleSend}
          />
        </section>

        <SourcePanel
          citations={selectedSources.citations}
          sourceChunks={selectedSources.sourceChunks}
          onPreviewSource={(source, trigger) => {
            setPreviewSource(source)
            setPreviewTrigger(trigger)
          }}
        />
      </div>

      <DocumentPreviewDialog
        open={previewSource !== null}
        source={previewSource}
        onOpenChange={(open) => {
          if (!open) {
            setPreviewSource(null)
            window.requestAnimationFrame(() => previewTrigger?.focus())
          }
        }}
      />

      <Dialog
        open={conversationToDeleteId !== null}
        onOpenChange={(open) => {
          if (!open) {
            setConversationToDeleteId(null)
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Conversation</DialogTitle>
            <DialogDescription>
              This will permanently delete{" "}
              <span className="font-medium text-foreground">
                {conversationToDelete?.title ?? "this conversation"}
              </span>{" "}
              and all of its messages.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <DialogClose render={<Button variant="outline" />}>Cancel</DialogClose>
            <Button
              variant="destructive"
              disabled={!conversationToDelete || busyState === "refreshing" || isSending}
              onClick={() => {
                if (conversationToDelete) {
                  void handleDeleteConversation(conversationToDelete.id)
                }
              }}
            >
              <Trash2Icon className="size-4" />
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </PageContainer>
  )
}

export default function ChatPage() {
  return <AuthGate><ChatPageContent /></AuthGate>
}

function MessageBubble({
  message,
  isSourceSelected,
  isFeedbackPending,
  onSelectSources,
  onFeedback,
}: {
  message: ConversationMessage
  isSourceSelected: boolean
  isFeedbackPending: boolean
  onSelectSources: () => void
  onFeedback: (rating: FeedbackRating) => void
}) {
  const isAssistant = message.role === "assistant"
  const sourceChunks = message.source_chunks ?? []
  const feedbackRating = message.feedback_rating ?? null
  const hasSources = sourceChunks.length > 0

  return (
    <div className={cn("flex gap-3", isAssistant ? "justify-start" : "justify-end")}>
      {isAssistant ? (
        <div className="flex size-8 shrink-0 items-center justify-center rounded-md border bg-muted">
          <BotIcon className="size-4" />
        </div>
      ) : null}
      <div className="flex max-w-[80%] flex-col items-start gap-2">
        <button
          type="button"
          disabled={!isAssistant}
          onClick={isAssistant ? onSelectSources : undefined}
          className={cn(
            "w-full rounded-lg border px-4 py-3 text-left text-sm leading-6 outline-none",
            isAssistant
              ? "bg-background focus-visible:ring-2 focus-visible:ring-ring"
              : "cursor-default bg-primary text-primary-foreground",
            isAssistant && hasSources && "hover:bg-muted/60",
            isAssistant && isSourceSelected && hasSources && "border-primary"
          )}
        >
          {message.content ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <TypingIndicator />
          )}
        </button>

        {isAssistant && message.content ? (
          <div className="flex items-center gap-1">
            <Button
              type="button"
              variant={feedbackRating === "positive" ? "secondary" : "ghost"}
              size="icon"
              aria-label="Mark assistant response helpful"
              disabled={isFeedbackPending || message.id.startsWith("pending-")}
              onClick={() => onFeedback("positive")}
              className="size-8"
            >
              <ThumbsUpIcon className="size-4" />
            </Button>
            <Button
              type="button"
              variant={feedbackRating === "negative" ? "secondary" : "ghost"}
              size="icon"
              aria-label="Mark assistant response not helpful"
              disabled={isFeedbackPending || message.id.startsWith("pending-")}
              onClick={() => onFeedback("negative")}
              className="size-8"
            >
              <ThumbsDownIcon className="size-4" />
            </Button>
            {hasSources ? (
              <Button
                type="button"
                variant={isSourceSelected ? "secondary" : "ghost"}
                size="sm"
                onClick={onSelectSources}
                className="h-8"
              >
                Sources
              </Button>
            ) : null}
          </div>
        ) : null}
      </div>
      {!isAssistant ? (
        <div className="flex size-8 shrink-0 items-center justify-center rounded-md border bg-background">
          <UserIcon className="size-4" />
        </div>
      ) : null}
    </div>
  )
}

function TypingIndicator() {
  return (
    <div
      className="flex h-6 items-center gap-1"
      role="status"
      aria-label="Assistant is generating a response"
    >
      <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.2s]" />
      <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.1s]" />
      <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground" />
    </div>
  )
}

function createOptimisticMessage(
  role: ConversationMessage["role"],
  content: string,
  conversationId: string
): ConversationMessage {
  const now = new Date().toISOString()
  return {
    id: `pending-${role}-${crypto.randomUUID()}`,
    conversation_id: conversationId,
    role,
    content,
    model_name: null,
    created_at: now,
    citations: [],
    source_chunks: [],
    feedback_rating: null,
  }
}

function replaceConversation(
  conversations: Conversation[],
  replacement: Conversation
): Conversation[] {
  return conversations.map((conversation) =>
    conversation.id === replacement.id ? replacement : conversation
  )
}

function upsertConversationMessage(
  conversations: Conversation[],
  conversationId: string,
  message: ConversationMessage
): Conversation[] {
  return conversations.map((conversation) => {
    if (conversation.id !== conversationId) {
      return conversation
    }

    const exists = conversation.messages.some((current) => current.id === message.id)
    return {
      ...conversation,
      messages: exists
        ? conversation.messages.map((current) => (current.id === message.id ? message : current))
        : [...conversation.messages, message],
    }
  })
}

function updateMessageContent(
  conversations: Conversation[],
  conversationId: string,
  messageId: string,
  token: string
): Conversation[] {
  return conversations.map((conversation) => {
    if (conversation.id !== conversationId) {
      return conversation
    }

    return {
      ...conversation,
      messages: conversation.messages.map((message) =>
        message.id === messageId
          ? {
              ...message,
              content: `${message.content}${token}`,
            }
          : message
      ),
    }
  })
}

function replaceMessageById(
  conversations: Conversation[],
  conversationId: string,
  messageId: string,
  replacement: ConversationMessage
): Conversation[] {
  return conversations.map((conversation) => {
    if (conversation.id !== conversationId) {
      return conversation
    }

    return {
      ...conversation,
      messages: conversation.messages.map((message) =>
        message.id === messageId ? replacement : message
      ),
    }
  })
}

function setMessageContent(
  conversations: Conversation[],
  conversationId: string,
  messageId: string,
  content: string
): Conversation[] {
  return conversations.map((conversation) => {
    if (conversation.id !== conversationId) {
      return conversation
    }

    return {
      ...conversation,
      messages: conversation.messages.map((message) =>
        message.id === messageId
          ? {
              ...message,
              content,
            }
          : message
      ),
    }
  })
}

function setMessageSources(
  conversations: Conversation[],
  conversationId: string,
  messageId: string,
  citations: AnswerCitation[],
  sourceChunks: RetrievalResult[]
): Conversation[] {
  return conversations.map((conversation) => {
    if (conversation.id !== conversationId) {
      return conversation
    }

    return {
      ...conversation,
      messages: conversation.messages.map((message) =>
        message.id === messageId
          ? {
              ...message,
              citations,
              source_chunks: sourceChunks,
            }
          : message
      ),
    }
  })
}

function setMessageFeedback(
  conversations: Conversation[],
  conversationId: string,
  messageId: string,
  rating: FeedbackRating | null
): Conversation[] {
  return conversations.map((conversation) => {
    if (conversation.id !== conversationId) {
      return conversation
    }

    return {
      ...conversation,
      messages: conversation.messages.map((message) =>
        message.id === messageId
          ? {
              ...message,
              feedback_rating: rating,
            }
          : message
      ),
    }
  })
}

function latestAssistantMessageWithSources(
  messages: ConversationMessage[]
): ConversationMessage | undefined {
  return [...messages].reverse().find((message) => (message.source_chunks ?? []).length > 0)
}

function errorMessage(caught: unknown): string {
  return caught instanceof Error ? caught.message : "Something went wrong."
}
