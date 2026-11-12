# Digital Pathshala — Free Video Resources

**Digital Pathshala by Aaryaman Goenka** · **Learn · Create · Grow**

Welcome to the official resource website project for [Digital Pathshala on YouTube](https://www.youtube.com/@DigitalPathshalabyAaryaman).

Our channel makes useful digital skills easier to learn through practical demonstrations of ChatGPT, Google Gemini, Excel, Canva, AI tools, automation, and everyday technology.

## Purpose

This **one public GitHub repository** will host the consistent GitHub Pages website for all Digital Pathshala videos. Each published video can have its own resource page and downloadable materials.

- The public catalogue starts at **zero resources** and grows as videos are published.
- Resource pages appear **only when the corresponding YouTube video is live** and release checks pass.
- Visitors see the content of a pack, then click **Download Resources** to open a short form.
- Name and email are required; phone number is optional; privacy consent is required.
- After Google Apps Script confirms that the request was saved to a private Google Sheet, the corresponding ZIP download starts.
- Viewers may send private feedback. Comments never appear as a public discussion feed.
- The same design, spreadsheet and Apps Script backend work for future videos without creating additional repositories.

**Channel:** https://www.youtube.com/@DigitalPathshalabyAaryaman

## Publication status

The approved viewer-facing frontend and release-aware publishing code are committed. **The live GitHub Pages deployment awaits one-time Pages activation** in repository Settings, followed by end-to-end testing of the lead form.

**Release calendar:** one prepared Short each day, `short-s01` on 16 November 2026 through `short-s50` on 4 January 2027. All 40 long-video dates remain blank pending the channel owner's instructions. Dates are eligibility gates, not guaranteed publication times. The public site shows only YouTube-verified releases; unreleased resource ZIPs are not committed in plaintext. No YouTube API key is required: a scheduled GitHub Actions job discovers public Shorts through YouTube's feed and remembers the matching links. The encrypted resource archive, its private passphrase, a privacy contact, working public channel discovery and GitHub Pages enablement are still needed before downloads will appear. See [release setup](docs/RELEASE_SETUP.md).

The repository contains no visitor emails, private Google Sheets, tokens or passwords.

---

*Digital Pathshala by Aaryaman Goenka — Learn · Create · Grow*

## Free independent resources (new)

The website also supports a separate **Free E-books & Tools** section for PDF e-books, Excel workbooks, guides and HTML tools packaged as ZIPs. These are independent of YouTube video release dates and use the existing site design, common search and lead form.

For each approved resource, `scripts/register_resource.py` generates a permanent title-based slug. GitHub Actions builds a dedicated SEO-ready landing page under `ebooks/<title-slug>/` (or templates, guides, tools, resources), preview images, and an original-format download. Unpublished files must never be uploaded unencrypted to the public repository.

The existing `/?v=short-s01` through `/?v=short-s50` routes and daily Shorts schedule have not changed.

**Backend update required:** Replace the existing bound Apps Script `Code.gs` with `backend/Code.gs` Version 3.0, run `setupSheets()` and `checkSetup()`, then deploy a **new version of the existing web app deployment**. This adds independent download/feedback Sheet tabs without replacing the old ones. See [complete setup guide](docs/INDEPENDENT_RESOURCE_WORKFLOW.md).

Note: ZIP vault staging and real YouTube discovery are separate pending tasks, not fixed by this library upgrade.
