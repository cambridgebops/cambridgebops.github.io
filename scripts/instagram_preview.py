#!/usr/bin/env python3
"""Offline Instagram preview generation. Never collects events or publishes posts."""
import argparse
from collections import Counter
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
LONDON = ZoneInfo('Europe/London')
SIZE = (1080, 1350)
WEBSITE = 'cambridgebops.github.io'
HASHTAGS = '#CambridgeBops #CambridgeUniversity #CambridgeStudentLife'


def local_start(event):
    value = datetime.fromisoformat(event['starts_at'].replace('Z', '+00:00'))
    if value.tzinfo is None:
        raise ValueError('starts_at must include a timezone offset')
    return value.astimezone(LONDON)


def select_events(data, day):
    # Sort by the actual instant, including during the repeated hour when BST ends.
    return sorted((e for e in data['bops'] if local_start(e).date() == day),
                  key=lambda e: local_start(e).astimezone(timezone.utc))


def event_time(event):
    return 'Time TBC' if 'Time not stated.' in (event.get('details') or '') else local_start(event).strftime('%H:%M')


def display_date(day):
    return f'{day:%A}, {day.day} {day:%B %Y}'


def event_fields(event):
    fields = []
    for key in ('college', 'venue', 'details', 'price', 'host', 'guests', 'dress'):
        value = event.get(key)
        if key == 'details' and value:
            value = value.replace('Time not stated.', '').strip()
        if value is not None and str(value).strip():
            fields.append((key.capitalize(), str(value)))
    return fields


def caption(day, events):
    lines = [f'Cambridge BOPs — {display_date(day)}', '']
    lines += [f'{len(events)} event' + ('s' if len(events) != 1 else '') + ' listed for the day.' if events else 'No events today in the verified listings.', '']
    for event in events:
        lines.append(f"{event_time(event)} — {event['title']} ({event['kind']})")
        lines.extend(f'{label}: {value}' for label, value in event_fields(event))
        lines.append('')
    lines += [f'More at {WEBSITE}. Listings are checked daily; check the source for updates.',
              'Preview only — not yet posted.', '', HASHTAGS]
    return '\n'.join(lines) + '\n'


def font(size, bold=False):
    # DejaVu is free; Pillow searches standard system font directories.
    return ImageFont.truetype('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf', size)


def wrap(text, face, width=920):
    """Wrap by measured pixels, including unbroken words, without dropping text."""
    lines = []
    for paragraph in str(text).split('\n'):
        line = ''
        for word in paragraph.split(' '):
            candidate = f'{line} {word}' if line else word
            if face.getlength(candidate) <= width:
                line = candidate
                continue
            if line:
                lines.append(line)
                line = ''
            for char in word:
                if line and face.getlength(line + char) > width:
                    lines.append(line)
                    line = ''
                line += char
        lines.append(line)
    return lines


def paginate(blocks, capacity=880):
    """Each page contains measured text rows; overflow becomes another slide."""
    pages, page, used = [], [], 0
    for text, size, bold, color in blocks:
        for line in wrap(text, font(size, bold)):
            height = size + 16
            if used + height > capacity:
                pages.append(page)
                page, used = [], 0
            page.append((line, size, bold, color))
            used += height
    if page:
        pages.append(page)
    return pages


def slide_pages(day, events, city):
    counts = Counter(e['kind'] for e in events)
    summary = ' / '.join(f'{n} {kind}' for kind, n in sorted(counts.items()))
    pages = []
    def add(label, blocks, event_index=None):
        for part, rows in enumerate(paginate(blocks)):
            pages.append({'label': label + (' · continued' if part else ''),
                          'rows': rows, 'event_index': event_index})
    add('DAILY LISTINGS', [('What’s on', 86, True, 'fg'),
        (display_date(day), 48, False, 'accent'),
        (f'{len(events)} events' if events else 'No events today', 64, True, 'fg'),
        (summary if events else 'No events listed for this date in the verified data.', 38, False, 'muted')])
    for i, event in enumerate(events):
        add(f"{event_time(event)} / {event['kind']}",
            [(event['title'], 58, True, 'fg')] +
            [(f'{label}: {value}', 36, False, 'fg') for label, value in event_fields(event)], i)
    add('KEEP IN THE LOOP', [('More at', 64, True, 'fg'),
        (WEBSITE, 48, True, 'accent'), ('Listings are checked daily.', 40, False, 'fg'),
        ('Check the source for tickets, access and updates.', 36, False, 'muted'),
        ('Preview only — not yet posted', 32, False, 'muted')])
    return pages


def render(page, city, number, total):
    palette = city['palette']['light']
    image = Image.new('RGB', SIZE, palette['bg'])
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1080, 22), fill=palette['cam'])
    draw.text((80, 75), f"{city['name']} BOPs", font=font(40, True), fill=palette['cam-ink'])
    # Labels can contain long categories, so wrap them too.
    for i, line in enumerate(wrap(page['label'], font(28))):
        draw.text((80, 165 + i * 40), line, font=font(28), fill=palette['accent'])
    y = 280
    for line, size, bold, color in page['rows']:
        draw.text((80, y), line, font=font(size, bold), fill=palette[color])
        y += size + 16
    draw.line((80, 1220, 1000, 1220), fill=palette['rule'], width=2)
    draw.text((80, 1250), 'PREVIEW ONLY', font=font(24), fill=palette['muted'])
    draw.text((850, 1250), f'{number:02} / {total:02}', font=font(24), fill=palette['muted'])
    return image


def generate(day, out=ROOT / 'instagram_previews'):
    source = (ROOT / 'docs/events.json').read_bytes()
    data = json.loads(source)
    city = json.loads((ROOT / 'city.json').read_text(encoding='utf-8'))
    events = select_events(data, day)
    pages = slide_pages(day, events, city)
    directory = Path(out) / day.isoformat()
    directory.mkdir(parents=True, exist_ok=True)
    # Only remove this generator's slide names, so shorter reruns leave no stale slides.
    for old in directory.glob('slide-*.png'):
        if old.stem.removeprefix('slide-').isdigit():
            old.unlink()
    slides = []
    for i, page in enumerate(pages, 1):
        filename = f'slide-{i:02}.png'
        render(page, city, i, len(pages)).save(directory / filename)
        slides.append(filename)
    (directory / 'caption.txt').write_text(caption(day, events), encoding='utf-8')
    manifest = {'date': day.isoformat(), 'timezone': 'Europe/London', 'event_count': len(events),
                'slides': slides, 'caption': 'caption.txt', 'events': events,
                'slide_event_indices': [p['event_index'] for p in pages],
                'source': 'docs/events.json', 'source_generated': data.get('generated'),
                'source_sha256': hashlib.sha256(source).hexdigest(), 'preview_only': True,
                'warnings': []}
    if len(pages) > 20:
        manifest['warnings'].append('More than 20 slides: split into separate carousels before future publishing.')
    if len(caption(day, events)) > 2200:
        manifest['warnings'].append('Caption exceeds 2,200 characters: edit before future publishing.')
    if not str(data.get('generated', '')).startswith(day.isoformat()):
        manifest['warnings'].append('Source generation date differs from target date; review freshness.')
    (directory / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return directory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--date', type=date.fromisoformat, default=None, help='YYYY-MM-DD (default: today in Europe/London)')
    parser.add_argument('--out', type=Path, default=ROOT / 'instagram_previews', help='Output root; a date subdirectory is created')
    args = parser.parse_args()
    print(generate(args.date or datetime.now(LONDON).date(), args.out))


if __name__ == '__main__':
    main()
