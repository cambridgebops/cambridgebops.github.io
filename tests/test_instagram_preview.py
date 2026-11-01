"""Offline preview contract, pagination, timezone and real file checks."""
import copy
from datetime import date
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import instagram_preview as preview

DAY = date(2026, 11, 1)


def event(**updates):
    result = {'title': 'College social', 'kind': 'bop', 'starts_at': '2026-11-01T21:00:00+00:00'}
    result.update(updates)
    return result


class TestInstagramPreview(unittest.TestCase):
    def test_no_events(self):
        self.assertEqual(preview.select_events({'bops': []}, DAY), [])
        self.assertIn('No events today', preview.caption(DAY, []))
        city = json.loads((preview.ROOT / 'city.json').read_text())
        pages = preview.slide_pages(DAY, [], city)
        self.assertEqual(len(pages), 2)
        self.assertTrue(any('No events today' in r[0] for r in pages[0]['rows']))

    def test_one_event_missing_optional_fields(self):
        e = event()
        self.assertEqual(preview.select_events({'bops': [e]}, DAY), [e])
        self.assertEqual(preview.event_fields(e), [])
        self.assertIn('21:00 — College social (bop)', preview.caption(DAY, [e]))

    def test_multiple_categories_no_merging_or_mutation(self):
        events = [event(kind=k, starts_at=f'2026-11-01T{20-i}:00:00Z')
                  for i, k in enumerate(('bop', 'formal', 'ball', 'other'))]
        events.append(copy.deepcopy(events[0]))
        original = copy.deepcopy(events)
        selected = preview.select_events({'bops': events}, DAY)
        self.assertEqual(len(selected), 5)
        self.assertEqual([e['kind'] for e in selected], ['other', 'ball', 'formal', 'bop', 'bop'])
        self.assertEqual(events, original)

    def test_unstated_time(self):
        e = event(details='Time not stated. Tickets at the door.')
        text = preview.caption(DAY, [e])
        self.assertIn('Time TBC', text)
        self.assertIn('Tickets at the door.', text)
        self.assertNotIn('21:00', text)
        self.assertNotIn('Time not stated.', text)

    def test_timezone_summer_midnight_and_winter(self):
        e = event(starts_at='2026-07-01T23:30:00Z')
        self.assertEqual(preview.select_events({'bops': [e]}, date(2026, 7, 2)), [e])
        self.assertEqual(preview.event_time(e), '00:30')
        self.assertEqual(preview.select_events({'bops': [e]}, date(2026, 7, 1)), [])
        self.assertEqual(preview.event_time(event()), '21:00')

    def test_dst_repeated_hour_sorts_by_instant(self):
        earlier = event(starts_at='2026-10-25T01:45:00+01:00')
        later = event(starts_at='2026-10-25T01:15:00+00:00')
        self.assertEqual(preview.select_events({'bops': [later, earlier]}, date(2026, 10, 25)), [earlier, later])

    def test_naive_time_rejected(self):
        with self.assertRaises(ValueError):
            preview.local_start(event(starts_at='2026-11-01T21:00:00'))

    def test_long_text_paginates_without_loss(self):
        text = 'Long title ' * 100 + 'x' * 300
        city = json.loads((preview.ROOT / 'city.json').read_text())
        e = event(title=text, details='Full details ' * 400)
        pages = preview.slide_pages(DAY, [e], city)
        event_pages = [p for p in pages if p['event_index'] == 0]
        self.assertGreater(len(event_pages), 1)
        rows = [r for p in event_pages for r in p['rows']]
        self.assertEqual(''.join(r[0] for r in rows if r[1] == 58).replace(' ', ''), text.replace(' ', ''))
        self.assertTrue(all(sum(r[1] + 16 for r in p['rows']) <= 880 for p in pages))
        self.assertTrue(all(preview.font(r[1], r[2]).getlength(r[0]) <= 920 for r in rows))

    def test_caption_deterministic_exact_fields(self):
        events = [event(college="King's", venue='Bar', price='£5', details='Theme: stars.')]
        first = preview.caption(DAY, events)
        self.assertEqual(first, preview.caption(DAY, events))
        for value in ("King's", 'Bar', '£5', 'Theme: stars.', '#CambridgeBops'):
            self.assertIn(value, first)

    def test_output_files_and_rerun_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as out:
            root = Path(tmp)
            (root / 'docs').mkdir()
            (root / 'city.json').write_bytes((preview.ROOT / 'city.json').read_bytes())
            datafile = root / 'docs/events.json'
            for events in ([event(), event(kind='formal')], [event()], []):
                datafile.write_text(json.dumps({'bops': events, 'generated': '2026-11-01T10:00:00Z'}))
                with patch.object(preview, 'ROOT', root):
                    directory = preview.generate(DAY, out)
                manifest = json.loads((directory / 'manifest.json').read_text())
                self.assertEqual(manifest['events'], events)
                self.assertEqual(manifest['event_count'], len(events))
                self.assertEqual(sorted(p.name for p in directory.glob('*.png')), manifest['slides'])
                self.assertEqual((directory / 'caption.txt').read_text(), preview.caption(DAY, events))
                for name in manifest['slides']:
                    with Image.open(directory / name) as image:
                        self.assertEqual(image.size, (1080, 1350))
                        self.assertEqual(image.format, 'PNG')

    def test_cli_real_data(self):
        data = json.loads((preview.ROOT / 'docs/events.json').read_text())
        day = preview.local_start(data['bops'][0]).date() if data['bops'] else DAY
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run([sys.executable, str(preview.ROOT / 'scripts/instagram_preview.py'),
                                     '--date', day.isoformat(), '--out', tmp], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((Path(tmp) / day.isoformat() / 'manifest.json').read_text())
            self.assertEqual(manifest['event_count'], len(preview.select_events(data, day)))
