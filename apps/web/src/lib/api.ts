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

export type RetrievalResult = {
  chunk_id: string
  document_id: string
  filename: string
  rank: number
  similarity_score: number
  content: string
  page_number: number | null
  chunk_index: number
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

export async function retrieveChunks(
  knowledgeBaseId: string,
  question: string,
  limit = 5
): Promise<{ question: string; results: RetrievalResult[] }> {
  return apiFetch(`/knowledge-bases/${knowledgeBaseId}/retrieval-query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, limit }),
  })
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init)
  if (!response.ok) {
    const fallback = `Request failed with status ${response.status}`
    let detail = fallback

    try {
      const body = await response.json()
      detail = body.detail ?? fallback
    } catch {
      detail = fallback
    }

    throw new Error(detail)
  }

  return response.json()
}
