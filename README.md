# Cambridge Bops

A static page that lists and maps every college bop in Cambridge for the next fortnight, in the spirit of talks.cam. No backend and no submission form: a Claude Code cloud routine checks college calendars, ents pages and student press every morning, keeps only what it can verify, rewrites one JSON file and pushes it.

- **Site:** https://cambridgebops.github.io/ (GitHub Pages, deployed from `docs/` by the test workflow)
- **Data:** `docs/events.json`, rewritten daily by the routine. The page reads it and shows the next 14 days in Cambridge time.
- **Routine:** prompt in `docs/ROUTINE.md`; manage it at https://claude.ai/code/routines.

## Layout

| File | Role |
|---|---|
| `docs/index.html` | The whole page: Cambridge blue palette, a sticky filter bar (When segmented control, college chips with counts, result line with Clear), "Tonight" band, Leaflet map of colleges with a bop count per pin (OpenStreetMap tiles), and a day-by-day list with price, guest policy, dress code, end time and source link. |
| `docs/events.json` | `{generated, sources, bops: [...]}`. Fields per bop: title, starts_at, ends_at, college, venue, host, price, guests, dress, url, details, source. |
| `docs/sources.json` | The registry of verified sources, about 150 across the 31 colleges: JCR, MCR and ents sites, calendars, termcards, college events pages, SU listings, student press, and each college's JCR or ents Instagram. The routine reads only these. |
| `docs/ROUTINE.md` | The routine's instructions: check every registered source, write the JSON, run the tests, commit and push. |
| `tests/` | Unit tests for the data contract (`events.json`), the registry (`sources.json`) and the page. |
| `scripts/check_sources.py` | Reachability test: probes every registered URL and reports colleges without a working source. |
| `.github/workflows/deploy.yml` | Runs the tests on every push and deploys `docs/` to GitHub Pages only when they pass. |

## Working on it

Edit `docs/index.html` directly, open it in a browser (`python3 -m http.server -d docs 8765`, since `fetch` needs a server), run the tests, commit and push. GitHub Pages redeploys when the tests pass.

```bash
python3 -m unittest discover -s tests      # data contract, registry, page: must pass before any deploy
python3 scripts/check_sources.py           # are all 31 colleges' sources still reachable?
``` To change what the routine does, edit `docs/ROUTINE.md` and paste the same text into the routine.

## Hosting

The repository lives in the `cambridgebops` organization and is served by GitHub Pages at https://cambridgebops.github.io/. Pushes to `main` run the tests and deploy `docs/`. The daily routine commits to the same repository.
