-- Server-side idempotency storage used by the control-plane repository.
-- No client-facing RLS policy is intentionally created: access is through the
-- trusted control-plane database connection only.
CREATE TABLE IF NOT EXISTS public.idempotency_keys (
  scope TEXT NOT NULL,
  key TEXT NOT NULL,
  response JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (scope, key)
);

CREATE INDEX IF NOT EXISTS idx_idempotency_keys_created_at
  ON public.idempotency_keys(created_at);
