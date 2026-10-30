# Cambridge Bops

A static page that lists and maps every college bop in Cambridge for the next fortnight, in the spirit of talks.cam. No backend: a Claude Code cloud routine checks college calendars, ents pages and student press every morning, reviews submissions, rewrites one JSON file and pushes it.

- **Site:** https://kostadindev.github.io/cambops/ (GitHub Pages from `docs/`)
- **Data:** `docs/events.json`, rewritten daily by the routine. The page reads it and shows the next 14 days in Cambridge time.
- **Submissions:** "Add a bop" on the page opens a prefilled GitHub issue (`.github/ISSUE_TEMPLATE/bop.yml`, label `bop-submission`). The routine reviews open issues, adds the good ones to the file and closes them with a comment.
- **Routine:** prompt in `docs/ROUTINE.md`; manage it at https://claude.ai/code/routines.

## Layout

| File | Role |
|---|---|
| `docs/index.html` | The whole page: Cambridge blue palette, "Tonight" band, Leaflet map of colleges with a bop count per pin (OpenStreetMap tiles), college filter, day-by-day list with price, guest policy, dress code and links, and the submission form. |
| `docs/events.json` | `{generated, sources, bops: [...]}`. Fields per bop: title, starts_at, ends_at, college, venue, host, price, guests, dress, url, details, source. |
| `.github/ISSUE_TEMPLATE/bop.yml` | The submission form on GitHub. Field ids match the query parameters the page prefills. |
| `docs/ROUTINE.md` | The routine's instructions: check calendars, review issues, write the JSON, commit and push. |

## Working on it

Edit `docs/index.html` directly, open it in a browser (`python3 -m http.server -d docs 8765`, since `fetch` needs a server), commit and push. GitHub Pages redeploys on push. To change what the routine does, edit `docs/ROUTINE.md` and paste the same text into the routine.

## Hosting setup (one time)

```bash
gh repo create kostadindev/cambops --public --source=. --remote=origin --push
gh api -X POST repos/kostadindev/cambops/pages -f build_type=legacy -f 'source[branch]=main' -f 'source[path]=/docs'
```

Then add the repository as the routine's source so it can commit, and allow it to push to `main` (or let it open pull requests).
