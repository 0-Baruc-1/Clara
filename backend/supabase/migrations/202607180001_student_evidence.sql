-- Clara student section: immutable, teacher-attested practice material.
--
-- The source pack may change later. Student evidence never does: it is tied to
-- this published snapshot, its verified OA attestation, and its frozen validator.

create extension if not exists pgcrypto;

create table if not exists public.clara_user_roles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  role text not null check (role in ('teacher', 'student')),
  created_at timestamptz not null default now()
);

create table if not exists public.classes (
  id uuid primary key default gen_random_uuid(),
  teacher_id uuid not null references auth.users(id) on delete restrict,
  name text not null check (char_length(trim(name)) > 0),
  subject text not null check (char_length(trim(subject)) > 0),
  grade_level text not null check (char_length(trim(grade_level)) > 0),
  evidence_min_distinct_items smallint not null default 3
    check (evidence_min_distinct_items between 1 and 10),
  created_at timestamptz not null default now()
);

create table if not exists public.class_enrollments (
  class_id uuid not null references public.classes(id) on delete cascade,
  student_id uuid not null references auth.users(id) on delete cascade,
  status text not null default 'active' check (status in ('active', 'inactive')),
  enrolled_at timestamptz not null default now(),
  primary key (class_id, student_id)
);

-- Changing a threshold changes how a teacher reads the evidence; it must not be
-- an invisible setting change.
create table if not exists public.class_evidence_policy_events (
  id uuid primary key default gen_random_uuid(),
  class_id uuid not null references public.classes(id) on delete cascade,
  teacher_id uuid not null references auth.users(id) on delete restrict,
  previous_min_distinct_items smallint,
  new_min_distinct_items smallint not null check (new_min_distinct_items between 1 and 10),
  changed_at timestamptz not null default now()
);

create table if not exists public.published_material_versions (
  id uuid primary key default gen_random_uuid(),
  class_id uuid not null references public.classes(id) on delete restrict,
  teacher_id uuid not null references auth.users(id) on delete restrict,
  source_pack_reference text not null,
  source_pack_version_reference text,
  source_review_reference text,
  title text not null check (char_length(trim(title)) > 0),
  version_number integer not null check (version_number > 0),
  status text not null default 'draft' check (status in ('draft', 'published')),
  content_snapshot jsonb not null,
  declared_objective_codes jsonb not null default '[]'::jsonb,
  snapshot_hash text not null default '',
  created_at timestamptz not null default now(),
  published_at timestamptz,
  unique (class_id, source_pack_reference, version_number)
);

create table if not exists public.publication_attestations (
  id uuid primary key default gen_random_uuid(),
  publication_version_id uuid not null unique references public.published_material_versions(id) on delete restrict,
  teacher_id uuid not null references auth.users(id) on delete restrict,
  attestation_statement_version text not null,
  attested_at timestamptz not null default now()
);

create table if not exists public.publication_objective_attestations (
  id uuid primary key default gen_random_uuid(),
  publication_version_id uuid not null references public.published_material_versions(id) on delete restrict,
  teacher_id uuid not null references auth.users(id) on delete restrict,
  objective_code text not null check (char_length(trim(objective_code)) > 0),
  official_wording_snapshot text not null check (char_length(trim(official_wording_snapshot)) > 0),
  curriculum_source_url text not null check (curriculum_source_url ~ '^https?://'),
  verification_run_id text not null check (char_length(trim(verification_run_id)) > 0),
  attested_at timestamptz not null default now(),
  unique (publication_version_id, objective_code)
);

create table if not exists public.published_material_items (
  id uuid primary key default gen_random_uuid(),
  publication_version_id uuid not null references public.published_material_versions(id) on delete restrict,
  source_assessment_item_id text,
  ordinal smallint not null check (ordinal > 0),
  item_snapshot jsonb not null,
  content_hash text not null default '',
  -- Null means the item is allowed as practice only: it produces no OA evidence.
  evidence_objective_code text,
  evidence_attestation_id uuid references public.publication_objective_attestations(id) on delete restrict,
  evidence_exclusion_reason text,
  validation_mode text not null check (validation_mode in ('deterministic', 'teacher_judgment')),
  deterministic_validator jsonb,
  created_at timestamptz not null default now(),
  unique (publication_version_id, ordinal),
  check (
    (evidence_objective_code is null and evidence_attestation_id is null)
    or (evidence_objective_code is not null and evidence_attestation_id is not null)
  ),
  check (
    (validation_mode = 'deterministic' and deterministic_validator is not null)
    or (validation_mode = 'teacher_judgment' and deterministic_validator is null)
  ),
  check (
    evidence_objective_code is not null
    or evidence_exclusion_reason is not null
  )
);

-- Availability is deliberately outside the immutable content version. A teacher
-- can stop assigning a sheet without mutating the attested snapshot.
create table if not exists public.student_material_releases (
  id uuid primary key default gen_random_uuid(),
  publication_version_id uuid not null unique references public.published_material_versions(id) on delete restrict,
  class_id uuid not null references public.classes(id) on delete restrict,
  is_active boolean not null default true,
  released_at timestamptz not null default now(),
  closed_at timestamptz
);

create table if not exists public.student_response_attempts (
  id uuid primary key default gen_random_uuid(),
  published_item_id uuid not null references public.published_material_items(id) on delete restrict,
  student_id uuid not null references auth.users(id) on delete restrict,
  answer_payload jsonb not null,
  submitted_at timestamptz not null default now(),
  auto_feedback_state text not null check (auto_feedback_state in ('not_applicable', 'verified', 'unavailable')),
  auto_feedback_payload jsonb,
  teacher_review_state text not null default 'not_required'
    check (teacher_review_state in ('not_required', 'pending', 'reviewed')),
  constraint deterministic_feedback_consistency check (
    (auto_feedback_state = 'verified' and auto_feedback_payload is not null)
    or (auto_feedback_state in ('not_applicable', 'unavailable'))
  )
);

create table if not exists public.teacher_response_reviews (
  id uuid primary key default gen_random_uuid(),
  response_attempt_id uuid not null unique references public.student_response_attempts(id) on delete restrict,
  teacher_id uuid not null references auth.users(id) on delete restrict,
  note text not null check (char_length(trim(note)) > 0),
  reviewed_at timestamptz not null default now()
);

-- Only the backend service role can mint this ticket after querying the
-- curriculum provider. A browser cannot forge a verified OA by calling the
-- publication RPC directly.
create table if not exists public.publication_verification_tickets (
  id uuid primary key default gen_random_uuid(),
  teacher_id uuid not null references auth.users(id) on delete cascade,
  payload_hash text not null,
  verified_objectives jsonb not null,
  expires_at timestamptz not null,
  consumed_at timestamptz
);

create index if not exists idx_class_enrollments_student on public.class_enrollments(student_id, status);
create index if not exists idx_published_versions_class on public.published_material_versions(class_id, status);
create index if not exists idx_published_items_version on public.published_material_items(publication_version_id, ordinal);
create index if not exists idx_response_student_item on public.student_response_attempts(student_id, published_item_id, submitted_at desc);

create or replace function public.clara_is_teacher()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1 from public.clara_user_roles r
    where r.user_id = auth.uid() and r.role = 'teacher'
  );
$$;

create or replace function public.clara_is_teacher_of_class(p_class_id uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1
    from public.classes c
    join public.clara_user_roles r on r.user_id = auth.uid() and r.role = 'teacher'
    where c.id = p_class_id and c.teacher_id = auth.uid()
  );
$$;

create or replace function public.clara_is_active_student_in_class(p_class_id uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1 from public.class_enrollments e
    where e.class_id = p_class_id and e.student_id = auth.uid() and e.status = 'active'
  );
$$;

create or replace function public.clara_set_snapshot_hash()
returns trigger
language plpgsql
security definer
set search_path = public, extensions
as $$
begin
  if tg_table_name = 'published_material_versions' then
    new.snapshot_hash := encode(digest(jsonb_build_object(
      'content_snapshot', new.content_snapshot,
      'declared_objective_codes', new.declared_objective_codes,
      'title', new.title
    )::text, 'sha256'), 'hex');
  else
    new.content_hash := encode(digest(jsonb_build_object(
      'item_snapshot', new.item_snapshot,
      'ordinal', new.ordinal,
      'evidence_objective_code', new.evidence_objective_code,
      'evidence_exclusion_reason', new.evidence_exclusion_reason,
      'validation_mode', new.validation_mode,
      'deterministic_validator', new.deterministic_validator
    )::text, 'sha256'), 'hex');
  end if;
  return new;
end;
$$;

create or replace function public.clara_reject_published_content_mutation()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  version_status text;
begin
  if tg_table_name = 'published_material_versions' then
    if tg_op in ('UPDATE', 'DELETE') and old.status = 'published' then
      raise exception 'Published material versions are immutable.' using errcode = '55000';
    end if;
    if tg_op = 'DELETE' then
      return old;
    end if;
    return new;
  end if;

  if tg_op = 'DELETE' then
    select status into version_status from public.published_material_versions where id = old.publication_version_id;
  else
    select status into version_status from public.published_material_versions where id = new.publication_version_id;
  end if;

  if version_status = 'published' then
    raise exception 'Published material content and attestations are immutable.' using errcode = '55000';
  end if;
  if tg_op = 'DELETE' then
    return old;
  end if;
  return new;
end;
$$;

create or replace function public.clara_validate_publish_transition()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  if old.status = 'draft' and new.status = 'published' then
    if new.published_at is null then
      new.published_at := now();
    end if;
    if not exists (select 1 from public.publication_attestations a where a.publication_version_id = new.id and a.teacher_id = new.teacher_id) then
      raise exception 'A teacher attestation is required before publication.' using errcode = '23514';
    end if;
    if not exists (select 1 from public.published_material_items i where i.publication_version_id = new.id) then
      raise exception 'At least one practice item is required before publication.' using errcode = '23514';
    end if;
    if exists (
      select 1
      from public.published_material_items i
      left join public.publication_objective_attestations a on a.id = i.evidence_attestation_id
      where i.publication_version_id = new.id
        and i.evidence_objective_code is not null
        and (a.id is null or a.publication_version_id <> new.id or a.objective_code <> i.evidence_objective_code)
    ) then
      raise exception 'Every evidence OA must be a verified attested OA of this publication.' using errcode = '23514';
    end if;
  end if;
  return new;
end;
$$;

create or replace function public.clara_create_release_after_publish()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  if old.status = 'draft' and new.status = 'published' then
    insert into public.student_material_releases (publication_version_id, class_id)
    values (new.id, new.class_id);
  end if;
  return new;
end;
$$;

create or replace function public.clara_reject_response_mutation()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  if tg_op = 'UPDATE'
    and auth.role() = 'service_role'
    and old.auto_feedback_state = 'unavailable'
    and new.student_id = old.student_id
    and new.published_item_id = old.published_item_id
    and new.answer_payload = old.answer_payload
    and new.submitted_at = old.submitted_at
    and new.teacher_review_state = old.teacher_review_state then
    return new;
  end if;
  if tg_op in ('UPDATE', 'DELETE') then
    raise exception 'Student response attempts are immutable.' using errcode = '55000';
  end if;
  return new;
end;
$$;

create or replace function public.clara_create_publication_verification_ticket(
  p_teacher_id uuid,
  p_payload jsonb,
  p_verified_objectives jsonb
)
returns uuid
language plpgsql
security definer
set search_path = public, extensions
as $$
declare
  ticket_id uuid;
begin
  if auth.role() <> 'service_role' then
    raise exception 'Only the Clara backend may create verification tickets.' using errcode = '42501';
  end if;
  insert into public.publication_verification_tickets (
    teacher_id, payload_hash, verified_objectives, expires_at
  ) values (
    p_teacher_id,
    encode(digest(p_payload::text, 'sha256'), 'hex'),
    p_verified_objectives,
    now() + interval '5 minutes'
  ) returning id into ticket_id;
  return ticket_id;
end;
$$;

create or replace function public.clara_publish_student_material(
  p_payload jsonb,
  p_ticket_id uuid
)
returns uuid
language plpgsql
security definer
set search_path = public, extensions
as $$
declare
  v_class_id uuid := (p_payload ->> 'class_id')::uuid;
  v_version_id uuid;
  v_ticket public.publication_verification_tickets%rowtype;
  v_item jsonb;
  v_objective jsonb;
  v_next_version integer;
  v_attestation_id uuid;
begin
  if not public.clara_is_teacher_of_class(v_class_id) then
    raise exception 'Only the class teacher may publish material.' using errcode = '42501';
  end if;
  select * into v_ticket
  from public.publication_verification_tickets
  where id = p_ticket_id and teacher_id = auth.uid() and consumed_at is null and expires_at > now()
  for update;
  if not found or v_ticket.payload_hash <> encode(digest(p_payload::text, 'sha256'), 'hex') then
    raise exception 'The publication verification ticket is invalid or expired.' using errcode = '42501';
  end if;

  perform pg_advisory_xact_lock(hashtext(v_class_id::text || ':' || (p_payload ->> 'source_pack_reference')));
  select coalesce(max(version_number), 0) + 1 into v_next_version
  from public.published_material_versions
  where class_id = v_class_id and source_pack_reference = p_payload ->> 'source_pack_reference';

  insert into public.published_material_versions (
    class_id, teacher_id, source_pack_reference, source_pack_version_reference,
    source_review_reference, title, version_number, content_snapshot, declared_objective_codes
  ) values (
    v_class_id, auth.uid(), p_payload ->> 'source_pack_reference',
    p_payload ->> 'source_pack_version_reference', p_payload ->> 'source_review_reference',
    p_payload ->> 'title', v_next_version, p_payload -> 'content_snapshot',
    coalesce(p_payload -> 'declared_objective_codes', '[]'::jsonb)
  ) returning id into v_version_id;

  insert into public.publication_attestations (
    publication_version_id, teacher_id, attestation_statement_version
  ) values (v_version_id, auth.uid(), p_payload ->> 'attestation_statement_version');

  for v_objective in select value from jsonb_array_elements(v_ticket.verified_objectives)
  loop
    insert into public.publication_objective_attestations (
      publication_version_id, teacher_id, objective_code, official_wording_snapshot,
      curriculum_source_url, verification_run_id
    ) values (
      v_version_id, auth.uid(), v_objective ->> 'objective_code',
      v_objective ->> 'official_wording_snapshot', v_objective ->> 'curriculum_source_url',
      v_objective ->> 'verification_run_id'
    );
  end loop;

  for v_item in select value from jsonb_array_elements(p_payload -> 'items')
  loop
    v_attestation_id := null;
    if nullif(v_item ->> 'evidence_objective_code', '') is not null then
      select id into v_attestation_id
      from public.publication_objective_attestations
      where publication_version_id = v_version_id
        and objective_code = v_item ->> 'evidence_objective_code';
      if v_attestation_id is null then
        raise exception 'An item attempted to use an OA not verified by the host.' using errcode = '23514';
      end if;
    end if;
    insert into public.published_material_items (
      publication_version_id, source_assessment_item_id, ordinal, item_snapshot,
      evidence_objective_code, evidence_attestation_id, evidence_exclusion_reason,
      validation_mode, deterministic_validator
    ) values (
      v_version_id, nullif(v_item ->> 'source_assessment_item_id', ''),
      (v_item ->> 'ordinal')::smallint, v_item -> 'item_snapshot',
      nullif(v_item ->> 'evidence_objective_code', ''), v_attestation_id,
      nullif(v_item ->> 'evidence_exclusion_reason', ''),
      v_item ->> 'validation_mode', v_item -> 'deterministic_validator'
    );
  end loop;

  update public.published_material_versions set status = 'published' where id = v_version_id;
  update public.publication_verification_tickets set consumed_at = now() where id = p_ticket_id;
  return v_version_id;
end;
$$;

create or replace function public.clara_submit_student_response(
  p_published_item_id uuid,
  p_answer_payload jsonb
)
returns uuid
language plpgsql
security definer
set search_path = public
as $$
declare
  v_response_id uuid;
  v_mode text;
  v_item public.published_material_items%rowtype;
  v_version public.published_material_versions%rowtype;
begin
  select i.* into v_item
  from public.published_material_items i
  join public.published_material_versions v on v.id = i.publication_version_id
  join public.student_material_releases r on r.publication_version_id = v.id
  where i.id = p_published_item_id and v.status = 'published' and r.is_active
    and public.clara_is_active_student_in_class(r.class_id);
  if not found then
    raise exception 'This practice item is unavailable to the current student.' using errcode = '42501';
  end if;
  select * into v_version from public.published_material_versions where id = v_item.publication_version_id;
  if v_version.snapshot_hash <> encode(digest(jsonb_build_object(
    'content_snapshot', v_version.content_snapshot,
    'declared_objective_codes', v_version.declared_objective_codes,
    'title', v_version.title
  )::text, 'sha256'), 'hex')
  or v_item.content_hash <> encode(digest(jsonb_build_object(
    'item_snapshot', v_item.item_snapshot,
    'ordinal', v_item.ordinal,
    'evidence_objective_code', v_item.evidence_objective_code,
    'evidence_exclusion_reason', v_item.evidence_exclusion_reason,
    'validation_mode', v_item.validation_mode,
    'deterministic_validator', v_item.deterministic_validator
  )::text, 'sha256'), 'hex') then
    raise exception 'Published item integrity check failed.' using errcode = '22000';
  end if;
  v_mode := v_item.validation_mode;
  insert into public.student_response_attempts (
    published_item_id, student_id, answer_payload, auto_feedback_state, teacher_review_state
  ) values (
    p_published_item_id, auth.uid(), p_answer_payload,
    case when v_mode = 'deterministic' then 'unavailable' else 'not_applicable' end,
    case when v_mode = 'deterministic' then 'not_required' else 'pending' end
  ) returning id into v_response_id;
  return v_response_id;
end;
$$;

create or replace function public.clara_host_item_validation(p_item_id uuid)
returns table (validation_mode text, deterministic_validator jsonb)
language plpgsql
security definer
set search_path = public, extensions
as $$
declare
  v_item public.published_material_items%rowtype;
begin
  if auth.role() <> 'service_role' then
    raise exception 'Only the Clara backend may read a validator.' using errcode = '42501';
  end if;
  select * into v_item from public.published_material_items where id = p_item_id;
  if not found or v_item.content_hash <> encode(digest(jsonb_build_object(
    'item_snapshot', v_item.item_snapshot,
    'ordinal', v_item.ordinal,
    'evidence_objective_code', v_item.evidence_objective_code,
    'evidence_exclusion_reason', v_item.evidence_exclusion_reason,
    'validation_mode', v_item.validation_mode,
    'deterministic_validator', v_item.deterministic_validator
  )::text, 'sha256'), 'hex') then
    raise exception 'Published validator integrity check failed.' using errcode = '22000';
  end if;
  return query select v_item.validation_mode, v_item.deterministic_validator;
end;
$$;

-- This is an evidence rollup, not a mastery score. It intentionally returns
-- response counts and the current class threshold only.
create or replace function public.clara_teacher_student_evidence(p_class_id uuid)
returns table (
  student_id uuid,
  objective_code text,
  declared_publication_count integer,
  attested_item_count integer,
  distinct_items_responded integer,
  evidence_threshold smallint,
  evidence_state text
)
language plpgsql
security invoker
set search_path = public
as $$
begin
  if not public.clara_is_teacher_of_class(p_class_id) then
    raise exception 'Only the class teacher may read student evidence.' using errcode = '42501';
  end if;
  return query
  with declared as (
    select v.id as version_id, jsonb_array_elements_text(v.declared_objective_codes) as objective_code
    from public.published_material_versions v
    where v.class_id = p_class_id and v.status = 'published'
  ), objective_universe as (
    select objective_code from declared
    union
    select a.objective_code
    from public.publication_objective_attestations a
    join public.published_material_versions v on v.id = a.publication_version_id
    where v.class_id = p_class_id and v.status = 'published'
  ), students as (
    select e.student_id from public.class_enrollments e
    where e.class_id = p_class_id and e.status = 'active'
  ), attested_items as (
    select i.id, i.evidence_objective_code
    from public.published_material_items i
    join public.published_material_versions v on v.id = i.publication_version_id
    where v.class_id = p_class_id and v.status = 'published'
  )
  select
    s.student_id,
    o.objective_code,
    count(distinct d.version_id)::integer as declared_publication_count,
    count(distinct i.id)::integer as attested_item_count,
    count(distinct r.published_item_id) filter (where r.id is not null)::integer as distinct_items_responded,
    c.evidence_min_distinct_items,
    case when count(distinct r.published_item_id) filter (where r.id is not null) >= c.evidence_min_distinct_items
      then 'evidencia_suficiente' else 'evidencia_insuficiente' end
  from students s
  cross join objective_universe o
  join public.classes c on c.id = p_class_id
  left join declared d on d.objective_code = o.objective_code
  left join attested_items i on i.evidence_objective_code = o.objective_code
  left join public.student_response_attempts r on r.published_item_id = i.id and r.student_id = s.student_id
  group by s.student_id, o.objective_code, c.evidence_min_distinct_items;
end;
$$;

create or replace function public.clara_attach_host_feedback(
  p_response_attempt_id uuid,
  p_feedback jsonb
)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  if auth.role() <> 'service_role' then
    raise exception 'Only the Clara backend may attach automatic feedback.' using errcode = '42501';
  end if;
  update public.student_response_attempts
  set auto_feedback_state = 'verified', auto_feedback_payload = p_feedback
  where id = p_response_attempt_id and auto_feedback_state = 'unavailable';
  if not found then
    raise exception 'Automatic feedback cannot be attached to this response.' using errcode = '55000';
  end if;
end;
$$;

create trigger clara_hash_version_snapshot
before insert or update on public.published_material_versions
for each row execute function public.clara_set_snapshot_hash();

create trigger clara_freeze_published_version
before update or delete on public.published_material_versions
for each row execute function public.clara_reject_published_content_mutation();

create trigger clara_validate_publish
before update of status on public.published_material_versions
for each row execute function public.clara_validate_publish_transition();

create trigger clara_release_published_version
after update of status on public.published_material_versions
for each row execute function public.clara_create_release_after_publish();

create trigger clara_hash_item_snapshot
before insert or update on public.published_material_items
for each row execute function public.clara_set_snapshot_hash();

create trigger clara_freeze_published_item
before insert or update or delete on public.published_material_items
for each row execute function public.clara_reject_published_content_mutation();

create trigger clara_freeze_publication_attestation
before insert or update or delete on public.publication_attestations
for each row execute function public.clara_reject_published_content_mutation();

create trigger clara_freeze_objective_attestation
before insert or update or delete on public.publication_objective_attestations
for each row execute function public.clara_reject_published_content_mutation();

create trigger clara_freeze_response_attempt
before update or delete on public.student_response_attempts
for each row execute function public.clara_reject_response_mutation();

-- A dedicated RPC is the only supported student material read path. It verifies
-- both hashes on every read and raises rather than returning altered content.
create or replace function public.clara_student_material_snapshot(p_release_id uuid)
returns table (
  release_id uuid,
  publication_version_id uuid,
  title text,
  item_id uuid,
  ordinal smallint,
  item_snapshot jsonb,
  evidence_objective_code text,
  validation_mode text
)
language plpgsql
security definer
set search_path = public, extensions
as $$
declare
  v_version public.published_material_versions%rowtype;
begin
  select v.* into v_version
  from public.student_material_releases r
  join public.published_material_versions v on v.id = r.publication_version_id
  where r.id = p_release_id and r.is_active and v.status = 'published'
    and public.clara_is_active_student_in_class(r.class_id);

  if not found then
    raise exception 'Published material is not available to this student.' using errcode = '42501';
  end if;
  if v_version.snapshot_hash <> encode(digest(jsonb_build_object(
    'content_snapshot', v_version.content_snapshot,
    'declared_objective_codes', v_version.declared_objective_codes,
    'title', v_version.title
  )::text, 'sha256'), 'hex') then
    raise exception 'Published material integrity check failed.' using errcode = '22000';
  end if;
  if exists (
    select 1 from public.published_material_items i
    where i.publication_version_id = v_version.id
      and i.content_hash <> encode(digest(jsonb_build_object(
        'item_snapshot', i.item_snapshot,
        'ordinal', i.ordinal,
        'evidence_objective_code', i.evidence_objective_code,
        'evidence_exclusion_reason', i.evidence_exclusion_reason,
        'validation_mode', i.validation_mode,
        'deterministic_validator', i.deterministic_validator
      )::text, 'sha256'), 'hex')
  ) then
    raise exception 'Published item integrity check failed.' using errcode = '22000';
  end if;

  return query
  select p_release_id, v_version.id, v_version.title, i.id, i.ordinal,
         i.item_snapshot, i.evidence_objective_code, i.validation_mode
  from public.published_material_items i
  where i.publication_version_id = v_version.id
  order by i.ordinal;
end;
$$;

alter table public.clara_user_roles enable row level security;
alter table public.classes enable row level security;
alter table public.class_enrollments enable row level security;
alter table public.class_evidence_policy_events enable row level security;
alter table public.published_material_versions enable row level security;
alter table public.publication_attestations enable row level security;
alter table public.publication_objective_attestations enable row level security;
alter table public.published_material_items enable row level security;
alter table public.student_material_releases enable row level security;
alter table public.student_response_attempts enable row level security;
alter table public.teacher_response_reviews enable row level security;
alter table public.publication_verification_tickets enable row level security;

create policy "teachers manage their classes" on public.classes
  for all using (teacher_id = auth.uid() and public.clara_is_teacher())
  with check (teacher_id = auth.uid() and public.clara_is_teacher());
create policy "students read their enrolled classes" on public.classes
  for select using (public.clara_is_active_student_in_class(id));

create policy "teachers manage class enrollment" on public.class_enrollments
  for all using (public.clara_is_teacher_of_class(class_id)) with check (public.clara_is_teacher_of_class(class_id));
create policy "students read own enrollment" on public.class_enrollments
  for select using (student_id = auth.uid());

create policy "teachers read their policy history" on public.class_evidence_policy_events
  for select using (public.clara_is_teacher_of_class(class_id));

create policy "teachers manage own publication versions" on public.published_material_versions
  for all using (public.clara_is_teacher_of_class(class_id)) with check (public.clara_is_teacher_of_class(class_id));

create policy "teachers manage publication attestations" on public.publication_attestations
  for all using (exists (select 1 from public.published_material_versions v where v.id = publication_version_id and public.clara_is_teacher_of_class(v.class_id)))
  with check (exists (select 1 from public.published_material_versions v where v.id = publication_version_id and public.clara_is_teacher_of_class(v.class_id)));
create policy "teachers manage objective attestations" on public.publication_objective_attestations
  for all using (exists (select 1 from public.published_material_versions v where v.id = publication_version_id and public.clara_is_teacher_of_class(v.class_id)))
  with check (exists (select 1 from public.published_material_versions v where v.id = publication_version_id and public.clara_is_teacher_of_class(v.class_id)));
create policy "teachers manage publication items" on public.published_material_items
  for all using (exists (select 1 from public.published_material_versions v where v.id = publication_version_id and public.clara_is_teacher_of_class(v.class_id)))
  with check (exists (select 1 from public.published_material_versions v where v.id = publication_version_id and public.clara_is_teacher_of_class(v.class_id)));
create policy "teachers manage release visibility" on public.student_material_releases
  for all using (public.clara_is_teacher_of_class(class_id)) with check (public.clara_is_teacher_of_class(class_id));
-- Students intentionally have no direct SELECT policy for publication content.
-- They must use clara_student_material_snapshot(), which recomputes both hashes
-- and rejects a mismatch instead of returning possibly altered material.

create policy "students read own responses" on public.student_response_attempts
  for select using (student_id = auth.uid());
create policy "teachers read class responses" on public.student_response_attempts
  for select using (exists (
    select 1 from public.published_material_items i
    join public.published_material_versions v on v.id = i.publication_version_id
    where i.id = published_item_id and public.clara_is_teacher_of_class(v.class_id)
  ));
create policy "teachers manage class reviews" on public.teacher_response_reviews
  for all using (exists (
    select 1 from public.student_response_attempts s
    join public.published_material_items i on i.id = s.published_item_id
    join public.published_material_versions v on v.id = i.publication_version_id
    where s.id = response_attempt_id and public.clara_is_teacher_of_class(v.class_id)
  ));

-- Verification tickets are backend-only and have no browser-facing RLS policy.
revoke all on public.publication_verification_tickets from anon, authenticated;
revoke all on function public.clara_create_publication_verification_ticket(uuid, jsonb, jsonb) from public;
revoke all on function public.clara_publish_student_material(jsonb, uuid) from public;
revoke all on function public.clara_submit_student_response(uuid, jsonb) from public;
revoke all on function public.clara_host_item_validation(uuid) from public;
revoke all on function public.clara_teacher_student_evidence(uuid) from public;
revoke all on function public.clara_attach_host_feedback(uuid, jsonb) from public;
grant execute on function public.clara_student_material_snapshot(uuid) to authenticated;
grant execute on function public.clara_publish_student_material(jsonb, uuid) to authenticated;
grant execute on function public.clara_submit_student_response(uuid, jsonb) to authenticated;
grant execute on function public.clara_teacher_student_evidence(uuid) to authenticated;
grant execute on function public.clara_create_publication_verification_ticket(uuid, jsonb, jsonb) to service_role;
grant execute on function public.clara_attach_host_feedback(uuid, jsonb) to service_role;
grant execute on function public.clara_host_item_validation(uuid) to service_role;
