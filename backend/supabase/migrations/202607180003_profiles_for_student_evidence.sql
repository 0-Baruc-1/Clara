-- A deliberately small, explicit display-name source. Auth metadata is not a
-- curriculum or roster contract, so Clara does not depend on it.
create table if not exists public.profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  full_name text not null check (char_length(trim(full_name)) > 0),
  created_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

create policy "users read own profile"
  on public.profiles for select
  using (user_id = auth.uid());

-- A teacher sees only names of active students enrolled in one of their classes.
create policy "teachers read enrolled student profiles"
  on public.profiles for select
  using (
    exists (
      select 1
      from public.class_enrollments e
      join public.classes c on c.id = e.class_id
      where e.student_id = profiles.user_id
        and e.status = 'active'
        and c.teacher_id = auth.uid()
        and public.clara_is_teacher()
    )
  );

grant select on public.profiles to authenticated;

-- PostgreSQL cannot change a RETURNS TABLE shape in place. Recreate this
-- teacher-only RPC with the optional profile name. LEFT JOIN keeps evidence
-- rows usable when a profile has not yet been seeded.
drop function public.clara_teacher_student_evidence(uuid);

create function public.clara_teacher_student_evidence(p_class_id uuid)
returns table (
  student_id uuid,
  student_full_name text,
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
    p.full_name,
    o.objective_code,
    count(distinct d.version_id)::integer as declared_publication_count,
    count(distinct i.id)::integer as attested_item_count,
    count(distinct r.published_item_id) filter (where r.id is not null)::integer as distinct_items_responded,
    c.evidence_min_distinct_items,
    case when count(distinct r.published_item_id) filter (where r.id is not null) >= c.evidence_min_distinct_items
      then 'evidencia_suficiente' else 'evidencia_insuficiente' end
  from students s
  left join public.profiles p on p.user_id = s.student_id
  cross join objective_universe o
  join public.classes c on c.id = p_class_id
  left join declared d on d.objective_code = o.objective_code
  left join attested_items i on i.evidence_objective_code = o.objective_code
  left join public.student_response_attempts r on r.published_item_id = i.id and r.student_id = s.student_id
  group by s.student_id, p.full_name, o.objective_code, c.evidence_min_distinct_items;
end;
$$;

grant execute on function public.clara_teacher_student_evidence(uuid) to authenticated;
