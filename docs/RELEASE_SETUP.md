# Digital Pathshala — no-API-key automatic Shorts release

## Release schedule

- One Short daily at **11:00 AM IST**, starting with `short-s01` on **16 November 2026** and ending with `short-s50` on **4 January 2027**.
- All 40 long videos are **on hold**, with no dates assigned.
- The public GitHub Pages website starts at **0 published resources**, then grows only as verified Shorts are released and the corresponding resource ZIP is staged.
- The workflow polls the public YouTube channel after 11 AM IST, retries periodically during the day, and publishes the prepared resource page and ZIP only when the video's match is unambiguous.
- **No YouTube Data API key is needed.** The tool reads the public YouTube RSS/Atom channel feed and Shorts page. YouTube does not guarantee these public formats remain unchanged. If discovery is unavailable or ambiguous, it holds the resource rather than guess.
- Confirmed matches are saved as `config/discovered.json` and reused so already released resources remain in the catalogue as the public RSS feed rolls forward.
- The GitHub Actions scheduler operates automatically: no scheduled ChatGPT conversation or repetitive manual HTML edits are needed. Execution times can be delayed by GitHub.

## One-time actions still required

1. **GitHub Pages:** In **Settings → Pages → Build and deployment → Source** select **GitHub Actions**. The GitHub connector cannot configure repository Pages settings, and the current workflow stops at `actions/configure-pages@v5` until Pages is enabled.
2. **Protected resource vault:** Upload the existing encrypted `batch-001.zip.enc` to the repository's `vault/` directory. Store its separate passphrase in the GitHub Actions secret **`DP_VAULT_PASSPHRASE`**. *This is an encryption passphrase, not a YouTube API key.* Never commit the password or decrypted ZIPs to GitHub.
3. **Privacy contact:** Set an official email address the channel owner approves for privacy/data-deletion requests in `config/site.json` as `privacy_contact_email`. The builder intentionally holds downloadable files while it is missing.
4. **Google Apps Script:** In Script Properties set `PUBLISHED_MANIFEST_URL` to **`https://digitalpathshala-by-aaryaman.github.io/digital-pathshala-resources/videos.json`**; the supplied Apps Script `/exec` URL is already referenced by the site's frontend, but should be validated end to end after Pages works.
5. **Channel identity:** Public discovery is currently receiving HTTP 404 from YouTube in GitHub Actions. The fallback uses the verified public channel trailer in `config/site.json`; if both public routes remain unavailable, a stable YouTube **channel ID** (starting with `UC`) may need to be provided once as `youtube_channel_id`. This is public channel metadata, *not* an API credential.

## Publication safety

The system verifies scheduled eligibility, a matched public feed entry (plus Shorts tab or a strong title match), the SHA-256 integrity of the ZIP, and presence of the encrypted staging batch.

If multiple unrelated YouTube videos appear on the same day, the system holds uncertain cases. Publication can occur after 11 AM rather than exactly at 11:00. A public GitHub Pages ZIP URL is not access-protected: the form is a soft lead-collection gate before offering the download.

As of 12 November 2026, the GitHub repository and automated code exist, but the Pages website is **not yet live**, and the encrypted resource archive has **not** been uploaded to the repository.
