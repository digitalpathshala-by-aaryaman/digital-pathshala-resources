# Digital Pathshala release setup

The public resource count starts at **0**. The 90 prepared videos are internal registry records, **not** public downloads.

## One-time setup

1. In **GitHub Settings → Pages**, select **GitHub Actions** as the Pages source.
2. Add Actions secrets `DP_VAULT_PASSPHRASE` (the private batch encryption key) and `YOUTUBE_API_KEY` (YouTube Data API v3, videos.list).
3. Add the encrypted resource file `vault/batch-001.zip.enc`. **Do not upload plaintext resources to any public branch, even temporarily.**
4. Enter an official privacy request contact email in `config/site.json` under `privacy_contact_email`. The release script refuses to publish resources until this is done.
5. In the existing private Google Sheet Apps Script, set Script Property `PUBLISHED_MANIFEST_URL` to `https://digitalpathshala-by-aaryaman.github.io/digital-pathshala-resources/videos.json`; then check `setupSheets()` and deployment.
6. Run the **Publish Digital Pathshala Resources** GitHub Actions workflow once to deploy the empty site. Scheduled builds repeat every 15 minutes (best effort).

## Adding videos

Each new video's metadata goes in `config/videos.json`. Set `youtube_id` (11-character public YouTube video ID), `release_at_ist` (`YYYY-MM-DD HH:mm`), `approved: true`, and the SHA-256 of its resource ZIP. Place only the **encrypted** ZIP batch in `vault/`. The workflow releases a resource only if the due time has passed, YouTube's API reports the video as **public**, the ZIP is found in the encrypted batch, and its SHA-256 matches. Without any one of these requirements, it remains unpublished.

All released videos share one page template, one Apps Script endpoint, one Google Sheet, and one public repository. Public links look like `https://digitalpathshala-by-aaryaman.github.io/digital-pathshala-resources/?v=long-01`.

## Security limitations

The form is a soft gate: after publication, anyone who knows the ZIP URL may download it without filling the form. Apps Script confirms a saved submission before the browser starts the download. The site does not publicly display private feedback. The scheduled Actions check is not exact-to-the-second and can run late. Verify the privacy notice, retention policy, and contact method before collecting data.
