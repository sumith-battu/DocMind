CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE chunks (
	id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
	document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
	chunk_index INTEGER NOT NULL,
	content TEXT NOT NULL,
	embedding vector(384) NOT NULL,
	create_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_chunks_document ON chunks(document_id);