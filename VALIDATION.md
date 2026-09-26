# Validation — 26 September 2026

- 15 distinct automated workflow tests passed using fresh temporary SQLite databases.
- Covered: login and CSRF protection; learner/staff isolation; private attachment access; stale edit rejection; submission locking; returns and resubmission; independent IQA; forced password change and disabled-account revocation; administrator enrolment; attendance/hours; reviews/resources; repeat practical records; range validation; separate assessor ticks; course boundaries; exam role restrictions; JSON export isolation.
- Fictional demo initialisation succeeded with four accounts, three course areas and five VRQ units.
- Offline backup creation and restore into a temporary directory passed checksum, account-count and unit-count checks with synthetic data. This is not live-host restore acceptance.
- Python compilation and JavaScript syntax checks passed during development.
- A Chromium download failed in this environment. Desktop/mobile visual browser QA remains outstanding.

Qualification verification is limited to the five unit numbers/titles against the 3002 v3.3 handbook. Full criteria, required observations, range coverage, knowledge requirements and the exact registered award remain centre review tasks. No claim of awarding-body approval, security certification or production readiness is made.

A DOM-based interface check against a running test server also passed: all learner sections rendered, the Short hair checkbox persisted through UI submission, submitted fields became read-only, assessor criterion controls rendered, and administration forms rendered. This checks interface behaviour, not visual layout or real-browser compatibility.
