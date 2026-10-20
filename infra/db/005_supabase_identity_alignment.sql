-- Align the local/integration schema with the Supabase-backed identity repository.
-- Safe to re-run; existing project/device/workspace data is preserved.
ALTER TABLE public.projects
  ADD COLUMN IF NOT EXISTS owner_id UUID;

ALTER TABLE public.devices
  ADD COLUMN IF NOT EXISTS owner_id UUID;

CREATE TABLE IF NOT EXISTS public.workspace_members (
  workspace_id TEXT NOT NULL REFERENCES public.workspaces(workspace_id) ON DELETE CASCADE,
  user_id UUID NOT NULL,
  role TEXT NOT NULL DEFAULT 'member',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (workspace_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_projects_owner_id
  ON public.projects(owner_id);

CREATE INDEX IF NOT EXISTS idx_workspace_members_user_id
  ON public.workspace_members(user_id);
