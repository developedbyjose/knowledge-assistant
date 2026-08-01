# Retrieval Evaluation

The first vertical slice proves the retrieval system independently from answer
generation:

1. Upload a text-based PDF.
2. Extract text with `pypdf`.
3. Clean extracted pages by removing control characters, repairing hyphenated
   line breaks, and normalizing whitespace.
4. Mark the document as `processing`, then chunk page text with an 800-word
   window and 150-word overlap.
5. Store chunk content with metadata including source type, page number, word
   offsets, chunk size, overlap, and token count.
6. Embed chunks locally with `sentence-transformers/all-MiniLM-L6-v2`.
7. Store 384-dimensional vectors in pgvector.
8. Mark the document as `processed` when indexing succeeds or `failed` with an
   error message when extraction, chunking, embedding, or storage fails.
9. Embed one question and retrieve the top five chunks by cosine distance.
10. Inspect the returned chunks in the Retrieval Lab UI.

LLM answer generation should be connected only after this flow returns relevant
source chunks for representative PDFs and questions.
