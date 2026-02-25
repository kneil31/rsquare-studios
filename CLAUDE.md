# CLAUDE.md — Rsquare Studios Dashboard

## IMPORTANT: Mobile-First Design

**Most users access this site on their phones via WhatsApp links.** Every change must be tested and optimized for mobile viewports first, desktop second. Always check how things look at 375px width (iPhone SE) and 390px width (iPhone 14).

## Project Overview

Notion-style dark-themed dashboard for Rsquare Studios photography business. Hosted on GitHub Pages.

- **Live URL:** https://portfolio.rsquarestudios.com/ (custom domain, CNAME → kneil31.github.io)
- **Legacy URL:** https://kneil31.github.io/rsquare-studios/ (redirects to custom domain)
- **GitHub Repo:** kneil31/rsquare-studios (public)
- **Generator:** `generate_dashboard.py` → outputs `index.html`
- **Client password:** `***REMOVED***` (unlocks pricing, booking, quote builder)
- **Internal password:** `***REMOVED***` (unlocks workflow, checklists, posing guides, editing projects)

## 3 Sections

1. **Portfolio** (client-facing) — Category tiles with cover photos linking to SmugMug galleries
2. **Investment / Pricing** (client-facing) — Hourly rate cards with interactive quote builder
3. **Workflow Dashboard** (password-protected) — Posing guides, workflow checklists, editing reference, editing project tracker

## Key Design Decisions

- **Mobile-first:** Bottom nav bar, floating WhatsApp button, large touch targets
- **Dark theme:** Notion-inspired (#191919 background, #8b5cf6 accent purple)
- **Hero layout:** Option D split (image left, text right) with CSS `mask-image` blend — photo dissolves into a purple-to-black gradient (`#2d1854` → `#0e0518` → `#050208`). On mobile, stacks vertically with bottom-fade blend.
- **Hero stats:** 300+ Galleries, 5+ Years, 50+ Weddings (real numbers from SmugMug + Ram)
- **Hero image:** `hero.jpg` — purple silhouette wedding photo (145KB, 1600px wide)
- **Two-level AES-256-GCM encryption:** Client sections (pricing, booking, `__config__`) and internal sections (workflow, checklists, posing guides) encrypted with separate passwords. No plaintext in HTML source. Encrypted payloads contain JSON data objects; JS builds DOM at runtime (no innerHTML).
- **Cover images:** Pulled from SmugMug API (highlight images per album). Each category tile has a background photo
- **Tile labels below image:** Category name and gallery count are displayed below the tile image (not overlaid on top), to avoid clashing with text in photos
- **Background position:** Per-category `background-position` values in `category_covers` dict (tuples of URL + position). Adjust position values when photos crop subjects poorly
- **No external dependencies:** Single self-contained HTML file, no frameworks
- **Professional copy:** "Investment" not "pricing", "images" not "pictures", "coverage" not "shooting"
- **Open Graph tags:** og:title, og:description, og:image (hero.jpg), og:url — enables WhatsApp/social link previews

## My Gear Section

- **Inline expandable section** on the home page — replaces the old kit.co external link
- **Data:** `GEAR_LIST` dict in `generate_dashboard.py` — 7 categories rendered at build time
- **Layout:** Collapsed by default, click to expand. 2-col grid (mobile) / 3-col (desktop)
- **Categories:** Camera Bodies, Lenses, Lighting, Light Modifiers, Stabilization & Drone, Monitors, Accessories
- **To update gear:** Edit the `GEAR_LIST` dict, then regenerate

## Data Sources

| Data | Source Path |
|------|-------------|
| Gallery links | `../rsqr_whatsapp_api/smugmug_galleries.json` |
| Posing guides | `../../../Upskill/Posing_Upskill/prompts/{couples,families,weddings}.md` |
| Workflow reference | `../../photo_workflow/PHOTO_WORKFLOW_CHEATSHEET.md` |
| Cover images | SmugMug API (image keys hardcoded in `category_covers` dict) |
| Editing projects | Google Sheet (primary) → `editing_projects.json` (fallback) |
| Client reviews | Google Sheet "Reviews" tab (primary) → `SEED_REVIEWS` in code (fallback) |
| Gear list | `GEAR_LIST` dict in `generate_dashboard.py` |

## Cover Images (SmugMug)

Each portfolio category has a cover photo. To swap an image:

1. Get the image key from a SmugMug organize URL (e.g., `i-BvTChsc` from `https://www.smugmug.com/app/organize/.../i-BvTChsc`)
2. Fetch the image URL via SmugMug API: `GET /api/v2/image/{imageKey}!sizes`
3. Use the `X3LargeImageUrl` (1600px — good balance of quality vs load time)
4. Update the `category_covers` dict in `generate_dashboard.py`
5. Adjust the background-position tuple value if the subject gets cropped

Current covers (all 9 categories have tuned `background-position`):
| Category | Image Key | Position |
|----------|-----------|----------|
| Wedding | BvTChsc | center 43% |
| Engagement | 8NfsLKT | 38% 47% |
| Pre-Wedding | GfR24FT | center 24% |
| Half Saree | MCmGphP | 68% 52% |
| Maternity | ZqWs3n5 | center 18% |
| Baby Shower | 3MjgbV3 | 37% 18% |
| Birthday | Xq8BHgp | center 40% |
| Cradle | R3QTwKk | center 47% |
| Celebrations | J8zjNdj | 38% 30% |

Homepage hero: `hero.jpg` — purple silhouette wedding photo (local file, not SmugMug). Option D split layout with CSS mask blend. Also used as OG image for WhatsApp/social link previews.

Spare image (not yet used): `i-6trRsbK`

## Custom Domain

- **Domain:** `portfolio.rsquarestudios.com`
- **CNAME file:** In repo root, content `portfolio.rsquarestudios.com`
- **DNS:** CNAME record `portfolio` → `kneil31.github.io` (GoDaddy, domaincontrol.com nameservers)
- **HTTPS:** Enforced via GitHub Pages (after DNS propagation)
- **OG tags and Slack messages** all reference the custom domain URL

## SmugMug API Auth

- **Credentials:** `~/.smugmug_config.json` (API key, API secret, OAuth1 tokens — never hardcode in source)
- **Helper scripts:** `fetch_cover_images.py`, `fetch_smugmug_sizes.py`, `fetch_album_stats.py`, `detect_cover_faces.py`

## Workflow

```bash
# Regenerate after changes
python3 generate_dashboard.py

# Push to GitHub Pages
git add index.html generate_dashboard.py
git commit -m "description"
git push

# Generate new client OTP (from terminal)
python3 generate_otp.py              # Generate + rebuild + push + Slack notify
python3 generate_otp.py --no-push    # Generate + rebuild only (no git push, no Slack)

# Generate new client OTP (from Slack)
# Type "otp" in #instagram-posts channel — generates, pushes, and sends password

# Cache busting — tell user to add ?v=N or use incognito

# Detect new video editing projects (aliases: megaup, megadet)
python3 detect_video_projects.py --scan-ssd      # Scan SSD, upload to MEGA + add to Sheet
python3 detect_video_projects.py --mega           # List MEGA folders, detect untracked
python3 detect_video_projects.py --mega-url URL   # Add specific MEGA URL directly
python3 detect_video_projects.py --scan-ssd --auto  # Unattended (LaunchAgent, 10 PM daily)

# Daily sync (runs automatically at 1 AM via LaunchAgent)
python3 sync_dashboard.py           # Sync from Google Sheet + deploy if changed
python3 sync_dashboard.py --force   # Regenerate + deploy even if unchanged
python3 sync_dashboard.py --dry-run # Regenerate but don't push
```

## OTP (Rotating Client Password)

- **Script:** `generate_otp.py` — generates random 8-char password, updates `.secret`, rebuilds dashboard, pushes to GitHub Pages
- **Slack command:** Type `otp` in #instagram-posts → bot calls `generate_otp.py`, sends password to Slack
- **Expiry:** 48 hours (logged in `.otp_log.json`, last 20 entries kept)
- **Internal password (`***REMOVED***`) is permanent** — OTP only rotates the client password
- **Slack notify:** Sends two messages: (1) client-ready copy-paste message with URL + password + sign-off, (2) internal expiry context
- **Slack message tone:** Warm & conversational — "Hey! Here's a private link to our portfolio and pricing" + "Let me know if you have any questions! — Ram"
- **Uses system python3** (`/opt/homebrew/bin/python3`) because `cryptography` package is not in Instagram AutoPoster venv

## Pricing (AES-encrypted in output)

- Solo Photography: $150/hr
- Solo Photo + Video: $235/hr
- Dual Coverage (Photo + Video): $325/hr
- All packages include: edited images, cinematic teaser, SmugMug gallery, lifetime cloud storage
- **Rate amounts are inside the encrypted `__config__` blob** — not visible in HTML source or JS
- Dropdown uses stable IDs (`photo_only`, `photo_video`, `dual_coverage`) instead of display strings

## Security

- **Two-level AES-256-GCM** encryption at build time (Python `cryptography` package)
  - `ENCRYPTED_CLIENT` blob: pricing, booking, `__config__` (rates) — password `***REMOVED***`
  - `ENCRYPTED_INTERNAL` blob: workflow, checklists, posing guides, editing projects — password `***REMOVED***`
- **Data-driven DOM building (no innerHTML):** Encrypted payloads contain JSON data objects, not pre-built HTML. JS uses `createElement`/`textContent` DOM builders to render all decrypted content (pricing cards, booking form, workflow sections, checklists, posing guides, editing projects). Matches krithin-neel's security pattern.
- **Safe markdown renderer:** Workflow reference and posing guides use a client-side markdown-to-DOM converter that builds elements via `createElement`/`textContent` — no `innerHTML` or `dangerouslySetInnerHTML`.
- **URL allowlist enforced:** `isAllowedUrl()` validates all dynamically set URLs — enforced in `makeLink()` (all anchor creation), `buildWorkflowHome()` (Notion link), and `shareQuoteWA()` (wa.me link). Unrecognized domains are blocked.
- **Referrer protection:** `referrerpolicy="no-referrer"` on hero `<img>` tag; `rel="noreferrer noopener"` on external links.
- **Web Crypto API** decryption at runtime (PBKDF2, 400k iterations, SHA-256)
- Random 16-byte salt + 12-byte IV per build (`os.urandom`)
- No sessionStorage/localStorage — decrypted content is memory-only (`_appConfig`)
- **Schema versioned** encrypted payloads (`"v": 1`)
- 3-strike lockout with 15s cooldown on wrong password
- **Password toggle** (show/hide eye icon) + password hint
- **Logout button** (visible when unlocked, clears decrypted content + reloads)
- **"Don't share" reminder** on password gate
- **Quote builder:** DOM-based construction (no innerHTML with user input — XSS safe)
- **Privacy:** `<meta name="robots" content="noindex, nofollow, noarchive">`
- Git history cleaned with `filter-repo` — no plaintext in old commits
- Client password cannot decrypt internal sections (verified via cross-test)

## Editing Project Tracker

- **Data:** Google Sheet is the single source of truth (Sheet ID in `sheets_sync.py`, "anyone with link")
- **Fallback:** `editing_projects.json` (local) used when Google Sheet is unreachable
- **Shared module:** `sheets_sync.py` — reads via public CSV export (no credentials needed for reads)
- **Sheet headers:** `Task`, `Neal Sent`, `Priority`, `Status`, `EDIT Completed`, `WeTransfer Link` — mapped generically
- **Date format:** Sheet uses `M/D/YYYY`, normalized to `YYYY-MM-DD` by `_normalize_date()`
- **Dashboard shows pending only:** Completed projects ("PROJECT Completed") filtered out — only SENT/OVERDUE shown
- **Status auto-detection:** SENT (blue), OVERDUE (red, >14 days)
- **Daily sync:** `sync_dashboard.py` runs at 1 AM via `com.rsquare.dashboard-sync.plist` — regenerates from Google Sheet + pushes if changed
- **Daily reminder:** `editing_reminder.py` runs at 10 AM via `com.rsquare.editing-reminder.plist`
- **Auto-detection (photo):** `detect_new_projects.py` scans Lightroom catalogs → adds new projects to Google Sheet (tab 1)
- **Auto-detection (video):** `detect_video_projects.py` scans SSD `Videos/` folders and MEGA → adds to Google Sheet (tab 2)
- **Video write access:** Apps Script POST (shared with reviews handler, `type=video_project` param) — no GCP/gspread needed
- **MEGA upload:** `detect_video_projects.py --scan-ssd` uploads MP4s to `/Root/Video RAW Data/{name} Videos/` via `megatools put`
- **MEGA account:** See `~/.megarc` for credentials
- **MEGA shared folder:** `https://***REMOVED***`
- **Video detect LaunchAgent:** `com.rsquare.video-detect.plist` — runs daily at 10 PM (`--scan-ssd --auto`), log: `/tmp/video-detect.log`
- **Aliases:** `megaup` (scan SSD + upload to MEGA), `megadet` (scan MEGA folders for untracked)
- **WhatsApp follow-up:** "Follow Up" button opens wa.me link with pre-filled message to editor
- **Laxman updates status directly in Google Sheet** — daily sync picks up changes automatically
- **Sync log:** `/tmp/dashboard-sync.log`

## Client Reviews

- **Google Sheet:** "Reviews" tab in `Rsquare_Review_Sheet` (separate sheet from editing projects)
- **Google Apps Script:** Shared `doPost(e)` handles both reviews (default) and video projects (`type=video_project`)
- **Apps Script URL:** `REVIEW_FORM_URL` constant in `generate_dashboard.py` (reviews); `VIDEO_PROJECT_SCRIPT_URL` in `sheets_sync.py` (video projects)
- **Module:** `sheets_sync.py` → `read_reviews()` reads approved reviews from the "Reviews" tab
- **Fallback:** `SEED_REVIEWS` list in `generate_dashboard.py` (4 hardcoded reviews)
- **Form:** Star rating (default 5), name, event type dropdown, textarea — on home page below reviews grid
- **Submit flow:** Form POSTs via `fetch` with `URLSearchParams` to Google Apps Script
- **Moderation:** All submissions land as "pending" → Ram approves in Google Sheet → regenerate to display
- **Status values:** `pending` / `approved` / `rejected`
- **XSS safe:** Reviews are HTML-escaped at build time in Python, not rendered dynamically

## Video Feedback Page

Client-facing page for submitting song choices and timestamped video corrections directly to the editor — removes Ram as middleman. Includes an **editor dashboard** for viewing and resolving corrections.

- **Client URL:** `portfolio.rsquarestudios.com/feedback/?p={project_slug}`
- **Editor URL:** `portfolio.rsquarestudios.com/feedback/?role=editor`
- **Generator:** `generate_feedback.py` → `feedback/index.html` (same file, role-switched via URL param)
- **Client access:** Project-specific passphrase (in `.feedback_secrets.json`, not the dashboard password)
- **Editor/Admin access:** Role passwords (in `.feedback_secrets.json`)
- **Encryption:** AES-256-GCM, same pattern as main dashboard — all secrets in `.feedback_secrets.json` (gitignored)

### Project Registry

Project config stored in `.feedback_secrets.json` (gitignored). Each project has slug, name, passphrase, editor info, phone numbers. All sensitive data encrypted into per-project and per-role blobs at build time.

### Forms

1. **Song Choice:** Song name + link + notes → Apps Script POST → WhatsApp to editor
2. **Corrections:** Timestamp rows (time + description + priority) + general notes → Apps Script POST → WhatsApp to editor

### Data Flow

```
Client submits form → fetch() POST → Google Apps Script (type=feedback)
  → appends to "Feedback" tab in Google Sheet
  → page shows wa.me link to editor with formatted message
```

### Google Sheet — "Feedback" Tab

Columns: `Project`, `Type` (song/correction), `Timestamp`, `Content`, `Priority`, `Submitted`, `PIN`, `Fixed`

- Column H (`Fixed`): "yes" or empty. Updated by editor via Apps Script `type=feedback_update` handler.

### Editor Dashboard

The editor view (`?role=editor`) provides:
- **Live data:** Fetches corrections from Google Sheet public CSV at runtime (no regenerate needed)
- **Project cards:** All projects grouped with status, version links, song choices, corrections
- **Fixed toggle:** Editor clicks "Fix" button → POSTs `type=feedback_update` to Apps Script → updates column H
- **Stats:** Shows X/Y corrections fixed per project
- **Client sees status:** Client view also fetches from Sheet and shows which corrections are fixed (read-only, green checkmarks)

Data flow:
```
Editor clicks "Fix" → fetch() POST (type=feedback_update) → Apps Script
  → finds row by Project + Timestamp + Content → sets column H = "yes"
  → editor UI updates immediately
  → client page shows green checkmark on next load
```

### WhatsApp Auto-Message Format

Opens `wa.me/{editor_phone}?text=...` with:
```
Hi bro

{Project} corrections:

[2:34] Remove this clip
[4:12] Add more of ceremony

Notes: ...
```

### Commands

```bash
# Generate feedback page
python3 generate_feedback.py

# Deploy (push to GitHub Pages with dashboard)
git add feedback/index.html generate_feedback.py
git commit -m "description"
git push
```

### Security

- PIN gate (4-digit, per-project, entered manually — not in URL)
- XSS safe: all DOM via `createElement`/`textContent`
- CSP with nonce, `connect-src` allows `script.google.com` + `docs.google.com` (CSV reads)
- URL allowlist for wa.me, script.google.com, docs.google.com
- No sensitive data exposed (only project name after PIN)

## Subprojects

- **krithin-neel/** — Separate repo (`kneil31/krithin-neel`), lives locally in this folder but is `.gitignore`d from rsquare-studios. Never add krithin-neel files to this repo.
  - **Custom domain:** `krithin.rsquarestudios.com` (CNAME → kneil31.github.io)

## Mobile-Specific Notes

- Bottom nav bar with 5 tabs (Home, Portfolio, Pricing, Book, Contact)
- Floating WhatsApp button (bottom-right, above nav bar)
- Category tiles use 2-column grid on mobile
- `safe-area-inset-bottom` for iPhone notch/home indicator
- Hero: split layout on desktop (image left 50%, text right), stacks vertically on mobile
- Hero image uses CSS `mask-image` to blend into background gradient (no hard edge)
- Test every layout change at 375px width minimum
