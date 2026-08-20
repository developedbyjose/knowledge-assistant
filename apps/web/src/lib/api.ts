const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"

export type KnowledgeBase = {
  id: string
  name: string
  description: string | null
  embedding_model: string
  is_active: boolean
  created_at: string
  document_count: number
  chunk_count: number
}

export type UserRole = "superadmin" | "admin" | "user"

export type AuthUser = {
  id: string
  email: string
  display_name: string
  role: UserRole
  is_active: boolean
  must_change_password: boolean
  created_at: string
  updated_at: string
  last_login_at: string | null
}

export type LoginResponse = { user: AuthUser; must_change_password: boolean }

export class ApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message)
    this.name = "ApiError"
  }
}

export type UploadedDocument = {
  id: string
  filename: string
  original_filename: string
  status: string
  page_count: number | null
  chunk_count: number
  error_message: string | null
}

export type KnowledgeDocument = UploadedDocument & {
  knowledge_base_id: string
  mime_type: string
  created_at: string
  processed_at: string | null
}

export type RetrievalResult = {
  chunk_id: string
  document_id: string
  filename: string
  rank: number
  similarity_score: number
  content: string
  page_number: number | null
  chunk_index: number
  metadata: Record<string, unknown>
}

export type AnswerCitation = {
  chunk_id: string
  document_id: string
  filename: string
  page_number: number | null
  chunk_index: number
  rank: number
  similarity_score: number | null
}

export type FeedbackRating = "positive" | "negative"

export type CitedAnswer = {
  question: string
  answer: string
  citations: AnswerCitation[]
  source_chunks: RetrievalResult[]
}

export type MessageRole = "user" | "assistant" | "system"

export type ConversationMessage = {
  id: string
  conversation_id: string
  role: MessageRole
  content: string
  model_name: string | null
  created_at: string
  citations: AnswerCitation[]
  source_chunks: RetrievalResult[]
  feedback_rating: FeedbackRating | null
}

export type Conversation = {
  id: string
  user_id: string | null
  knowledge_base_id: string
  title: string
  created_at: string
  updated_at: string
  messages: ConversationMessage[]
}

export type ConversationMessageResponse = {
  conversation: Conversation
  user_message: ConversationMessage
  assistant_message: ConversationMessage
  citations: AnswerCitation[]
  source_chunks: RetrievalResult[]
}

export type ChatStreamEvent =
  | {
      event: "message_start"
      data: {
        conversation_id: string
        user_message: ConversationMessage
      }
    }
  | {
      event: "token"
      data: {
        content: string
      }
    }
  | {
      event: "sources"
      data: {
        citations: AnswerCitation[]
        source_chunks: RetrievalResult[]
      }
    }
  | {
      event: "message_done"
      data: {
        conversation: Conversation
        assistant_message: ConversationMessage
      }
    }
  | {
      event: "error"
      data: {
        detail: string
      }
    }

export async function listKnowledgeBases(): Promise<KnowledgeBase[]> {
  return apiFetch("/knowledge-bases")
}

export async function createKnowledgeBase(payload: {
  name: string
  description?: string
}): Promise<KnowledgeBase> {
  return apiFetch("/knowledge-bases", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
}

export async function getKnowledgeBase(id: string): Promise<KnowledgeBase> {
  return apiFetch(`/knowledge-bases/${id}`)
}

export async function updateKnowledgeBase(
  id: string,
  payload: {
    name?: string
    description?: string | null
    is_active?: boolean
  }
): Promise<KnowledgeBase> {
  return apiFetch(`/knowledge-bases/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
}

export async function deleteKnowledgeBase(id: string): Promise<void> {
  await apiFetchNoContent(`/knowledge-bases/${id}`, { method: "DELETE" })
}

export async function uploadPdf(
  knowledgeBaseId: string,
  file: File
): Promise<UploadedDocument> {
  const formData = new FormData()
  formData.append("file", file)

  return apiFetch(`/knowledge-bases/${knowledgeBaseId}/documents`, {
    method: "POST",
    body: formData,
  })
}

export async function listDocuments(knowledgeBaseId: string): Promise<KnowledgeDocument[]> {
  return apiFetch(`/knowledge-bases/${knowledgeBaseId}/documents`)
}

export async function getDocument(id: string): Promise<KnowledgeDocument> {
  return apiFetch(`/documents/${id}`)
}

export async function deleteDocument(id: string): Promise<void> {
  await apiFetchNoContent(`/documents/${id}`, { method: "DELETE" })
}

export async function reprocessDocument(id: string): Promise<KnowledgeDocument> {
  return apiFetch(`/documents/${id}/reprocess`, { method: "POST" })
}

export async function retrieveChunks(
  knowledgeBaseId: string,
  question: string,
  limit = 5
): Promise<{ question: string; results: RetrievalResult[] }> {
  return apiFetch(`/knowledge-bases/${knowledgeBaseId}/query-embedding`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, limit }),
  })
}

export async function answerQuestion(
  knowledgeBaseId: string,
  question: string,
  limit = 5
): Promise<CitedAnswer> {
  return apiFetch(`/knowledge-bases/${knowledgeBaseId}/answers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, limit }),
  })
}

export async function createConversation(payload: {
  knowledge_base_id: string
  title?: string | null
}): Promise<Conversation> {
  const conversation = await apiFetch<Conversation>("/conversations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  return normalizeConversation(conversation)
}

export async function listConversations(): Promise<Conversation[]> {
  const conversations = await apiFetch<Conversation[]>("/conversations")
  return conversations.map(normalizeConversation)
}

export async function getConversation(id: string): Promise<Conversation> {
  const conversation = await apiFetch<Conversation>(`/conversations/${id}`)
  return normalizeConversation(conversation)
}

export async function deleteConversation(id: string): Promise<void> {
  await apiFetchNoContent(`/conversations/${id}`, { method: "DELETE" })
}

export async function sendConversationMessage(
  conversationId: string,
  content: string,
  limit = 5
): Promise<ConversationMessageResponse> {
  const response = await apiFetch<ConversationMessageResponse>(`/conversations/${conversationId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content, limit }),
  })
  return normalizeConversationMessageResponse(response)
}

export async function streamConversationMessage(
  conversationId: string,
  content: string,
  onEvent: (event: ChatStreamEvent) => void,
  limit = 5
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}/messages`, {
    method: "POST",
    headers: {
      Accept: "text/event-stream",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ content, limit, stream: true }),
    credentials: "include",
  })

  if (!response.ok || !response.body) {
    const fallback = `Request failed with status ${response.status}`
    throw new ApiError(await responseDetail(response, fallback), response.status)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""

  while (true) {
    const { done, value } = await reader.read()
    if (done) {
      break
    }

    buffer += decoder.decode(value, { stream: true })
    const frames = buffer.split("\n\n")
    buffer = frames.pop() ?? ""

    for (const frame of frames) {
      const event = parseSseFrame(frame)
      if (event) {
        onEvent(normalizeChatStreamEvent(event))
      }
    }
  }

  if (buffer.trim()) {
    const event = parseSseFrame(buffer)
    if (event) {
      onEvent(normalizeChatStreamEvent(event))
    }
  }
}

export async function recordMessageFeedback(
  messageId: string,
  rating: FeedbackRating
): Promise<{
  id: string
  message_id: string
  rating: FeedbackRating
  created_at: string
}> {
  return apiFetch(`/messages/${messageId}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rating }),
  })
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  return apiFetch("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  })
}

export async function logout(): Promise<void> {
  await apiFetchNoContent("/auth/logout", { method: "POST" })
}

export async function getMe(): Promise<AuthUser> {
  return apiFetch("/auth/me")
}

export async function changePassword(currentPassword: string, newPassword: string): Promise<LoginResponse> {
  return apiFetch("/auth/change-password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  })
}

export async function listUsers(): Promise<AuthUser[]> {
  return apiFetch("/users")
}

export async function createUser(payload: {
  email: string
  display_name: string
  role: UserRole
  temporary_password: string
}): Promise<AuthUser> {
  return apiFetch("/users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
}

export async function updateUser(
  id: string,
  payload: { display_name?: string; role?: UserRole; is_active?: boolean }
): Promise<AuthUser> {
  return apiFetch(`/users/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
}

export async function resetUserPassword(id: string, temporaryPassword: string): Promise<AuthUser> {
  return apiFetch(`/users/${id}/reset-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ temporary_password: temporaryPassword }),
  })
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, credentials: "include" })
  if (!response.ok) {
    const fallback = `Request failed with status ${response.status}`
    throw new ApiError(await responseDetail(response, fallback), response.status)
  }

  return response.json()
}

async function apiFetchNoContent(path: string, init?: RequestInit): Promise<void> {
  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, credentials: "include" })
  if (!response.ok) {
    const fallback = `Request failed with status ${response.status}`
    throw new ApiError(await responseDetail(response, fallback), response.status)
  }
}

async function responseDetail(response: Response, fallback: string): Promise<string> {
  try {
    const body = await response.json()
    return body.detail ?? fallback
  } catch {
    return fallback
  }
}

function parseSseFrame(frame: string): ChatStreamEvent | null {
  const eventLine = frame
    .split("\n")
    .find((line) => line.startsWith("event:"))
  const dataLine = frame
    .split("\n")
    .find((line) => line.startsWith("data:"))

  if (!eventLine || !dataLine) {
    return null
  }

  return {
    event: eventLine.replace("event:", "").trim(),
    data: JSON.parse(dataLine.replace("data:", "").trim()),
  } as ChatStreamEvent
}

function normalizeConversation(conversation: Conversation): Conversation {
  return {
    ...conversation,
    messages: (conversation.messages ?? []).map(normalizeMessage),
  }
}

function normalizeMessage(message: ConversationMessage): ConversationMessage {
  return {
    ...message,
    citations: Array.isArray(message.citations) ? message.citations : [],
    source_chunks: Array.isArray(message.source_chunks) ? message.source_chunks : [],
    feedback_rating: message.feedback_rating ?? null,
  }
}

function normalizeConversationMessageResponse(
  response: ConversationMessageResponse
): ConversationMessageResponse {
  return {
    ...response,
    conversation: normalizeConversation(response.conversation),
    user_message: normalizeMessage(response.user_message),
    assistant_message: normalizeMessage(response.assistant_message),
    citations: Array.isArray(response.citations) ? response.citations : [],
    source_chunks: Array.isArray(response.source_chunks) ? response.source_chunks : [],
  }
}

function normalizeChatStreamEvent(event: ChatStreamEvent): ChatStreamEvent {
  if (event.event === "message_start") {
    return {
      ...event,
      data: {
        ...event.data,
        user_message: normalizeMessage(event.data.user_message),
      },
    }
  }

  if (event.event === "sources") {
    return {
      ...event,
      data: {
        citations: Array.isArray(event.data.citations) ? event.data.citations : [],
        source_chunks: Array.isArray(event.data.source_chunks) ? event.data.source_chunks : [],
      },
    }
  }

  if (event.event === "message_done") {
    return {
      ...event,
      data: {
        conversation: normalizeConversation(event.data.conversation),
        assistant_message: normalizeMessage(event.data.assistant_message),
      },
    }
  }

  return event
}
