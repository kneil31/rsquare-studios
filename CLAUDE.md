# CLAUDE.md — Rsquare Studios Dashboard

## IMPORTANT: Mobile-First Design

**Most users access this site on their phones via WhatsApp links.** Every change must be tested and optimized for mobile viewports first, desktop second. Always check how things look at 375px width (iPhone SE) and 390px width (iPhone 14).

## IMPORTANT: No Secrets in This File

**This file is on a PUBLIC repo.** Never put passwords, phone numbers, emails, API keys, Sheet IDs, MEGA links, or any personal information here. All secrets live in gitignored local files (`.secret`, `.dashboard_secrets.json`, `.feedback_secrets.json`).

## Project Overview

Notion-style dark-themed dashboard for Rsquare Studios photography business. Hosted on GitHub Pages.

- **Live URL:** https://portfolio.rsquarestudios.com/ (custom domain, CNAME → kneil31.github.io)
- **GitHub Repo:** kneil31/rsquare-studios (public)
- **Generator:** `generate_dashboard.py` → outputs `index.html`, `photos.html`, `videos.html`
- **Passwords:** Stored in `.secret` file (gitignored, never committed)

## 3 Sections (All Encrypted)

1. **Portfolio** (client-facing, password-protected) — Category tiles, gallery cards, videos, reviews, gear — all encrypted
2. **Investment / Pricing** (client-facing, password-protected) — Hourly rate cards with interactive quote builder
3. **Workflow Dashboard** (password-protected) — Posing guides, workflow checklists, editing reference, editing project tracker

**Nothing is visible without a password or auto-unlock link.** Home page shows only a password gate.

## Key Design Decisions

- **Mobile-first:** Bottom nav bar, floating WhatsApp button, large touch targets
- **Dark theme:** Notion-inspired (#191919 background, #8b5cf6 accent purple)
- **Hero layout:** Option D split (image left, text right) with CSS `mask-image` blend
- **Full AES-256-GCM encryption:** Portfolio, pricing, workflow — ALL content encrypted. Home page shows only password gate. No plaintext gallery data, SmugMug URLs, YouTube IDs, or client names in HTML source.
- **Data-driven DOM building (no innerHTML):** Encrypted payloads contain JSON data objects; JS builds DOM at runtime (`buildHome`, `buildPortfolioHome`, `buildPortfolioCategory`, `buildVideos`, `buildPricing`, etc.)
- **Cover images:** Pulled from SmugMug API (highlight images per album)
- **Tile labels below image:** Category name and gallery count displayed below the tile image, not overlaid
- **No external dependencies:** Single self-contained HTML file, no frameworks
- **Professional copy:** "Investment" not "pricing", "images" not "pictures", "coverage" not "shooting"
- **Open Graph tags:** og:title, og:description, og:image (hero.jpg), og:url

## My Gear Section

- **Inline expandable section** on the home page (inside encrypted blob)
- **Data:** `GEAR_LIST` dict in `generate_dashboard.py` — 7 categories, encrypted into client blob, rebuilt by `buildHome()` JS function
- **Layout:** Collapsed by default, click to expand. 2-col grid (mobile) / 3-col (desktop)

## Cover Images (SmugMug)

Each portfolio category has a cover photo. To swap:
1. Get image key from SmugMug organize URL
2. Fetch URL via SmugMug API: `GET /api/v2/image/{imageKey}!sizes`
3. Use `X3LargeImageUrl` (1600px)
4. Update `category_covers` dict in `generate_dashboard.py`
5. Adjust `background-position` if subject gets cropped

## Custom Domain

- **Domain:** `portfolio.rsquarestudios.com`
- **CNAME file:** In repo root
- **DNS:** CNAME record at GoDaddy
- **HTTPS:** Enforced via GitHub Pages

## SmugMug API Auth

- **Credentials:** `~/.smugmug_config.json` (never hardcode in source)
- **Helper scripts:** `fetch_cover_images.py`, `fetch_smugmug_sizes.py`, `fetch_album_stats.py`

## Workflow

```bash
# Regenerate after changes
python3 generate_dashboard.py

# Push to GitHub Pages
git add index.html generate_dashboard.py
git commit -m "description"
git push

# Daily sync (runs automatically at 1 AM via LaunchAgent)
python3 sync_dashboard.py           # Sync from Google Sheet + deploy if changed
python3 sync_dashboard.py --force   # Regenerate + deploy even if unchanged
python3 sync_dashboard.py --dry-run # Regenerate but don't push
```

## Security

- **Three AES-256-GCM blobs** at build time (Python `cryptography` package):
  - `ENCRYPTED_CLIENT` — portfolio, videos, reviews, gear, hero, pricing, booking, `__config__` (client password)
  - `ENCRYPTED_INTERNAL` — workflow, checklists, posing guides, editing projects (internal password)
  - `ENCRYPTED_CLIENT_ADMIN` — same client content, encrypted with internal password (admin access)
- **Internal password unlocks everything** — decrypts both internal and client sections in one go
- **Client password** unlocks all client sections (portfolio, videos, pricing, booking)
- **Auto-unlock links:** `?k=<password>&t=<timestamp>&s=<section>` — clients click and land on the section instantly, no password gate. Query params cleared from URL bar after decryption. Links expire after 24 hours; expired links show toast, password gate shown.
  - `s=home` — lands on home page (default)
  - `s=pricing` — lands on pricing page
  - `s=booking` — lands on quote builder / booking page
- **Standalone page links (48h expiry):**
  - `python3 generate_link.py photos` → all photo categories
  - `python3 generate_link.py photos wedding` → just wedding galleries
  - `python3 generate_link.py videos` → video highlights
  - iOS Shortcuts: "PHOTOS LINK", "VIDEOS LINK", "WEDDING LINK" etc.
- **4 ways to generate dashboard links:**
  - **Slack:** Type `otp` in #instagram-posts → copy-friendly message ready to forward to WhatsApp
  - **iPhone Shortcut:** "CLIENT LINK" → SSH to Mac → share sheet to WhatsApp (pricing link)
  - **iPhone Shortcut:** "Booking LINK" → SSH to Mac → share sheet to WhatsApp (booking link)
  - **Terminal:** `python3 generate_link.py` (client) or `python3 generate_link.py internal` → copies to clipboard
- **Apple Shortcut setup:** Runs `~/client_link.sh` or `~/booking_link.sh` via SSH over Tailscale VPN. Uses Tailscale IP (not local 192.168.x.x) so it works from anywhere (LTE, Wi-Fi, etc.). Reads `~/.r2_secret` (synced from `.secret` by `generate_otp.py`). Works with Mac locked.
- **Passwords:** Stored in `.secret` (gitignored) + `~/.r2_secret` (SSH-safe copy for Shortcut)
- **Password rotation:** `python3 generate_otp.py` rotates client password (24h cycle), regenerates dashboard, pushes to GitHub, auto-syncs `~/.r2_secret`
- **Manual password gate:** Home page has its own password gate for direct visitors without the auto-unlock link
- **Internal/editor dashboard:** Always requires password (no auto-unlock for internal sections)
- **Data-driven DOM building (no innerHTML):** All decrypted content rendered via `createElement`/`textContent`
- **Safe markdown renderer:** Markdown-to-DOM converter via `createElement`/`textContent`
- **URL allowlist enforced:** `isAllowedUrl()` validates all dynamic URLs (HTTPS-only, no HTTP)
- **Referrer protection:** `referrerpolicy="no-referrer"` + `rel="noreferrer noopener"`
- **Web Crypto API** decryption at runtime (PBKDF2, 400k iterations, SHA-256)
- Random 16-byte salt + 12-byte IV per build
- No sessionStorage/localStorage — decrypted content is memory-only
- 3-strike lockout with 15s cooldown
- Git history cleaned with `filter-repo`
- **Contact info (phone, WhatsApp):** Inside encrypted blob, populated via JS after decryption — not in plaintext HTML

## Secrets Architecture

All secrets stored in gitignored local files:

| File | Contains | Used by |
|------|----------|---------|
| `.secret` | Client + internal passwords | `generate_dashboard.py`, `generate_otp.py` |
| `.dashboard_secrets.json` | Phone, email, Sheet IDs, Apps Script URLs, booking URL | `generate_dashboard.py`, `sheets_sync.py`, `detect_new_projects.py` |
| `.feedback_secrets.json` | Feedback passphrases, editor phones, role passwords | `generate_feedback.py` |
| `~/.r2_secret` | Passwords + sheet_id (SSH-safe copy) | `~/client_link.sh`, `~/booking_link.sh`, `~/reminder_*.sh` |
| `~/.smugmug_config.json` | SmugMug API key, secret, OAuth tokens | `fetch_*.py` scripts |
| `~/.megarc` | MEGA account credentials | `detect_video_projects.py` |

## Editing Project Tracker

- **Data:** Google Sheet (single source of truth, Sheet ID in `.dashboard_secrets.json`)
- **Module:** `sheets_sync.py` — reads via public CSV export
- **Daily sync:** `sync_dashboard.py` at 1 AM via LaunchAgent
- **Auto-detection (photo):** `detect_new_projects.py` scans Lightroom catalogs
- **Auto-detection (video):** `detect_video_projects.py` scans SSD + MEGA

## Client Reviews

- **Google Sheet:** "Reviews" tab (separate sheet)
- **Module:** `sheets_sync.py` → `read_reviews()`
- **Form:** Star rating, name, event type, textarea — on home page
- **Moderation:** Submissions land as "pending" → approve in Google Sheet → regenerate

## Video Feedback Page

- **Client URL:** `portfolio.rsquarestudios.com/feedback/?p={slug}` (passphrase-gated)
- **Editor/Admin URL:** `portfolio.rsquarestudios.com/feedback/?role={role}`
- **Bare URL landing page:** `portfolio.rsquarestudios.com/feedback/` shows a welcome page explaining how to access projects (instead of an error)
- **Generator:** `generate_feedback.py` → `feedback/index.html`
- **Encryption:** AES-256-GCM with PBKDF2 (400k iterations), same pattern as dashboard. Per-project blobs (PIN-encrypted) + per-role blobs (password-encrypted). Slug hashing via SHA-256. All secrets in `.feedback_secrets.json` (gitignored).
- **Config:** Project registry, passphrases, editor info all in `.feedback_secrets.json`
- **Server-side PIN validation:** `feedback_update` and `feedback_notify` require valid project PIN (verified by Apps Script)
- **POST rate limiting:** 5-second cooldown on all form submissions (client-side)

## Quote Builder Booking

- **Flow:** Client fills quote builder → clicks "Request Booking" → POSTs to Apps Script → row in "Bookings" tab + email to Ram
- **Apps Script handler:** `type=booking` in `doPost()` (same deployment as reviews/feedback)
- **Sheet columns:** Name, Event, Date, Hours, Coverage, Quote, Live Streaming, Location, Submitted, Status
- **Auto-creates tab:** If "Bookings" tab doesn't exist, Apps Script creates it with headers
- **Rate limiting:** 5-second cooldown prevents double submission
- **Config:** `bookingScriptUrl` in encrypted `__config__` blob (from `booking_script_url` in `.dashboard_secrets.json`)
- **iPhone Shortcut:** "Booking LINK" → SSH `~/booking_link.sh` → share sheet. Generates `?s=booking` link that auto-unlocks and lands on quote builder

## Editor Reminders (iPhone Shortcuts)

- **Scripts:** `~/reminder_laxman.sh`, `~/reminder_madhu.sh` — self-contained, SSH-callable
- **Data source:** Fetches Google Sheets directly via public CSV export (no Documents access needed)
- **Sheet ID:** Stored in `~/.r2_secret` (SSH-safe, preserved across OTP rotations)
- **Editor mapping:** Photo projects (tab 0) = all Laxman. Video projects (tab 2) = editor column, defaults to Madhu
- **Humanized messages:** `message_variants.py` randomizes greeting, list format, and closing each run. Editor-aware — Madhu gets urgency style ("late avthundi bro", "valu adgthunaru"), Laxman gets casual tone. Single message output, no robotic "Pending projects update:" format.
- **iPhone Shortcut:** "Remind Laxman" / "Remind Madhu" → SSH over Tailscale → share to WhatsApp
- **Also in repo:** `editor_reminder.sh` + `editor_reminder_summary.py` (full-featured version using `sheets_sync.py`, includes `--feedback` flag for corrections)

## Standalone Pages

- **photos.html** — Standalone encrypted photo portfolio for freelance sharing. Category tiles → gallery cards (SmugMug links). No pricing/booking/workflow. 48h auto-unlock via `?k=&t=` (no password gate). Dark theme, mobile-first. Generated by `generate_standalone_photos_html()` in `generate_dashboard.py`.
- **videos.html** — Standalone encrypted video highlights for freelance sharing. YouTube thumbnail grid with play overlay + duration. No pricing/booking/workflow. 48h auto-unlock. Generated by `generate_standalone_videos_html()` in `generate_dashboard.py`.
- **Link generation:** `python3 generate_link.py photos` / `python3 generate_link.py photos wedding` / `python3 generate_link.py videos` → 48h link copied to clipboard. Category filter via `&c=` param.
- **iOS Shortcuts:** `~/photos_link.sh [category]`, `~/videos_link.sh` — SSH over Tailscale, output to Share Sheet → WhatsApp. Valid categories: wedding, engagement, pre_wedding, half_saree, maternity, baby_shower, birthday, cradle, celebrations.
- **dhriti-storyboard.html** — Dhriti's cradle ceremony shot storyboard with 16 base64-embedded LENshiv reference photos. Self-contained (595KB), no encryption, phone-first layout. Source of truth: `canon_c50/cradle_ceremony/storyboard.html` — always edit there first, then overwrite this copy. Live at `https://portfolio.rsquarestudios.com/dhriti-storyboard.html`. localStorage checklist state is origin-specific.
- **dhriti.html** — Dhriti shoot checklist (separate from storyboard).

## Subprojects

- **krithin-neel/** — Separate repo (`kneil31/krithin-neel`), `.gitignore`d from rsquare-studios. Never add krithin-neel files to this repo.

## Mobile-Specific Notes

- Bottom nav bar with 5 tabs (Home, Portfolio, Pricing, Book, Contact)
- Floating WhatsApp button (bottom-right, above nav bar)
- Category tiles use 2-column grid on mobile
- `safe-area-inset-bottom` for iPhone notch/home indicator
- Hero: split layout on desktop, stacks vertically on mobile
- Test every layout change at 375px width minimum
