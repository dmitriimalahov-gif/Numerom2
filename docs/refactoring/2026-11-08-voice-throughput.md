# NumerOM narration throughput — 8 November 2026

The current report queue produces hundreds of long chapters. The low-memory
worker reloaded Qwen3-TTS, its stress adapter and Whisper for every fragment.
Alphabetical chapter priority also spread work across every report, delaying
the first complete video.

## Changes

- `--reuse-models` keeps the existing TTS and recognition models loaded within
  one chapter. Each fragment still receives its own seed, pronunciation
  preparation, recognition check and the unchanged 7% word-difference gate.
- Reuse requires at least 32 GiB installed memory and 8 GiB available according
  to local memory telemetry. Missing telemetry or pressure causes conservative
  unloading. Pressure is checked between attempts. Both models are released
  before the shared generation lock is released, including on exceptions.
- The launchd voice service uses this adaptive mode. `--low-memory` remains
  available as a mutually exclusive rollback option.
- New report overviews retain their priority. Other paid chapters concentrate
  on the report with the least unvoiced text, so its video becomes eligible
  sooner. Remaining work is checked against valid audio files, not marker
  existence. No report content or chapters are removed.
- `generation.json.performance` records model load counts and the time spent
  loading TTS, synthesizing and recognizing. This distinguishes useful work
  from repeated initialization.

## Verification and scope

`test_voice_retry_seeds.py`, `test_report_generation_slot.py` and
`test_service_recovery.py` cover reuse, memory fallback during a chapter,
cleanup on recognition failure, queue ordering, damaged audio, selected voice,
tempo and persistent retries.

`scripts/benchmark-voice-memory.py` runs the actual worker on one public script,
with identical seeds and separate private queues under the existing GPU lock.
Both modes warm up before the measured pair. The production word check and
audio integrity gate apply to every sample. Results are recorded separately
from production jobs; sample audio and the voice reference remain private.

Measured after warming both modes: the same 43.91-second recording took
40.613 seconds in low-memory mode and 30.642 seconds with reuse (24.6% less
processing time, 1.325× throughput on this sample). TTS/ASR loads fell from
3/3 to 1/1. Decoded master PCM was exactly equal, and maximum word difference
was 2.5% in both modes. This is one controlled sample, not an ETA for the whole
queue. The initial cold-start comparison is deliberately excluded from the
claimed improvement. Evidence: `artifacts/voice-speed-2026-11-08/benchmark.json`.

Runtime code and the previous voice LaunchAgent are backed up in
`runtime/backend/private/recovery/voice-speed-2026-11-08/`.
Only `scripts/generate-project-voices.py`, `scripts/numerom_services.py` and
the voice LaunchAgent are deployed. The selected voice, 1.2× speech tempo,
stress version, transcripts, accepted chunks, report data, payment and email
configuration are unchanged. Audio speed gains do not establish a video
rendering speed gain or completion of the remaining queue.
