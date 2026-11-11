# Public mobile pilot API review — 2026-10-16

Scope: the mobile client, the local application on port 8000, and the separate
`backend/public_gateway.py` allowlist proxy. The gateway is the only API listener
that should be connected to the public tunnel. The main backend remains on
loopback. This review does not authorize making the complete legacy API public.

## Public route contract

All paths below start with `/api`. All require the account Bearer token except
the four authentication routes and the short-lived signed media URL.

| Method | Path | Input restriction |
|---|---|---|
| POST | `/auth/login` | Email, password only |
| POST | `/auth/register` | Email, password, full_name, birth_date; optional name, surname, city, phone_number |
| POST | `/auth/forgot-password` | Email only |
| POST | `/auth/reset-password` | Token and new password only |
| GET/PATCH | `/user/profile-v2` | PATCH accepts the existing explicit editable profile fields |
| GET | `/user/credit-history` | Optional single `limit` 1–100 and `offset` 0–100000 |
| GET | `/numerology/costs` | No query |
| POST | `/numerology/personal-numbers` | Single valid `birth_date=DD.MM.YYYY`, no body |
| GET | `/numerology/personal-numbers/latest` | Own latest saved result only; no query, writes or debit |
| GET | `/learning-v2/lessons` | Active lessons at the student's level; safe content and stored `progress_data` |
| GET | `/learning-v2/lessons/{lesson_id}` | Same access check, safe content and progress |
| GET | `/student/lesson-progress/{lesson_id}` | Own progress, no writes or attendance tracking |
| POST | `/student/lesson-progress/{lesson_id}/theory` | Empty object; explicit theory-read action |
| GET | `/student/exercise-responses/{lesson_id}` | Own answers to actual lesson exercises |
| POST | `/student/exercise-response` | lesson_id, exercise_id, response_text; text 1–10000 characters |
| GET | `/student/quiz-attempts/{lesson_id}` | Last 100 server-graded own attempts |
| POST | `/student/quiz-attempt` | lesson_id, quiz_id, answers, UUIDv4 submission_id; at most 100 answers, 4000 characters each |
| GET | `/student/lesson-files/{lesson_id}` | Safe metadata without disk paths/stored filenames |
| GET | `/student/lesson-files/{lesson_id}/{file_id}/access` | Authenticated scoped URL issuance |
| GET | `/student/lesson-video/{lesson_id}/access` | Authenticated configured Bunny URL issuance |
| GET/HEAD | `/student/media/{token}` | Short-lived file capability; only single byte ranges |

IDs use ASCII letters, digits, `_` and `-`, length 1–128. Unknown methods/paths,
encoded path separators, extra query fields and arbitrary uploads are rejected.
The gateway does not follow upstream redirects. The old Bunny `video-url`, old
downloads, time-activity, challenge/reward writes, payments, admin, docs and
login-v2 are not public routes.

## Confirmed source defects addressed for this pilot

- Both student lesson-detail registrations and the lesson list previously
  returned stored `correct_answer`/`explanation` and ignored user level. They now
  use `StudentLearningService`; inactive lessons are unavailable, and current
  admin flags only bypass the level restriction. Answer keys and internal fields
  are removed before serialization.
- Quiz submission previously accepted client score, passed and points_earned.
  It now rejects these fields and grades actual stored questions. Choice answers
  must be exact option strings; text answers compare trimmed, case-folded text.
- Exercise submission previously accepted arbitrary exercise IDs and awarded
  points for each invented ID. The exercise must belong to the accessible lesson.
- Opening progress previously inserted attendance and implicitly marked theory
  read during updates. Reads are now read-only; theory completion is an explicit
  authenticated action. The lesson list returns stored progress without N+1
  requests or synthetic attendance.
- File metadata previously exposed paths and stored names without checking
  lesson access. Only safe metadata is now returned; actual media uses the
  separately reviewed scoped media router.
- The parent integration also addresses the previously non-atomic personal
  calculation debit and date validation before debit. Those changes and media
  signature/range implementation have their own tests and ownership.

Personal-number calculation now prepares the user-dependent response and any
name-number cache update before payment. The complete calculation record and
debit-history entry are committed in the same user-document mutation as the
balance decrement. A later archive/history outage does not replace the prepared
HTTP result with an error. Pending calculation records are delivered by unique ID
on the next calculation or a credit-history read; delivery retries never issue a
new debit. No automatic client request retries or new request fields were added.

## Reward and retry semantics

The backend chooses configured quiz/exercise rewards (integer 0–1000). A passing
quiz can earn its reward once per user/lesson/quiz; an exercise once per
user/lesson/exercise. Completing all required sections earns the existing
50-point lesson bonus once. A legacy already-completed lesson does not receive
that bonus again. Legacy exercise responses keep their prior reward behavior.

A unique submission document identifies each quiz retry. The same submission ID
and payload return the same result; another payload with that ID returns 409.
The reward marker, balance increment and pending credit-history entry are one
conditional Mongo user-document mutation. Concurrent attempts therefore share
one reward. Ledger delivery uses a deterministic unique `_id`; a failure keeps
the outbox entry for retry and cannot increment the balance again. This works on
standalone Mongo without multi-document transactions. Attempts and cached
progress are separate documents, so a crash can leave them temporarily behind
the committed reward; retrying the same submission finishes those writes.

Old quiz records trusted client-provided results. They remain stored but are
excluded from the server-graded history and from new quiz completion checks.
Existing cached legacy progress is preserved; it is not evidence that an old
result was independently verified. No old balances are rewritten by this change.

## Gateway operating limits

- Configure exact HTTPS origins in `PUBLIC_GATEWAY_ORIGINS`, for example
  `https://dmitriimalahov-gif.github.io` (origin only, no `/numerom-app/` path).
  CORS is not authentication; native clients may omit Origin.
- Use one worker: limits and the temporary personal-calculation serialization
  lock are local to the gateway process. General limit is 600 requests/minute,
  at most eight active upstream requests. Per-IP limits: login 8/minute,
  registration 3/hour, recovery 3/10 minutes, writes and personal calculations
  20/minute, reads/media 90/minute. Registration also has a global 10/hour limit.
- Body limits: ordinary JSON 16 KiB, exercises 128 KiB, quizzes 512 KiB.
  JSON responses are at most 4 MiB. Media streams without buffering the complete
  file, checks declared and actual size up to 512 MiB, and forwards single Range
  and If-Range headers. Upstream media read timeout is 60 seconds.
- `PUBLIC_GATEWAY_TRUST_CLOUDFLARE=1` is only for a local cloudflared process.
  CF-Connecting-IP is accepted only from the loopback peer and validated as an
  IP address. All incoming forwarding headers and cookies are otherwise ignored.
  Run the gateway with `--no-proxy-headers` so this peer check is meaningful.
  The backend may trust forwarding from its loopback gateway for recovery limits.
- Run gateway and backend with `--no-access-log`: signed media tokens are in
  paths. Do not log authorization headers, reset tokens or request bodies.
- Recovery requires configured SMTP and a configured public reset page. Missing
  configuration returns an unavailable response; tests do not prove mail delivery.

Example from the backend directory (port is an operator choice):

```sh
PUBLIC_GATEWAY_ORIGINS=https://dmitriimalahov-gif.github.io \
PUBLIC_GATEWAY_TRUST_CLOUDFLARE=1 \
.venv/bin/uvicorn public_gateway:create_app --factory --host 127.0.0.1 \
  --port 8004 --workers 1 --no-proxy-headers --no-access-log
```

## Remaining pilot limitations

Registration still grants 100 welcome points to an unverified email. The gateway
limits throughput and refuses injected role/credit fields, but multiple people
or addresses can still obtain multiple bonuses. Verified-email onboarding and
durable distributed abuse controls are a separate phase. Case-sensitive account
lookup and the legacy registration insert sequence are unchanged. Do not expose
payments or the rest of the legacy reward API as a consequence of this pilot.

Rate counters reset on gateway restart and are not shared across workers. The
pilot tunnel URL is temporary. Bunny playback and SMTP delivery require real
configuration and separate operational checks. Tests below do not establish
physical-device playback or public deployment readiness.

## Verification in this change

- `tests/test_public_gateway.py`: 13 HTTP policy tests with an isolated upstream
  transport, including hidden routes, origin/schema checks, rate limits, trusted
  peer IP handling, JSON response bounds, media Range/HEAD/size/redirect handling.
- `tests/test_student_learning.py`: 8 tests against a disposable real MongoDB
  on port 27028. Each creates a unique `numerom_test_*` database and removes it.
  Tests cover active/level access, redaction, authoritative grading, actual server
  route wiring, concurrent submissions and exercise/completion rewards, ledger
  failure/retry, and preservation of previously awarded completion bonuses.
- Red tests were observed before implementing the learning service and before
  enabling the newly reviewed gateway routes. No application DB writes, live
  registrations, email sends or service restarts were performed by this work.
- The final personal-number payment regression adds seven fault/unit tests and
  four isolated real-Mongo tests in `test_personal_numbers.py`,
  `test_credit_debit.py` and `test_credit_debit_mongo.py`. The actual HTTP handler
  returns 200 with the prepared result when both archive and history delivery
  fail. A crash after archive insertion and eight simultaneous delivery retries
  still produce exactly one calculation and one ledger record. Insufficient
  credit creates no pending calculation; a zero-cost calculation is archived
  without a debit-history entry.

## Detailed personal report follow-up

The new latest-result GET scopes both the archive and pending durable outbox to
the authenticated user and `personal_numbers` type. It projects only report
fields and does not flush the outbox, change the profile, or debit credits.
Disabled accounts are rejected. An absent result is an explicit null; database
failure is not disguised as an empty history. The gateway rejects query-based
user selection and methods other than GET on this path.

The paid handler prepares and validates the complete report before atomic debit.
The name number is derived from the supplied Latin name and surname; wisdom is
destiny plus that number, or unavailable when required name data is absent.
Existing saved values are not silently recalculated with a changed profile.
Focused report tests include seven disposable real-Mongo scenarios for ownership,
ordering, disabled users, repeated reads at zero balance, and pending-only results.
The entire backend suite passes 128 tests. Live public checks after restart
confirm 401 without authentication for the new route and 404 for admin/docs.
