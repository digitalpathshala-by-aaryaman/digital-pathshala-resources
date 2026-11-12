# Independent Free Resource Library — Digital Pathshala

The current website now has **two distinct collections** that share the same brand, search field and visitor form:

- **Video Resources** retain their 50 fixed URLs such as `/?v=short-s01`, their existing Shorts schedule and separate encrypted-ZIP workflow.
- **Independent Resource Library** generates permanent pages under `/ebooks/<slug>/`, `/templates/<slug>/`, `/guides/<slug>/`, `/tools/<slug>/` or `/resources/<slug>/`, and publishes only approved PDFs, Excel workbooks and ZIPs.

## Adding a new title

Do not manually create HTML pages. Put an approved public resource file in a local workspace, then run the helper from the repository root:

```sh
python scripts/register_resource.py --kind ebook --title "50 Practical AI Prompts" --file "/path/to/guide.pdf" --description "A free practical e-book" --category "AI Tools" --publish
```

The helper creates a URL-safe title slug, calculates SHA-256, writes `config/independent.json`, and copies the file into `independent_source/ebooks/<slug>/`. Commit the new metadata and source file together. The next GitHub Actions run creates the page, download file, SEO title, OG metadata and public `independent.json` entry. Example: `/ebooks/50-practical-ai-prompts/`.

**Safety:** This is a **public GitHub repository**. Every source file is readable immediately after being committed, even if the website does not display it. **Do not commit private drafts or future-dated source files** to `independent_source`. Add only resources approved for immediate public release. Files for a future launch need separate encrypted staging.

Supported independent-download extensions: `.pdf`, `.xlsx`, `.xlsm` (review macro safety), and `.zip`. Standalone HTML tools should be delivered in ZIP form rather than executing arbitrary visitor-provided HTML on the website's own origin. Cover URLs, if supplied, must be owned images under `/covers/`.

**Permanent URLs:** Slug is fixed at registration. Editing a title, description, cover or file does not change the canonical URL; do not change existing `kind` or `slug` values after publication. Each page has its own SEO title, description, canonical link and social preview tags. An actual social cover image appears once `cover_url` is supplied.

## Google Apps Script v3 — one-time upgrade

1. Open the **existing Apps Script project** connected to the same private Google Sheet.
2. Replace the entire old `Code.gs` with the full **`backend/Code.gs` Version 3.0** file.
3. **Keep the existing Script Property `PUBLISHED_MANIFEST_URL` unchanged** (it already points to the public `videos.json`). Version 3 automatically derives `independent.json` from it.
4. Run `setupSheets()` once, then `checkSetup()`. The setup method creates `Independent_Downloads` and `Independent_Feedback` without erasing or renaming existing tabs. The old `Download_Leads`, `Private_Feedback`, `Request_Receipts` and `Videos` remain intact.
5. **Deploy → Manage deployments → Edit existing web app deployment → Version: New version → Deploy.** Updating source code without deploying a new web app version does not change the public `/exec` endpoint. Editing the existing deployment preserves the URL already embedded in the frontend.
6. Confirm the backend health endpoint reports version `3.0` and `configured:true`.

Video submissions continue to use their existing Sheet tabs. Independent download submissions use `Independent_Downloads` and feedback uses `Independent_Feedback`. Both share the same receipt-confirmation table and validation. For independent pages, the server derives the ID from the canonical page URL and checks the **published-only manifest** before recording and returning its file URL.

**No new Google Sheet, API key, or Apps Script deployment URL is required.**

## Verification and remaining video-specific release work

GitHub Actions verifies the new independent page builder, release gating, SHA checks and JavaScript syntax before publishing. A fixture has tested generation of an approved PDF page and blocked an unpublished PDF.

**Separate from this upgrade:** The previously prepared 90 encrypted video ZIPs still need to be staged in the vault and the key set in GitHub Secrets; the live YouTube feed discovery still needs resolving. The resource library upgrade does **not** pretend those video-release blockers are fixed.

The browser submission → Sheet write → automatic file download will require a live end-to-end test once one real independent resource is approved and the new Apps Script is deployed. Never submit a real visitor's personal information for a test without authorization.
