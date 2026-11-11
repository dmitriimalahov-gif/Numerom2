# Business 250 API and integration review — 2026-10-18

## Scope and result

Reviewed `backend/services/business.py`, `backend/routers/business.py`, router registration, domain parser/model integration, `mobile/src/lib/useBusiness.ts`, `mobile/src/app/business.tsx`, business editors/report UI, and native/web report delivery. The API contract matches the design: owner-private workspace, explicit free pilot activation, employee import/edit/remove, manual task groups, skills-only coverage, private reports and a CSV template. No numerological hiring/ranking/role-assignment logic is present.

API verification uses a real disposable MongoDB at `127.0.0.1:27040` in `numerom-business-qa-20261018`, with tmpfs storage and random `numerom_test_business_*` databases removed after each test. It never connects to production MongoDB.

## Findings resolved before release

1. **Stale editors could overwrite newer remote changes after refresh.** Initially `useBusiness.mutate` always sent the current workspace revision while `EmployeeEditor` and `TeamEditor` retained their original local drafts. After a 409 and refresh, resending the old draft would therefore pass CAS with a new revision. The screen now captures `editingRevision` when opening an editor, passes it to save/remove, and presents a conflict notice until the owner reopens the form. The lifecycle regression confirms the old editor sends its original revision after a workspace reload.

2. **A reloaded workspace could retain an outdated open group report.** Initially `load()` updated the envelope but left the previous report and its export action intact. It now clears the report whenever a workspace reload succeeds. The targeted lifecycle test covers reopening data after an existing report.

3. **A delayed export could open an old account's employee report.** Initial native delivery awaited capability/PDF generation and unconditionally opened the share dialog; web delivery printed on a late iframe `onload`. A synthetic native harness reproduced delivery after the simulated owner changed. Delivery helpers now accept an optional `isCurrent` guard, check it after the asynchronous boundaries and immediately before printing/sharing, and clean up temporary PDFs/frames on cancellation. Business exports pass a guard bound to owner, token and operation epoch; route/background changes invalidate it. Five new export regression tests cover native cancellation after PDF generation, cancellation before the direct-print path, web late iframe cancellation, cleanup, and compatibility for existing callers.

4. **Control characters in company names could create an unreadable workspace.** Independent client review identified that initial activation accepted a name the mobile response parser rejected. Activation now rejects Unicode control/surrogate/format characters, normalizes NFC and collapses whitespace before persistence. Model and HTTP regression tests prove invalid activation does not create a document.

## Executed validation

- `NUMEROM_TEST_MONGO_URL=mongodb://127.0.0.1:27040 backend/.venv/bin/python -m unittest backend.tests.test_business_api -q`: **16 passed**, no skips. Includes live auth/disabled/deleted users, cross-owner isolation even for an administrator, free activation concurrency, 250/251 limits, exact duplicate all-or-nothing behavior, original preview row numbers, no raw-file persistence, optimistic CAS races, concurrent same-import replay, changed-body request-ID conflicts, bounded hidden receipts, group/member limits, atomic membership cleanup and name/DOB-independent team output.
- `node --test test/business.export.test.js`: **5 passed**. These exercise the actual TypeScript delivery implementations through isolated dependency stubs; they do not claim physical-device or native share-sheet testing.
- `node --test mobile/test/business.lifecycle.test.js`: **6 passed** after the empty-team fixture was aligned with the domain's known zero available hours. Covers single-flight/idempotent uncertain imports, late picker and old-account responses, stale editor revisions and report invalidation on reload.
- Source review confirms the parser processes uploads in memory, bounds compressed/expanded ZIP/XML dimensions, rejects formulas/macros/external links, and produces entered-skill coverage without inference from names or dates of birth. Domain parsing has its own test suite owned by the domain agent.

## Boundaries

The isolated backend tests and stubbed delivery tests do not establish public deployment, physical iPhone/Android behavior, commercial billing, or legal authority to upload real employee data. The free pilot does not touch Stripe or credits. Import receipts retain the latest 64 operations; older requests still cannot replay with their stale expected revision. No production process restart, deployment, source commit or production database mutation was performed by this task.
