# HF Training — GitHub Pages testing version

Prepared for Hairforce1 Training Academy. This version runs directly on GitHub Pages in Chrome, including on a Chromebook. No Python, terminal, server account or build step is needed to use it.

Open **READ-ME-FIRST.html** for the illustrated setup guide and demo login details.

## What to upload

Extract this ZIP. Inside `HF-Training-GitHub-Demo`, upload the files and the complete `hf-demo` folder to the top level of your GitHub repository. Do not upload the outer folder itself and do not upload the ZIP.

The repository must contain:

```text
index.html
hf-demo/
    app.js
    ui.js
    styles.css
    demo-store.js
    unit-outlines.js
    learning.js
    portfolio.js
    admin.js
READ-ME-FIRST.html
README.md
```

The preview PNGs and TEST-RESULTS.md can also be uploaded. They are documentation, not required for sign-in. The included `.nojekyll` file can be included if your file browser shows it; this app does not require a build tool.

If using the same repository as the earlier pack, **replace its root `index.html`** with this one and add the `hf-demo` folder. The older `hf`, `static`, Python files and setup files are not used by this demo. You do not need to delete them to make this work. Keep them until you have a backup and have confirmed the demo works. No automatic migration or deletion of old records is performed.

If GitHub has `index.md` or `README.md` but no root `index.html`, it may display a document instead of the app. Ensure this pack's `index.html` is at the top level.

## GitHub Pages settings

In the repository, choose **Settings → Pages**:

- Source: **Deploy from a branch**.
- Branch: the branch containing these files, normally **main**.
- Folder: **/(root)**.
- Select **Save** and wait for the deployment to finish. Use the published address shown in Pages settings.

Your screenshot showed `https://hf-training-1.github.io/HF-Training-1/`. If that is still the chosen repository, use that address after uploading. No remote changes or deployment have been made by this code pack.

If you still see the old screen, use **Ctrl + Shift + R** on your Chromebook to refresh the published page. You should see **TESTING VERSION** across the top and buttons for Administrator, VRQ student, Assessor, IQA and Apprentice.

GitHub Pages availability depends on your GitHub plan and repository visibility. If private-repository Pages is unavailable, use a separate public repository containing only this demo's code and fictional samples. Do not make an existing repository containing sensitive files public.

Official Pages setup instructions: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site

## Login

Click a role button on the sign-in screen for one-click entry, or enter:

| Role | Email |
|---|---|
| Administrator | admin@demo.invalid |
| VRQ student — Alex | learner@demo.invalid |
| Assessor | assessor@demo.invalid |
| IQA | iqa@demo.invalid |
| Apprenticeship student — Jordan | apprentice@demo.invalid |

**Password for all five: `HF-Demo-2026!`**

These credentials are intentionally public demo credentials. They do not access the old HF app, ATS, or any real student system. Never use a real academy/ATS password here.

The Administrator account opens all demo administration areas. It is not a secure master key. All role checks run in the browser and can be bypassed by someone editing browser code/storage.

## Try it

1. Open the **VRQ student** demo. Go to E-portfolio and open Unit 202 or another unit.
2. Enter fictional consultation/service notes, reflection and the relevant practical ranges. Save the draft.
3. Optionally upload a sample PDF, JPG or PNG (5 MB per file, 20 per record, 30 MB total demo file storage).
4. Click **Save & submit for assessment**. The service objectives, service, what went well and improvement fields are required.
5. Sign out and choose **Assessor**. Open Assessment & IQA. Tick the demonstrated criteria and record feedback. You can return work for changes or record it as assessed.
6. Sign out and choose **IQA**. Review assessed work and record independent sampling feedback. The same account cannot assess and IQA the same record.
7. Try attendance, learning hours, reviews and exam-result recording. These simulate academy workflows; they do not issue qualifications or deliver official exams.
8. Choose **Apprentice**. Jordan sees only the separate apprenticeship course area; its units are not populated yet. The VRQ units are not in Jordan's view.

Multiple service records per unit are supported, with one unfinished draft per learner/unit. Learner ticks and assessor ticks are stored separately. The history retains feedback and the recorded demo actor.

In Administration you can create fictional accounts, courses and units, enrol test learners, assign staff, add learning resources, reset test passwords and disable test accounts. A newly created account needs a 14–128 character test passphrase and must change it on first login. Seeded public demo accounts do not require that first-login step.

## Included course content

- VRQ: five unit outlines carried over from the revised pack — **202, 203, 204, 210 and 211**.
- City & Guilds Level 2 Barbering Apprenticeship: separate empty course area.
- VTCT Barbering: separate empty course area.

The VRQ titles in the revised source pack are: Follow Health and Safety Practice in the Salon; Client Consultation for Hair Services; Shampoo and Condition the Hair and Scalp; Cut Men's Hair; Cut Facial Hair. Checklists are **centre draft prompts**, not the full official performance, knowledge or range requirements. The hair-length and texture checkboxes are practical descriptors for testing. They do not establish qualification completion.

## Where demo data goes

Demo records and sample file bytes are stored in IndexedDB in **this browser on this device**. Login selection is stored in this tab's session storage. Different devices/browsers have separate, independent demos. Sign out and switch roles in the same browser to test the complete workflow.

Refreshing the page keeps the demo records under normal browser settings. Clearing site data, browser storage removal, private browsing, changing device/profile, or changing the website's path can make them unavailable. This is not a backup service.

**Reset demo** deletes only this version's demo store at its current website path and restores the fictional starter accounts. It does not call `localStorage.clear()` or delete the original HF app's localStorage. Reset permanently removes this demo's test records and attachments in the current browser.

**Download learner record (JSON)** exports one learner's visible records and attachment metadata. Download each sample attachment separately if you want to keep it. No import/restore function is supplied.

## What this version is and is not

This is a working browser-only demonstration for exploring the design and workflows on GitHub Pages. It is not the server-backed v3 application, and it is not a live or secure multi-user VLE. Do not enter real learner names, client images, safeguarding information, health records or real passwords.

No background server, database subscription or Python installation is involved. The internal `/api/...` strings are local function routes; they are not network requests to a server. There is no cross-device sharing, email, cloud backup, protected authentication, immutable audit log, official qualification result or ATS integration.

For live learner use later, retain the front-end design and connect it to independently reviewed server-side authentication, data storage and file permissions. No external account is required for testing this pack.

## Why the earlier page looked plain

The published page referenced styling and scripts under `/static/...`, which resolved outside your GitHub repository path and were not available. It also expected a Python backend. This pack uses relative `./hf-demo/...` paths and replaces backend calls with an explicitly labelled local demo store.

Do not fix the old version just by changing the stylesheet path and assume its login is working. Upload this complete connected demo pack instead.

## Troubleshooting

- **Plain text / no blue styling:** confirm `hf-demo/styles.css` exists directly under the repository's `hf-demo` folder and the root `index.html` is this version.
- **Old wording / no role buttons:** replace the root `index.html`, wait for Pages deployment and hard-refresh.
- **Role buttons do nothing:** confirm all eight JavaScript/CSS files listed above are present with exact names. Open the GitHub Pages HTTPS address, not an HTML preview inside GitHub or the ZIP.
- **Login fails after changing a test password:** enter your changed test password, or use Reset demo if you no longer need the local test records.
- **Storage error:** use a normal Chrome profile with site storage enabled and sufficient free space. On a managed Chromebook, school/work policies may restrict browser storage; ask its administrator if blocked.
- **Another device cannot see your changes:** that is expected in this browser-only demo.

See TEST-RESULTS.md for the checks actually performed.
