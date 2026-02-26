# CLAUDE.md — Rsquare Studios Dashboard

## IMPORTANT: Mobile-First Design

**Most users access this site on their phones via WhatsApp links.** Every change must be tested and optimized for mobile viewports first, desktop second. Always check how things look at 375px width (iPhone SE) and 390px width (iPhone 14).

## IMPORTANT: No Secrets in This File

**This file is on a PUBLIC repo.** Never put passwords, phone numbers, emails, API keys, Sheet IDs, MEGA links, or any personal information here. All secrets live in gitignored local files (`.secret`, `.dashboard_secrets.json`, `.feedback_secrets.json`).

## Project Overview

Notion-style dark-themed dashboard for Rsquare Studios photography business. Hosted on GitHub Pages.

- **Live URL:** https://portfolio.rsquarestudios.com/ (custom domain, CNAME → kneil31.github.io)
- **GitHub Repo:** kneil31/rsquare-studios (public)
- **Generator:** `generate_dashboard.py` → outputs `index.html`
- **Passwords:** Stored in `.secret` file (gitignored, never committed)

## 3 Sections

1. **Portfolio** (client-facing) — Category tiles with cover photos linking to SmugMug galleries
2. **Investment / Pricing** (client-facing, password-protected) — Hourly rate cards with interactive quote builder
3. **Workflow Dashboard** (password-protected) — Posing guides, workflow checklists, editing reference, editing project tracker

## Key Design Decisions

- **Mobile-first:** Bottom nav bar, floating WhatsApp button, large touch targets
- **Dark theme:** Notion-inspired (#191919 background, #8b5cf6 accent purple)
- **Hero layout:** Option D split (image left, text right) with CSS `mask-image` blend
- **Two-level AES-256-GCM encryption:** Client and internal sections encrypted with separate passwords. No plaintext secrets in HTML source.
- **Data-driven DOM building (no innerHTML):** Encrypted payloads contain JSON data objects; JS builds DOM at runtime
- **Cover images:** Pulled from SmugMug API (highlight images per album)
- **Tile labels below image:** Category name and gallery count displayed below the tile image, not overlaid
- **No external dependencies:** Single self-contained HTML file, no frameworks
- **Professional copy:** "Investment" not "pricing", "images" not "pictures", "coverage" not "shooting"
- **Open Graph tags:** og:title, og:description, og:image (hero.jpg), og:url

## My Gear Section

- **Inline expandable section** on the home page
- **Data:** `GEAR_LIST` dict in `generate_dashboard.py` — 7 categories rendered at build time
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
  - `ENCRYPTED_CLIENT` — pricing, booking, `__config__` (client password)
  - `ENCRYPTED_INTERNAL` — workflow, checklists, posing guides, editing projects (internal password)
  - `ENCRYPTED_CLIENT_ADMIN` — same client content, encrypted with internal password (admin access)
- **Internal password unlocks everything** — decrypts both internal and client sections in one go
- **Client password** unlocks only client sections (pricing, booking)
- **No OTP system** — removed Feb 2026 (was confusing for users). Single client password, single internal/admin password.
- **Passwords:** Stored in `.secret` (gitignored) — never in source code or docs
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
| `.dashboard_secrets.json` | Phone, email, Sheet IDs, Apps Script URLs | `generate_dashboard.py`, `sheets_sync.py`, `detect_new_projects.py` |
| `.feedback_secrets.json` | Feedback passphrases, editor phones, role passwords | `generate_feedback.py` |
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

## Subprojects

- **krithin-neel/** — Separate repo (`kneil31/krithin-neel`), `.gitignore`d from rsquare-studios. Never add krithin-neel files to this repo.

## Mobile-Specific Notes

- Bottom nav bar with 5 tabs (Home, Portfolio, Pricing, Book, Contact)
- Floating WhatsApp button (bottom-right, above nav bar)
- Category tiles use 2-column grid on mobile
- `safe-area-inset-bottom` for iPhone notch/home indicator
- Hero: split layout on desktop, stacks vertically on mobile
- Test every layout change at 375px width minimum
