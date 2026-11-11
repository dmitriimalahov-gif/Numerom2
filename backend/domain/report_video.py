"""Timed visual script from the exact audio that will be muxed, never TTS estimates."""
import hashlib
import math
import re

from domain.full_report import _cardinal, _speech_formula
from services.report_files import read_json

FPS = 24
GAP = 0.38

def words(text):
    text = _speech_formula(str(text)).lower().replace('ё', 'е')
    text = re.sub(r'\b[0-9]{1,4}\b', lambda m: _cardinal(int(m[0])), text)
    return ' '.join(re.findall('[а-яa-z0-9]+', text))

def _mentions(text, section):
    """Ordered references to saved fields; numeric coincidences are not targets."""
    normalized = words(text)
    candidates = []
    for index, value in enumerate(section.get('values', [])):
        label = str(value.get('label', ''))
        aliases = [label]
        # The age range explains a task; it is not part of its spoken name.
        if str(value.get('key', '')).startswith('problem') and '·' in label:
            aliases.append(label.split('·', 1)[0])
        # Short names occur in the overview, but require the actual saved result.
        short = {'soul': 'душа', 'mind': 'ум', 'destiny': 'судьба', 'helping_mind': 'помогающий ум',
                 'life_path': 'жизненный путь', 'ruling': 'предназначение'}.get(value.get('key'))
        if short and isinstance(value.get('value'), (int, str)):
            aliases.append(short + ' ' + str(value['value']))
        for alias in set(words(a) for a in aliases):
            if not alias:
                continue
            for match in re.finditer(r'(?<!\w)' + re.escape(alias) + r'(?!\w)', normalized):
                candidates.append((match.start(), match.end(), index))
    # Narrated codes are ordered positions, including repeated digits. Do not
    # confuse the same number elsewhere in a sentence with a code position.
    values = section.get('values', [])
    code = None
    if section.get('id') == 'fractal' and len(values) == 4 and 'фрактал' in normalized:
        code = [words(str(value.get('value'))) for value in values]
    elif section.get('id') in ('square', 'vedic-yantra') and len(values) == 9 and 'расположение ячеек' in normalized:
        code = [words(str(value.get('label', '')).split('·')[0]) for value in values]
    if code and all(code):
        sequence = ' '.join(code)
        for match in re.finditer(r'(?<!\w)' + re.escape(sequence) + r'(?!\w)', normalized):
            position = match.start()
            for index, digit in enumerate(code):
                candidates.append((position, position + len(digit), index))
                position += len(digit) + 1
    # "Помогающее число ума" must not also select its nested "число ума".
    chosen = []
    for start, end, index in sorted(candidates, key=lambda c: (-(c[1] - c[0]), c[0])):
        if not any(start < other_end and end > other_start for other_start, other_end, _ in chosen):
            chosen.append((start, end, index))
    return normalized, sorted(chosen)

def _focus_cues(cue, section, offset, first_frame, end_frame, fps):
    normalized, mentions = _mentions(cue['text'], section)
    timed_words = cue.get('words') or []
    # Optional ASR word timings may be supplied by a newer verified recording.
    # Never call character interpolation word alignment.
    exact = bool(timed_words) and words(' '.join(str(w.get('word', '')) for w in timed_words)) == normalized
    spans, position = [], 0
    if exact:
        previous_end = float(cue['start'])
        for word in timed_words:
            start, end = float(word['start']), float(word['end'])
            if not math.isfinite(start + end) or not float(cue['start']) <= start < end <= float(cue['end']) + .001 or start < previous_end - .001:
                raise ValueError('Word timing outside its narration cue')
            previous_end = end
            token = words(word['word'])
            spans.append((position, position + len(token), start))
            position += len(token) + 1
    starts = []
    for start, _, index in mentions:
        seconds = next((at for a, b, at in spans if a <= start < b), None) if exact else None
        if seconds is None:
            seconds = float(cue['start']) + (float(cue['end']) - float(cue['start'])) * start / max(1, len(normalized))
        frame = max(first_frame, min(end_frame - 1, round((offset + seconds) * fps)))
        # Several names can round to one frame; prefer the later spoken name.
        if starts and starts[-1][0] == frame:
            starts[-1] = (frame, index)
        else:
            starts.append((frame, index))
    return [{'fromFrame': frame, 'durationInFrames': (starts[i + 1][0] if i + 1 < len(starts) else end_frame) - frame,
             'focusIndex': index, 'timingSource': 'asr-word' if exact else 'estimated'}
            for i, (frame, index) in enumerate(starts)]

def cue_segments(meta, section, fps=FPS, *, summary=False, limit=None):
    """`limit` is the chapter's frame count. Recordings sped up 1.2× scale their recognised cues by 1/1.2,
    while the chapter length is the measured audio: the last cue may round one frame past it."""
    labels = [(i, words(value['label'])) for i, value in enumerate(section.get('values', []))]
    result, offset, active = [], 0.0, None
    for check in meta.get('segments', []):
        duration = float(check['seconds'])
        if not math.isfinite(duration) or duration <= 0:
            raise ValueError('Invalid narration timing')
        cues = check.get('cues')
        timing_source = 'asr' if cues else 'estimated'
        if not cues:
            # Older verified audio carries fragment timing. Divide only that
            # fragment into readable subtitles; no stretching of the audio.
            sentences = [t for t in re.split(r'(?<=[.!?;])\s+', check['text']) if t]
            total = sum(len(t) for t in sentences) or 1
            at = 0.0
            cues = []
            for sentence in sentences:
                seconds = duration * len(sentence) / total
                cues.append({'start': at, 'end': at + seconds, 'text': sentence})
                at += seconds
        previous_end = 0.0
        for cue in cues:
            start, end = float(cue['start']), float(cue['end'])
            if not 0 <= start < end <= duration + .1 or start < previous_end - .001:
                raise ValueError('Narration cue outside its audio fragment')
            previous_end = end
            normalized = ' ' + words(cue['text']) + ' '
            found = [i for i, label in labels if label and ' ' + label + ' ' in normalized]
            if summary:
                # The introduction moves between calculations. A cue about
                # the fractal or calendar must not retain a personal-number
                # highlight from an earlier sentence; multiple labels are
                # an overview, not a reliable single target.
                active = found[0] if len(found) == 1 else None
            elif found:
                active = found[0]
            # Round shared boundaries, not independent lengths: rounding a
            # length can otherwise extend one subtitle into the next frame.
            first_frame = round((offset + start) * fps)
            end_frame = round((offset + end) * fps)
            if limit is not None:
                if first_frame >= limit:
                    break
                end_frame = min(end_frame, limit)
            if end_frame <= first_frame:
                raise ValueError('Narration cue is shorter than one video frame')
            item = {'fromFrame': first_frame, 'durationInFrames': end_frame - first_frame,
                    'text': cue['text'], 'timingSource': timing_source}
            if active is not None:
                item['focusIndex'] = active
            focus = _focus_cues(cue, section, offset, first_frame, end_frame, fps)
            if focus:
                item['focusCues'] = focus
                if not summary:
                    active = focus[-1]['focusIndex']
            result.append(item)
        offset += duration + GAP
    return result

def build_manifest(report, voice, *, clip_ids=None, verify_hash=True):
    chapters = []
    sections = report['sections']
    for clip in report['narration']:
        if clip_ids is not None and clip['id'] not in clip_ids:
            continue
        if voice.state(clip)['status'] != 'ready':
            raise ValueError('Every included audio chapter must be ready')
        target = voice.folder(clip['hash'])
        audio = target / 'audio.m4a'
        meta = read_json(target / 'ready.json')
        if not meta or not meta.get('segments') or audio.is_symlink():
            raise ValueError('Incomplete audio metadata')
        if verify_hash and hashlib.sha256(audio.read_bytes()).hexdigest() != meta.get('sha256'):
            raise ValueError('Audio integrity mismatch')
        seconds = float(meta['seconds'])
        if not math.isfinite(seconds) or not 0 < seconds <= 7200:
            raise ValueError('Invalid chapter length')
        if not isinstance(meta['segments'], list) or not 1 <= len(meta['segments']) <= 256:
            raise ValueError('Invalid audio fragment count')
        measured = sum(float(s['seconds']) for s in meta['segments']) + GAP * (len(meta['segments']) - 1)
        if not math.isfinite(measured) or abs(measured - seconds) > .12:
            raise ValueError('Audio fragment timing does not match the completed recording')
        candidates = [s for s in sections if clip['id'] == 'full-report-' + s['id'] or clip['id'].startswith('full-report-' + s['id'] + '-')]
        section = max(candidates, key=lambda s: len(s['id'])) if candidates else (
            next((s for s in sections if s['id'] == 'personal'), None) if clip['id'] == 'full-report-summary' else None)
        frames = math.ceil(seconds * FPS)
        chapter = {'id': clip['id'], 'title': clip['title'], 'audioPath': str(audio), 'durationInFrames': frames,
            'segments': cue_segments(meta, section or {}, summary=clip['id'] == 'full-report-summary', limit=frames)}
        # A chapter with no report section (calculation limits) shows its own title; the
        # renderer rejects an empty section object.
        if section:
            chapter['section'] = section
        chapters.append(chapter)
    if not chapters or sum(c['durationInFrames'] for c in chapters) > FPS * 14400:
        raise ValueError('Invalid complete video duration')
    return {'version': 1, 'title': report['title'], 'birthDate': report['birth_date'], 'asOfDate': report['as_of_date'],
            'fps': FPS, 'width': 1280, 'height': 720, 'chapters': chapters, 'report': report}
