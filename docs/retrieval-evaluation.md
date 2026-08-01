# Retrieval Evaluation

The first vertical slice proves the retrieval system independently from answer
generation:

1. Upload a text-based PDF.
2. Extract text with `pypdf`.
3. Chunk page text with an 800-word window and 150-word overlap.
4. Embed chunks with `sentence-transformers/all-MiniLM-L6-v2`.
5. Store 384-dimensional vectors in pgvector.
6. Embed one question and retrieve the top five chunks by cosine distance.
7. Inspect the returned chunks in the Retrieval Lab UI.

LLM answer generation should be connected only after this flow returns relevant
source chunks for representative PDFs and questions.
