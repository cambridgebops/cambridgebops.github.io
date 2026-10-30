# Cambridge Bops

A minimalist listing and map of college bops in Cambridge. Modelled on talks.cam, for the one kind of event talks.cam will never cover.

- **Site:** https://kostadindev.github.io/cambops/ (static page, GitHub Pages from `docs/`)
- **Backend:** Supabase project `cambops` (`xixflbudqcpzjxdijlta`, London region): Postgres with row-level security, reached directly from the page with the publishable key. Supabase does not render HTML on `*.supabase.co`, so the Edge Function `site` only redirects to the page.
- **Daily refresh:** a Claude Code cloud routine with the Supabase connector scrapes venue and society pages each morning, writes approved events, reviews public submissions and prunes old rows. Its prompt is in `docs/ROUTINE.md`; manage it at https://claude.ai/code/routines.

## How it fits together

| Piece | Where | Notes |
|---|---|---|
| Page | `site/index.html` | Vanilla HTML plus Leaflet (OpenStreetMap tiles). Reads bops and the latest `scrape_runs` row through PostgREST, groups them by day, filters by college (select or map pin) and shows a count per college on the map. The form inserts a row with `status = 'pending'`, `kind = 'bop'`. |
| Built page | `docs/index.html` | `scripts/build.sh <supabase-url> <publishable-key>` writes it. Commit and push to deploy. |
| Schema | `supabase/migrations/` | `events` (approved or pending, deduplicated by `source_key`; `college` is constrained to the 31 colleges; `lat`/`lng` reserved for non-college venues) and `scrape_runs` (one row per routine run, shown in the footer). College coordinates live in the page, keyed by the same names. |
| Access rules | same file | Anonymous: read approved upcoming bops, insert pending bops only (no status, source, kind or coordinates of their choosing). Nothing else. The routine writes with the connector's privileges. |
| Routine | `docs/ROUTINE.md` | Four steps: gather, write, review submissions, housekeeping. |

## Working on it

```bash
scripts/build.sh https://xixflbudqcpzjxdijlta.supabase.co <publishable-key>   # after editing site/index.html
open docs/index.html                                                           # works locally too
git commit -am "..." && git push                                               # GitHub Pages redeploys
```

Submissions go live only after the routine's next run, which keeps the public form from being a spam vector. To moderate by hand, change `status` in the Supabase table editor.

Spam the honeypot field does not catch is still inserted as pending and will be rejected by the routine. If that becomes a problem, add a Cloudflare Turnstile check in an Edge Function and route the form through it.
