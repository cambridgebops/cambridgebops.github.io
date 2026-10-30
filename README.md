# Cambridge Bops

A minimalist listing of the small things on in Cambridge: bops, gigs, pub quizzes, formals, comedy nights and parties. Modelled on talks.cam, for everything talks.cam does not cover.

- **Site:** https://kostadindev.github.io/cambops/ (static page, GitHub Pages from `docs/`)
- **Backend:** Supabase project `cambops` (`xixflbudqcpzjxdijlta`, London region): Postgres with row-level security, reached directly from the page with the publishable key. Supabase does not render HTML on `*.supabase.co`, so the Edge Function `site` only redirects to the page.
- **Daily refresh:** a Claude Code cloud routine with the Supabase connector scrapes venue and society pages each morning, writes approved events, reviews public submissions and prunes old rows. Its prompt is in `docs/ROUTINE.md`; manage it at https://claude.ai/code/routines.

## How it fits together

| Piece | Where | Notes |
|---|---|---|
| Page | `site/index.html` | Vanilla HTML, no build step beyond filling in the URL and key. Reads `events` and the latest `scrape_runs` row through PostgREST. The form inserts a row with `status = 'pending'`. |
| Built page | `docs/index.html` | `scripts/build.sh <supabase-url> <publishable-key>` writes it. Commit and push to deploy. |
| Schema | `supabase/migrations/` | `events` (approved or pending, deduplicated by `source_key`) and `scrape_runs` (one row per routine run, shown in the footer). |
| Access rules | same file | Anonymous: read approved upcoming events, insert pending submissions only. Nothing else. The routine writes with the connector's privileges. |
| Routine | `docs/ROUTINE.md` | Four steps: gather, write, review submissions, housekeeping. |

## Working on it

```bash
scripts/build.sh https://xixflbudqcpzjxdijlta.supabase.co <publishable-key>   # after editing site/index.html
open docs/index.html                                                           # works locally too
git commit -am "..." && git push                                               # GitHub Pages redeploys
```

Submissions go live only after the routine's next run, which keeps the public form from being a spam vector. To moderate by hand, change `status` in the Supabase table editor.

Spam the honeypot field does not catch is still inserted as pending and will be rejected by the routine. If that becomes a problem, add a Cloudflare Turnstile check in an Edge Function and route the form through it.
