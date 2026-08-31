-- Applied to Supabase project jxwgohecmcktbgwqjsim (customer-churn-ml-platform)
-- via Supabase migration tooling on 2026-08-30.
-- Mirrored here for local reference / re-application to another environment.

create table if not exists public.prediction_history (
  id bigint generated always as identity primary key,
  customer_reference text,
  prediction text not null check (prediction in ('Churn', 'No Churn')),
  churn_probability numeric(5,4) not null check (churn_probability >= 0 and churn_probability <= 1),
  risk_level text not null check (risk_level in ('Low', 'Medium', 'High')),
  model_version text not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_prediction_history_created_at on public.prediction_history (created_at desc);
create index if not exists idx_prediction_history_risk_level on public.prediction_history (risk_level);

alter table public.prediction_history enable row level security;

-- No anon-key policies are defined intentionally: all reads/writes go
-- through the FastAPI backend using the service_role key server-side.
-- The browser never talks to Supabase directly with a privileged key.
