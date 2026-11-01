# Instagram previews

This is an offline review tool. It only reads `docs/events.json` (all kinds in
`bops`) and branding from `city.json`. It never collects, edits or publishes events,
uses an LLM, contacts Meta, or needs an account, secret or paid service.

## Local use

Use Python 3.12 (3.10+ supported), Pillow and the free DejaVu Sans fonts.
On Ubuntu, install fonts with `sudo apt-get install fonts-dejavu-core`, then:

```sh
python3 -m pip install -r scripts/requirements-instagram.txt
python3 scripts/instagram_preview.py --date 2026-11-01
python3 scripts/instagram_preview.py                 # today in Europe/London
python3 scripts/instagram_preview.py --date 2026-11-01 --out /tmp/previews
python3 -m unittest discover -s tests -p 'test_instagram_preview.py' -v
```

Open `instagram_previews/YYYY-MM-DD/slide-01.png`, then the remaining numbered
PNGs in order. All are 1080 × 1350. Read `caption.txt` alongside them and check
`manifest.json`: it records every selected event unchanged, the input generation
time and SHA-256, slide order, event-to-slide indices (zero-based), and warnings.
The output directory is ignored by Git. Rerunning replaces the day's generated
files and removes stale numbered slides; use a separate output root to retain a version.

Events are selected by London calendar day and ordered by instant. Nothing is
merged. “Time not stated.” becomes “Time TBC” in graphics and captions, while
other details are retained. Cover, individual event cards and closing slides use
the light city palette. Long text flows into continuation slides at readable font
sizes; no event or long detail is silently dropped. Empty days have a cover saying
“No events today” and a closing slide. Styling, font sizes, wrapping and pagination
are in `scripts/instagram_preview.py` (`slide_pages`, `render`, `paginate`). No remote
fonts or images are fetched.

## GitHub Actions

After committing the implementation, open **Actions → Instagram preview → Run
workflow**. Leave date blank for today or enter `YYYY-MM-DD`. Download the
`instagram-preview-<run number>` artifact from the completed run, unzip it, and
review the PNGs, caption and manifest. Artifacts last 14 days. Automatic GitHub triggers are disabled; this workflow is manual only. For a
recurring Codex cloud task, schedule the command below in Codex after the daily
event refresh. Inspect the source generation time and freshness warning.
The workflow is independent of deployment and only has read permission.

## Limits and future publishing

Data is only as current as the checked-out JSON. An empty date means no verified
listings, not proof that no event exists. Historical dates outside this JSON's
window cannot be reconstructed by this tool. The renderer uses DejaVu Sans rather
than the site's remote web fonts; unusual characters unsupported by that font may
need a future bundled font. Review every slide before use.

All events and caption details are retained, even when a busy day exceeds a single
Instagram carousel or caption limit. The manifest warns above 20 slides or 2,200
caption characters; a reviewer would need to split/edit these before publishing.
Actual publishing is deliberately absent. A separate future task would need an
approved account/API integration, secure credentials, media hosting/upload,
platform limit validation, explicit approval and retry/duplicate protection.

## Codex cloud daily task

Use this repository and the prepared cloud environment. Schedule daily at 08:30
Europe/London (after the documented 06:00 UTC data refresh). Task instructions:

> Run `python3 scripts/instagram_preview.py` from the repository root using the
> current `docs/events.json`. Do not collect, edit or publish events. Review the
> generated manifest for freshness and platform-limit warnings. Report the event
> count and caption, and attach all numbered PNGs, caption.txt and manifest.json
> as downloadable task outputs using the task's supported attachment mechanism.
> No Instagram publishing.

The cloud environment setup alone does not create a recurring task or retain live
processes. Create the schedule in Codex's scheduling UI if available. This chat
cannot register it automatically.
