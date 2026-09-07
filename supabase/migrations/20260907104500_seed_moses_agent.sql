insert into public.agents (agent_id, name, role, version, enabled, configuration)
values (
  'moses',
  'Moses',
  'mobile',
  '0.1.0',
  true,
  '{"specialization":"mobile_application_development","platforms":["react_native","expo","flutter","ios","android"]}'::jsonb
)
on conflict (agent_id) do update set
  name = excluded.name,
  role = excluded.role,
  version = excluded.version,
  enabled = excluded.enabled,
  configuration = excluded.configuration;
