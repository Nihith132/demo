-- Schema for Healthcare Triage Assistant (FastAPI + SQLAlchemy)
-- Target: Supabase Postgres

-- NOTE:
-- 1) Run this in Supabase SQL editor.
-- 2) If you already have these tables, review before applying.

-- ----------------------------
-- doctors
-- ----------------------------
create table if not exists public.doctors (
  id            bigserial primary key,
  name          text not null,
  department    text not null,
  current_load  integer not null default 0,
  is_available  boolean not null default true,
  password_hash text,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

create index if not exists idx_doctors_department on public.doctors(department);

-- ----------------------------
-- patient_records
-- ----------------------------
create table if not exists public.patient_records (
  id                    bigserial primary key,
  patient_id            text unique,
  patient_name          text,
  age                   integer,

  raw_symptoms          text,
  uploaded_file_uris_json text not null default '[]',
  pdf_extracted_text    text,
  ocr_required          boolean not null default false,

  department            text,

  structured_symptoms_json text,

  sbar_situation        text,
  sbar_background       text,
  sbar_assessment       text,
  sbar_recommendation   text,

  severity_score        integer,
  severity_reasoning    text,

  ai_status             text not null default 'pending',

  status                text not null default 'processing',

  assigned_doctor_id    bigint references public.doctors(id) on delete set null,

  prerequisites         text not null default '[]',

  created_at            timestamptz not null default now(),
  updated_at            timestamptz not null default now()
);

create index if not exists idx_patient_records_patient_id on public.patient_records(patient_id);
create index if not exists idx_patient_records_department on public.patient_records(department);
create index if not exists idx_patient_records_assigned_doctor_id on public.patient_records(assigned_doctor_id);

-- ----------------------------
-- appointments
-- ----------------------------
create table if not exists public.appointments (
  id                bigserial primary key,
  patient_record_id bigint not null references public.patient_records(id) on delete cascade,
  doctor_id         bigint not null references public.doctors(id) on delete cascade,

  scheduled_time    timestamptz not null,
  status            text not null default 'booked',

  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now()
);

create index if not exists idx_appointments_doctor_id on public.appointments(doctor_id);
create index if not exists idx_appointments_patient_record_id on public.appointments(patient_record_id);
create index if not exists idx_appointments_status on public.appointments(status);

-- ----------------------------
-- updated_at trigger helper
-- ----------------------------
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists set_updated_at_doctors on public.doctors;
create trigger set_updated_at_doctors
before update on public.doctors
for each row execute function public.set_updated_at();

drop trigger if exists set_updated_at_patient_records on public.patient_records;
create trigger set_updated_at_patient_records
before update on public.patient_records
for each row execute function public.set_updated_at();

drop trigger if exists set_updated_at_appointments on public.appointments;
create trigger set_updated_at_appointments
before update on public.appointments
for each row execute function public.set_updated_at();
