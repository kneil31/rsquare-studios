#!/usr/bin/env python3
"""
KRITHIN NEEL FAMILY MEMORIES PAGE GENERATOR
Generates a warm, baby/family-themed single-page site for GitHub Pages.

Tabs: Krithin | Monika | Family
Each tab shows gallery cards (SmugMug links) and video cards (YouTube links).

Usage:
    python3 generate_krithin_page.py
    # Generates output/index.html

Data source:
    ../album_stats.json (image counts + SmugMug URLs)
"""

import json
import os
import base64
import webbrowser
from pathlib import Path
from datetime import datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "output"
OUTPUT_FILE = OUTPUT_DIR / "index.html"
ALBUM_STATS_FILE = SCRIPT_DIR.parent / "album_stats.json"
COVER_IMAGES_FILE = SCRIPT_DIR / "cover_images.json"

# Password for AES-256-GCM encryption
PAGE_PASSWORD = "Kn!7h$Xw9#mP2@vR4&qZ"
PBKDF2_ITERATIONS = 100_000


def encrypt_content(plaintext, password):
    """AES-256-GCM encrypt plaintext using password via PBKDF2 key derivation.
    Returns base64-encoded salt(16) + iv(12) + ciphertext."""
    salt = os.urandom(16)
    iv = os.urandom(12)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    key = kdf.derive(password.encode("utf-8"))
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(iv, plaintext.encode("utf-8"), None)
    return base64.b64encode(salt + iv + ciphertext).decode("ascii")

# ─── Content Data ──────────────────────────────────────────────────────────────

KRITHIN_GALLERIES = [
    {
        "title": "Fresh 48",
        "subtitle": "Medical City",
        "date": "April 10, 2024",
        "url": "https://www.rsquarestudios.com/2024/Krithin-Neel/n-LD72KK",
        "node_id": "LD72KK",
        "icon": "👶",
        "cover": "https://photos.smugmug.com/photos/i-Cg8LkMz/0/NTgCnFrWmW7cBxGkN3B4b4gVbCzm2CWFtfhSRXf8z/XL/i-Cg8LkMz-XL.jpg",
    },
    {
        "title": "Cradle Ceremony",
        "subtitle": "Irving",
        "cover": "https://photos.smugmug.com/photos/i-zbjFvnD/0/L9hFHp6hkzfKgfdRQxWjmbDbRSdJX8hTFGWW4DRRm/XL/i-zbjFvnD-XL.jpg",
        "date": "April 30, 2024",
        "url": "https://www.rsquarestudios.com/2024/Krithin-Cradle-Ceremony/n-nKgrKN",
        "node_id": "nKgrKN",
        "icon": "🪷",
    },
    {
        "title": "Sankranthi 2025",
        "subtitle": "Corinth",
        "date": "January 13, 2025",
        "url": "https://www.rsquarestudios.com/2025/KAYU-Sankranthi-2025/n-83VJzP",
        "node_id": "83VJzP",
        "icon": "🪁",
        "cover": "https://photos.smugmug.com/photos/i-ZqK2JFp/0/LZMCkXT53j5xskC8tKJbj2Gd8LLTCh6s9x8j6gxPB/XL/i-ZqK2JFp-XL.jpg",
    },
    {
        "title": "Temple Visit",
        "subtitle": "Pittsburgh",
        "date": "February 12, 2025",
        "url": "https://www.rsquarestudios.com/2025/2025-02-12---Krithin-Temple---Pittsburgh/n-Sstqs8",
        "node_id": "Sstqs8",
        "icon": "🛕",
        "cover": "https://photos.smugmug.com/photos/i-z5F449L/0/KcVc6pSg4Gbzx8JHk5VNNd6SmX8SzSKZbXFH362Df/XL/i-z5F449L-XL.jpg",
    },
    {
        "title": "Cake Smash",
        "subtitle": "Home",
        "date": "April 8, 2025",
        "url": "https://www.rsquarestudios.com/2025/2025-04-08-Krithin-Cake-Smash-Home/n-GfWtSm",
        "node_id": "GfWtSm",
        "icon": "🎂",
        "cover": "https://photos.smugmug.com/photos/i-qGFd3mp/0/KZh4xRXd8RxxkbMDFh2H5WxGMMNrXx76xmhMzHDkd/XL/i-qGFd3mp-XL.jpg",
    },
    {
        "title": "Adugulu",
        "subtitle": "Home",
        "date": "June 1, 2025",
        "url": "https://www.rsquarestudios.com/2025/Krithiin-Adugulu-Home/n-fZQgS5",
        "node_id": "fZQgS5",
        "icon": "👣",
    },
    {
        "title": "Halloween",
        "subtitle": "Dallas",
        "date": "November 2, 2025",
        "url": "https://www.rsquarestudios.com/2025/KAYU-Halloween/n-K9g7f3",
        "node_id": "K9g7f3",
        "icon": "🎃",
    },
    {
        "title": "New Year 2026",
        "subtitle": "",
        "date": "January 2026",
        "url": "https://www.rsquarestudios.com/2026/Krithin-New-year-2026/n-rj9Mvw",
        "node_id": "rj9Mvw",
        "icon": "🎉",
    },
]

KRITHIN_VIDEOS = [
    {
        "title": "Krithin Meets Small World",
        "subtitle": "3:53",
        "url": "https://www.youtube.com/watch?v=8awZJqW4boQ",
    },
    {
        "title": "Krithin Neel Unfiltered",
        "subtitle": "12:32",
        "url": "https://www.youtube.com/watch?v=GJCwUlpokXU",
    },
    {
        "title": "Krithin 11 Days Ceremony",
        "subtitle": "3:02",
        "url": "https://www.youtube.com/watch?v=FATM1815Jnk",
    },
    {
        "title": "Krithin Cradle Ceremony",
        "subtitle": "5:44",
        "url": "https://www.youtube.com/watch?v=6jWjQbBwAuM",
    },
    {
        "title": "Parents Meet",
        "subtitle": "3:57",
        "url": "https://www.youtube.com/watch?v=rQOVRxyDUCc",
    },
    {
        "title": "KAYU Fly High",
        "subtitle": "",
        "url": "https://www.youtube.com/watch?v=55YmZmdXFY4",
    },
]

REELS = [
    {
        "title": "Krithins Sounds",
        "url": "https://www.youtube.com/watch?v=uFXAysFTwxs",
        "cover": "https://photos.smugmug.com/photos/i-FB75HpZ/0/Ldjs2ZvhXJsKJ2t3sbnF6Rk7hQnh2MkdF3Rg5M5wX/XL/i-FB75HpZ-XL.jpg",
    },
    {
        "title": "Nanaaaa",
        "url": "https://www.youtube.com/watch?v=hTQqfABqDqc",
        "cover": "https://photos.smugmug.com/photos/i-WdLdnMJ/0/KJDCkQLCh4fSHt2HffN8KXMF6hRCPDmg2kbMRhgpB/XL/i-WdLdnMJ-XL.jpg",
    },
    {
        "title": "Alavari Intiki",
        "url": "https://www.youtube.com/watch?v=Wv32slqYjtw",
        "cover": "https://photos.smugmug.com/photos/i-KLPGwqN/0/LCG3wmvcFnTCGzpcWpFnBks9VFSMfDsjWqXqF2M2P/XL/i-KLPGwqN-XL.jpg",
    },
    {
        "title": "Raja Saab Gilli Gilli go",
        "url": "https://www.youtube.com/watch?v=AIV-ScsxWcU",
        "cover": "https://photos.smugmug.com/photos/i-vxk3sxS/0/LsSbsxWnLWCM6XQKwhf2BVLrB8zxcLT5m8SdQsp4d/XL/i-vxk3sxS-XL.jpg",
    },
    {
        "title": "Krithin Yuku Ice Cream Ride",
        "url": "https://www.youtube.com/watch?v=SGj7XQao77M",
        "cover": "https://photos.smugmug.com/photos/i-Fk3BhXj/0/LFb6s8sxrtkXQBpBFHZ9Nn2wF6ZKXj4jzLLPdTRfL/XL/i-Fk3BhXj-XL.jpg",
    },
    {
        "title": "Kannepetta Rooooo",
        "url": "https://www.youtube.com/watch?v=Hl8RlKhZUA0",
        "cover": "https://photos.smugmug.com/photos/i-R9s6BNV/0/LhCvRRLLV4JnxT9sMVHKpDLwJsN59kMM2VFMfvXQW/XL/i-R9s6BNV-XL.jpg",
    },
    {
        "title": "Krithin Neel Back with Overloaded Cuteness",
        "url": "https://www.youtube.com/watch?v=W3yxm6FqWuo",
        "cover": "https://photos.smugmug.com/photos/i-WG5jLXN/0/MGFJbbP3TkzvqR76bm24wxgcQhqrDGj3mWdsDwVR9/XL/i-WG5jLXN-XL.jpg",
    },
    {
        "title": "Advi Entry Cherishment",
        "url": "https://www.youtube.com/watch?v=cnpZXtlNjIM",
        "cover": "https://photos.smugmug.com/photos/i-2XjPwWn/0/MHzf97DVbv6vQZ9gP3XgCmPSLGF5CKB7Pd59Cp4zM/XL/i-2XjPwWn-XL.jpg",
    },
    {
        "title": "Kannu Bommaluuu",
        "url": "https://www.youtube.com/watch?v=cx36zgbJRIc",
        "cover": "https://photos.smugmug.com/photos/i-qdvxfqp/0/Kg7fFhHNwCxsTzbL59VZMwhVZB9tBgHnMTL2CVPrv/XL/i-qdvxfqp-XL.jpg",
    },
    {
        "title": "Kannepetta roo V2",
        "url": "https://www.youtube.com/watch?v=dEx0wmr2zCY",
        "cover": "https://photos.smugmug.com/photos/i-6H3L5FG/0/LS6ZmB5NNcJVRNvWMkTCMG8BKcqpDpPqNgMxmBhdG/XL/i-6H3L5FG-XL.jpg",
    },
    {
        "title": "Ivandi Nana Garu",
        "url": "https://www.youtube.com/watch?v=M3UdzuLS9e8",
        "cover": "https://photos.smugmug.com/photos/i-Qn45S38/0/MKxTVSQ5cv2gN2SgKJwpHqLmd7XTHDGMckLbM3X9G/XL/i-Qn45S38-XL.jpg",
    },
    {
        "title": "Yuku Dance",
        "url": "https://www.youtube.com/watch?v=gg7rgX4Yd_4",
        "cover": "https://photos.smugmug.com/photos/i-7pPcLp2/0/MchbGN5S6JhKCSWckXQFqwxkc5DFmc2Sc57c7vGcX/XL/i-7pPcLp2-XL.jpg",
    },
    {
        "title": "Advi & Yuku Bond",
        "url": "https://www.youtube.com/watch?v=V8-NBGBIovI",
        "cover": "https://photos.smugmug.com/photos/i-ntK9K7Z/0/M4zddJ8QPkKG9JfBZDnq5qsgssMdxSccbHgpfdtKm/XL/i-ntK9K7Z-XL.jpg",
    },
    {
        "title": "Yuku Dance Performance",
        "url": "https://www.youtube.com/watch?v=-o0lslWCvhw",
        "cover": "https://photos.smugmug.com/photos/i-BXXN28n/0/Mz2Nqk5PfS8L3JXfWzxZ6zWG63mBT7phTrkTg4nxn/XL/i-BXXN28n-XL.jpg",
    },
]

MONIKA_VIDEOS = [
    {
        "title": "Monika Baby Shower",
        "subtitle": "",
        "url": "https://www.youtube.com/watch?v=Y3ZxYrE0Tmk",
        "cover": "https://photos.smugmug.com/photos/i-4skD5ZP/0/MCT2ptf5vCVr6P3WcRsNTTw6d2qBqrfcPjW69PKMs/XL/i-4skD5ZP-XL.jpg",
    },
    {
        "title": "Baby Shower",
        "subtitle": "",
        "url": "https://www.youtube.com/watch?v=YLNRZk9M6ng",
        "cover": "https://photos.smugmug.com/photos/i-frcTRf7/0/L7Thw4wRcS2wKffZwF4zBNX4DG9knJJ4qL5gKSdvf/XL/i-frcTRf7-XL.jpg",
    },
    {
        "title": "Bee Is On The Way",
        "subtitle": "",
        "url": "https://www.youtube.com/watch?v=Y0iIsJWd6ys",
        "cover": "https://photos.smugmug.com/photos/i-mxmxb7S/0/KJTZcZr39B2fTVt8ccdkS8mt6fgXLMjhwsCdLbpBq/XL/i-mxmxb7S-XL.jpg",
    },
]

MONIKA_GALLERIES = [
    {
        "title": "Baby Shower",
        "subtitle": "Irving",
        "date": "March 17, 2024",
        "url": "https://www.rsquarestudios.com/2024/Monika-Babyshower/n-r78HKK",
        "node_id": "r78HKK",
        "icon": "🍼",
        "cover": "https://photos.smugmug.com/photos/i-bfcjZSM/0/MfNWxFNxHsn7BkDxgwmWkP9M29Pf4JRLFHvsdr8FF/XL/i-bfcjZSM-XL.jpg",
    },
    {
        "title": "Maternity 2024",
        "subtitle": "Texas",
        "date": "April 2, 2024",
        "url": "https://www.rsquarestudios.com/2024/Monika-Maternity/n-txJ8H6",
        "node_id": "txJ8H6",
        "icon": "🤰",
    },
    {
        "title": "Girls Shoot 2023",
        "subtitle": "Mandalay",
        "date": "November 26, 2023",
        "url": "https://www.rsquarestudios.com/2023/Monika-and-girls-shoot-Mandlay/n-Wc7RjD",
        "node_id": "",
        "icon": "👯",
        "cover": "https://photos.smugmug.com/photos/i-NQzhzqV/0/LVVzvjswhRXc7JPtrn5KjG4FkP7bL5xHtmL65ZFQ6/XL/i-NQzhzqV-XL.jpg",
    },
]

FAMILY_GALLERIES = [
    {
        "title": "Moniel Housewarming",
        "subtitle": "Corinth",
        "date": "December 29, 2024",
        "url": "https://www.rsquarestudios.com/2024/2024-12-29---Monika-Neel-HW---Corinth/n-cDsRTB",
        "node_id": "cDsRTB",
        "icon": "👨‍👩‍👦",
        "cover": "https://photos.smugmug.com/photos/i-2vgmVNq/0/NLBrZ6bJRj78FcHMGhh8VPGPPfQhBCB67KfKmmRQF/XL/i-2vgmVNq-XL.jpg",
    },
]


def load_image_counts():
    """Load image counts from album_stats.json keyed by node_id."""
    counts = {}
    if ALBUM_STATS_FILE.exists():
        with open(ALBUM_STATS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for album in data.get("albums_ranked", []):
            nid = album.get("node_id", "")
            if nid:
                counts[nid] = album.get("image_count", 0)
    return counts


def load_cover_images():
    """Load cover image URLs from cover_images.json keyed by node_id."""
    if COVER_IMAGES_FILE.exists():
        with open(COVER_IMAGES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def escape_html(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def build_gallery_card(gallery, image_counts, cover_images):
    title = escape_html(gallery["title"])
    subtitle = escape_html(gallery.get("subtitle", ""))
    date = escape_html(gallery.get("date", ""))
    url = gallery["url"]
    icon = gallery.get("icon", "📷")
    node_id = gallery.get("node_id", "")
    count = image_counts.get(node_id, 0)

    count_badge = f'<span class="tile-badge">{count} images</span>' if count > 0 else ""
    location_html = f' &middot; {subtitle}' if subtitle else ""

    # Use custom cover if provided, otherwise fall back to cover_images.json
    custom_cover = gallery.get("cover")
    cover = cover_images.get(node_id)
    if custom_cover:
        bg_url = custom_cover
    elif cover and cover.get("large"):
        bg_url = cover["large"]
    else:
        bg_url = None
    if bg_url:
        return f"""
      <a href="{url}" target="_blank" rel="noopener" class="tile" style="background-image:url('{bg_url}')">
        <div class="tile-content">
          <div class="tile-title">{title}</div>
          <div class="tile-meta">{date}{location_html}</div>
          {count_badge}
        </div>
      </a>"""
    else:
        # Fallback for galleries without cover images
        return f"""
      <a href="{url}" target="_blank" rel="noopener" class="tile tile-no-image">
        <div class="tile-icon">{icon}</div>
        <div class="tile-content">
          <div class="tile-title">{title}</div>
          <div class="tile-meta">{date}{location_html}</div>
          {count_badge}
        </div>
      </a>"""


def build_video_card(video):
    title = escape_html(video["title"])
    url = video.get("url", "")

    if not url:
        return ""

    # Use custom cover if provided, otherwise YouTube thumbnail
    thumb_url = video.get("cover", "")
    if not thumb_url:
        vid_id = url.split("v=")[-1].split("&")[0] if "v=" in url else ""
        thumb_url = f"https://img.youtube.com/vi/{vid_id}/hqdefault.jpg" if vid_id else ""

    return f"""
      <a href="{url}" target="_blank" rel="noopener" class="video-card" style="background-image:url('{thumb_url}')">
        <div class="video-card-content">
          <div class="tile-title">{title}</div>
        </div>
      </a>"""


def build_reel_card(video):
    title = escape_html(video["title"])
    url = video.get("url", "")
    if not url:
        return ""
    # Use custom cover image if provided, otherwise YouTube thumbnail
    thumb_url = video.get("cover", "")
    if not thumb_url:
        vid_id = url.split("v=")[-1].split("&")[0] if "v=" in url else ""
        thumb_url = f"https://img.youtube.com/vi/{vid_id}/hqdefault.jpg" if vid_id else ""
    return f"""
      <a href="{url}" target="_blank" rel="noopener" class="reel-tile">
        <img src="{thumb_url}" alt="{title}" loading="lazy">
        <div class="reel-content">
          <div class="reel-title">{title}</div>
        </div>
      </a>"""


def build_reels_tab(reels):
    cards_html = '<div class="reels-grid">\n'
    for r in reels:
        cards_html += build_reel_card(r)
    cards_html += "\n</div>\n"
    return f"""
    <div id="tab-reels" class="tab-content">
      {cards_html}
    </div>"""


def build_tab_content(tab_id, galleries, videos, image_counts, cover_images):
    cards_html = ""
    if galleries:
        cards_html += '<div class="section-label">Photo Galleries</div>\n'
        cards_html += '<div class="cards-list">\n'
        for g in galleries:
            cards_html += build_gallery_card(g, image_counts, cover_images)
        cards_html += "\n</div>\n"
    if videos:
        cards_html += '<div class="section-label">Videos</div>\n'
        cards_html += '<div class="cards-list video-grid">\n'
        for v in videos:
            cards_html += build_video_card(v)
        cards_html += "\n</div>\n"
    return f"""
    <div id="tab-{tab_id}" class="tab-content">
      {cards_html}
    </div>"""


def generate_html(image_counts, cover_images):
    """Generate the full HTML page with AES-256-GCM encrypted content."""
    krithin_content = build_tab_content("krithin", KRITHIN_GALLERIES, KRITHIN_VIDEOS, image_counts, cover_images)
    monika_content = build_tab_content("monika", MONIKA_GALLERIES, MONIKA_VIDEOS, image_counts, cover_images)
    family_content = build_tab_content("family", FAMILY_GALLERIES, [], image_counts, cover_images)
    reels_content = build_reels_tab(REELS)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Encrypt all tab content into a single blob
    content_payload = json.dumps({
        "krithin": krithin_content,
        "monika": monika_content,
        "family": family_content,
        "reels": reels_content,
    })
    encrypted_blob = encrypt_content(content_payload, PAGE_PASSWORD)
    print(f"  Encrypted content: {len(encrypted_blob)} chars")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <title>Krithin Neel — Family Memories</title>
  <meta name="description" content="One stop for Krithin Neel's family memories — photo galleries and videos">
  <meta name="theme-color" content="#FFF8F0">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}

    :root {{
      --bg: #FFF8F0;
      --bg-card: #FFFFFF;
      --text: #3D2C2E;
      --text-secondary: #8B7355;
      --accent: #E8A87C;
      --accent-soft: #FBE8D3;
      --pink: #F4978E;
      --pink-soft: #FDDEDE;
      --lavender: #C3AED6;
      --lavender-soft: #EDE7F6;
      --mint: #9DC5BB;
      --mint-soft: #E0F2EE;
      --shadow: 0 2px 12px rgba(61, 44, 46, 0.08);
      --shadow-hover: 0 4px 20px rgba(61, 44, 46, 0.14);
      --radius: 16px;
      --radius-sm: 10px;
    }}

    body {{
      font-family: 'Nunito', -apple-system, BlinkMacSystemFont, sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      -webkit-font-smoothing: antialiased;
    }}

    /* ── Header ────────────────────────────────────── */
    .header {{
      text-align: center;
      padding: 40px 20px 24px;
      background: linear-gradient(180deg, #FFF0E5 0%, var(--bg) 100%);
    }}

    .header-icon {{
      font-size: 64px;
      margin-bottom: 8px;
      line-height: 1;
    }}

    .header h1 {{
      font-size: 28px;
      font-weight: 800;
      color: var(--text);
      margin-bottom: 4px;
      letter-spacing: -0.5px;
    }}

    .header .subtitle {{
      font-size: 15px;
      color: var(--text-secondary);
      font-weight: 600;
    }}

    /* ── Tabs ──────────────────────────────────────── */
    .tabs {{
      display: flex;
      justify-content: center;
      gap: 8px;
      padding: 0 20px 20px;
      position: sticky;
      top: 0;
      z-index: 100;
      background: var(--bg);
      padding-top: 12px;
    }}

    .tab-btn {{
      padding: 10px 24px;
      border: none;
      border-radius: 50px;
      font-family: 'Nunito', sans-serif;
      font-size: 15px;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.25s ease;
      background: var(--bg-card);
      color: var(--text-secondary);
      box-shadow: var(--shadow);
    }}

    .tab-btn.active {{
      background: var(--accent);
      color: #fff;
      box-shadow: 0 4px 16px rgba(232, 168, 124, 0.4);
    }}

    .tab-btn:not(.active):hover {{
      background: var(--accent-soft);
      color: var(--text);
    }}

    /* ── Tab Content ──────────────────────────────── */
    .tab-content {{
      display: none;
      padding: 0 16px 100px;
      max-width: 600px;
      margin: 0 auto;
      animation: fadeIn 0.3s ease;
    }}

    .tab-content.active {{
      display: block;
    }}

    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(8px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}

    .section-label {{
      font-size: 13px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1.2px;
      color: var(--text-secondary);
      padding: 16px 4px 8px;
    }}

    /* ── Tile Grid ─────────────────────────────────── */
    .cards-list {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
    }}

    .tile {{
      position: relative;
      border-radius: var(--radius);
      overflow: hidden;
      aspect-ratio: 3/4;
      display: flex;
      align-items: flex-end;
      background-size: cover;
      background-position: center;
      text-decoration: none;
      color: #fff;
      transition: transform 0.15s, box-shadow 0.2s;
    }}

    .tile::before {{
      content: '';
      position: absolute;
      inset: 0;
      background: linear-gradient(180deg, transparent 30%, rgba(0,0,0,0.7) 100%);
      z-index: 0;
    }}

    .tile:hover {{
      transform: translateY(-3px);
      box-shadow: 0 8px 24px rgba(0,0,0,0.2);
    }}

    .tile-content {{
      position: relative;
      z-index: 1;
      padding: 14px 16px;
      width: 100%;
    }}

    .tile-title {{
      font-size: 16px;
      font-weight: 700;
      color: #fff;
      text-shadow: 0 1px 4px rgba(0,0,0,0.6);
      line-height: 1.3;
      margin-bottom: 2px;
    }}

    .tile-meta {{
      font-size: 12px;
      color: #d1d5db;
      text-shadow: 0 1px 2px rgba(0,0,0,0.5);
    }}

    .tile-badge {{
      display: inline-block;
      font-size: 11px;
      font-weight: 700;
      padding: 2px 8px;
      border-radius: 50px;
      background: rgba(255,255,255,0.2);
      color: #fff;
      margin-top: 4px;
      backdrop-filter: blur(4px);
    }}

    .tile-icon {{
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      font-size: 40px;
      z-index: 1;
    }}

    .tile-no-image {{
      background: linear-gradient(135deg, var(--accent-soft) 0%, var(--lavender-soft) 100%);
    }}

    .tile-no-image::before {{
      background: none;
    }}

    .tile-no-image .tile-title {{
      color: var(--text);
      text-shadow: none;
    }}

    .tile-no-image .tile-meta {{
      color: var(--text-secondary);
      text-shadow: none;
    }}

    .tile-no-image .tile-badge {{
      background: var(--lavender-soft);
      color: #7C6B9E;
    }}

    /* ── Video Cards ──────────────────────────────── */
    .video-card {{
      position: relative;
      text-decoration: none;
      border-radius: var(--radius);
      overflow: hidden;
      aspect-ratio: 16/9;
      background-size: cover;
      background-position: center;
      display: flex;
      align-items: flex-end;
      transition: transform 0.15s, box-shadow 0.2s;
    }}

    .video-card::before {{
      content: '';
      position: absolute;
      inset: 0;
      background: linear-gradient(180deg, transparent 40%, rgba(0,0,0,0.8) 100%);
    }}

    .video-card:hover {{
      transform: translateY(-3px);
      box-shadow: 0 8px 24px rgba(0,0,0,0.2);
    }}

    .video-card-content {{
      position: relative;
      z-index: 1;
      padding: 14px 16px;
      width: 100%;
    }}

    .video-grid {{
      grid-template-columns: repeat(2, 1fr) !important;
    }}


    /* ── Reels Grid (vertical 9:16) ─────────────────── */
    .reels-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
    }}

    .reel-tile {{
      position: relative;
      border-radius: var(--radius-sm);
      overflow: hidden;
      aspect-ratio: 9/16;
      display: flex;
      align-items: flex-end;
      text-decoration: none;
      color: #fff;
      transition: transform 0.15s, box-shadow 0.2s;
    }}

    .reel-tile img {{
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
      object-position: center;
    }}

    .reel-tile::before {{
      content: '';
      position: absolute;
      inset: 0;
      background: linear-gradient(180deg, transparent 60%, rgba(0,0,0,0.6) 100%);
      z-index: 1;
    }}

    .reel-tile:hover {{
      transform: translateY(-3px);
      box-shadow: 0 8px 24px rgba(0,0,0,0.2);
    }}

    .reel-content {{
      position: relative;
      z-index: 2;
      padding: 8px 10px;
      width: 100%;
    }}

    .reel-title {{
      font-size: 11px;
      font-weight: 700;
      color: #fff;
      text-shadow: 0 1px 4px rgba(0,0,0,0.6);
      line-height: 1.3;
    }}

    @media (max-width: 374px) {{
      .reels-grid {{
        grid-template-columns: repeat(2, 1fr);
      }}
    }}

    /* ── Password Gate ─────────────────────────────── */
    .pw-gate {{
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 60vh;
      padding: 40px 20px;
      text-align: center;
    }}

    .pw-gate .gate-icon {{
      font-size: 64px;
      margin-bottom: 16px;
    }}

    .pw-gate h2 {{
      font-size: 22px;
      font-weight: 800;
      color: var(--text);
      margin-bottom: 8px;
    }}

    .pw-gate p {{
      font-size: 14px;
      color: var(--text-secondary);
      margin-bottom: 24px;
    }}

    .pw-form {{
      display: flex;
      gap: 8px;
      max-width: 300px;
      width: 100%;
    }}

    .pw-form input {{
      flex: 1;
      padding: 12px 16px;
      border: 2px solid var(--accent-soft);
      border-radius: 12px;
      font-family: 'Nunito', sans-serif;
      font-size: 15px;
      font-weight: 600;
      background: var(--bg-card);
      color: var(--text);
      outline: none;
      transition: border-color 0.2s;
    }}

    .pw-form input:focus {{
      border-color: var(--accent);
    }}

    .pw-form button {{
      padding: 12px 20px;
      border: none;
      border-radius: 12px;
      background: var(--accent);
      color: #fff;
      font-family: 'Nunito', sans-serif;
      font-size: 15px;
      font-weight: 700;
      cursor: pointer;
      transition: opacity 0.2s;
    }}

    .pw-form button:hover {{
      opacity: 0.85;
    }}

    .pw-error {{
      color: var(--pink);
      font-size: 13px;
      font-weight: 700;
      margin-top: 12px;
      display: none;
    }}

    .pw-lockout {{
      color: var(--pink);
      font-size: 13px;
      font-weight: 700;
      margin-top: 8px;
      display: none;
    }}

    .app-content {{
      display: none;
    }}

    .app-content.unlocked {{
      display: block;
    }}

    /* ── Footer ────────────────────────────────────── */
    .footer {{
      text-align: center;
      padding: 32px 20px;
      color: var(--text-secondary);
      font-size: 13px;
      font-weight: 600;
    }}

    .footer a {{
      color: var(--accent);
      text-decoration: none;
    }}

    .footer a:hover {{
      text-decoration: underline;
    }}

    .footer .whatsapp-link {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      margin-top: 8px;
      padding: 8px 20px;
      background: #25D366;
      color: #fff;
      border-radius: 50px;
      font-weight: 700;
      font-size: 14px;
      text-decoration: none;
      transition: opacity 0.2s;
    }}

    .footer .whatsapp-link:hover {{
      opacity: 0.85;
      text-decoration: none;
    }}

    /* ── Small mobile (single column tiles) ────────── */
    @media (max-width: 374px) {{
      .cards-list {{
        grid-template-columns: 1fr;
      }}
      .tile {{
        aspect-ratio: 16/9;
      }}
    }}

    /* ── Desktop ───────────────────────────────────── */
    @media (min-width: 768px) {{
      .header {{
        padding: 60px 20px 32px;
      }}
      .header h1 {{
        font-size: 36px;
      }}
      .tab-btn {{
        padding: 12px 32px;
        font-size: 16px;
      }}
      .cards-list {{
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
      }}
      .tile-title {{
        font-size: 18px;
      }}
    }}
  </style>
</head>
<body>
  <div class="header">
    <div class="header-icon">👶</div>
    <h1>Krithin Neel</h1>
    <p class="subtitle">One stop for family memories</p>
  </div>

  <!-- Password Gate -->
  <div id="pw-gate" class="pw-gate">
    <div class="gate-icon">🔒</div>
    <h2>Family Access</h2>
    <p>Enter the password to view memories</p>
    <div class="pw-form">
      <input type="password" id="pw-input" placeholder="Password" autocomplete="off"
             onkeydown="if(event.key==='Enter')checkPassword()">
      <button id="pw-btn" onclick="checkPassword()">Enter</button>
    </div>
    <div id="pw-error" class="pw-error">Wrong password. Try again.</div>
    <div id="pw-lockout" class="pw-lockout"></div>
  </div>

  <!-- Encrypted content injected here after unlock -->
  <div id="app-content" class="app-content">
    <div class="tabs">
      <button class="tab-btn active" onclick="switchTab('krithin')">Krithin</button>
      <button class="tab-btn" onclick="switchTab('monika')">Monika</button>
      <button class="tab-btn" onclick="switchTab('family')">Family</button>
      <button class="tab-btn" onclick="switchTab('reels')">Reels</button>
    </div>

    <div id="tab-krithin" class="tab-content active"></div>
    <div id="tab-monika" class="tab-content"></div>
    <div id="tab-family" class="tab-content"></div>
    <div id="tab-reels" class="tab-content"></div>
  </div>

  <div class="footer" style="display:none" id="app-footer">
    <p>Captured with love by <a href="https://kneil31.github.io/rsquare-studios/" target="_blank">Rsquare Studios</a></p>
    <a href="https://wa.me/14697095978" class="whatsapp-link" target="_blank">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M12 0C5.373 0 0 5.373 0 12c0 2.625.846 5.059 2.284 7.034L.789 23.492a.5.5 0 00.611.611l4.458-1.495A11.948 11.948 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 22c-2.35 0-4.514-.81-6.228-2.164l-.435-.347-3.012 1.01 1.01-3.012-.348-.436A9.948 9.948 0 012 12C2 6.486 6.486 2 12 2s10 4.486 10 10-4.486 10-10 10z"/></svg>
      WhatsApp
    </a>
    <p style="margin-top: 12px; font-size: 11px; opacity: 0.5;">Generated {now}</p>
  </div>

  <script>
    const ENCRYPTED_BLOB = "{encrypted_blob}";
    const PBKDF2_ITERATIONS = {PBKDF2_ITERATIONS};

    function switchTab(tabId) {{
      document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
      document.getElementById('tab-' + tabId).classList.add('active');
      event.currentTarget.classList.add('active');
      window.scrollTo({{ top: 0, behavior: 'smooth' }});
    }}

    async function deriveKey(password, salt) {{
      const enc = new TextEncoder();
      const keyMaterial = await crypto.subtle.importKey(
        'raw', enc.encode(password), 'PBKDF2', false, ['deriveKey']
      );
      return crypto.subtle.deriveKey(
        {{ name: 'PBKDF2', salt: salt, iterations: PBKDF2_ITERATIONS, hash: 'SHA-256' }},
        keyMaterial,
        {{ name: 'AES-GCM', length: 256 }},
        false,
        ['decrypt']
      );
    }}

    async function decryptContent(password, blob) {{
      const raw = Uint8Array.from(atob(blob), c => c.charCodeAt(0));
      const salt = raw.slice(0, 16);
      const iv = raw.slice(16, 28);
      const ciphertext = raw.slice(28);
      const key = await deriveKey(password, salt);
      const decrypted = await crypto.subtle.decrypt(
        {{ name: 'AES-GCM', iv: iv }}, key, ciphertext
      );
      return new TextDecoder().decode(decrypted);
    }}

    let _failCount = 0;
    let _lockedOut = false;

    function startLockout() {{
      _lockedOut = true;
      let seconds = 15;
      const lockoutEl = document.getElementById('pw-lockout');
      const btn = document.getElementById('pw-btn');
      btn.disabled = true;
      lockoutEl.style.display = 'block';
      lockoutEl.textContent = `Too many attempts. Wait ${{seconds}}s...`;
      const timer = setInterval(() => {{
        seconds--;
        if (seconds <= 0) {{
          clearInterval(timer);
          _lockedOut = false;
          _failCount = 0;
          lockoutEl.style.display = 'none';
          btn.disabled = false;
        }} else {{
          lockoutEl.textContent = `Too many attempts. Wait ${{seconds}}s...`;
        }}
      }}, 1000);
    }}

    async function checkPassword() {{
      if (_lockedOut) return;
      const input = document.getElementById('pw-input').value;
      if (!input) return;
      const btn = document.getElementById('pw-btn');
      btn.disabled = true;
      btn.textContent = 'Checking...';

      try {{
        const plaintext = await decryptContent(input, ENCRYPTED_BLOB);
        const sections = JSON.parse(plaintext);

        // Inject decrypted content into tab containers
        for (const [tabId, html] of Object.entries(sections)) {{
          const el = document.getElementById('tab-' + tabId);
          if (el) el.innerHTML = html;
        }}

        // Show app, hide gate
        document.getElementById('pw-gate').style.display = 'none';
        document.getElementById('app-content').classList.add('unlocked');
        document.getElementById('app-footer').style.display = 'block';
        _failCount = 0;
      }} catch(e) {{
        _failCount++;
        document.getElementById('pw-error').style.display = 'block';
        document.getElementById('pw-input').value = '';
        document.getElementById('pw-input').focus();
        if (_failCount >= 3) {{
          startLockout();
        }}
      }}

      btn.disabled = false;
      btn.textContent = 'Enter';
    }}

    // Focus password input on load
    document.getElementById('pw-input').focus();
  </script>
</body>
</html>"""


def main():
    print("Loading album stats...")
    image_counts = load_image_counts()
    print(f"  Found {len(image_counts)} albums with image counts")

    print("Loading cover images...")
    cover_images = load_cover_images()
    print(f"  Found {len(cover_images)} cover images")

    all_galleries = KRITHIN_GALLERIES + MONIKA_GALLERIES + FAMILY_GALLERIES
    for g in all_galleries:
        nid = g.get("node_id", "")
        count = image_counts.get(nid, 0)
        has_cover = "+" if nid in cover_images else "-"
        if count:
            print(f"  [{has_cover}] {g['title']}: {count} images")
        elif nid:
            print(f"  [{has_cover}] {g['title']}: no count found")
        else:
            print(f"  [-] {g['title']}: no node_id")

    print("\nGenerating HTML...")
    html = generate_html(image_counts, cover_images)

    OUTPUT_DIR.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  Written to {OUTPUT_FILE}")
    print(f"  File size: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")

    webbrowser.open(f"file://{OUTPUT_FILE.resolve()}")
    print("\nDone! Opening in browser...")


if __name__ == "__main__":
    main()
