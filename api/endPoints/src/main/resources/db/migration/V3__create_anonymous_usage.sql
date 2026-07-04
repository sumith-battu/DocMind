CREATE TABLE anonymous_usage (
	anon_id VARCHAR PRIMARY KEY,
	question_count INT NOT NULL DEFAULT 0,
	updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);