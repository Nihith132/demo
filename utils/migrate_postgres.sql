-- Minimal migration to add patient_users + link patient_records to patient_user_id
-- Run in Supabase SQL Editor

create table if not exists public.patient_users (
  id bigserial primary key,
  firebase_uid text not null unique,
  email text,
  display_name text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.patient_records
  add column if not exists patient_user_id bigint;

alter table public.patient_records
  add constraint if not exists fk_patient_records_patient_user_id
  foreign key (patient_user_id)
  references public.patient_users(id)
  on delete set null;

create index if not exists idx_patient_users_firebase_uid on public.patient_users(firebase_uid);
create index if not exists idx_patient_records_patient_user_id on public.patient_records(patient_user_id);
