# HF Training v3 — academy pilot

A complete replacement source pack for a NEW repository and NEW database. All connected files are included; the pack reuses the prior authentication and administration foundation and extends the assessment workflows. It is not a line-for-line rewrite and is not a production-certified VLE.

## Start on a computer

Install Python 3.11 or newer. Extract this pack. Open a terminal in the folder containing `manage.py`.

```sh
python -m venv .venv
```

Activate the environment:

- Windows PowerShell: `.venv\Scripts\Activate.ps1`
- macOS/Linux: `source .venv/bin/activate`

```sh
python -m pip install -r requirements.txt
```

### Fictional demonstration (recommended first)

Set a NEW demonstration directory and enable local HTTP:

Windows PowerShell:
```powershell
$env:HF_DATA_DIR = "$PWD/demo-instance"
$env:HF_LOCAL_HTTP = "1"
```

macOS/Linux:
```sh
export HF_DATA_DIR="$PWD/demo-instance"
export HF_LOCAL_HTTP=1
```

```sh
python demo.py
python manage.py serve
```

Choose your own demo passphrase when prompted; it is never included in this pack. Visit http://127.0.0.1:8000. The four fictional account addresses are `admin@demo.invalid`, `learner@demo.invalid`, `assessor@demo.invalid` and `iqa@demo.invalid`. They share the passphrase you choose for demonstration ONLY. Demo setup refuses to alter a non-empty database. Do not use real records in this demo.

### Empty academy installation

Use a different NEW HF_DATA_DIR, then run:
```sh
python manage.py init
python manage.py admin
python manage.py serve
```

The admin command asks for your name, email and private passphrase. No default administrator key exists. Create learners and staff in Administration, assign staff, check unit content, and enrol each learner on the appropriate course. A newly created user must change their temporary passphrase. An empty course can be assigned but has no assessments until its units are added.

## What works

- Administrator, learner, assessor and IQA accounts; staff assignment; private course enrolments.
- Consultation fields, service notes, learner reflection, academy range descriptors (including short/mid-length/long hair), and criterion checkboxes.
- Multiple service records per unit, one open draft per unit; private PDF/JPEG/PNG evidence uploads.
- Separate assessor criterion ticks and written feedback. Learner ticks are not assessor approval.
- Submitted records lock. Assessors can return work, learners resubmit, and decisions retain snapshots.
- An IQA can sample assessed work but cannot verify their own assessment.
- Academy attendance; learning hours split into academy/placement/other and approved separately.
- Exam attempt/result recording, progress reviews, course resources and JSON record export.
- Offline backup utility covering the database and uploaded evidence.

## Course content boundaries

The five VRQ identifiers are correctly named against the official City & Guilds 3002 handbook:

| Unit | Title |
|---|---|
|202|Follow Health and Safety Practice in the Salon|
|203|Client Consultation for Hair Services|
|204|Shampoo and Condition the Hair and Scalp|
|210|Cut Men's Hair|
|211|Cut Facial Hair|

The included checklists are short CENTRE DRAFT prompts. They are NOT the complete official performance, knowledge or range requirements. Practical descriptors are centre metadata, not a claim that these satisfy an awarding-body range. The academy must map its authorised assessment pack, observation counts, range requirements and knowledge assessment before live sign-off. The exact award earned by the selected-unit programme still needs centre confirmation. No certificate is generated.

The apprenticeship and VTCT are separate empty course areas. Their precise qualifications and units must be added by the academy. They are not ready for course assessment merely because their menu entries exist.

The VRQ 18 placement / 6 academy weekly plan is the academy's stated target, not a validated funding rule. The app stores actual submitted/approved activity; it does not automatically classify shadowing as guided learning or statutory off-the-job training. Attendance is not added to learning hours again. Duration and missed-week monitoring remain manual. Exams take place externally; this app records results only.

Source: https://www.cityandguilds.com/qualifications-and-apprenticeships/hairdressing/hairdressing/3002-hairdressing (Level 2 handbook v3.3, January 2025; consulted 26 September 2026).

## Upload to GitHub

1. Create a NEW private repository, for example `HF-Training-v3`.
2. Upload the CONTENTS of this extracted folder, preserving `hf`, `static`, `tests` and `docs` directories. Upload source files, not the ZIP.
3. Include `.gitignore` (it may be hidden in your file browser).
4. Never upload `instance`, `demo-instance`, any data directory, backups, evidence, credentials or `.venv`.
5. Keep the old project/data unchanged; this version has a different database schema. It is not an in-place v2 migration.

GitHub stores the code. GitHub Pages cannot execute this Python backend. Do not open `static/index.html` directly to test the app; start the server and use its URL.

## Application hosting

Use a Python host or a Docker host with a persistent private disk. Run `python manage.py init` and `python manage.py admin` against that host's HF_DATA_DIR once, then run:

```sh
waitress-serve --listen=0.0.0.0:8000 wsgi:app
```

Put a trusted HTTPS reverse proxy in front of it, terminate TLS there, restrict direct access to the backend, apply login rate limiting and request size limits, and do NOT set HF_LOCAL_HTTP=1 in production. HF_DATA_DIR must point to persistent storage shared by this single application instance. SQLite here is designed for a small single-instance pilot; do not deploy multiple independent instances with divergent disks.

The included Dockerfile is an optional packaging route. It does not provision hosting, HTTPS, a domain or backups. No deployment has been performed for you.

## Backup and restore

Stop the app before backup:
```sh
python backup.py /secure/path/hf-backup.zip --app-stopped
```

Use a new destination outside HF_DATA_DIR. Backups contain private records. Store securely and never upload to a public repository.

For a restore rehearsal: stop the app, preserve the old data directory, extract a trusted backup into a NEW empty private directory, verify each file against `manifest.json` SHA-256 values, point HF_DATA_DIR to that directory, and start the same v3 code. Verify accounts, record counts and an evidence download before switching. Treat sessions in a restored database as sensitive; expire them with `DELETE FROM sessions` using a local SQLite operator tool before exposing the restored service. Automated encrypted scheduled backups and full live-host restore acceptance remain deployment work.

## Testing and limitations

```sh
python -m unittest discover -s tests -v
```

See docs/VALIDATION.md for observed results and docs/PILOT-CHECKLIST.md for acceptance steps. Dashboard percentage is assessed SERVICE RECORDS, not complete units, range coverage or qualification achievement. There is no automatic ATS integration, awarding-body certification, funding eligibility engine, multi-college tenancy, bulk import, email notifications, MFA or email password recovery. Operator/admin password reset exists. Upload content scanning, security/privacy review and mobile/browser acceptance are launch gates for real learner use.
