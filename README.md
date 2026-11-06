# EAAR Amateur Radio Exam Prep

Technician, General, and Amateur Extra exam preparation in one mobile-friendly, browser-based training site. The layout follows the supplied CAP Comms Training `index.html`. No server database or paid hosting is required.

## The three replaceable databases

| File | License class | Effective dates | Starter questions |
| --- | --- | --- | ---: |
| `pools/technician.json` | Technician / Element 2 | July 1, 2026 – June 30, 2030 | 409 |
| `pools/general.json` | General / Element 3 | July 1, 2023 – June 30, 2027 | 423 |
| `pools/extra.json` | Amateur Extra / Element 4 | July 1, 2024 – June 30, 2028 | 599 |

Each pool stores the question ID, question, four choices, correct answer, group, source, version, revision date, and effective dates. The supplied original study programs were the source of the starter banks. Four Technician wording corrections from NCVEC's February 19, 2026 errata have been incorporated. Check the official NCVEC website for future updates before publishing.

## Publish for free on GitHub Pages

1. Sign into [GitHub](https://github.com/) and create a **public** repository, such as `eaar-exam-prep`.
2. Unzip the supplied `EAAR_GitHub_Pages_Updater.zip` onto your computer. Use **GitHub Desktop** (or Git) to copy **the contents** of `EAAR_GitHub_Pages_Updater` into the new repository, preserving folders and the hidden `.github/workflows` directory. Commit and push. Do not upload the ZIP itself as the website.
3. In your repository, open **Settings → Pages**. Under **Build and deployment**, select **Deploy from a branch**, then choose **main** and **/(root)**; click Save.
4. GitHub will publish to `https://YOUR-USERNAME.github.io/eaar-exam-prep/` if the repo is named `eaar-exam-prep`.
5. Once published, share that URL with students. Anyone can study without a GitHub account.

> If your repository uses an organization name or a different repository name, the web address changes accordingly. GitHub Pages is a **public website**. Do not commit personal student records, API keys or internal material.

## Publish a new question pool (easiest: JSON)

1. In the running website select the license class, then open **Update Pools**.
2. Upload a full EAAR/NCVEC JSON file, a plain-text NCVEC question pool, or a `.docx` pool. DOCX import uses built-in browser ZIP decompression; current Chrome/Edge are recommended.
3. Review the **added / modified / removed** question IDs, version and effective dates. The browser rejects incomplete banks, missing choices, duplicate IDs or missing question groups.
4. Check the confirmation box, then choose **Download pool JSON for GitHub**. **You do not need to press Apply to this browser** to export the revised pool.
5. In GitHub replace just `pools/technician.json`, `pools/general.json`, or `pools/extra.json`, then commit. Only authorized repository collaborators can publish updates. GitHub Pages automatically publishes the changed file.
6. Students refresh the website to load the new bank. Their browser profiles and exam history are not overwritten. Modified and removed question progress is archived rather than being counted toward a new pool.

For a local standalone HTML update, use **Apply to this browser** then **Export updated standalone HTML**. The standalone file includes all three banks and the originally supplied reference diagrams, so it can work without a web connection.

## Official Word or PDF import directly through GitHub

The site includes a GitHub Actions workflow to convert an official NCVEC `.docx`, text-based `.pdf`, `.txt`, or compatible `.json` file. PDFs with only scans/photos cannot be read accurately without OCR and are rejected. Conversion is a best-effort parser of NCVEC question/answer layouts, not a guarantee that the imported questions are accurate.

1. Download the latest complete pool and errata from [NCVEC](https://www.ncvec.org/index.php/amateur-question-pools).
2. Sign into GitHub as a repository collaborator. Open the `incoming/` folder and choose **Add file → Upload files**. Upload the official document and commit it.
3. Open **Actions → Update Question Pool → Run workflow**.
4. Select the license class and enter the uploaded relative filename, e.g. `incoming/general.docx`.
5. Fill in version and effective dates if they were not plainly identifiable. Run the workflow.
6. The workflow parses and validates all questions, verifies there are 35 groups (Technician/General) or 50 groups (Extra), and **stops without publishing** if the file is incomplete or incorrectly formatted. If it succeeds, it commits the one selected JSON pool; Pages publishes it automatically.
7. Review the updated question bank on the website, ideally against the source document. Roll back through GitHub's file history if necessary.

**Note:** A successful parser check cannot establish that the official answer key is correct. Always confirm the document is the latest release, that withdrawn questions are excluded, and that the dates/answers and figures are accurate.

Local command-line conversion (requires Python 3.10+, `python-docx` and `pymupdf`):

```bash
python -m pip install python-docx pymupdf
python scripts/import_pool.py --class general --source incoming/general.docx --effective-from 2023-07-01 --effective-to 2027-06-30 --version 2026-02-04
```

Only run it after checking the source and use `git diff pools/general.json` before committing. The converter preserves existing per-group labels where possible.

## Student data and limits

- Saved study records live **only in each browser's local storage**. GitHub Pages does not provide student logins or synchronized accounts. If students switch devices or clear site data, they must use **Print & Settings → Export progress JSON**, then import the backup in the other browser.
- Progress for unchanged question IDs carries forward; progress for revised or deleted questions is moved to an archive within the student backup. Historical exams are kept.
- The website is a study simulator, **not** an official FCC examination platform.
- Updater actions in a student's browser are **local previews only**. The GitHub repository is the authoritative published source; browser visitors cannot write to it.
- Older standalone HTML files remain valid offline but do not fetch new pools automatically. Export a new standalone file after updating.
- Reference figures are individual PNG files in `figures/` for GitHub hosting. The standalone version embeds figures within its HTML. If a later pool introduces or changes diagrams, upload the matching `figures/*.png` files before running the conversion; the GitHub workflow blocks a pool if a required figure is missing.

## Local testing

To test the hosted site on your own computer:

```bash
python -m http.server 8080
```

Open `http://localhost:8080/`. This is necessary for browser `fetch()` to read the independent JSON databases. Simply double-clicking hosted `index.html` may fail because browsers restrict local-file fetching. To use it without a server, open `EAAR_Updated_Standalone.html` instead.

## Current official NCVEC sources

- Technician: <https://www.ncvec.org/index.php/2026-2030-technician-question-pool>
- General: <https://www.ncvec.org/index.php/2023-2027-general-question-pool-release>
- Extra: <https://www.ncvec.org/index.php/2024-2028-extra-class-question-pool-release>

Published updates take effect only when you replace/commit the corresponding class's pool and GitHub Pages has redeployed. Do not publish personal profile backups in the repository.
