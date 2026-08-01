const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"

export type KnowledgeBase = {
  id: string
  name: string
  description: string | null
  embedding_model: string
  created_at: string
  document_count: number
  chunk_count: number
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
}

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
  return apiFetch("/conversations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
}

export async function listConversations(): Promise<Conversation[]> {
  return apiFetch("/conversations")
}

export async function getConversation(id: string): Promise<Conversation> {
  return apiFetch(`/conversations/${id}`)
}

export async function deleteConversation(id: string): Promise<void> {
  await apiFetchNoContent(`/conversations/${id}`, { method: "DELETE" })
}

export async function sendConversationMessage(
  conversationId: string,
  content: string,
  limit = 5
): Promise<ConversationMessageResponse> {
  return apiFetch(`/conversations/${conversationId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content, limit }),
  })
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
  })

  if (!response.ok || !response.body) {
    const fallback = `Request failed with status ${response.status}`
    throw new Error(await responseDetail(response, fallback))
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
        onEvent(event)
      }
    }
  }

  if (buffer.trim()) {
    const event = parseSseFrame(buffer)
    if (event) {
      onEvent(event)
    }
  }
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init)
  if (!response.ok) {
    const fallback = `Request failed with status ${response.status}`
    throw new Error(await responseDetail(response, fallback))
  }

  return response.json()
}

async function apiFetchNoContent(path: string, init?: RequestInit): Promise<void> {
  const response = await fetch(`${API_BASE_URL}${path}`, init)
  if (!response.ok) {
    const fallback = `Request failed with status ${response.status}`
    throw new Error(await responseDetail(response, fallback))
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
