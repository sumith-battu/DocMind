CREATE TABLE documents(
	id UUID PRIMARY KEY,
	owner_id VARCHAR(255) NOT NULL,
	filename VARCHAR(512) NOT NULL,
	s3_key VARCHAR(1024),
	status VARCHAR(32) NOT NULL DEFAULT 'UPLOADING',
	page_count INTEGER,
	created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
	updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_documents_owner ON documents(owner_id);
CREATE INDEX idx_documents_status ON documents(status);