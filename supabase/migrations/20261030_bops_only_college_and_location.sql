-- Applied to project xixflbudqcpzjxdijlta on 2026-10-30 (as migration bops_only_college_and_location).
alter table public.events
  add column college text check (college is null or college in (
    'Christ''s','Churchill','Clare','Clare Hall','Corpus Christi','Darwin','Downing','Emmanuel','Fitzwilliam','Girton',
    'Gonville & Caius','Homerton','Hughes Hall','Jesus','King''s','Lucy Cavendish','Magdalene','Murray Edwards','Newnham',
    'Pembroke','Peterhouse','Queens''','Robinson','St Catharine''s','St Edmund''s','St John''s','Selwyn','Sidney Sussex',
    'Trinity','Trinity Hall','Wolfson')),
  add column lat double precision check (lat is null or lat between 51.9 and 52.5),
  add column lng double precision check (lng is null or lng between -0.2 and 0.4);

alter table public.events alter column kind set default 'bop';

-- The public form may only insert pending bops; it cannot choose status, source, kind or coordinates.
drop policy "public submits pending events" on public.events;
create policy "public submits pending bops" on public.events
  for insert to anon, authenticated
  with check (status = 'pending' and source = 'submission' and source_key is null and kind = 'bop' and lat is null and lng is null);
