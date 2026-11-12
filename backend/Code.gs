/**
 * DIGITAL PATHSHALA BY AARYAMAN GOENKA — PERMANENT RESOURCE FORM BACKEND
 * Code.gs | Version 3.0 | 11 November 2026 | Time zone: Asia/Kolkata
 *
 * ONE-TIME SETUP
 * 1. Create a PRIVATE Google Sheet -> Extensions -> Apps Script.
 * 2. Paste this file into Code.gs. Run setupSheets() and grant permissions.
 * 3. Project Settings -> Script properties: add PUBLISHED_MANIFEST_URL with the
 *    HTTPS URL of the PUBLIC, RELEASED-VIDEOS-ONLY JSON manifest on GitHub Pages:
 *    https://YOUR-ACCOUNT.github.io/YOUR-REPO/videos.json
 * 4. Deploy -> New deployment -> Web app; Execute as: Me; Access: Anyone.
 *    Copy the /exec URL. Never put your private Sheet URL on your website.
 * 5. Once the publisher is deployed, run syncPublishedVideos() to fill Videos
 *    automatically, and optionally run installRegistrySyncTrigger() once.
 *
 * ADDING VIDEOS LATER: DO NOT EDIT OR REDEPLOY THIS SCRIPT.
 * The GitHub publication workflow updates videos.json when each video is live.
 * This script checks the public manifest directly on each form submission and
 * (optionally) mirrors the metadata into the Videos tab. A Sheets status cannot
 * override the public manifest: no early releases from manual Sheet edits.
 *
 * Frontend communication from GitHub Pages:
 *   POST text/plain JSON with fetch(...,{mode:'no-cors'}) and a random UUID.
 *   That response is opaque; NEVER treat request transmission as success.
 *   Poll GET ?action=receipt&request_id=<UUID>&callback=<safeCallback> as JSONP.
 * JSONP results contain NO names, email addresses, phone numbers or feedback.
 *
 * SECURITY/OPERATIONAL NOTES
 * - A public GitHub-hosted ZIP cannot be secured by an HTML form: soft gate only.
 * - Do NOT place unreleased ZIPs in a public branch, even if the page hides them.
 *   A publisher must keep packages private or encrypted until release time.
 * - Google Apps Script form endpoints can receive spam; honeypot is best-effort.
 * - Check your privacy notice, retention policy, quotas, and consent wording.
 * - This script does NOT upload ZIPs or publish GitHub Pages. That is the job
 *   of the GitHub Actions release workflow (configured separately).
 */

const DP = Object.freeze({
  VERSION: '3.0',
  TIMEZONE: 'Asia/Kolkata',
  MANIFEST_PROPERTY: 'PUBLISHED_MANIFEST_URL',
  SHEET_PROPERTY: 'SPREADSHEET_ID',
  PAUSE_PROPERTY: 'PAUSE_PUBLIC_SUBMISSIONS', // set to TRUE to halt new form submissions
  MANIFEST_CACHE_SECONDS: 45,
  RECEIPT_CACHE_SECONDS: 900,
  MAX_POST_BYTES: 12000,
  MAX_VIDEOS: 10000,
  SHEETS: Object.freeze({
    VIDEOS: 'Videos',
    LEADS: 'Download_Leads',
    FEEDBACK: 'Private_Feedback',
    RECEIPTS: 'Request_Receipts',
    INDEPENDENT_LEADS: 'Independent_Downloads',
    INDEPENDENT_FEEDBACK: 'Independent_Feedback'
  })
});

const DP_COLUMNS = Object.freeze({
  Videos: [
    'video_id','video_title','video_type','release_at_ist','status',
    'resource_url','youtube_url','notes','last_synced_ist'
  ],
  Download_Leads: [
    'submitted_at_ist','request_id','video_id','video_title','video_type',
    'full_name','email','phone','privacy_consent','marketing_opt_in',
    'page_url','referrer','utm_source','utm_medium','utm_campaign'
  ],
  Private_Feedback: [
    'submitted_at_ist','request_id','video_id','video_title','feedback_type',
    'message','name','email','privacy_consent','page_url'
  ],
  Independent_Downloads: [
    'submitted_at_ist','request_id','resource_id','resource_title','resource_type',
    'full_name','email','phone','privacy_consent','marketing_opt_in',
    'page_url','referrer','utm_source','utm_medium','utm_campaign'
  ],
  Independent_Feedback: [
    'submitted_at_ist','request_id','resource_id','resource_title','feedback_type',
    'message','name','email','privacy_consent','page_url'
  ],
  Request_Receipts: [
    'request_id','submitted_at_ist','action','video_id','status','download_url'
  ]
});

/** Run once from Apps Script editor while bound to your private Google Sheet. */
function setupSheets() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  if (!ss) {
    throw new Error('Create this Apps Script from Google Sheet > Extensions > Apps Script.');
  }
  PropertiesService.getScriptProperties().setProperty(DP.SHEET_PROPERTY, ss.getId());
  Object.keys(DP_COLUMNS).forEach(function(tabName) {
    const columns = DP_COLUMNS[tabName];
    let sh = ss.getSheetByName(tabName);
    if (!sh) sh = ss.insertSheet(tabName);
    if (sh.getMaxColumns() < columns.length) {
      sh.insertColumnsAfter(sh.getMaxColumns(), columns.length - sh.getMaxColumns());
    }
    if (sh.getLastRow() === 0) {
      sh.getRange(1, 1, 1, columns.length).setValues([columns]);
    } else {
      const actual = sh.getRange(1, 1, 1, columns.length).getDisplayValues()[0];
      // Safe migration from v1: original Videos tab has the same first 8
      // headers and no ninth 'last_synced_ist' column. Add only the header.
      if (tabName === DP.SHEETS.VIDEOS &&
          actual.slice(0, 8).join('\t') === columns.slice(0, 8).join('\t') &&
          actual[8] === '') {
        sh.getRange(1, 9).setValue('last_synced_ist');
      } else if (actual.join('\t') !== columns.join('\t')) {
        throw new Error('Tab ' + tabName + ' already has different columns. Nothing was erased.');
      }
    }
    sh.setFrozenRows(1);
    sh.getRange(1, 1, 1, columns.length)
      .setBackground('#102A43').setFontColor('#FFFFFF').setFontWeight('bold');
  });
  const videos = ss.getSheetByName(DP.SHEETS.VIDEOS);
  videos.getRange('A:I').setNumberFormat('@');
  Logger.log('Sheet is ready. Add Script Property PUBLISHED_MANIFEST_URL, then deploy /exec.');
  return { ready: true, sheet: ss.getUrl() };
}

/** Optional once-only hourly mirror of the public manifest into the Videos tab. */
function installRegistrySyncTrigger() {
  const exists = ScriptApp.getProjectTriggers().some(function(trigger) {
    return trigger.getHandlerFunction() === 'syncPublishedVideos';
  });
  if (!exists) ScriptApp.newTrigger('syncPublishedVideos').timeBased().everyHours(1).create();
  Logger.log(exists ? 'Registry trigger already installed.' : 'Hourly registry trigger installed.');
}

/** Public-safe read endpoints. No personally identifying information returned. */
function doGet(e) {
  const p = e && e.parameter ? e.parameter : {};
  const callback = dpText_(p.callback, 70);
  let result;
  try {
    if (p.action === 'health' || !p.action) {
      result = { status: 'ok', service: 'Digital Pathshala Resources', version: DP.VERSION,
        configured: !!PropertiesService.getScriptProperties().getProperty(DP.MANIFEST_PROPERTY) };
    } else if (p.action === 'receipt') {
      const id = dpText_(p.request_id, 80);
      result = dpIsUuid_(id) ? dpGetReceipt_(id) : dpErrorResult_('INVALID_REQUEST_ID', 'Invalid request ID.');
    } else if (p.action === 'video' || p.action === 'resource') {
      const id = dpText_(p.video_id || p.v, 72).toLowerCase();
      result = dpPublicVideoStatus_(id);
    } else {
      result = dpErrorResult_('UNKNOWN_ACTION', 'Unknown action.');
    }
  } catch (err) {
    console.error('GET failed: ' + String(err && err.message || err));
    result = dpErrorResult_(err && err.dpCode || 'TEMPORARILY_UNAVAILABLE',
      'Service temporarily unavailable. Please try again.');
  }
  if (!callback) return dpJson_(result);
  // Prevent callback injection; allow only a single JavaScript identifier.
  if (!/^[A-Za-z_$][A-Za-z0-9_$]{0,63}$/.test(callback)) {
    return ContentService.createTextOutput('/* invalid callback */')
      .setMimeType(ContentService.MimeType.JAVASCRIPT);
  }
  // JSONP is intentionally READ-ONLY and never includes private Sheet data.
  const js = callback + '(' + JSON.stringify(result)
    .replace(/</g, '\\u003c').replace(/\u2028/g, '\\u2028').replace(/\u2029/g, '\\u2029') + ');';
  return ContentService.createTextOutput(js).setMimeType(ContentService.MimeType.JAVASCRIPT);
}

/** Receives a form as text/plain JSON. Responses need receipt polling in browser. */
function doPost(e) {
  let requestId = '';
  try {
    if (!e || !e.postData || !e.postData.contents) throw dpProblem_('EMPTY_REQUEST', 'No form received.');
    if (e.postData.contents.length > DP.MAX_POST_BYTES) throw dpProblem_('TOO_LARGE', 'Form is too large.');
    const p = JSON.parse(e.postData.contents);
    if (!p || typeof p !== 'object' || Array.isArray(p)) throw dpProblem_('INVALID_BODY', 'Invalid form.');
    requestId = dpText_(p.request_id, 80);
    if (!dpIsUuid_(requestId)) throw dpProblem_('INVALID_REQUEST_ID', 'Invalid request ID.');
    const result = dpProcessSubmission_(p, requestId);
    dpCacheReceipt_(requestId, result);
    return dpJson_(result);
  } catch (err) {
    const answer = dpErrorResult_(err && err.dpCode || 'SUBMISSION_FAILED',
      err && err.dpCode ? err.message : 'Could not save your submission. Please try again.');
    if (dpIsUuid_(requestId)) dpCacheReceipt_(requestId, answer);
    console.error('POST failed (' + answer.code + '): ' + String(err && err.message || err));
    return dpJson_(answer);
  }
}

function dpProcessSubmission_(p, requestId) {
  if (dpIsPaused_()) throw dpProblem_('PAUSED', 'Submissions are temporarily unavailable.');
  const action = dpText_(p.action, 20).toLowerCase();
  if (action !== 'download' && action !== 'feedback') throw dpProblem_('INVALID_ACTION', 'Invalid form type.');
  if (dpText_(p.website, 180)) throw dpProblem_('NOT_ACCEPTED', 'Form was not accepted.');
  if (p.privacy_consent !== true) throw dpProblem_('CONSENT_REQUIRED', 'Please accept the privacy notice.');
  const manifestUrl = dpManifestUrl_();
  const siteRoot = dpSiteRoot_(manifestUrl);
  const pageUrl = dpText_(p.page_url, 700);
  const videoId = dpIdFromPage_(pageUrl, siteRoot);
  if (!videoId) throw dpProblem_('INVALID_PAGE', 'Please open the official resource page.');
  if (p.resource_id && dpText_(p.resource_id, 72).toLowerCase() !== videoId) {
    throw dpProblem_('RESOURCE_MISMATCH', 'Page and resource do not match.');
  }
  if (p.video_id && dpText_(p.video_id, 72).toLowerCase() !== videoId) {
    throw dpProblem_('VIDEO_MISMATCH', 'The page and video do not match.');
  }
  // Publication is authoritative: Sheet rows NEVER authorize a release.
  const video = dpPublishedVideo_(videoId, dpPublishedManifest_());
  if (!video) throw dpProblem_('NOT_RELEASED', 'This resource is not available yet.');
  if (action === 'download' && !dpValidResourceUrl_(video.resource_url, siteRoot, video.type)) {
    throw dpProblem_('RESOURCE_NOT_READY', 'The download has not been published yet.');
  }

  // Validate all user inputs BEFORE acquiring a Sheets lock.
  const fullName = action === 'download'
    ? dpRequired_(p.full_name, 100, 'Name') : dpText_(p.full_name, 100);
  const email = dpEmail_(p.email, action === 'download');
  const phone = action === 'download' ? dpPhone_(p.phone) : '';
  const message = action === 'feedback' ? dpRequired_(p.message, 1800, 'Message') : '';
  const feedbackType = dpText_(p.feedback_type, 50) || 'question';
  const now = Utilities.formatDate(new Date(), DP.TIMEZONE, 'yyyy-MM-dd HH:mm:ss');
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(20000)) throw dpProblem_('BUSY', 'Server busy. Please try again.');
  try {
    const old = dpFindReceiptInSheet_(requestId);
    if (old) return dpCheckedReceipt_(old, action, videoId);

    // Repair interrupted submissions: lead/feedback written, receipt not yet written.
    const repaired = dpRepairReceipt_(requestId, action, videoId, video, now);
    if (repaired) return repaired;

    const ss = dpSpreadsheet_();
    if (action === 'download') {
      ss.getSheetByName(dpIsIndependentType_(video.type) ? DP.SHEETS.INDEPENDENT_LEADS : DP.SHEETS.LEADS).appendRow([
        now, requestId, video.id, dpCell_(video.title), dpCell_(video.type),
        dpCell_(fullName), dpCell_(email), dpCell_(phone), 'YES',
        p.marketing_opt_in === true ? 'YES' : 'NO', dpCell_(pageUrl),
        dpCell_(dpText_(p.referrer, 700)), dpCell_(dpText_(p.utm_source, 100)),
        dpCell_(dpText_(p.utm_medium, 100)), dpCell_(dpText_(p.utm_campaign, 100))
      ]);
    } else {
      ss.getSheetByName(dpIsIndependentType_(video.type) ? DP.SHEETS.INDEPENDENT_FEEDBACK : DP.SHEETS.FEEDBACK).appendRow([
        now, requestId, video.id, dpCell_(video.title), dpCell_(feedbackType),
        dpCell_(message), dpCell_(fullName), dpCell_(email), 'YES', dpCell_(pageUrl)
      ]);
    }
    const response = { status: 'ok', action: action, video_id: video.id,
      download_url: action === 'download' ? video.resource_url : '' };
    dpStoreReceipt_(requestId, now, response);
    return response;
  } finally {
    lock.releaseLock();
  }
}

function dpRepairReceipt_(requestId, action, videoId, video, now) {
  const sh = dpSpreadsheet_().getSheetByName(
    action === 'download'
      ? (dpIsIndependentType_(video.type) ? DP.SHEETS.INDEPENDENT_LEADS : DP.SHEETS.LEADS)
      : (dpIsIndependentType_(video.type) ? DP.SHEETS.INDEPENDENT_FEEDBACK : DP.SHEETS.FEEDBACK));
  const rowNum = dpFindIdRow_(sh, requestId, 2);
  if (!rowNum) return null;
  const rowVideoId = dpText_(sh.getRange(rowNum, 3).getValue(), 72);
  if (rowVideoId !== videoId) throw dpProblem_('REQUEST_ID_REUSED', 'Request ID already used.');
  const response = { status: 'ok', action: action, video_id: videoId,
    download_url: action === 'download' ? video.resource_url : '' };
  dpStoreReceipt_(requestId, now, response);
  return response;
}

function dpStoreReceipt_(requestId, now, response) {
  dpSpreadsheet_().getSheetByName(DP.SHEETS.RECEIPTS).appendRow([
    requestId, now, response.action, response.video_id, 'ok', response.download_url
  ]);
}

function dpCheckedReceipt_(old, action, videoId) {
  if (old.action !== action || old.video_id !== videoId) {
    throw dpProblem_('REQUEST_ID_REUSED', 'Request ID already used.');
  }
  return old;
}

function dpGetReceipt_(requestId) {
  const cached = CacheService.getScriptCache().get('dp-receipt-' + requestId);
  if (cached) { try { return JSON.parse(cached); } catch (ignore) {} }
  return dpFindReceiptInSheet_(requestId) || { status: 'pending' };
}

function dpFindReceiptInSheet_(requestId) {
  const sh = dpSpreadsheet_().getSheetByName(DP.SHEETS.RECEIPTS);
  const rowNumber = dpFindIdRow_(sh, requestId, 1);
  if (!rowNumber) return null;
  const row = sh.getRange(rowNumber, 1, 1, 6).getValues()[0];
  return { status: String(row[4]), action: String(row[2]),
    video_id: String(row[3]), download_url: String(row[5] || '') };
}

function dpFindIdRow_(sheet, id, col) {
  if (sheet.getLastRow() < 2) return 0;
  const match = sheet.getRange(2, col, sheet.getLastRow() - 1, 1)
    .createTextFinder(id).matchEntireCell(true).findNext();
  return match ? match.getRow() : 0;
}

function dpCacheReceipt_(id, result) {
  try { CacheService.getScriptCache().put('dp-receipt-' + id,
      JSON.stringify(result), DP.RECEIPT_CACHE_SECONDS); }
  catch (ignore) { /* Successful receipts remain in Sheet. */ }
}

function dpPublicVideoStatus_(id) {
  if (!dpValidVideoId_(id)) return dpErrorResult_('INVALID_VIDEO', 'Invalid video identifier.');
  const video = dpPublishedVideo_(id, dpPublishedManifest_());
  return video ? { status: 'live', video_id: video.id, title: video.title,
    resource_available: true } : { status: 'not_released', video_id: id };
}

/** One authoritative, PUBLIC manifest generated by the GitHub release workflow. */
function dpPublishedManifest_() {
  const url = dpManifestUrl_();
  const cache = CacheService.getScriptCache();
  const key = 'dp-published-catalog-v3';
  const cached = cache.get(key);
  if (cached) {
    try { return JSON.parse(cached); } catch (ignore) {}
  }
  let response;
  try {
    response = UrlFetchApp.fetch(url, { muteHttpExceptions: true,
      followRedirects: true, validateHttpsCertificates: true,
      headers: { 'Accept': 'application/json' } });
  } catch (err) {
    throw dpProblem_('CATALOG_UNAVAILABLE', 'The video catalogue is unavailable.');
  }
  if (response.getResponseCode() !== 200) {
    throw dpProblem_('CATALOG_UNAVAILABLE', 'The video catalogue is unavailable.');
  }
  let data;
  try { data = JSON.parse(response.getContentText()); }
  catch (ignore) { throw dpProblem_('CATALOG_INVALID', 'The video catalogue has invalid JSON.'); }
  if (!data || !Array.isArray(data.videos) || data.videos.length > DP.MAX_VIDEOS) {
    throw dpProblem_('CATALOG_INVALID', 'The video catalogue is not in the supported format.');
  }
  // Merge only the live independent catalogue published by the same Pages site.
  // Draft metadata never authorizes a download.
  const independentUrl = url.replace(/videos\.json$/, 'independent.json');
  let independentResponse;
  try {
    independentResponse = UrlFetchApp.fetch(independentUrl, {
      muteHttpExceptions: true, followRedirects: true, validateHttpsCertificates: true,
      headers: { 'Accept': 'application/json' }
    });
  } catch (err) {
    throw dpProblem_('CATALOG_UNAVAILABLE', 'Independent resource catalogue is unavailable.');
  }
  if (independentResponse.getResponseCode() !== 200) {
    throw dpProblem_('CATALOG_UNAVAILABLE', 'Independent resource catalogue has not been published.');
  }
  let independent;
  try { independent = JSON.parse(independentResponse.getContentText()); }
  catch (ignore) { throw dpProblem_('CATALOG_INVALID', 'Invalid independent resource catalogue.'); }
  if (!independent || !Array.isArray(independent.resources) ||
      independent.resources.length > DP.MAX_VIDEOS) {
    throw dpProblem_('CATALOG_INVALID', 'Unexpected independent resource catalogue.');
  }
  independent.resources.forEach(function(r) {
    const id = dpText_(r.id, 72).toLowerCase();
    const kind = dpText_(r.kind, 30).toLowerCase();
    const slug = dpText_(r.slug, 72).toLowerCase();
    const root = dpSiteRoot_(url);
    const paths = {ebook:'ebooks',template:'templates',guide:'guides',tool:'tools',resource:'resources'};
    if (!paths[kind] || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug) ||
        id !== kind + '-' + slug ||
        dpText_(r.page_url, 1000) !== root + paths[kind] + '/' + slug + '/' ||
        dpText_(r.status, 30) !== 'live' ||
        !dpValidResourceUrl_(dpText_(r.resource_url, 1500), root, kind)) {
      throw dpProblem_('CATALOG_INVALID', 'Invalid published independent resource.');
    }
    data.videos.push({
      id: id, title: r.title, type: kind, status: 'live',
      release_at_ist: r.published_at_ist, resource_url: r.resource_url,
      page_url: r.page_url, youtube_url: ''
    });
  });
  // Treat duplicate IDs as a deployment mistake: fail CLOSED.
  const ids = {};
  data.videos.forEach(function(v) {
    const id = dpText_(v && (v.id || v.slug), 72).toLowerCase();
    if (!dpValidVideoId_(id) || ids[id]) {
      throw dpProblem_('CATALOG_INVALID', 'Duplicate or invalid video identifier.');
    }
    ids[id] = true;
  });
  const json = JSON.stringify(data);
  // Google ScriptCache has a per-item limit. Skip caching if too large.
  if (json.length < 90000) {
    try { cache.put(key, json, DP.MANIFEST_CACHE_SECONDS); } catch (ignore) {}
  }
  return data;
}

function dpPublishedVideo_(id, manifest) {
  const siteRoot = dpSiteRoot_(dpManifestUrl_());
  for (let i = 0; i < manifest.videos.length; i++) {
    const v = manifest.videos[i];
    if (dpText_(v.id || v.slug, 72).toLowerCase() !== id) continue;
    // Backend authorizes ONLY explicitly live entries with valid release times.
    if (dpText_(v.status, 30).toLowerCase() !== 'live') return null;
    const release = dpReleaseTime_(v.release_at_ist);
    if (!release || dpNowIstMinute_() < release) return null;
    const resource = dpText_(v.resource_url, 1500);
    if (!dpValidResourceUrl_(resource, siteRoot, v.type)) return null;
    return { id: id, title: dpText_(v.title, 250) || id,
      type: dpText_(v.type, 50), release_at_ist: release,
      resource_url: resource, youtube_url: dpText_(v.youtube_url, 700) };
  }
  return null;
}

/** Updates ONLY the non-sensitive Videos mirror; does not release any file. */
function syncPublishedVideos() {
  const manifest = dpPublishedManifest_();
  const ss = dpSpreadsheet_();
  const sh = ss.getSheetByName(DP.SHEETS.VIDEOS);
  if (!sh) throw new Error('Run setupSheets() first.');
  const siteRoot = dpSiteRoot_(dpManifestUrl_());
  const observed = {};
  const now = Utilities.formatDate(new Date(), DP.TIMEZONE, 'yyyy-MM-dd HH:mm:ss');
  const newRows = [];
  const existing = {};
  if (sh.getLastRow() > 1) {
    const rows = sh.getRange(2, 1, sh.getLastRow() - 1, 1).getValues();
    rows.forEach(function(row, i) { if (row[0]) existing[String(row[0])] = i + 2; });
  }
  const updates = [];
  manifest.videos.forEach(function(v) {
    const id = dpText_(v.id || v.slug, 72).toLowerCase();
    const release = dpReleaseTime_(v.release_at_ist);
    const ready = dpPublishedVideo_(id, { videos: [v] });
    // A future-dated or incomplete item is mirrored as HOLD, never as live.
    const status = ready ? 'LIVE' : 'HOLD';
    const zip = dpText_(v.resource_url, 1500);
    const notes = existing[id] ? sh.getRange(existing[id], 8).getValue() : '';
    if (dpIsIndependentType_(v.type)) return; // Independent submissions use separate Sheets tabs.
    const row = [id, dpCell_(dpText_(v.title, 250)), dpCell_(dpText_(v.type, 50)),
      release || '', status, dpValidResourceUrl_(zip, siteRoot) ? zip : '',
      dpCell_(dpText_(v.youtube_url, 700)), notes, now];
    observed[id] = true;
    if (existing[id]) updates.push({ row: existing[id], values: row });
    else newRows.push(row);
  });
  updates.forEach(function(x) { sh.getRange(x.row, 1, 1, 9).setValues([x.values]); });
  if (newRows.length) {
    sh.getRange(sh.getLastRow() + 1, 1, newRows.length, 9).setValues(newRows);
  }
  // Preserve older rows for reporting, but clearly mark removed items inactive.
  Object.keys(existing).forEach(function(id) {
    if (!observed[id] && String(sh.getRange(existing[id], 5).getValue()) === 'LIVE') {
      sh.getRange(existing[id], 5).setValue('UNPUBLISHED');
    }
  });
  Logger.log('Synchronized ' + manifest.videos.length + ' public manifest records.');
  return { mirrored: manifest.videos.length, new_rows: newRows.length, observed_at_ist: now };
}

/** Safe editor-side diagnostics. Returns no private submissions or messages. */
function checkSetup() {
  const ss = dpSpreadsheet_();
  const url = dpManifestUrl_();
  Object.keys(DP_COLUMNS).forEach(function(n) {
    if (!ss.getSheetByName(n)) throw new Error('Missing tab ' + n + '; run setupSheets().');
  });
  Logger.log('Configured Sheet: ' + ss.getName());
  Logger.log('Public manifest: ' + url);
  const manifest = dpPublishedManifest_();
  Logger.log('Published manifest entries: ' + manifest.videos.length);
  return { version: DP.VERSION, manifest_items: manifest.videos.length, ready: true };
}

function dpSpreadsheet_() {
  const id = PropertiesService.getScriptProperties().getProperty(DP.SHEET_PROPERTY);
  if (!id) throw dpProblem_('NOT_CONFIGURED', 'Run setupSheets() in the bound Sheet first.');
  return SpreadsheetApp.openById(id);
}

function dpManifestUrl_() {
  const url = dpText_(PropertiesService.getScriptProperties()
    .getProperty(DP.MANIFEST_PROPERTY), 1000);
  if (!/^https:\/\/[A-Za-z0-9.-]+(?:\/[A-Za-z0-9_./-]*)?\/videos\.json$/.test(url)) {
    throw dpProblem_('NOT_CONFIGURED', 'Set Script Property PUBLISHED_MANIFEST_URL to your GitHub Pages videos.json URL.');
  }
  return url;
}

function dpSiteRoot_(url) { return url.replace(/videos\.json$/, ''); }
function dpIsPaused_() {
  return String(PropertiesService.getScriptProperties().getProperty(DP.PAUSE_PROPERTY) || '')
    .toUpperCase() === 'TRUE';
}
function dpIsIndependentType_(type) {
  return /^(ebook|template|guide|tool|resource)$/.test(String(type || ''));
}
function dpValidResourceUrl_(url, root, type) {
  if (!url || /[\s#]/.test(url) || url.length > 1500) return false;
  if (dpIsIndependentType_(type)) {
    return url.indexOf(root + 'downloads/') === 0 &&
      /\.(pdf|xlsx|xlsm|zip)$/i.test(url) &&
      !/[?\\]/.test(url);
  }
  return url.indexOf(root + 'resources/') === 0 && /\.zip(?:\?.*)?$/i.test(url);
}
function dpIdFromPage_(url, root) {
  // Ignore URL fragments; browsers may append #resources when users navigate.
  const cleanUrl = String(url || '').split('#')[0];
  if (!cleanUrl || cleanUrl.indexOf(root) !== 0 || /\s/.test(cleanUrl)) return '';
  const suffix = cleanUrl.slice(root.length);
  const indie = /^(ebooks|templates|guides|tools|resources)\/([a-z0-9]+(?:-[a-z0-9]+)*)\/(?:index\.html)?(?:\?[^#]*)?$/.exec(suffix);
  if (indie) {
    const singular = {ebooks:'ebook',templates:'template',guides:'guide',tools:'tool',resources:'resource'};
    return singular[indie[1]] + '-' + indie[2];
  }
  // Only resource page paths are accepted: video.html?v=<ID>, index.html?v=<ID>
  // or future clean URLs v/<ID>. Never trust a visitor-selected video ID.
  const page = /^(?:index|video)\.html\?/.test(suffix) || /^\?/.test(suffix);
  const clean = /^v\/([a-z0-9][a-z0-9-]{1,71})\/?(?:\?.*)?$/i.exec(suffix);
  if (clean) return clean[1].toLowerCase();
  if (!page) return '';
  const query = suffix.indexOf('?') >= 0 ? suffix.slice(suffix.indexOf('?') + 1) : '';
  const match = /(?:^|&)v=([a-z0-9][a-z0-9-]{1,71})(?:&|$)/i.exec(query);
  return match && dpValidVideoId_(match[1].toLowerCase()) ? match[1].toLowerCase() : '';
}
function dpNowIstMinute_() {
  return Utilities.formatDate(new Date(), DP.TIMEZONE, 'yyyy-MM-dd HH:mm');
}
function dpReleaseTime_(value) {
  const raw = dpText_(value, 44);
  const date = raw.replace('T', ' ').replace(/(?::00)?\+05:30$/, '');
  // Only explicit India-local time; publishers should supply YYYY-MM-DD HH:mm.
  if (!/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/.test(date)) return '';
  const m = /^(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2})$/.exec(date);
  const y = Number(m[1]), mon = Number(m[2]), d = Number(m[3]);
  const h = Number(m[4]), min = Number(m[5]);
  const test = new Date(Date.UTC(y, mon - 1, d));
  if (test.getUTCFullYear() !== y || test.getUTCMonth() !== mon - 1 ||
      test.getUTCDate() !== d || h > 23 || min > 59) return '';
  return date;
}
function dpValidVideoId_(id) { return /^[a-z0-9][a-z0-9-]{1,71}$/.test(id); }
function dpIsUuid_(id) {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id);
}
function dpText_(x, length) {
  return String(x === null || x === undefined ? '' : x)
    .replace(/[\x00-\x08\x0b\x0c\x0e-\x1f]/g, '').trim().slice(0, length);
}
function dpRequired_(x, length, name) {
  const value = dpText_(x, length);
  if (!value) throw dpProblem_('MISSING_FIELD', name + ' is required.');
  return value;
}
function dpEmail_(x, required) {
  const v = dpText_(x, 180).toLowerCase();
  if (!v && !required) return '';
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) throw dpProblem_('INVALID_EMAIL', 'Enter a valid email address.');
  return v;
}
function dpPhone_(x) {
  const v = dpText_(x, 30);
  if (v && !/^[+0-9()\s-]{7,30}$/.test(v)) throw dpProblem_('INVALID_PHONE', 'Enter a valid phone number.');
  return v;
}
function dpCell_(x) {
  const value = String(x === null || x === undefined ? '' : x);
  return /^\s*[=+\-@]/.test(value) ? "'" + value : value;
}
function dpProblem_(code, message) { const error = new Error(message); error.dpCode = code; return error; }
function dpErrorResult_(code, message) { return { status: 'error', code: code, message: message }; }
function dpJson_(object) {
  return ContentService.createTextOutput(JSON.stringify(object))
    .setMimeType(ContentService.MimeType.JSON);
}