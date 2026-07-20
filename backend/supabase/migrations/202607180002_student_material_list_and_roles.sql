-- Student material discovery exposes only immutable release metadata.  Content
-- remains available exclusively through the integrity-checking snapshot RPC.
alter table public.student_material_releases
  add column if not exists title_snapshot text;

update public.student_material_releases r
set title_snapshot = v.title
from public.published_material_versions v
where v.id = r.publication_version_id
  and r.title_snapshot is null;

alter table public.student_material_releases
  alter column title_snapshot set not null;

create or replace function public.clara_create_release_after_publish()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  if old.status = 'draft' and new.status = 'published' then
    insert into public.student_material_releases (publication_version_id, class_id, title_snapshot)
    values (new.id, new.class_id, new.title);
  end if;
  return new;
end;
$$;

-- RLS, rather than a class identifier supplied by the browser, decides whether
-- a student can discover a release.  The row carries no pack content.
create policy "students list active releases in their enrolled classes"
  on public.student_material_releases
  for select
  using (is_active and public.clara_is_active_student_in_class(class_id));

-- The client needs only its own role to choose the appropriate experience.
-- This does not grant access to any other profile or role-management action.
create policy "users read own Clara role"
  on public.clara_user_roles
  for select
  using (user_id = auth.uid());
