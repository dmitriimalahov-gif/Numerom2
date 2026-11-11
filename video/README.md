# NumerOM narrated report video

An isolated Remotion renderer for saved report snapshots and existing, verified
male narration. It does not calculate numerology, generate speech, or call a
model. The backend owns authorization, payment, audio verification and publishing
the completed file. A successful CLI exit means a local video was rendered; it
does not mark a purchased report ready on its own.

## Installation

Node 22 is required. Remotion packages use the same exact version in the lockfile.
Installation is the only step that needs network access:

```sh
cd video
npm ci --ignore-scripts --no-fund --no-audit
npm run prepare-browser
npm test
```

`prepare-browser` downloads the official, separate Chrome Headless Shell into
this package's `node_modules/.remotion/`. It does not open or control the user's
Chrome. The saved browser path, browser binary, compiled bundles and dependency
cache are local, ignored files. Rendering fails if the prepared browser is absent
or is not the expected version; it never downloads a replacement mid-render.

## CLI

From the repository root:

```sh
node video/render.mjs \
  --input /absolute/private/manifest.json \
  --output /absolute/private/report.pending.mp4 \
  --still /absolute/private/preview.png
```

Use `--preview-seconds 8` for a short QA render from the beginning. The optional
still is at three seconds, or the final frame of a shorter preview. Existing
outputs are never overwritten. Exit code 0 is success; other exits retain a
diagnostic on stderr and remove the CLI's incomplete pending MP4. Stdout contains
only JSON progress records such as `{"progress":42}`. SIGINT/SIGTERM cancel the
render and close its browser and resource server.

## Manifest version 1

```json
{
  "version": 1,
  "title": "Полный разбор NumerOM",
  "birthDate": "10.01.1982",
  "asOfDate": "2026-10-23",
  "fps": 24,
  "width": 1280,
  "height": 720,
  "motion": "calm",
  "report": {"sections": [], "raw": {}},
  "chapters": [{
    "id": "full-report-personal",
    "title": "Личные числа",
    "audioPath": "/absolute/private/verified.m4a",
    "durationInFrames": 240,
    "segments": [{
      "fromFrame": 0,
      "durationInFrames": 240,
      "text": "Ваше число души — один.",
      "focusIndex": 0,
      "timingSource": "asr",
      "focusCues": [{
        "fromFrame": 24,
        "durationInFrames": 216,
        "focusIndex": 0,
        "timingSource": "estimated"
      }]
    }],
    "section": {
      "id": "personal",
      "title": "Личные числа",
      "paragraphs": [],
      "values": [{"key": "soul", "label": "Число души", "value": 1, "meaning": "Инициатива."}]
    }
  }]
}
```

`report` is the full saved snapshot used only on the Node side to derive a
canonical `section.diagram` through `packages/full-report/schematics.js`. It is
removed from browser props. A previously derived diagram can also be supplied.
Missing raw data uses the section's existing matrix, bars, series or value cards.
Null-valued synthesis entries become text cards, never zero-score graphs.

Every chapter's duration comes from verified audio metadata; total video length
is the exact sum of these frame counts. Segment positions are chapter-relative,
ordered, non-overlapping and within its duration. Round adjacent boundaries
together to avoid one-frame overlaps. Gaps retain the last caption. Long captions
are divided into short pages without dropping words, weighted by text length
within the supplied segment timing. `timingSource: "asr"` means the caption has
verified speech-recognition boundaries; `"estimated"` means older audio only
has fragment boundaries. Neither alone implies word-level forced alignment.

Optional `focusCues` give the focus track its own timing. Each cue's `fromFrame`
is chapter-relative and its duration must fit inside its parent segment. Cues
must be ordered and non-overlapping. One caption can therefore highlight several
spoken values in order, including separate positions containing the same digit.
Legacy manifests containing only `focusIndex` still work. The backend identifies
saved field labels and exact saved code sequences; it does not select a field
because an unrelated sentence happens to contain the same number.

The current recordings retain ASR segment boundaries. Within a segment, focus
positions are estimated from the position of each field name in that segment's
text and marked `"estimated"`. If verified audio metadata supplies matching,
ordered word timestamps, the backend uses those times and marks the focus cue
`"asr-word"`. It never describes estimated timing as exact word alignment.

`focusIndex` is zero-based: matrix order is exactly the saved `1,4,7 / 2,5,8 /
3,6,9`; line order is three horizontals, three verticals, two diagonals. Other
schemes use their saved entry order. Out-of-range focus leaves the scheme
unhighlighted. Long tables page around the focused entry; the 100-year graph
retains all saved points. Tall canonical schemes have a magnified active viewport
and full thumbnail alongside; viewport cropping never redraws or changes values.

## Frame-based direction

The active number appears with a short downward movement; saved cells enter in
order. Active verticals, horizontals and diagonals are traced on the canonical
diagram. Camera movement takes 18 frames and starts from its current position
when a new cue interrupts it. It zooms back out when narration leaves the active
field. Brief enumerations stay on the overview with the correct field highlighted,
so the camera does not chase half-second mentions. The full scheme remains visible in a thumbnail with the current viewport
outlined, including all points of a 100-year graph. Values never count up through
invented numbers, shuffle or change their saved order.

All movement depends only on the Remotion frame, using no CSS transitions,
wall-clock timers or randomness. Optional `motion: "reduced"` keeps useful
framing, subtitles and highlights but removes movement and fades. Chapter counts
and lengths come from the manifest; adding report sections requires no scene
count change. The shared diagram remains the source of geometry, labels and
numeric data.

Direction, cue ordering, interrupted camera moves, reduced motion and unchanged
canonical labels/routes are covered by `npm test`. The author triangle retains all
45 saved positions and the human-name scheme retains all seven positions in the
same geometry as the existing mobile/web diagrams; their focus follows entry IDs,
not numeric coincidences. Backend cue construction has
pure tests in `backend/tests/test_report_video_directing.py`.

## Local rendering and boundaries

- The renderer binds an ephemeral HTTP server to `127.0.0.1` only. Random
  capability paths expose only pre-opened allowlisted audio files and the
  compiled video bundle. No project directory, manifest or raw report is served.
- HTTP Host and Origin checks, a restrictive resource policy, safe byte-range
  responses and no-store headers protect the local resource interface.
- Fonts are system fonts, the logo is the existing local NumerOM SVG, and diagrams
  are canonical local SVG. No remote assets, services or browser downloads are
  used during rendering; browser web security remains enabled.
- Output is 1280×720, 24 fps, H.264/yuv420p and AAC. Remotion's MP4 finalizer puts
  the `moov` atom first for Fast Start. Browser rendering and FFmpeg encoding each
  use one worker/thread. Caches stay inside `video/.cache`.
- The caller must keep manifests, voices and completed personal reports private
  and only serve them after ownership and payment checks. This CLI deliberately
  does not implement or bypass backend authorization.

Official APIs used: [bundle](https://www.remotion.dev/docs/bundle),
[ensureBrowser](https://www.remotion.dev/docs/renderer/ensure-browser),
[openBrowser](https://www.remotion.dev/docs/renderer/open-browser), and
[renderMedia](https://www.remotion.dev/docs/renderer/render-media).

## Runtime location on macOS

On this macOS 27 host, processes started from the Desktop checkout intermittently
stalled, including plain Node/Python commands and Chromium captures. The same
native renderer completed an actual H.264/AAC preview from an isolated runtime in
`/private/tmp`, with no Chromium security changes. Keep production runtime,
working directory, browser and bundle cache outside protected Desktop folders.
After relocating, regenerate `video/.cache/browser.json` with `prepare-browser`
or update its `path` to the already copied official browser inside that runtime's
`video/node_modules`; the renderer validates that boundary. Do not treat the
earlier stalled captures alone as evidence of a Chromium engine defect. A bounded
render-only readiness timer is covered by `frame-scheduler.mjs`.

The worker selects `NUMEROM_NODE_PATH` when configured, then the installed Node 22
path before falling back to `PATH`. A service should set an absolute Node 22 path
and its runtime working directory explicitly. Moving the runtime does not require
controlling the user's Chrome or changing its security settings.

## Optional isolated Linux runtime

The Linux renderer uses the same real Remotion composition and every video frame,
not a slideshow of PDF screenshots. It requires an already running Docker daemon;
these commands do not start, restart or reconfigure Docker.

```sh
node video/build-docker.mjs
node video/render-docker.mjs \
  --input /absolute/private/manifest.json \
  --output /absolute/private/report.pending.mp4 \
  --still /absolute/private/preview.png \
  --preview-seconds 8
```

The build follows the [official Remotion Docker setup](https://www.remotion.dev/docs/docker)
and sends an explicit source allowlist to Docker, never a whole project tree.
Only installation has network access. Runtime uses `--network none`, two CPUs,
2 GiB RAM, no added capabilities, no published ports, and the image's non-root
user. No Docker socket or unrelated project directory is mounted. Per-job audio
copies and sanitized manifests stay in a private temporary directory and are
removed after the process exits. Only that job's randomly named container is
stopped on cancellation. Missing images fail rather than pulling during a render.
Rebuild the image after video or shared diagram source changes.
