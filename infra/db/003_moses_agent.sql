INSERT INTO agents (agent_id, name, role, version, enabled, configuration)
VALUES (
  'moses',
  'Moses',
  'mobile',
  '0.1.0',
  TRUE,
  '{"specialization":"mobile_application_development","platforms":["react_native","expo","flutter","ios","android"]}'::jsonb
)
ON CONFLICT (agent_id) DO UPDATE SET
  name = EXCLUDED.name,
  role = EXCLUDED.role,
  version = EXCLUDED.version,
  enabled = EXCLUDED.enabled,
  configuration = EXCLUDED.configuration;
