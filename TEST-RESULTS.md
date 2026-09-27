# GitHub Pages demo — delivery checks

Checked 27 September 2026. Testing used fictional records and sample file bytes only.

## Browser result: passed

The actual app was served as static files under `/HF-Training-1/`, matching the project-path structure in the supplied screenshot. There was no Python application backend. The check used Chromium 133 through Playwright, with a 1366 × 900 desktop viewport and a 390 × 844 mobile viewport.

The automated browser flow successfully:

- Loaded the stylesheet and every JavaScript module from the nested project path.
- Signed in with the public administrator demo and opened every navigation section.
- Switched to the VRQ student, entered service notes and saved practical range and criterion ticks.
- Uploaded a sample PDF, downloaded it, saved and submitted the service record.
- Confirmed submitted fields were read only and stored HTML-like text did not become an executable image element.
- Switched to the assessor, selected demonstrated criteria and recorded feedback.
- Switched to the independent IQA and verified the assessment.
- Switched to the apprenticeship learner and confirmed its course view did not contain VRQ unit records.
- Refreshed the page and retained the locally stored records.
- Rendered the dashboard and sign-in page at mobile width without page-wide horizontal overflow.

The browser reported **zero uncaught page errors**. All network requests were for static application assets; no server `/api/` requests were made. Internal `api()` calls are routed into the local demo store.

## Additional workflow checks: 28 passed

The browser also directly exercised the local data layer for course/learner restrictions in normal app use; submitted-record locking; new practical records; duplicate-draft prevention; academy-hour submission and approval; rejecting hours for an unenrolled course; attendance; progress reviews; exam records; fictional user creation; empty VTCT enrolment; learner export; course and unit creation; pre-enrolment unit editing; staff assignment; resources; rejecting unsafe resource URLs; preventing edits to already-enrolled unit outlines; forced change of a new test user's passphrase; course resource visibility; stale record versions; returned work and resubmission; independent IQA; account disable; account re-enable and password reset.

These are **demo workflow checks, not security tests**. All checks run in browser code; browser users can edit that code or its storage. This build must not hold real learner records.

## Reset and old-data preservation: passed

A synthetic `hfUsers` item was placed in localStorage to represent the original app's storage. Reset demo removed only the new demo's IndexedDB state, retained that localStorage item unchanged, and restored the five VRQ drafts and public demo accounts without carrying over test hours.

## Visual review: completed

The supplied LOGIN-PREVIEW.png, DASHBOARD-PREVIEW.png and MOBILE-PREVIEW.png are screenshots of this build. They were visually checked for styling, legibility, layout and overflow. The dashboard screenshot includes records created by the test; a new browser starts with the default unassessed drafts.

## Limits

No remote GitHub repository was changed and no public deployment was performed. Chromium viewport testing is not the same as testing on the user's physical Chromebook. Managed ChromeOS restrictions, older browsers, private browsing, browser quota/eviction behaviour and actual GitHub publishing settings were not verified on the user's account.

No official course assessment mapping, security certification, shared accounts, cloud synchronisation, real student data handling, multi-college tenancy, funding compliance or ATS integration is supplied by this demo.
