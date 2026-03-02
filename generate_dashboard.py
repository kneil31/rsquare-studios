#!/usr/bin/env python3
"""
RSQUARE STUDIOS DASHBOARD GENERATOR — Notion-style
Generates a clean HTML dashboard with sidebar navigation for GitHub Pages.

Sections:
  1. Portfolio — Client-facing gallery links (SmugMug)
  2. Packages & Pricing — Client-facing pricing cards
  3. Workflow Dashboard — Password-protected internal tools

Usage:
    python3 generate_dashboard.py
    # Generates index.html and opens in browser

Data sources:
    ../rsqr_whatsapp_api/smugmug_galleries.json
    ../rsqr_whatsapp_api/photography_info_messages.py (pricing hardcoded below)
    ../../photo_workflow/PHOTO_WORKFLOW_CHEATSHEET.md
    ../../../Upskill/Posing_Upskill/prompts/*.md
    ../TwoMann_Course/chapters/*.md
"""

import json
import os
import sys
import base64
import webbrowser
import secrets
from pathlib import Path
from datetime import datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

SCRIPT_DIR = Path(__file__).parent
OUTPUT_FILE = SCRIPT_DIR / "index.html"
SECRET_FILE = SCRIPT_DIR / ".secret"
GALLERIES_FILE = SCRIPT_DIR.parent / "rsqr_whatsapp_api" / "smugmug_galleries.json"
WORKFLOW_FILE = SCRIPT_DIR.parent.parent / "photo_workflow" / "PHOTO_WORKFLOW_CHEATSHEET.md"
POSING_DIR = SCRIPT_DIR.parent.parent.parent / "Upskill" / "Posing_Upskill" / "prompts"
TWOMANN_DIR = SCRIPT_DIR.parent / "TwoMann_Course" / "chapters"
EDITING_PROJECTS_FILE = SCRIPT_DIR / "editing_projects.json"

# Gear list — rendered inline on the home page
GEAR_LIST = {
    "\U0001f4f7 Camera Bodies": [
        "Canon EOS R5 C (Cinema)",
        "Canon EOS C50 (Cinema)",
        "Canon EOS R6 Mark II",
        "Canon EOS R6 (\u00d72)",
    ],
    "\U0001f52d Lenses": [
        "Canon RF 28-70mm f/2L USM",
        "Canon RF 15-35mm f/2.8L IS USM",
        "Canon RF 70-200mm f/2.8L IS USM",
"Canon RF 35mm f/1.8 IS Macro STM",
        "Canon RF 50mm f/1.8 STM",
        "Canon RF 16mm f/2.8 STM",
    ],
    "\U0001f4a1 Lighting": [
        "Godox VL300 LED",
        "Godox AD600 Pro",
        "Godox AD200 Pro",
        "Godox M1 RGB LED",
        "Godox LC500 Light Stick",
        "Flashpoint Zoom Li-on X R2 TTL",
        "GVM 2-Pack LED Video Lights",
    ],
    "\U0001f527 Light Modifiers": [
        "MagMod MagBox PRO 24\u2033 Octa",
        "MagMod MagShoe v2",
        "MagMod MagRing 2",
        "Godox CS-85D Lantern",
        "Neewer C-Stand",
    ],
    "\U0001f3ac Stabilization & Drone": [
        "DJI RS 4 Gimbal",
        "DJI R Twist Grip Dual Handle",
        "DJI Mavic Air 2",
    ],
    "\U0001f5a5 Monitors": [
        "Atomos Ninja V 5\u2033",
    ],
    "\U0001f392 Accessories": [
        "SmallRig Cage (R5/R6)",
        "FALCAM F22 Quick Release Handle",
        "FALCAM F22 Articulating Arm",
        "Freewell 95mm Variable ND",
        "Pelican 1510 Case",
        "Logitech Mevo Start (streaming)",
    ],
}

# Seed reviews — used as fallback when Google Sheet is unreachable
SEED_REVIEWS = [
    {"name": "Client", "event_type": "Event Photography", "rating": 5,
     "review": "Pictures came out so well. We feel that we made the right choice. We definitely recommend too."},
    {"name": "Client", "event_type": "Wedding Photography", "rating": 5,
     "review": "Your relaxed, personable approach made us feel very welcome. Your work is flawless. Thank you so much for capturing the strong emotions of the day."},
    {"name": "Client", "event_type": "Photo & Video", "rating": 5,
     "review": "Editing and videography looks so amazing and thanks for being so flexible to add changes that we asked for. It was so good working with you."},
    {"name": "Client", "event_type": "Event Photography", "rating": 5,
     "review": "All the photos look stunning! Everyone in the house loved the pictures a lot."},
]

# Load shared secrets
_DASHBOARD_SECRETS_FILE = SCRIPT_DIR / ".dashboard_secrets.json"
def _load_dashboard_secrets():
    with open(_DASHBOARD_SECRETS_FILE) as f:
        return json.load(f)
_dashboard_secrets = _load_dashboard_secrets()

# Load feedback secrets (optional — feedback section only shown if file exists)
_FEEDBACK_SECRETS_FILE = SCRIPT_DIR / ".feedback_secrets.json"
def _load_feedback_secrets():
    if not _FEEDBACK_SECRETS_FILE.exists():
        return None
    with open(_FEEDBACK_SECRETS_FILE) as f:
        return json.load(f)
_feedback_secrets = _load_feedback_secrets()

REVIEW_FORM_URL = _dashboard_secrets["review_form_url"]
RAM_PHONE = _dashboard_secrets["ram_phone"]

# Passwords loaded from .secret file or env vars (never hardcoded)
def _load_passwords():
    """Load client and internal passwords from .secret JSON, env vars, or defaults."""
    if SECRET_FILE.exists():
        try:
            secrets = json.loads(SECRET_FILE.read_text(encoding="utf-8"))
            return secrets.get("client", ""), secrets.get("internal", "")
        except (json.JSONDecodeError, KeyError):
            pass
    client = os.environ.get("DASHBOARD_CLIENT_PASSWORD", "").strip()
    internal = os.environ.get("DASHBOARD_INTERNAL_PASSWORD", "").strip()
    if client and internal:
        return client, internal
    print("ERROR: No passwords found. Create .secret file:")
    print('  {"client": "your-client-pw", "internal": "your-internal-pw"}')
    sys.exit(1)


PBKDF2_ITERATIONS = 400_000


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


def load_galleries():
    if GALLERIES_FILE.exists():
        with open(GALLERIES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Fix doubled URLs
        for category in data:
            for gallery in data[category]:
                url = gallery.get("url", "")
                if "smugmug.comhttps://" in url:
                    gallery["url"] = "https://" + url.split("https://")[-1]
        return data
    return {}


def load_posing_guides():
    guides = {}
    for md_file in sorted(POSING_DIR.glob("*.md")):
        name = md_file.stem.replace("_", " ").title()
        with open(md_file, "r", encoding="utf-8") as f:
            guides[name] = f.read()
    return guides


def load_workflow():
    if WORKFLOW_FILE.exists():
        with open(WORKFLOW_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def load_twomann_chapters():
    chapters = []
    if TWOMANN_DIR.exists():
        for md_file in sorted(TWOMANN_DIR.glob("*.md")):
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
            title = content.split("\n")[0].replace("# ", "").strip() if content else md_file.stem
            chapters.append({"title": title, "file": md_file.stem, "content": content})
    return chapters


def escape_html(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def md_to_html_simple(md_text):
    """Minimal markdown to HTML: headers, bold, tables, lists, code blocks, horizontal rules."""
    import re
    lines = md_text.split("\n")
    html_lines = []
    in_table = False
    in_code = False
    in_list = False

    for line in lines:
        # Code blocks
        if line.strip().startswith("```"):
            if in_code:
                html_lines.append("</pre></div>")
                in_code = False
            else:
                html_lines.append('<div class="wf-code"><pre>')
                in_code = True
            continue
        if in_code:
            html_lines.append(escape_html(line))
            continue

        # Horizontal rule
        if line.strip() in ("---", "***", "___"):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            if in_table:
                html_lines.append("</table>")
                in_table = False
            html_lines.append("<hr>")
            continue

        # Headers
        if line.startswith("### "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f'<h4 class="wf-h4">{line[4:]}</h4>')
            continue
        if line.startswith("## "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f'<h3 class="wf-h3">{line[3:]}</h3>')
            continue
        if line.startswith("# "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f'<h2 class="wf-h2">{line[2:]}</h2>')
            continue

        # Table rows
        if "|" in line and line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            # Skip separator rows
            if all(set(c) <= set("- :") for c in cells):
                continue
            if not in_table:
                html_lines.append('<table class="wf-table">')
                in_table = True
                html_lines.append("<tr>" + "".join(f"<th>{c}</th>" for c in cells) + "</tr>")
            else:
                html_lines.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
            continue
        elif in_table:
            html_lines.append("</table>")
            in_table = False

        # Lists
        stripped = line.strip()
        if stripped.startswith("- ") or stripped.startswith("* "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            content = stripped[2:]
            # Bold
            content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
            html_lines.append(f"<li>{content}</li>")
            continue
        elif stripped.startswith("  - ") or stripped.startswith("  * "):
            content = stripped.strip()[2:]
            content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
            html_lines.append(f"<li style='margin-left:20px'>{content}</li>")
            continue
        elif in_list and stripped == "":
            html_lines.append("</ul>")
            in_list = False

        # Numbered lists
        if re.match(r'^\d+\. ', stripped):
            content = re.sub(r'^\d+\. ', '', stripped)
            content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
            html_lines.append(f'<p class="wf-step">{content}</p>')
            continue

        # Paragraphs
        if stripped:
            text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', stripped)
            text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
            html_lines.append(f"<p>{text}</p>")

    if in_table:
        html_lines.append("</table>")
    if in_list:
        html_lines.append("</ul>")
    if in_code:
        html_lines.append("</pre></div>")

    return "\n".join(html_lines)


def build_gallery_cards(galleries):
    """Build gallery card HTML for each category."""
    # Merge anniversary, pooja, naming, housewarming into "celebrations"
    # Do this before processing
    merge_into_celebrations = ["housewarming", "anniversary", "pooja", "naming"]
    if "celebrations" not in galleries:
        galleries["celebrations"] = []
    for merge_cat in merge_into_celebrations:
        if merge_cat in galleries:
            galleries["celebrations"].extend(galleries.pop(merge_cat))

    # Display order for categories (9 tiles)
    category_order = [
        "wedding", "engagement", "pre_wedding", "half_saree",
        "maternity", "baby_shower", "birthday", "cradle",
        "celebrations",
    ]
    category_icons = {
        "wedding": "💍",
        "engagement": "💎",
        "pre_wedding": "💐",
        "half_saree": "🪷",
        "maternity": "🤰",
        "baby_shower": "👶",
        "birthday": "🎂",
        "cradle": "🍼",
        "celebrations": "🎊",
    }
    category_labels = {
        "wedding": "Wedding",
        "engagement": "Engagement",
        "pre_wedding": "Pre-Wedding",
        "half_saree": "Half Saree",
        "maternity": "Maternity",
        "baby_shower": "Baby Shower",
        "birthday": "Birthday",
        "cradle": "Cradle Ceremony",
        "celebrations": "Celebrations",
    }
    category_covers = {
        "wedding": ("https://photos.smugmug.com/photos/i-BvTChsc/0/LwhGTh2B2pCPDgNpjPJp8J3nCSfRNdKwd3j5CVTKN/X3/i-BvTChsc-X3.jpg", "center 43%"),
        "engagement": ("https://photos.smugmug.com/photos/i-8NfsLKT/0/LVnhsbXXV3JPcX2r2PhvcKfCj9gK9czpWsZ2VXrSH/X3/i-8NfsLKT-X3.jpg", "38% 47%"),
        "pre_wedding": ("https://photos.smugmug.com/photos/i-GfR24FT/0/MHQbxRCTTvn8x7WXCkzHRjCWR96TC6TnBsTfQRFQ7/X3/i-GfR24FT-X3.jpg", "center 24%"),
        "half_saree": ("https://photos.smugmug.com/photos/i-MCmGphP/0/NZvk2KBMQzVZvJJTQh23xdmRRsvzNzGRdBgx2HX66/X3/i-MCmGphP-X3.jpg", "68% 52%"),
        "maternity": ("https://photos.smugmug.com/photos/i-ZqWs3n5/0/NcPVRqqFJXR3MJfcVn45gshTHXpxkZFvfv655D3mB/X3/i-ZqWs3n5-X3.jpg", "center 18%"),
        "baby_shower": ("https://photos.smugmug.com/photos/i-3MjgbV3/0/NWkJRQPLmfwjxBJ2qLpKLS2RHVpb39NtfssFhZJxp/X3/i-3MjgbV3-X3.jpg", "37% 18%"),
        "birthday": ("https://photos.smugmug.com/photos/i-Xq8BHgp/0/NGnrqRVd9gkP3r8gdC8BdwN2WrLPJT4MpQ594MTwF/X3/i-Xq8BHgp-X3.jpg", "center 40%"),
        "cradle": ("https://photos.smugmug.com/photos/i-R3QTwKk/0/KzsCGkHgZ6HKmVjVtFvwkWF9s9sRzMSTQWKPJfxQb/X3/i-R3QTwKk-X3.jpg", "center 47%"),
        "celebrations": ("https://photos.smugmug.com/photos/i-J8zjNdj/0/K3bnLswZ7LjTxLtFZ6TB3K35XXfx2PhcRnDg4fCG6/X3/i-J8zjNdj-X3.jpg", "38% 30%"),
    }
    # Hero banner positions (wide landscape strip — needs different crop than tiles)
    category_hero_positions = {
        "wedding": "center 30%",
        "engagement": "38% 35%",
        "pre_wedding": "center 20%",
        "half_saree": "68% 35%",
        "maternity": "center 15%",
        "baby_shower": "37% 15%",
        "birthday": "center 30%",
        "cradle": "center 35%",
        "celebrations": "38% 20%",
    }

    cards_by_category = {}
    # Iterate in display order, skip categories not in data
    ordered_cats = [(c, galleries[c]) for c in category_order if c in galleries]
    # Add any categories in data but not in order list
    for c in galleries:
        if c not in category_order:
            ordered_cats.append((c, galleries[c]))
    for cat, items in ordered_cats:
        cards = ""
        for g in items:
            name = g["name"]
            url = g["url"]
            # Extract short name: remove date prefix and location suffix
            parts = name.split(" | ")
            short_name = parts[1] if len(parts) > 1 else name
            location = parts[2] if len(parts) > 2 else ""
            date_str = parts[0] if len(parts) > 0 else ""

            # Format date nicely
            try:
                from datetime import datetime as dt
                d = dt.strptime(date_str.strip(), "%Y-%m-%d")
                display_date = d.strftime("%b %d, %Y")
                month_short = d.strftime("%b").upper()
                day_num = d.strftime("%-d")
            except Exception:
                display_date = date_str
                month_short = ""
                day_num = ""

            loc_display = f"{escape_html(location)} &middot; " if location else ""

            # Get first letter for monogram
            monogram = short_name[0].upper() if short_name else "?"

            # Style A: Monogram (wedding, cradle)
            icon_monogram = f'<div class="gallery-monogram">{monogram}</div>'

            # Style B: Date card (maternity, birthday)
            icon_date = f'<div class="gallery-date-card"><span class="date-month">{month_short}</span><span class="date-day">{day_num}</span></div>'

            # Style C: Accent line (newborn/baby shower)
            # No icon element needed — handled by CSS class

            # Assign style per category for demo
            demo_styles = {"wedding": "monogram", "cradle": "monogram", "engagement": "monogram", "half_saree": "monogram", "celebrations": "monogram", "maternity": "monogram", "birthday": "monogram", "baby_shower": "monogram", "pre_wedding": "monogram"}
            style = demo_styles.get(cat, "monogram")

            if style == "monogram":
                icon_html = icon_monogram
                card_class = "gallery-card"
            elif style == "date":
                icon_html = icon_date
                card_class = "gallery-card"
            else:  # line
                icon_html = ""
                card_class = "gallery-card style-line"

            cards += f"""
                <a href="{escape_html(url)}" target="_blank" rel="noreferrer noopener" class="{card_class}">
                    {icon_html}
                    <div class="gallery-info">
                        <div class="gallery-name">{escape_html(short_name)}</div>
                        <div class="gallery-meta">{loc_display}{escape_html(display_date)}</div>
                    </div>
                    <div class="gallery-arrow">→</div>
                </a>"""
        cards_by_category[cat] = {
            "html": cards,
            "icon": category_icons.get(cat, "📷"),
            "label": category_labels.get(cat, cat.title()),
            "count": len(items),
            "cover": category_covers.get(cat, ("", "center center"))[0],
            "cover_pos": category_covers.get(cat, ("", "center center"))[1],
            "hero_pos": category_hero_positions.get(cat, "center center"),
        }
    return cards_by_category


def build_pricing_section():
    """Build pricing cards with event-based packages."""
    html = """
            <!-- Photo Only -->
            <div class="pricing-card" style="--accent: #8b5cf6;">
                <div class="pricing-header">
                    <span class="pricing-icon">📷</span>
                    <span class="pricing-name">Photo Only</span>
                </div>
                <div class="tier-details" style="margin-bottom:12px;">Just me and my camera &mdash; all edited photos delivered</div>
                <div class="price-tier">
                    <div class="tier-header">
                        <span class="tier-name">2 Hours</span>
                        <span class="tier-price">$300</span>
                    </div>
                    <div class="tier-details">Maternity, portraits, small celebrations</div>
                </div>
                <div class="price-tier">
                    <div class="tier-header">
                        <span class="tier-name">3 Hours</span>
                        <span class="tier-price">$450</span>
                    </div>
                    <div class="tier-details">Baby showers, birthdays, cradle ceremonies</div>
                </div>
                <div class="price-tier">
                    <div class="tier-header">
                        <span class="tier-name">4 Hours</span>
                        <span class="tier-price">$600</span>
                    </div>
                    <div class="tier-details">Half saree, housewarming, larger events</div>
                </div>
            </div>

            <!-- Photo + Video (Solo) -->
            <div class="pricing-card" style="--accent: #3b82f6;">
                <div class="pricing-header">
                    <span class="pricing-icon">📷&thinsp;📹</span>
                    <span class="pricing-name">Photo + Video</span>
                </div>
                <div class="tier-details" style="margin-bottom:12px;">I shoot both photo and video &mdash; great for events you want to relive</div>
                <div class="price-tier">
                    <div class="tier-header">
                        <span class="tier-name">2 Hours</span>
                        <span class="tier-price">$470</span>
                    </div>
                    <div class="tier-details">Maternity, portraits, intimate events</div>
                </div>
                <div class="price-tier">
                    <div class="tier-header">
                        <span class="tier-name">3 Hours</span>
                        <span class="tier-price">$705</span>
                    </div>
                    <div class="tier-details">Baby showers, birthdays, cradle ceremonies</div>
                </div>
                <div class="price-tier">
                    <div class="tier-header">
                        <span class="tier-name">4 Hours</span>
                        <span class="tier-price">$940</span>
                    </div>
                    <div class="tier-details">Half saree, housewarming, engagement</div>
                </div>
            </div>

            <!-- Dual Coverage -->
            <div class="pricing-card" style="--accent: #f59e0b;">
                <div class="pricing-header">
                    <span class="pricing-icon">📷📷</span>
                    <span class="pricing-name">Dual Coverage</span>
                </div>
                <div class="tier-details" style="margin-bottom:12px;">Me on photos, videographer on video &mdash; nothing gets missed</div>
                <div class="price-tier">
                    <div class="tier-header">
                        <span class="tier-name">4 Hours</span>
                        <span class="tier-price">$1,300</span>
                    </div>
                    <div class="tier-details">Half saree, engagement, smaller weddings</div>
                </div>
                <div class="price-tier">
                    <div class="tier-header">
                        <span class="tier-name">8 Hours</span>
                        <span class="tier-price">$2,600</span>
                    </div>
                    <div class="tier-details">Full wedding day coverage</div>
                </div>
                <div class="price-tier">
                    <div class="tier-header">
                        <span class="tier-name">12 Hours</span>
                        <span class="tier-price">$3,900</span>
                    </div>
                    <div class="tier-details">Full wedding &mdash; morning prep to reception</div>
                </div>
            </div>

            <!-- Add-on -->
            <div class="pricing-card" style="--accent: #10b981;">
                <div class="pricing-header">
                    <span class="pricing-icon">📡</span>
                    <span class="pricing-name">Add-on</span>
                </div>
                <div class="price-tier">
                    <div class="tier-header">
                        <span class="tier-name">Live Streaming</span>
                        <span class="tier-price">+$100<span style="font-size:13px;font-weight:400;color:#6b7280;"> flat</span></span>
                    </div>
                    <div class="tier-details">Family back home can watch live on YouTube/Facebook</div>
                </div>
                <div class="price-tier">
                    <div class="tier-header">
                        <span class="tier-name">Extra Hour</span>
                        <span class="tier-price">+$150<span style="font-size:13px;font-weight:400;color:#6b7280;"> &ndash; $325</span></span>
                    </div>
                    <div class="tier-details">Add more time to any package (rate depends on coverage type)</div>
                </div>
            </div>"""

    return html


def build_posing_html(guides):
    """Build posing guide pages."""
    html = ""
    for name, content in guides.items():
        section_id = f"posing-{name.lower().replace(' ', '-')}"
        converted = md_to_html_simple(content)
        html += f"""
            <div class="page" id="{section_id}">
                <a class="back-link" href="#" data-section="workflow-home">&larr; Back to Workflow</a>
                <div class="page-breadcrumb">Posing Guides</div>
                <h1 class="page-title">{name} Prompts</h1>
                <div class="wf-content">{converted}</div>
            </div>"""
    return html


def build_twomann_sidebar(chapters):
    links = ""
    for i, ch in enumerate(chapters):
        section_id = f"twomann-{i}"
        short = ch["title"][:40] + ("..." if len(ch["title"]) > 40 else "")
        links += f'<a href="#{section_id}" class="sidebar-link sub-link" data-section="{section_id}">{short}</a>\n'
    return links


def build_twomann_pages(chapters):
    html = ""
    for i, ch in enumerate(chapters):
        section_id = f"twomann-{i}"
        converted = md_to_html_simple(ch["content"])
        html += f"""
            <div class="page" id="{section_id}">
                <a class="back-link" href="#" data-section="workflow-home">&larr; Back to Workflow</a>
                <div class="page-breadcrumb">TwoMann Course &middot; Chapter {i + 1} of {len(chapters)}</div>
                <h1 class="page-title">{escape_html(ch['title'])}</h1>
                <div class="wf-content">{converted}</div>
            </div>"""
    return html


def generate_html():
    now = datetime.now().strftime("%b %d, %Y")

    # CSP nonce — regenerated each build
    csp_nonce = secrets.token_hex(16)

    # Load data
    galleries = load_galleries()
    gallery_cards = build_gallery_cards(galleries)
    posing_guides = load_posing_guides()
    workflow_md = load_workflow()
    total_galleries = sum(c["count"] for c in gallery_cards.values())

    # Build gear categories HTML
    gear_categories_html = ""
    for category, items in GEAR_LIST.items():
        items_html = "".join(f'<div class="gear-item">{item}</div>' for item in items)
        gear_categories_html += (
            f'                        <div class="gear-category">'
            f'<div class="gear-category-label">{category}</div>'
            f'<div class="gear-grid">{items_html}</div>'
            f'</div>\n'
        )

    # Google Apps Script URL for review submissions
    review_form_url = REVIEW_FORM_URL

    # Client reviews — read from Google Sheet, fall back to seed data
    reviews = None
    try:
        from sheets_sync import read_reviews as _read_sheet_reviews
        reviews = _read_sheet_reviews()
        print(f"  Reviews: {len(reviews)} approved from Google Sheet")
    except Exception as e:
        print(f"  Reviews sheet unavailable ({e}), using seed reviews")

    if not reviews:
        reviews = SEED_REVIEWS

    import html as _html_mod

    def _build_review_cards(review_list):
        cards = []
        for r in review_list:
            name = _html_mod.escape(r["name"])
            event = _html_mod.escape(r["event_type"])
            text = _html_mod.escape(r["review"])
            rating = int(r.get("rating", 5))
            stars = "&#9733;" * rating + "&#9734;" * (5 - rating)
            cards.append(f'''                        <div class="testimonial-card">
                            <div class="testimonial-stars">{stars}</div>
                            <div class="testimonial-quote">{text}</div>
                            <div class="testimonial-name">{name}</div>
                            <div class="testimonial-event">{event}</div>
                        </div>''')
        return "\n".join(cards)

    reviews_html = _build_review_cards(reviews)

    # Build sidebar gallery links
    gallery_sidebar = ""
    for cat, info in gallery_cards.items():
        gallery_sidebar += f'<a href="#portfolio-{cat}" class="sidebar-link" data-section="portfolio-{cat}">{info["icon"]} {info["label"]} ({info["count"]})</a>\n'

    # Build portfolio category pages
    portfolio_pages = ""
    for cat, info in gallery_cards.items():
        portfolio_pages += f"""
            <div class="page gallery-page-wrap" id="portfolio-{cat}">
                <div class="gallery-backdrop" style="background-image:url('{info['cover']}')"></div>
                <a class="back-link" href="#" data-section="portfolio-home">&larr; Back to Portfolio</a>
                <div class="cat-hero" style="background-image:url('{info['cover']}');background-position:{info['hero_pos']}">
                    <div class="cat-hero-content">
                        <div class="cat-hero-title">{info['label']}</div>
                        <div class="cat-hero-sub">{info['count']} galleries</div>
                    </div>
                </div>
                <div class="gallery-grid">{info['html']}</div>
            </div>"""

    # Build posing sidebar links
    posing_sidebar = ""
    for name in posing_guides:
        sid = f"posing-{name.lower().replace(' ', '-')}"
        posing_sidebar += f'<a href="#{sid}" class="sidebar-link sub-link" data-section="{sid}">{name}</a>\n'

    # Checklist data
    pre_shoot_items = [
        "Charge all batteries (camera + flash)",
        "Format memory cards",
        "Check backup camera body",
        "Review shot list with client",
        "Scout location / check weather",
        "Clean lenses",
        "Pack: reflector, light stand, diffuser",
        "Confirm time & address with client",
    ]
    day_of_items = [
        "2 camera bodies",
        "24-70mm f/2.8 + 70-200mm f/2.8",
        "35mm f/1.4 or 50mm f/1.4",
        "Speedlite + spare batteries",
        "3+ memory cards",
        "Lens cloth",
        "Business cards",
        "Water bottle + snack",
    ]
    post_shoot_items = [
        "Ingest cards (Photo Mechanic)",
        "Sort files (sort_ingest.py)",
        "AI Cull (rsqr_aicull)",
        "Import to Lightroom",
        "Send to editor (MEGA)",
        "Review editor picks",
        "Final edit + color grade",
        "Export + upload to SmugMug",
        "Send gallery link to client",
        "Backup to external SSD",
    ]

    # Build protected content dicts — two levels of access
    # Client content: pricing, booking, rate config (password from .secret)
    # Internal content: workflow, checklists, posing guides, editing projects (password from .secret)
    client_content = {"v": 1}
    internal_content = {"v": 1}

    # Pricing page — structured data (no pre-built HTML)
    client_content["pricing"] = {
        "breadcrumb": "Pricing",
        "title": "Investment",
        "subtitle": "Simple packages. Pick your coverage and hours \u2014 everything else is included.",
        "packages": [
            {
                "name": "Photo Only",
                "icon": "\U0001f4f7",
                "accent": "#8b5cf6",
                "desc": "Just me and my camera \u2014 all edited photos delivered",
                "tiers": [
                    {"name": "2 Hours", "price": "$300", "desc": "Maternity, portraits, small celebrations"},
                    {"name": "3 Hours", "price": "$450", "desc": "Baby showers, birthdays, cradle ceremonies"},
                    {"name": "4 Hours", "price": "$600", "desc": "Half saree, housewarming, larger events"},
                ],
            },
            {
                "name": "Photo + Video",
                "icon": "\U0001f4f7\u2009\U0001f4f9",
                "accent": "#3b82f6",
                "desc": "I shoot both photo and video \u2014 great for events you want to relive",
                "tiers": [
                    {"name": "2 Hours", "price": "$470", "desc": "Maternity, portraits, intimate events"},
                    {"name": "3 Hours", "price": "$705", "desc": "Baby showers, birthdays, cradle ceremonies"},
                    {"name": "4 Hours", "price": "$940", "desc": "Half saree, housewarming, engagement"},
                ],
            },
            {
                "name": "Dual Coverage",
                "icon": "\U0001f4f7\U0001f4f7",
                "accent": "#f59e0b",
                "desc": "Me on photos, videographer on video \u2014 nothing gets missed",
                "tiers": [
                    {"name": "4 Hours", "price": "$1,300", "desc": "Half saree, engagement, smaller weddings"},
                    {"name": "8 Hours", "price": "$2,600", "desc": "Full wedding day coverage"},
                    {"name": "12 Hours", "price": "$3,900", "desc": "Full wedding \u2014 morning prep to reception"},
                ],
            },
            {
                "name": "Add-on",
                "icon": "\U0001f4e1",
                "accent": "#10b981",
                "desc": "",
                "tiers": [
                    {"name": "Live Streaming", "price": "+$100", "price_sub": "flat", "desc": "Family back home can watch live on YouTube/Facebook"},
                    {"name": "Extra Hour", "price": "+$150", "price_sub": "\u2013 $325", "desc": "Add more time to any package (rate depends on coverage type)"},
                ],
            },
        ],
        "includes": [
            "All edited photos \u2014 usually ready in 12\u201315 days",
            "Cinematic highlight video (4\u20136 min)",
            "Online gallery \u2014 download, share, print",
            "Full print rights \u2014 print anywhere you want",
        ],
        "comparison": {
            "title": "Solo or Dual \u2014 which one do you need?",
            "solo": {
                "label": "Solo",
                "color": "#10b981",
                "border": "#2d4a2d",
                "pros": [
                    "Easier on the budget",
                    "I handle both photo and video \u2014 ceremony, portraits, reception, all covered",
                ],
                "note": "Good for: birthdays, baby showers, smaller events",
            },
            "dual": {
                "label": "Dual",
                "color": "#3b82f6",
                "border": "#2d3a5e",
                "pros": [
                    "Two people, two angles \u2014 nothing gets missed",
                    "Way more candid shots and guest moments",
                    "Better highlight video with dedicated video guy",
                ],
                "note": "Go with this for: weddings, 100+ guests, multi-spot events",
            },
        },
        "reviews": [{"name": r["name"], "event_type": r["event_type"], "rating": int(r.get("rating", 5)), "text": r["review"]} for r in reviews[:2]],
    }

    # Booking page — structured data (no pre-built HTML)
    client_content["booking"] = {
        "breadcrumb": "Book",
        "title": "Request a Quote",
        "subtitle": "Fill in your details and I'll send you a quote on WhatsApp.",
        "event_types": ["Wedding", "Engagement", "Pre-Wedding", "Half Saree", "Baby Shower",
                        "Maternity", "Birthday", "Cradle Ceremony", "Housewarming",
                        "Anniversary", "Pooja", "Other"],
        "settings": ["Outdoor", "Indoor", "Outdoor + Indoor"],
        "coverage_types": [
            {"value": "photo_only", "label": "Photo Only"},
            {"value": "photo_video", "label": "Photo + Video"},
            {"value": "dual_coverage", "label": "Dual Coverage"},
        ],
        "live_streaming_label": "Add Live Streaming (+$100)",
    }

    # Workflow home — structured data
    internal_content["workflow-home"] = {
        "breadcrumb": "Internal",
        "title": "Workflow Dashboard",
        "subtitle": "Checklists, posing prompts, course notes & workflow reference",
        "pipeline": [
            {"label": "Inquiry", "color": "#3b82f6"},
            {"label": "Booked", "color": "#8b5cf6"},
            {"label": "Shot", "color": "#f59e0b"},
            {"label": "Editing", "color": "#ec4899"},
            {"label": "Delivered", "color": "#10b981"},
        ],
        "tiles": [
            {"icon": "\u2705", "label": "Checklists", "section": "checklists"},
            {"icon": "\U0001f4d6", "label": "Workflow Reference", "section": "workflow-ref"},
            {"icon": "\U0001f3ac", "label": "Photo Editing", "section": "editing-projects"},
            {"icon": "\U0001f3a5", "label": "Video Editing", "section": "video-projects"},
            {"icon": "\U0001f4ac", "label": "Client Feedback", "section": "client-feedback"},
            {"icon": "\U0001f491", "label": "Couple Poses", "section": "posing-couples"},
            {"icon": "\U0001f468\u200d\U0001f469\u200d\U0001f467", "label": "Family Poses", "section": "posing-families"},
            {"icon": "\U0001f48d", "label": "Wedding Poses", "section": "posing-weddings"},
            {"icon": "\U0001f4f8", "label": "Pose References", "url": "https://literate-basketball-b5e.notion.site/PLAN-POSES-13e48bb472084196a825703d7e8a4d10"},
            {"icon": "\U0001f4cb", "label": "Booking Confirm", "section": "booking-confirm"},
        ],
    }

    # Checklists — structured data
    internal_content["checklists"] = {
        "breadcrumb": "Workflow",
        "title": "Shoot Checklists",
        "subtitle": "Check items off as you go \u2014 state is saved in your browser",
        "has_back": True,
        "back_section": "workflow-home",
        "groups": [
            {"title": "PRE-SHOOT", "prefix": "pre", "items": pre_shoot_items},
            {"title": "DAY-OF GEAR", "prefix": "day", "items": day_of_items},
            {"title": "POST-SHOOT", "prefix": "post", "items": post_shoot_items},
        ],
    }

    # Workflow reference — raw markdown (rendered client-side)
    internal_content["workflow-ref"] = {
        "breadcrumb": "Workflow",
        "title": "Photo Workflow Reference",
        "subtitle": "Ingest \u2192 Sort \u2192 Cull \u2192 Edit \u2192 Export \u2192 Deliver",
        "has_back": True,
        "back_section": "workflow-home",
        "markdown": workflow_md,
    }

    # Editing projects tracker — read from Google Sheet, fall back to local JSON
    editing_rows_data = []
    editing_project_list = None
    try:
        from sheets_sync import read_projects as _read_sheet_projects
        editing_project_list = _read_sheet_projects()
        print(f"  Editing projects: {len(editing_project_list)} from Google Sheet")
    except Exception as e:
        print(f"  Google Sheet unavailable ({e}), falling back to local JSON")
        if EDITING_PROJECTS_FILE.exists():
            with open(EDITING_PROJECTS_FILE, "r", encoding="utf-8") as f:
                editing_project_list = json.load(f).get("projects", [])

    if editing_project_list:
        today = datetime.now()
        for p in editing_project_list:
            status = p["status"].strip().upper()
            # Skip completed projects — only show pending/active
            if "COMPLETED" in status or "DONE" in status:
                continue

            sent = datetime.strptime(p["date_sent"], "%Y-%m-%d")
            days_elapsed = (today - sent).days
            if days_elapsed > p.get("expected_days", 14):
                display_status = "OVERDUE"
            elif status == "SENT":
                display_status = "SENT"
            else:
                display_status = status

            editing_rows_data.append({
                "task": p["task"],
                "priority": p["priority"],
                "date_sent": sent.strftime("%b %d, %Y"),
                "days": days_elapsed,
                "status": display_status,
                "completed": p.get("edit_completed", "") or "\u2014",
                "delivery_link": p.get("delivery_link", ""),
            })

    internal_content["editing-projects"] = {
        "breadcrumb": "Workflow",
        "title": "Photo Editing",
        "subtitle": "Track outsourced photo editing \u2014 status, delivery links, and follow-ups",
        "has_back": True,
        "back_section": "workflow-home",
        "columns": ["Project", "Priority", "Sent", "Days", "Status", "Completed", "Files"],
        "rows": editing_rows_data,
    }

    # Video editing projects — read from Google Sheet tab 2
    video_rows_data = []
    try:
        from sheets_sync import read_video_projects as _read_video_projects
        video_project_list = _read_video_projects()
        print(f"  Video projects: {len(video_project_list)} from Google Sheet")
    except Exception as e:
        print(f"  Video projects unavailable ({e})")
        video_project_list = []

    if video_project_list:
        today = datetime.now()
        for p in video_project_list:
            status = p["status"].strip().upper()
            # Skip fully completed projects — keep "1st Cut DONE" as in-progress
            if "PROJECT COMPLETED" in status:
                continue
            if status == "COMPLETED":
                continue

            sent = datetime.strptime(p["date_sent"], "%Y-%m-%d")
            days_elapsed = (today - sent).days
            if days_elapsed > p.get("expected_days", 14):
                display_status = "OVERDUE"
            elif "1ST CUT" in status:
                display_status = "1ST CUT DONE"
            elif status == "SENT":
                display_status = "SENT"
            else:
                display_status = status

            video_rows_data.append({
                "task": p["task"],
                "editor": p.get("editor", "Madhu"),
                "priority": p["priority"],
                "date_sent": sent.strftime("%b %d, %Y"),
                "days": days_elapsed,
                "status": display_status,
                "completed": p.get("edit_completed", "") or "\u2014",
                "delivery_link": p.get("delivery_link", ""),
            })

    internal_content["video-projects"] = {
        "breadcrumb": "Workflow",
        "title": "Video Editing",
        "subtitle": "Track video editing \u2014 reels, teasers, wedding films",
        "has_back": True,
        "back_section": "workflow-home",
        "columns": ["Project", "Editor", "Priority", "Sent", "Days", "Status", "Completed", "Files"],
        "rows": video_rows_data,
    }

    # Client feedback — live corrections/song choices from clients (data from .feedback_secrets.json)
    if _feedback_secrets:
        import html as _html
        fb_projects = {}
        fb_project_pins = {}
        for slug, p in _feedback_secrets["projects"].items():
            fb_projects[slug] = {
                "name": _html.escape(p["name"]),
                "type": p.get("type", "video"),
                "editor": _html.escape(p["editor"]),
                "editor_phone": p["editor_phone"],
                "photo_editor": _html.escape(p.get("photo_editor", "") or ""),
                "photo_editor_phone": p.get("photo_editor_phone", ""),
                "status": p.get("status", "editing"),
                "photo_status": p.get("photo_status", ""),
                "video_status": p.get("video_status", ""),
                "delivery_link": p.get("delivery_link", ""),
                "gallery_count": p.get("gallery_count", 0),
                "versions": [{"label": _html.escape(v["label"]), "url": v["url"]} for v in p.get("versions", [])],
            }
            fb_project_pins[p["name"]] = p["pin"]

        internal_content["client-feedback"] = {
            "breadcrumb": "Workflow",
            "title": "Client Feedback",
            "subtitle": "Live corrections and song choices from clients",
            "has_back": True,
            "back_section": "workflow-home",
            "type": "feedback-admin",
            "projects": fb_projects,
            "project_pins": fb_project_pins,
            "script_url": _feedback_secrets["feedback_script_url"],
            "ram_phone": RAM_PHONE,
        }

    # Booking confirmation tool — WhatsApp message builder
    internal_content["booking-confirm"] = {
        "breadcrumb": "Workflow",
        "title": "Send Booking Confirmation",
        "subtitle": "Fill in details and send confirmation to client via WhatsApp",
        "has_back": True,
        "back_section": "workflow-home",
        "event_types": ["Wedding", "Maternity", "Newborn", "Birthday", "Cradle Ceremony", "Family"],
        "quick_fills": [
            {"label": "Wedding", "event": "Wedding Photography", "location": "Dallas, TX"},
            {"label": "Maternity", "event": "Maternity Photography", "location": "Dallas, TX"},
            {"label": "Newborn", "event": "Newborn Photography", "location": "Dallas, TX"},
            {"label": "Birthday", "event": "Birthday Photography", "location": "Dallas, TX"},
        ],
        "defaults": {"start_time": "18:00", "end_time": "22:00"},
        "phone": RAM_PHONE,
        "photographer_name": "Ram",
    }

    # Posing guide pages — each gets its own key with raw markdown
    posing_shells = ""
    for name, content in posing_guides.items():
        section_id = f"posing-{name.lower().replace(' ', '-')}"
        internal_content[section_id] = {
            "breadcrumb": "Posing Guides",
            "title": f"{name} Prompts",
            "has_back": True,
            "back_section": "workflow-home",
            "markdown": content,
        }
        posing_shells += f"""
            <div class="page" id="{section_id}">
                <div class="encrypted-placeholder">This content is encrypted. Enter the password to view posing guides.</div>
            </div>"""

    # Rate config — encrypted alongside client content so no dollar amounts in plaintext JS
    client_content["__config__"] = {
        "rateMap": {
            "photo_only": 150,
            "photo_video": 235,
            "dual_coverage": 325,
        },
        "labelMap": {
            "photo_only": "Photo Only ($150/hr)",
            "photo_video": "Photo + Video ($235/hr)",
            "dual_coverage": "Dual Coverage ($325/hr)",
        },
        "liveStreamingCost": 100,
        "reviewFormUrl": REVIEW_FORM_URL,
        "ramPhone": RAM_PHONE,
    }

    # Encrypt client and internal content with separate passwords
    client_pw, internal_pw = _load_passwords()
    client_json = json.dumps(client_content)
    internal_json = json.dumps(internal_content)
    encrypted_client_blob = encrypt_content(client_json, client_pw)
    encrypted_internal_blob = encrypt_content(internal_json, internal_pw)
    # Admin blob: client content encrypted with internal password (so internal pw unlocks everything)
    encrypted_client_admin_blob = encrypt_content(client_json, internal_pw)
    print(f"   Encrypted client + internal + admin sections")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="referrer" content="no-referrer">
    <meta http-equiv="Permissions-Policy" content="camera=(), microphone=(), geolocation=()">
    <meta name="robots" content="noindex, nofollow, noarchive">
    <meta property="og:title" content="Rsquare Studios">
    <meta property="og:description" content="Wedding & Portrait Photography — Dallas, TX">
    <meta property="og:image" content="https://portfolio.rsquarestudios.com/hero.jpg">
    <meta property="og:url" content="https://portfolio.rsquarestudios.com/">
    <meta property="og:type" content="website">
    <meta name="twitter:card" content="summary_large_image">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'nonce-{csp_nonce}'; style-src 'unsafe-inline'; img-src 'self' https://*.smugmug.com https://img.youtube.com data:; connect-src https://script.google.com https://script.googleusercontent.com; font-src 'none'; frame-src 'none'; base-uri 'none'; form-action https://script.google.com;">
    <title>Rsquare Studios — Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #191919;
            color: #e0e0e0;
            height: 100vh;
            overflow: hidden;
        }}

        .layout {{ display: flex; height: 100vh; }}

        /* Sidebar */
        .sidebar {{
            width: 270px;
            min-width: 270px;
            background: #202020;
            border-right: 1px solid #2d2d2d;
            padding: 20px 12px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
        }}
        .sidebar-brand {{
            padding: 8px 12px 16px;
            font-size: 15px;
            font-weight: 700;
            color: #9ca3af;
            letter-spacing: -0.3px;
        }}
        .sidebar-brand span {{ color: #ffffff; }}
        .sidebar-link {{
            display: block;
            padding: 6px 12px;
            margin: 1px 0;
            color: #9ca3af;
            text-decoration: none;
            font-size: 14px;
            border-radius: 6px;
            transition: all 0.15s;
            line-height: 1.5;
            cursor: pointer;
        }}
        .sidebar-link:hover {{ background: #2d2d2d; color: #e0e0e0; }}
        .sidebar-link.active {{ background: #2d2d2d; color: #ffffff; }}
        .sidebar-link.sub-link {{ padding-left: 28px; font-size: 13px; }}
        .sidebar-section-label {{
            padding: 14px 12px 4px;
            font-size: 11px;
            font-weight: 700;
            color: #525252;
            letter-spacing: 1px;
        }}
        .sidebar-divider {{
            height: 1px;
            background: #2d2d2d;
            margin: 8px 12px;
        }}
        .sidebar-footer {{
            margin-top: auto;
            padding: 16px 12px 8px;
            font-size: 11px;
            color: #525252;
        }}
        .sidebar-collapse {{
            display: none;
        }}

        /* Lock icon for protected sections */
        .lock-icon {{ opacity: 0.5; }}
        .lock-icon.unlocked {{ opacity: 1; }}

        /* Encrypted content placeholder */
        .encrypted-placeholder {{
            text-align: center;
            color: #525252;
            padding: 60px 20px;
            font-size: 14px;
        }}

        /* Content */
        .content {{
            flex: 1;
            overflow-y: auto;
            padding: 40px 60px;
        }}

        /* Pages */
        .page {{
            display: none;
            max-width: 800px;
            animation: fadeIn 0.2s;
        }}
        .page.active {{ display: block; }}
        @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}

        .back-link {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 13px;
            font-weight: 500;
            color: #9ca3af;
            text-decoration: none;
            margin-bottom: 20px;
            padding: 6px 12px;
            background: rgba(255,255,255,0.04);
            border-radius: 8px;
            cursor: pointer;
            transition: color 0.2s, background 0.2s;
        }}
        .back-link:hover {{ color: #fff; background: rgba(255,255,255,0.08); }}

        .page-breadcrumb {{
            font-size: 12px;
            color: #525252;
            margin-bottom: 8px;
            letter-spacing: 0.5px;
        }}
        .page-title {{
            font-size: 32px;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 6px;
            letter-spacing: -0.5px;
        }}
        .page-meta {{
            font-size: 14px;
            color: #6b7280;
            margin-bottom: 32px;
        }}

        /* Hero — Option D: split layout (image left, text right) */
        .hero {{
            border-radius: 16px;
            margin: 0 16px 24px;
            overflow: hidden;
            display: flex;
            align-items: stretch;
            background: linear-gradient(180deg, #2d1854 0%, #0e0518 35%, #050208 100%);
        }}
        .hero-img-wrap {{
            position: relative;
            width: 50%;
            flex-shrink: 0;
            background: linear-gradient(180deg, #2d1854 0%, #0e0518 35%, #050208 100%);
        }}
        .hero-image {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
            -webkit-mask-image: linear-gradient(to right, black 40%, transparent 100%);
            mask-image: linear-gradient(to right, black 40%, transparent 100%);
        }}
        .hero-body {{
            padding: 36px 32px;
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}
        .hero h1 {{
            font-size: 32px;
            font-weight: 800;
            color: #fff;
            margin-bottom: 10px;
            letter-spacing: -1px;
        }}
        .hero p {{
            font-size: 15px;
            color: #c4b5fd;
            line-height: 1.6;
            margin-bottom: 24px;
        }}
        .hero-stats {{
            display: flex;
            gap: 28px;
            margin-bottom: 24px;
        }}
        .hero-stat {{
            text-align: left;
        }}
        .hero-stat .number {{
            font-size: 24px;
            font-weight: 700;
            color: #c4b5fd;
        }}
        .hero-stat .label {{
            font-size: 11px;
            color: #9ca3af;
            letter-spacing: 0.5px;
            margin-top: 2px;
        }}
        .hero-cta {{
            display: inline-block;
            padding: 12px 28px;
            background: #8b5cf6;
            color: #fff;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            font-size: 15px;
            transition: background 0.2s;
            box-shadow: 0 4px 16px rgba(139,92,246,0.4);
            align-self: flex-start;
        }}
        .hero-cta:hover {{ background: #7c3aed; }}
        @keyframes bounce {{
            0%, 100% {{ transform: translateY(0); }}
            50% {{ transform: translateY(6px); }}
        }}

        /* Category tiles on portfolio home */
        .cat-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
            gap: 16px;
            margin-top: 24px;
        }}
        .cat-tile {{
            display: flex;
            flex-direction: column;
            cursor: pointer;
            transition: transform 0.15s, box-shadow 0.2s;
            text-decoration: none;
            color: inherit;
        }}
        .cat-tile:hover {{
            transform: translateY(-3px);
        }}
        .cat-tile-img {{
            position: relative;
            border-radius: 12px;
            overflow: hidden;
            aspect-ratio: 3/4;
            background-size: cover;
            background-position: center;
        }}
        .cat-tile:hover .cat-tile-img {{
            box-shadow: 0 8px 24px rgba(139,92,246,0.25);
        }}
        .cat-tile-content {{
            padding: 10px 4px 0;
            text-align: left;
        }}
        .cat-icon {{ display: none; }}
        .cat-name {{ font-size: 16px; font-weight: 700; color: #fff; margin-bottom: 1px; }}
        .cat-count {{ font-size: 13px; color: #9ca3af; }}

        /* Category hero banner */
        .cat-hero {{
            position: relative;
            border-radius: 16px;
            overflow: hidden;
            height: 240px;
            background-size: cover;
            background-position: center;
            margin-bottom: 28px;
            display: flex;
            align-items: flex-end;
        }}
        .cat-hero::before {{
            content: '';
            position: absolute;
            inset: 0;
            background: linear-gradient(180deg, transparent 20%, rgba(0,0,0,0.7) 100%);
        }}
        .cat-hero-content {{
            position: relative;
            z-index: 1;
            padding: 24px;
        }}
        .cat-hero-title {{
            font-size: 28px;
            font-weight: 800;
            color: #fff;
            letter-spacing: -0.5px;
            text-shadow: 0 2px 8px rgba(0,0,0,0.5);
        }}
        .cat-hero-sub {{
            font-size: 14px;
            color: #d1d5db;
            margin-top: 4px;
            text-shadow: 0 1px 4px rgba(0,0,0,0.5);
        }}

        /* Gallery page with blurred backdrop */
        .gallery-page-wrap {{
            position: relative;
        }}
        .gallery-backdrop {{
            position: fixed;
            inset: 0;
            background-size: cover;
            background-position: center;
            filter: blur(30px) brightness(0.15);
            z-index: -1;
            transform: scale(1.2);
            display: none;
        }}
        .page.active .gallery-backdrop {{
            display: block;
        }}

        /* Video grid */
        .video-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }}
        .video-card {{
            text-decoration: none;
            color: inherit;
            border-radius: 12px;
            overflow: hidden;
            background: #252525;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .video-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(139,92,246,0.2);
        }}
        .video-thumb {{
            position: relative;
            aspect-ratio: 16/9;
            background-size: cover;
            background-position: center;
        }}
        .video-play {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 48px;
            height: 48px;
            background: rgba(0,0,0,0.7);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            color: #fff;
        }}
        .video-duration {{
            position: absolute;
            bottom: 6px;
            right: 6px;
            background: rgba(0,0,0,0.8);
            color: #fff;
            font-size: 11px;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 600;
        }}
        .video-title {{
            padding: 10px 12px;
            font-size: 13px;
            font-weight: 600;
            color: #e0e0e0;
            line-height: 1.3;
        }}

        /* Gallery cards */
        .gallery-grid {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .gallery-card {{
            display: flex;
            align-items: center;
            gap: 14px;
            padding: 16px 18px;
            background: rgba(255,255,255,0.04);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 12px;
            text-decoration: none;
            color: inherit;
            transition: background 0.2s, transform 0.15s;
        }}
        .gallery-card:hover {{
            background: rgba(255,255,255,0.08);
            transform: translateY(-1px);
        }}

        /* Style A: Monogram — elegant serif initial in thin circle */
        .gallery-monogram {{
            width: 42px;
            height: 42px;
            border-radius: 50%;
            border: 1.5px solid rgba(255,255,255,0.2);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            font-weight: 300;
            font-family: 'Georgia', 'Times New Roman', serif;
            color: #d1d5db;
            flex-shrink: 0;
            letter-spacing: 1px;
        }}

        /* Style B: Date card — mini calendar */
        .gallery-date-card {{
            width: 42px;
            height: 46px;
            border-radius: 8px;
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.08);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            overflow: hidden;
        }}
        .gallery-date-card .date-month {{
            font-size: 9px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #8b5cf6;
            line-height: 1;
            margin-bottom: 2px;
        }}
        .gallery-date-card .date-day {{
            font-size: 16px;
            font-weight: 300;
            color: #e0e0e0;
            line-height: 1;
        }}

        /* Style C: Accent line — vertical bar, no icon */
        .gallery-card.style-line {{
            padding-left: 0;
            gap: 0;
            border-left: 3px solid #8b5cf6;
            border-radius: 0 12px 12px 0;
        }}
        .gallery-card.style-line .gallery-info {{
            padding-left: 18px;
        }}

        .gallery-info {{ flex: 1; }}
        .gallery-name {{
            font-size: 15px;
            font-weight: 600;
            color: #f0f0f0;
            letter-spacing: -0.2px;
        }}
        .gallery-meta {{
            font-size: 12px;
            color: rgba(255,255,255,0.35);
            margin-top: 3px;
            letter-spacing: 0.2px;
        }}
        .gallery-arrow {{
            font-size: 14px;
            color: rgba(255,255,255,0.2);
            transition: color 0.2s, transform 0.2s;
        }}
        .gallery-card:hover .gallery-arrow {{
            color: #8b5cf6;
            transform: translateX(2px);
        }}

        /* Pricing cards */
        .pricing-grid {{
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}
        .pricing-card {{
            background: #202020;
            border: 1px solid #2d2d2d;
            border-radius: 12px;
            padding: 24px;
            border-left: 3px solid var(--accent, #8b5cf6);
        }}
        .pricing-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 16px;
        }}
        .pricing-icon {{ font-size: 24px; }}
        .pricing-name {{ font-size: 20px; font-weight: 700; color: #fff; }}
        .price-tier {{
            padding: 12px 0;
            border-bottom: 1px solid #2d2d2d;
        }}
        .price-tier:last-of-type {{ border-bottom: none; }}
        .tier-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 4px;
        }}
        .tier-name {{ font-size: 15px; font-weight: 600; color: #e0e0e0; }}
        .tier-price {{ font-size: 18px; font-weight: 700; color: var(--accent, #8b5cf6); }}
        .tier-details {{ font-size: 13px; color: #6b7280; line-height: 1.5; }}
        .addons-label {{
            font-size: 12px;
            font-weight: 700;
            color: #525252;
            letter-spacing: 0.5px;
            margin-top: 14px;
            margin-bottom: 8px;
        }}
        .addons-list {{
            list-style: none;
            padding: 0;
        }}
        .addons-list li {{
            font-size: 13px;
            color: #9ca3af;
            padding: 3px 0;
        }}
        .addons-list li::before {{
            content: "+ ";
            color: var(--accent, #8b5cf6);
            font-weight: 600;
        }}
        .includes-box {{
            background: #1a1a2e;
            border: 1px solid #2d2d4e;
            border-radius: 10px;
            padding: 20px;
            margin-top: 24px;
        }}
        .includes-box h3 {{
            font-size: 14px;
            font-weight: 700;
            color: #a78bfa;
            margin-bottom: 12px;
        }}
        .includes-list {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 6px;
        }}
        .includes-list span {{
            font-size: 13px;
            color: #c4b5fd;
        }}

        /* Checklists */
        .checklist-group {{
            margin-bottom: 28px;
        }}
        .checklist-title {{
            font-size: 14px;
            font-weight: 700;
            color: #8b5cf6;
            letter-spacing: 0.5px;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid #2d2d2d;
        }}
        .check-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 12px;
            border-radius: 6px;
            cursor: pointer;
            transition: background 0.15s;
            font-size: 14px;
            color: #9ca3af;
        }}
        .check-item:hover {{ background: #2d2d2d; }}
        .check-item input[type="checkbox"] {{
            accent-color: #8b5cf6;
            width: 16px;
            height: 16px;
        }}
        .check-item input:checked + span {{
            text-decoration: line-through;
            color: #525252;
        }}

        /* Booking form */
        .book-form {{
            display: flex;
            flex-direction: column;
            gap: 14px;
            max-width: 500px;
        }}
        .form-row {{
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}
        .form-label {{
            font-size: 12px;
            font-weight: 700;
            color: #525252;
            letter-spacing: 0.5px;
        }}
        .form-input, .form-select {{
            padding: 10px 14px;
            background: #202020;
            border: 1px solid #2d2d2d;
            border-radius: 8px;
            color: #e0e0e0;
            font-size: 15px;
            outline: none;
            font-family: inherit;
            -webkit-appearance: none;
        }}
        .form-input:focus, .form-select:focus {{ border-color: #8b5cf6; }}
        .form-input::placeholder {{ color: #3d3d3d; }}
        .form-select {{ cursor: pointer; }}
        .form-select option {{ background: #202020; }}
        .form-row-inline {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }}
        /* Booking confirmation tool */
        .bc-quickfill {{ margin-bottom: 16px; }}
        .bc-qf-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
        .bc-qf-btn {{
            padding: 10px 12px;
            background: #202020;
            border: 1px solid #2d2d2d;
            border-radius: 8px;
            color: #d1d5db;
            font-size: 13px;
            cursor: pointer;
            transition: border-color .2s, background .2s;
        }}
        .bc-qf-btn:hover {{ border-color: #8b5cf6; background: rgba(139,92,246,0.1); }}
        .bc-form {{ display: flex; flex-direction: column; gap: 12px; }}
        .bc-actions {{ display: flex; gap: 10px; margin-top: 16px; }}
        .bc-send-btn {{
            flex: 1;
            padding: 14px;
            background: #25d366;
            color: #fff;
            font-weight: 600;
            font-size: 15px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: opacity .2s;
        }}
        .bc-send-btn:hover {{ opacity: .9; }}
        .bc-copy-btn {{
            flex: 1;
            padding: 14px;
            background: transparent;
            color: #8b5cf6;
            font-weight: 600;
            font-size: 15px;
            border: 1px solid #8b5cf6;
            border-radius: 10px;
            cursor: pointer;
            transition: background .2s;
        }}
        .bc-copy-btn:hover {{ background: rgba(139,92,246,0.1); }}
        .bc-preview {{
            background: #111;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 20px;
            margin-top: 16px;
        }}
        .bc-preview-label {{
            font-size: 11px;
            font-weight: 700;
            color: #525252;
            letter-spacing: 0.05em;
            margin-bottom: 10px;
        }}
        .bc-preview-label.bc-error {{ color: #ef4444; font-size: 13px; }}
        .bc-preview-text {{
            font-size: 14px;
            line-height: 1.6;
            color: #d1d5db;
        }}

        .quote-preview {{
            background: #111;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 24px;
            margin-top: 16px;
            font-size: 13px;
            line-height: 1.6;
            color: #9ca3af;
        }}
        .quote-section {{
            margin-bottom: 16px;
            padding-bottom: 16px;
            border-bottom: 1px solid rgba(255,255,255,0.06);
        }}
        .quote-section:last-child {{ border-bottom: none; margin-bottom: 0; padding-bottom: 0; }}
        .quote-section-title {{
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            color: #8b5cf6;
            margin-bottom: 8px;
        }}
        .quote-row {{
            display: flex;
            justify-content: space-between;
            padding: 3px 0;
        }}
        .quote-row .qlabel {{ color: #6b7280; }}
        .quote-row .qvalue {{ color: #e0e0e0; font-weight: 500; text-align: right; }}
        .quote-total {{
            font-size: 18px;
            font-weight: 700;
            color: #fff;
        }}
        .quote-note {{
            font-size: 12px;
            color: #6b7280;
            line-height: 1.5;
            margin-top: 4px;
        }}
        .quote-greeting {{
            font-size: 14px;
            color: #d1d5db;
            line-height: 1.6;
        }}
        .quote-signoff {{
            font-size: 13px;
            color: #9ca3af;
            font-style: italic;
        }}
        .copy-btn {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 12px 24px;
            background: #8b5cf6;
            color: #fff;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }}
        .copy-btn:hover {{ background: #7c3aed; }}
        .copy-btn:active {{ transform: scale(0.97); }}
        .share-wa-btn {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 12px 24px;
            background: #25D366;
            color: #fff;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            transition: background 0.2s;
        }}
        .share-wa-btn:hover {{ background: #1da851; }}
        .btn-row {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 8px;
        }}
        .crosssell-card {{
            display: flex;
            align-items: center;
            gap: 14px;
            padding: 16px 18px;
            background: #1c1917;
            border: 1px solid #4a3520;
            border-radius: 12px;
            margin-top: 28px;
            text-decoration: none;
            color: inherit;
            transition: border-color 0.2s;
        }}
        .crosssell-card:hover {{ border-color: #f59e0b; }}
        .crosssell-icon {{ font-size: 36px; }}
        .crosssell-info {{ flex: 1; }}
        .crosssell-title {{ font-size: 15px; font-weight: 600; color: #fef3c7; }}
        .crosssell-desc {{ font-size: 13px; color: #a8956e; margin-top: 2px; }}
        .proscons {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-top: 16px;
        }}
        .proscons-col {{
            background: #202020;
            border-radius: 10px;
            padding: 16px;
        }}
        .proscons-col h4 {{
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
        }}
        .proscons-col ul {{
            list-style: none;
            padding: 0;
        }}
        .proscons-col li {{
            font-size: 13px;
            color: #9ca3af;
            padding: 4px 0;
            line-height: 1.5;
        }}

        /* Site lock — hide everything until password entered */

        /* Password gate */
        .pw-gate {{
            text-align: center;
            padding: 80px 20px;
        }}
        .pw-gate h2 {{
            font-size: 24px;
            color: #fff;
            margin-bottom: 8px;
        }}
        .pw-gate p {{
            font-size: 14px;
            color: #6b7280;
            margin-bottom: 24px;
        }}
        .pw-input-wrap {{
            display: inline-flex;
            align-items: center;
            background: #202020;
            border: 1px solid #2d2d2d;
            border-radius: 8px;
            width: 260px;
            overflow: hidden;
        }}
        .pw-input-wrap:focus-within {{ border-color: #8b5cf6; }}
        .pw-input {{
            padding: 10px 16px;
            background: transparent;
            border: none;
            color: #e0e0e0;
            font-size: 15px;
            outline: none;
            flex: 1;
            text-align: center;
            min-width: 0;
        }}
        .pw-eye-btn {{
            background: none;
            border: none;
            color: #6b7280;
            cursor: pointer;
            padding: 8px 10px;
            font-size: 16px;
            line-height: 1;
        }}
        .pw-eye-btn:hover {{ color: #e0e0e0; }}
        .pw-btn {{
            display: inline-block;
            margin-left: 8px;
            padding: 10px 20px;
            background: #8b5cf6;
            color: #fff;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
        }}
        .pw-btn:hover {{ background: #7c3aed; }}
        .pw-reminder {{
            color: #525252;
            font-size: 11px;
            margin-top: 16px;
        }}
        .logout-btn {{
            position: fixed;
            top: 12px;
            right: 16px;
            background: #374151;
            color: #9ca3af;
            border: none;
            border-radius: 6px;
            padding: 6px 14px;
            font-size: 12px;
            cursor: pointer;
            display: none;
            z-index: 100;
        }}
        .logout-btn:hover {{ background: #4b5563; color: #e0e0e0; }}
        .pw-error {{
            color: #ef4444;
            font-size: 13px;
            margin-top: 12px;
            display: none;
        }}
        .pw-hint {{
            color: #525252;
            font-size: 12px;
            margin-top: 10px;
        }}
        .pw-lockout {{
            color: #f59e0b;
            font-size: 13px;
            margin-top: 12px;
            display: none;
        }}
        .pw-btn:disabled {{
            opacity: 0.4;
            cursor: not-allowed;
        }}

        /* Unlock animation */
        @keyframes unlockReveal {{
            from {{ opacity: 0; transform: translateY(12px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .page.unlocked {{ animation: unlockReveal 0.4s ease-out; }}

        /* Workflow content */
        .wf-content {{
            font-size: 14px;
            line-height: 1.7;
            color: #9ca3af;
        }}
        .wf-content h2 {{ font-size: 22px; font-weight: 700; color: #fff; margin: 28px 0 12px; }}
        .wf-content h3 {{ font-size: 18px; font-weight: 700; color: #e0e0e0; margin: 24px 0 10px; }}
        .wf-content h4 {{ font-size: 15px; font-weight: 600; color: #a78bfa; margin: 20px 0 8px; }}
        .wf-content p {{ margin-bottom: 10px; }}
        .wf-content ul {{ padding-left: 20px; margin-bottom: 12px; }}
        .wf-content li {{ margin-bottom: 4px; }}
        .wf-content hr {{ border: none; border-top: 1px solid #2d2d2d; margin: 20px 0; }}
        .wf-content strong {{ color: #e0e0e0; }}
        .wf-content code {{
            background: #2d2d2d;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 13px;
            color: #a78bfa;
        }}
        .wf-code {{
            background: #0f0f1a;
            border-radius: 8px;
            padding: 16px;
            margin: 12px 0;
            overflow-x: auto;
        }}
        .wf-code pre {{
            font-family: 'SF Mono', 'Fira Code', Menlo, Consolas, monospace;
            font-size: 13px;
            color: #a78bfa;
            line-height: 1.5;
        }}
        .wf-content .wf-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 12px 0;
        }}
        .wf-content .wf-table th,
        .wf-content .wf-table td {{
            padding: 8px 12px;
            text-align: left;
            border-bottom: 1px solid #2d2d2d;
            font-size: 13px;
        }}
        .wf-content .wf-table th {{
            color: #525252;
            font-weight: 600;
            font-size: 12px;
            letter-spacing: 0.5px;
        }}
        .wf-step {{
            padding-left: 20px;
            position: relative;
            margin-bottom: 8px;
        }}
        .wf-step::before {{
            content: "\\25B8";
            position: absolute;
            left: 4px;
            color: #8b5cf6;
        }}

        /* Workflow home tiles */
        .wf-tile-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 14px;
            margin-bottom: 24px;
        }}
        .wf-tile {{
            background: #202020;
            border: 1px solid #2d2d2d;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            cursor: pointer;
            transition: border-color 0.2s, transform 0.15s;
        }}
        .wf-tile:hover {{ border-color: #8b5cf6; transform: translateY(-2px); }}
        .wf-tile-icon {{ font-size: 28px; margin-bottom: 8px; }}
        .wf-tile-label {{ font-size: 14px; font-weight: 600; color: #e0e0e0; }}

        /* Pipeline stages */
        .pipeline-row {{
            display: flex;
            gap: 4px;
            margin-bottom: 24px;
            flex-wrap: wrap;
        }}
        .pipeline-stage {{
            flex: 1;
            min-width: 100px;
            padding: 12px 8px;
            text-align: center;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 600;
            color: #fff;
        }}

        /* Editing projects table */
        .editing-table-wrap {{
            overflow-x: auto;
            margin-top: 20px;
        }}
        .editing-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        .editing-table th {{
            text-align: left;
            padding: 10px 12px;
            color: #9ca3af;
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 1px solid #374151;
        }}
        .editing-table td {{
            padding: 12px;
            border-bottom: 1px solid #1f2937;
            color: #e5e7eb;
        }}
        .editing-table tbody tr:hover {{
            background: rgba(139,92,246,0.08);
        }}
        .status-badge {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .badge-sent {{ background: rgba(59,130,246,0.2); color: #60a5fa; }}
        .badge-progress {{ background: rgba(245,158,11,0.2); color: #fbbf24; }}
        .badge-completed {{ background: rgba(16,185,129,0.2); color: #34d399; }}
        .badge-overdue {{ background: rgba(239,68,68,0.2); color: #f87171; }}
        .priority-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 8px;
            font-size: 11px;
            font-weight: 700;
        }}
        .priority-p0 {{ background: rgba(239,68,68,0.2); color: #f87171; }}
        .priority-p1 {{ background: rgba(245,158,11,0.2); color: #fbbf24; }}
        .priority-p2 {{ background: rgba(107,114,128,0.2); color: #9ca3af; }}
        .delivery-link {{
            color: #8b5cf6;
            text-decoration: none;
            font-weight: 600;
        }}
        .delivery-link:hover {{ text-decoration: underline; }}

        /* Contact bar */
        .contact-bar {{
            display: flex;
            gap: 20px;
            justify-content: center;
            flex-wrap: wrap;
            margin-top: 8px;
        }}
        .contact-item {{
            font-size: 13px;
            color: #6b7280;
        }}
        .contact-item a {{
            color: #8b5cf6;
            text-decoration: none;
        }}
        .contact-item a:hover {{ text-decoration: underline; }}

        /* Mobile hamburger */
        .mobile-toggle {{
            display: none;
            position: fixed;
            top: 12px;
            left: 12px;
            z-index: 1000;
            background: #202020;
            border: 1px solid #2d2d2d;
            border-radius: 8px;
            padding: 8px 12px;
            color: #e0e0e0;
            font-size: 20px;
            cursor: pointer;
        }}

        /* Sidebar overlay */
        .sidebar-overlay {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.6);
            z-index: 998;
        }}
        .sidebar-overlay.show {{ display: block; }}

        /* Bottom nav (mobile) */
        .bottom-nav {{
            display: none;
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: #202020;
            border-top: 1px solid #2d2d2d;
            z-index: 900;
            padding: 6px 0;
            padding-bottom: max(6px, env(safe-area-inset-bottom));
        }}
        .bottom-nav-inner {{
            display: flex;
            justify-content: space-around;
            align-items: center;
            max-width: 500px;
            margin: 0 auto;
        }}
        .bnav-item {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 2px;
            padding: 6px 12px;
            color: #6b7280;
            text-decoration: none;
            font-size: 10px;
            font-weight: 600;
            cursor: pointer;
            border-radius: 8px;
            transition: color 0.15s;
            -webkit-tap-highlight-color: transparent;
        }}
        .bnav-item.active {{ color: #8b5cf6; }}
        .bnav-item:active {{ color: #a78bfa; }}
        .bnav-icon {{ font-size: 22px; }}

        /* WhatsApp floating button */
        .wa-float {{
            position: fixed;
            bottom: 24px;
            right: 20px;
            width: 56px;
            height: 56px;
            background: #25D366;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 16px rgba(37,211,102,0.4);
            z-index: 800;
            text-decoration: none;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .wa-float:hover {{ transform: scale(1.08); box-shadow: 0 6px 24px rgba(37,211,102,0.5); }}
        .wa-float:active {{ transform: scale(0.95); }}
        .wa-float svg {{ width: 28px; height: 28px; fill: #fff; }}

        /* Responsive */
        @media (max-width: 768px) {{
            .sidebar {{
                position: fixed;
                top: 0;
                left: -280px;
                height: 100vh;
                z-index: 999;
                transition: left 0.3s;
            }}
            .sidebar.open {{ left: 0; }}
            .mobile-toggle {{ display: block; }}
            .bottom-nav {{ display: block; }}
            .wa-float {{ bottom: 80px; right: 16px; width: 52px; height: 52px; }}
            .wa-float svg {{ width: 26px; height: 26px; }}

            .content {{
                padding: 56px 16px 80px;
            }}
            .page {{
                max-width: 100%;
            }}
            .page-title {{
                font-size: 24px;
                line-height: 1.2;
            }}
            .page-meta {{
                font-size: 13px;
                margin-bottom: 20px;
            }}

            /* Hero mobile — stack vertically */
            .hero {{
                flex-direction: column;
                margin: 0;
                border-radius: 0;
            }}
            .hero-img-wrap {{
                width: 100%;
                height: 250px;
                background: linear-gradient(180deg, #2d1854 0%, #0e0518 80%, #050208 100%);
            }}
            .hero-image {{
                -webkit-mask-image: linear-gradient(to bottom, black 50%, transparent 100%);
                mask-image: linear-gradient(to bottom, black 50%, transparent 100%);
            }}
            .hero-body {{
                padding: 24px 24px 32px;
                text-align: center;
                align-items: center;
            }}
            .hero h1 {{
                font-size: 32px;
                letter-spacing: -0.5px;
                margin-bottom: 12px;
            }}
            .hero p {{
                font-size: 15px;
                margin-bottom: 28px;
                line-height: 1.7;
            }}
            .hero-stats {{
                justify-content: center;
                gap: 28px;
                margin-bottom: 28px;
            }}
            .hero-stat {{ text-align: center; }}
            .hero-stat .number {{ font-size: 26px; }}
            .hero-cta {{
                padding: 16px 40px;
                font-size: 16px;
                border-radius: 10px;
                align-self: center;
            }}
            .contact-bar {{
                gap: 12px;
                flex-direction: column;
            }}

            /* Category tiles mobile — single column */
            .cat-grid {{
                grid-template-columns: 1fr;
                gap: 12px;
            }}
            .cat-tile-img {{
                aspect-ratio: 16/9;
            }}
            .cat-tile-content {{
                padding: 8px 4px 0;
            }}
            .cat-name {{ font-size: 15px; }}

            /* Category hero mobile */
            .cat-hero {{
                height: 160px;
                border-radius: 12px;
                margin-bottom: 20px;
            }}
            .cat-hero-content {{ padding: 16px; }}
            .cat-hero-title {{ font-size: 22px; }}

            /* Video grid mobile */
            .video-grid {{ grid-template-columns: 1fr; gap: 12px; }}
            .video-play {{ width: 40px; height: 40px; font-size: 16px; }}
            .video-title {{ font-size: 14px; padding: 8px 10px; }}

            /* Gallery cards mobile */
            .gallery-grid {{ gap: 8px; }}
            .gallery-card {{
                padding: 14px 16px;
                gap: 12px;
                border-radius: 10px;
            }}
            .gallery-monogram {{
                width: 38px;
                height: 38px;
                font-size: 16px;
            }}
            .gallery-date-card {{
                width: 38px;
                height: 42px;
            }}
            .gallery-date-card .date-day {{ font-size: 14px; }}
            .gallery-date-card .date-month {{ font-size: 8px; }}
            .gallery-name {{ font-size: 14px; }}
            .gallery-meta {{ font-size: 11px; }}

            /* Pricing mobile */
            .pricing-card {{ padding: 18px; }}
            .pricing-name {{ font-size: 18px; }}
            .tier-header {{ flex-direction: column; align-items: flex-start; gap: 2px; }}
            .tier-price {{ font-size: 20px; }}
            .tier-details {{ font-size: 14px; }}
            .addons-list li {{ font-size: 14px; padding: 5px 0; }}
            .includes-list {{ grid-template-columns: 1fr; gap: 8px; }}
            .includes-list span {{ font-size: 14px; }}

            /* Checklists mobile — bigger touch targets */
            .check-item {{
                padding: 12px;
                font-size: 15px;
                min-height: 48px;
            }}
            .check-item input[type="checkbox"] {{
                width: 20px;
                height: 20px;
            }}

            /* Workflow tiles */
            .wf-tile-grid {{
                grid-template-columns: 1fr 1fr;
                gap: 10px;
            }}
            .wf-tile {{ padding: 16px; }}
            .wf-tile-icon {{ font-size: 24px; }}
            .wf-tile-label {{ font-size: 13px; }}

            /* Pipeline */
            .pipeline-row {{ flex-direction: column; gap: 6px; }}
            .pipeline-stage {{ min-width: auto; padding: 10px; font-size: 13px; }}

            /* Editing table mobile */
            .editing-table {{ font-size: 13px; }}
            .editing-table th, .editing-table td {{ padding: 8px 6px; }}
            .editing-table th:nth-child(6), .editing-table td:nth-child(6) {{ display: none; }}

            /* Booking form mobile */
            .form-row-inline {{ grid-template-columns: 1fr; }}
            .btn-row {{ flex-direction: column; }}
            .bc-actions {{ flex-direction: column; }}
            .copy-btn, .share-wa-btn {{ width: 100%; justify-content: center; padding: 14px; }}
            .proscons {{ grid-template-columns: 1fr; }}

            /* Password gate */
            .pw-gate {{ padding: 40px 16px; }}
            .pw-input-wrap {{ width: 100%; max-width: 260px; }}
            .pw-input {{ font-size: 16px; padding: 12px 16px; }}
            .pw-btn {{ margin-left: 0; margin-top: 12px; display: block; width: 100%; max-width: 260px; padding: 14px; font-size: 16px; }}
            .pw-gate > div {{ display: flex; flex-direction: column; align-items: center; }}

            /* Workflow content */
            .wf-content {{ font-size: 15px; }}
            .wf-content .wf-table {{ font-size: 12px; display: block; overflow-x: auto; }}
            .wf-code {{ font-size: 12px; }}
            .back-link {{ font-size: 14px; padding: 8px 0; }}

            /* Testimonials mobile */
            .testimonials-grid {{ grid-template-columns: 1fr; }}
            .testimonial-card {{ padding: 16px; }}
            .testimonial-quote {{ font-size: 13px; }}
            .review-form {{ max-width: 100%; }}
            .star-rating .star {{ font-size: 32px; }}

            /* How It Works mobile */
            .how-steps {{ grid-template-columns: 1fr 1fr; gap: 10px; }}
            .how-step {{ padding: 16px 10px; }}
            .how-step-icon {{ font-size: 24px; }}
            .how-step-label {{ font-size: 13px; }}
        }}

        /* Small phones */
        @media (max-width: 380px) {{
            .cat-grid {{ grid-template-columns: 1fr; }}
            .hero-stats {{ flex-wrap: wrap; gap: 16px; }}
            .wf-tile-grid {{ grid-template-columns: 1fr; }}
        }}

        /* Testimonials */
        .testimonials-section {{
            padding: 20px 16px 0;
        }}
        .testimonials-title {{
            font-size: 13px;
            font-weight: 700;
            color: #525252;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            text-align: center;
            margin-bottom: 20px;
        }}
        .testimonials-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 14px;
        }}
        .testimonial-card {{
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 12px;
            padding: 20px;
            position: relative;
        }}
        .testimonial-quote {{
            font-size: 14px;
            color: #d1d5db;
            line-height: 1.6;
            font-style: italic;
            margin-bottom: 12px;
        }}
        .testimonial-quote::before {{
            content: '\\201C';
            font-size: 28px;
            color: #8b5cf6;
            font-style: normal;
            line-height: 0;
            position: relative;
            top: 8px;
            margin-right: 4px;
        }}
        .testimonial-name {{
            font-size: 12px;
            color: #6b7280;
            font-weight: 600;
        }}
        .testimonial-event {{
            font-size: 11px;
            color: #525252;
        }}
        .testimonial-stars {{
            color: #f59e0b;
            font-size: 14px;
            margin-bottom: 8px;
            letter-spacing: 2px;
        }}

        /* Review Form */
        .review-form-section {{
            margin-top: 32px;
            padding-top: 24px;
            border-top: 1px solid rgba(255,255,255,0.06);
        }}
        .review-form-header {{
            font-size: 15px;
            font-weight: 600;
            color: #d1d5db;
            text-align: center;
            margin-bottom: 20px;
        }}
        .review-form {{
            max-width: 480px;
            margin: 0 auto;
        }}
        .review-form .form-row {{
            margin-bottom: 16px;
        }}
        .review-form .form-label {{
            display: block;
            font-size: 11px;
            font-weight: 600;
            color: #6b7280;
            letter-spacing: 1px;
            margin-bottom: 6px;
        }}
        .review-form .form-input {{
            width: 100%;
            padding: 12px;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 8px;
            color: #e5e7eb;
            font-size: 14px;
            font-family: inherit;
            box-sizing: border-box;
            -webkit-appearance: none;
        }}
        .review-form .form-input:focus {{
            outline: none;
            border-color: #8b5cf6;
        }}
        .review-form select.form-input {{
            cursor: pointer;
        }}
        .review-form textarea.form-input {{
            resize: vertical;
            min-height: 80px;
        }}
        .star-rating {{
            display: flex;
            gap: 6px;
            flex-direction: row-reverse;
            justify-content: flex-end;
        }}
        .star-rating .star {{
            font-size: 28px;
            color: #374151;
            cursor: pointer;
            transition: color 0.15s;
            -webkit-tap-highlight-color: transparent;
        }}
        .star-rating .star.active,
        .star-rating .star.active ~ .star {{
            color: #f59e0b;
        }}
        .star-rating .star:hover,
        .star-rating .star:hover ~ .star {{
            color: #fbbf24;
        }}
        .review-submit-btn {{
            width: 100%;
            padding: 14px;
            background: #8b5cf6;
            color: #fff;
            border: none;
            border-radius: 10px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 8px;
            transition: opacity 0.2s;
        }}
        .review-submit-btn:hover {{
            opacity: 0.9;
        }}
        .review-submit-btn:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}
        .review-success {{
            text-align: center;
            padding: 24px 16px;
            margin-top: 16px;
        }}
        .review-success-icon {{
            width: 48px;
            height: 48px;
            background: #065f46;
            color: #10b981;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            margin: 0 auto 12px;
        }}
        .review-success-text {{
            color: #9ca3af;
            font-size: 14px;
        }}
        .review-error {{
            text-align: center;
            color: #ef4444;
            font-size: 13px;
            margin-top: 12px;
            padding: 10px;
            background: rgba(239,68,68,0.1);
            border-radius: 8px;
        }}

        /* How It Works */
        .how-section {{
            padding: 0 16px;
            margin-top: 8px;
        }}
        .how-title {{
            font-size: 13px;
            font-weight: 700;
            color: #525252;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            text-align: center;
            margin-bottom: 20px;
        }}
        .how-steps {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
        }}
        .how-step {{
            text-align: center;
            padding: 20px 12px;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 12px;
        }}
        .how-step-num {{
            font-size: 11px;
            font-weight: 700;
            color: #8b5cf6;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }}
        .how-step-icon {{
            font-size: 28px;
            margin-bottom: 8px;
        }}
        .how-step-label {{
            font-size: 14px;
            font-weight: 600;
            color: #e0e0e0;
            margin-bottom: 4px;
        }}
        .how-step-desc {{
            font-size: 12px;
            color: #6b7280;
            line-height: 1.4;
        }}

        /* Gear Section */
        .gear-section {{
            padding: 0 16px;
            margin-top: 32px;
        }}
        .gear-card {{
            display: flex;
            align-items: center;
            gap: 20px;
            padding: 24px;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.2s;
            text-decoration: none;
            color: inherit;
        }}
        .gear-card:hover {{
            background: rgba(139,92,246,0.08);
            border-color: rgba(139,92,246,0.2);
        }}
        .gear-card.expanded {{
            border-radius: 12px 12px 0 0;
            border-bottom: 1px solid rgba(139,92,246,0.15);
        }}
        .gear-icon {{
            font-size: 36px;
            flex-shrink: 0;
        }}
        .gear-info {{
            flex: 1;
        }}
        .gear-title {{
            font-size: 16px;
            font-weight: 600;
            color: #e0e0e0;
            margin-bottom: 4px;
        }}
        .gear-desc {{
            font-size: 13px;
            color: #6b7280;
            line-height: 1.4;
        }}
        .gear-arrow {{
            font-size: 18px;
            color: #525252;
            flex-shrink: 0;
            transition: transform 0.3s;
        }}
        .gear-card.expanded .gear-arrow {{
            transform: rotate(90deg);
        }}
        .gear-body {{
            display: none;
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.06);
            border-top: none;
            border-radius: 0 0 12px 12px;
            padding: 20px 24px 24px;
        }}
        .gear-body.open {{
            display: block;
        }}
        .gear-category {{
            margin-bottom: 20px;
        }}
        .gear-category:last-child {{
            margin-bottom: 0;
        }}
        .gear-category-label {{
            font-size: 13px;
            font-weight: 600;
            color: #8b5cf6;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
        }}
        .gear-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 6px 16px;
        }}
        .gear-item {{
            font-size: 13px;
            color: #9ca3af;
            line-height: 1.6;
        }}
        @media (min-width: 768px) {{
            .gear-grid {{
                grid-template-columns: 1fr 1fr 1fr;
            }}
        }}

        /* Toast */
        .toast {{
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: #7c3aed;
            color: #fff;
            padding: 12px 20px;
            border-radius: 8px;
            font-size: 14px;
            opacity: 0;
            transform: translateY(10px);
            transition: all 0.3s;
            z-index: 1000;
            pointer-events: none;
        }}
        .toast.show {{ opacity: 1; transform: translateY(0); }}

        /* ── Client Feedback ── */
        .fb-toolbar {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 16px;
            flex-wrap: wrap;
        }}
        .fb-refresh {{
            background: #374151;
            color: #e5e7eb;
            border: none;
            border-radius: 6px;
            padding: 6px 14px;
            font-size: 13px;
            cursor: pointer;
        }}
        .fb-refresh:hover {{ background: #4b5563; }}
        .fb-filter-tabs {{
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
            margin-bottom: 16px;
        }}
        .fb-filter-tab {{
            background: #1f2937;
            color: #9ca3af;
            border: 1px solid #374151;
            border-radius: 16px;
            padding: 4px 12px;
            font-size: 12px;
            cursor: pointer;
            white-space: nowrap;
        }}
        .fb-filter-tab.active {{
            background: #7c3aed;
            color: #fff;
            border-color: #7c3aed;
        }}
        .fb-project-card {{
            background: #1f2937;
            border-radius: 10px;
            border-left: 4px solid #7c3aed;
            padding: 16px;
            margin-bottom: 14px;
        }}
        .fb-project-header {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 10px;
            flex-wrap: wrap;
        }}
        .fb-project-name {{
            font-size: 16px;
            font-weight: 600;
            color: #f3f4f6;
        }}
        .fb-type-badge {{
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 10px;
            font-weight: 500;
        }}
        .fb-type-video {{ background: #312e81; color: #a5b4fc; }}
        .fb-type-photo {{ background: #064e3b; color: #6ee7b7; }}
        .fb-type-both {{ background: #78350f; color: #fbbf24; }}
        .fb-editor-badge {{
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 10px;
            background: #374151;
            color: #9ca3af;
        }}
        .fb-tracker {{
            margin: 12px 0;
            overflow-x: auto;
        }}
        .fb-tracker-steps {{
            display: flex;
            align-items: center;
            gap: 0;
            min-width: 360px;
        }}
        .fb-tracker-step {{
            display: flex;
            flex-direction: column;
            align-items: center;
            flex: 1;
            position: relative;
        }}
        .fb-tracker-step:not(:last-child)::after {{
            content: '';
            position: absolute;
            top: 12px;
            left: 50%;
            width: 100%;
            height: 2px;
            background: #374151;
            z-index: 0;
        }}
        .fb-tracker-step.completed:not(:last-child)::after {{
            background: #7c3aed;
        }}
        .fb-tracker-dot {{
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background: #374151;
            color: #6b7280;
            font-size: 11px;
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1;
        }}
        .fb-tracker-step.completed .fb-tracker-dot {{
            background: #7c3aed;
            color: #fff;
        }}
        .fb-tracker-step.active .fb-tracker-dot {{
            background: #7c3aed;
            color: #fff;
            box-shadow: 0 0 0 4px rgba(124, 58, 237, 0.3);
            animation: fbPulse 2s ease-in-out infinite;
        }}
        @keyframes fbPulse {{
            0%, 100% {{ box-shadow: 0 0 0 4px rgba(124, 58, 237, 0.3); }}
            50% {{ box-shadow: 0 0 0 8px rgba(124, 58, 237, 0.1); }}
        }}
        .fb-tracker-label {{
            font-size: 10px;
            color: #6b7280;
            margin-top: 4px;
            text-align: center;
            white-space: nowrap;
        }}
        .fb-tracker-step.completed .fb-tracker-label,
        .fb-tracker-step.active .fb-tracker-label {{
            color: #c4b5fd;
        }}
        .fb-section-title {{
            font-size: 13px;
            font-weight: 600;
            color: #9ca3af;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin: 14px 0 8px;
        }}
        .fb-song {{
            background: #111827;
            border-radius: 8px;
            padding: 10px 14px;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .fb-song-icon {{ font-size: 16px; }}
        .fb-song-text {{
            font-size: 14px;
            color: #e5e7eb;
            flex: 1;
        }}
        .fb-correction {{
            background: #111827;
            border-radius: 8px;
            padding: 10px 14px;
            margin-bottom: 6px;
        }}
        .fb-correction-header {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 4px;
        }}
        .fb-correction-ts {{
            font-size: 12px;
            color: #7c3aed;
            font-weight: 600;
        }}
        .fb-correction-pri {{
            font-size: 10px;
            padding: 1px 6px;
            border-radius: 8px;
        }}
        .fb-pri-high {{ background: #7f1d1d; color: #fca5a5; }}
        .fb-pri-medium {{ background: #78350f; color: #fbbf24; }}
        .fb-pri-low {{ background: #1e3a5f; color: #93c5fd; }}
        .fb-correction-text {{
            font-size: 13px;
            color: #d1d5db;
        }}
        .fb-correction-actions {{
            display: flex;
            gap: 6px;
            margin-top: 8px;
        }}
        .fb-fix-btn {{
            font-size: 11px;
            padding: 3px 10px;
            border-radius: 6px;
            border: 1px solid #374151;
            background: #1f2937;
            color: #9ca3af;
            cursor: pointer;
        }}
        .fb-fix-btn:hover {{ background: #374151; }}
        .fb-fix-btn.fixed {{
            background: #065f46;
            color: #6ee7b7;
            border-color: #065f46;
        }}
        .fb-fix-btn.cant-fix {{
            background: #7f1d1d;
            color: #fca5a5;
            border-color: #7f1d1d;
        }}
        .fb-fix-btn:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}
        .fb-notify-btn {{
            background: #25D366;
            color: #fff;
            border: none;
            border-radius: 6px;
            padding: 6px 14px;
            font-size: 13px;
            cursor: pointer;
            margin-top: 10px;
        }}
        .fb-notify-btn:hover {{ background: #20bd5a; }}
        .fb-notify-btn:disabled {{ opacity: 0.5; cursor: not-allowed; }}
        .fb-loading, .fb-empty {{
            text-align: center;
            color: #6b7280;
            padding: 40px 0;
            font-size: 14px;
        }}
        .fb-status-icon {{
            display: inline-block;
            width: 16px;
            text-align: center;
            margin-right: 4px;
        }}
        .fb-version-link {{
            font-size: 12px;
            color: #818cf8;
            margin-right: 10px;
        }}
    </style>
</head>
<body>
    <button class="mobile-toggle" id="mobile-toggle">&#9776;</button>
    <div class="sidebar-overlay" id="sidebar-overlay"></div>

    <!-- WhatsApp floating button — href set by JS after decryption -->
    <a id="wa-float-btn" class="wa-float" style="display:none" target="_blank" rel="noreferrer noopener" aria-label="Chat on WhatsApp">
        <svg viewBox="0 0 24 24"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
    </a>

    <!-- Bottom nav (mobile) -->
    <nav class="bottom-nav">
        <div class="bottom-nav-inner">
            <div class="bnav-item active" data-nav="home" id="bnav-home">
                <span class="bnav-icon">🏠</span>
                Home
            </div>
            <div class="bnav-item" data-nav="portfolio-home" id="bnav-portfolio">
                <span class="bnav-icon">📸</span>
                Portfolio
            </div>
            <div class="bnav-item" data-nav-protected="pricing" id="bnav-pricing">
                <span class="bnav-icon">💰</span>
                Pricing
            </div>
            <div class="bnav-item" data-nav-protected="booking" id="bnav-booking">
                <span class="bnav-icon">📋</span>
                Book
            </div>
            <div class="bnav-item" data-nav="contact" id="bnav-contact">
                <span class="bnav-icon">📞</span>
                Contact
            </div>
        </div>
    </nav>

    <div class="layout">
        <!-- Sidebar -->
        <div class="sidebar" id="sidebar">
            <div class="sidebar-brand">📷 <span>Rsquare Studios</span></div>

            <a class="sidebar-link" data-section="home">🏠 Home</a>

            <div class="sidebar-divider"></div>
            <div class="sidebar-section-label">PORTFOLIO</div>
            <a class="sidebar-link" data-section="portfolio-home">📸 All Categories</a>
            <a class="sidebar-link" data-section="videos">🎬 Videos</a>
            {gallery_sidebar}

            <div class="sidebar-divider"></div>
            <a class="sidebar-link client-link" data-access="pricing" style="display:none;">💰 Pricing</a>
            <a class="sidebar-link client-link" data-access="booking" style="display:none;">📋 Book / Get Quote</a>
            <div id="wf-sidebar-block" style="display:none;">
                <div class="sidebar-section-label" id="wf-section-label">WORKFLOW</div>
                <a class="sidebar-link internal-link" data-access="workflow-home">📋 Dashboard</a>
                <a class="sidebar-link internal-link" data-access="checklists">✅ Checklists</a>
                <a class="sidebar-link internal-link" data-access="workflow-ref">📖 Workflow Reference</a>
                <a class="sidebar-link internal-link" data-access="editing-projects">🎬 Photo Editing</a>
                <a class="sidebar-link internal-link" data-access="video-projects">🎥 Video Editing</a>
                <a class="sidebar-link internal-link" data-access="client-feedback">💬 Client Feedback</a>
                <div class="sidebar-section-label" style="padding-top:8px">POSING GUIDES</div>
                {posing_sidebar.replace('class="sidebar-link sub-link"', 'class="sidebar-link sub-link internal-link"').replace('data-section=', 'data-access=')}
            </div>
            <a class="sidebar-link" href="#" id="private-gate-link" style="margin-top:4px;">
                <span class="lock-icon" id="lock-icon">🔒</span> Private
            </a>



            <div class="sidebar-footer">
                Updated {now}<br>
                {total_galleries} galleries
            </div>
        </div>

        <!-- Content -->
        <div class="content" id="main-content">

            <!-- HOME -->
            <div class="page active" id="home">
                <div class="hero">
                    <div class="hero-img-wrap">
                        <img src="hero.jpg" alt="Rsquare Studios" class="hero-image" referrerpolicy="no-referrer">
                    </div>
                    <div class="hero-body">
                    <h1>Rsquare Studios</h1>
                    <p>Baby showers, maternity, birthdays, weddings &amp; family celebrations. Photography &amp; video across DFW.</p>
                    <div class="hero-stats">
                        <div class="hero-stat">
                            <div class="number">300+</div>
                            <div class="label">GALLERIES</div>
                        </div>
                        <div class="hero-stat">
                            <div class="number">5+</div>
                            <div class="label">YEARS</div>
                        </div>
                        <div class="hero-stat">
                            <div class="number">50+</div>
                            <div class="label">WEDDINGS</div>
                        </div>
                    </div>
                    <a href="#" class="hero-cta" data-section="portfolio-home">View Portfolio</a>
                    </div>
                </div>

                <!-- Testimonials -->
                <div class="testimonials-section">
                    <div class="testimonials-title">What Clients Say</div>
                    <div class="testimonials-grid">
{reviews_html}
                    </div>

                    <div class="review-form-section">
                        <div class="review-form-header">Loved working with us? Share your experience</div>
                        <form class="review-form" id="review-form">
                            <div class="form-row">
                                <label class="form-label">YOUR NAME</label>
                                <input class="form-input" id="rv-name" placeholder="Full name" required>
                            </div>
                            <div class="form-row">
                                <label class="form-label">EVENT TYPE</label>
                                <select class="form-input" id="rv-event" required>
                                    <option value="">Select event type</option>
                                    <option value="Wedding Photography">Wedding Photography</option>
                                    <option value="Engagement">Engagement</option>
                                    <option value="Pre-Wedding">Pre-Wedding</option>
                                    <option value="Half Saree">Half Saree</option>
                                    <option value="Maternity">Maternity</option>
                                    <option value="Baby Shower">Baby Shower</option>
                                    <option value="Birthday">Birthday</option>
                                    <option value="Cradle Ceremony">Cradle Ceremony</option>
                                    <option value="Event Photography">Event Photography</option>
                                    <option value="Photo &amp; Video">Photo &amp; Video</option>
                                </select>
                            </div>
                            <div class="form-row">
                                <label class="form-label">RATING</label>
                                <div class="star-rating" id="star-rating">
                                    <span class="star" data-value="1">&#9733;</span>
                                    <span class="star" data-value="2">&#9733;</span>
                                    <span class="star" data-value="3">&#9733;</span>
                                    <span class="star" data-value="4">&#9733;</span>
                                    <span class="star active" data-value="5">&#9733;</span>
                                </div>
                                <input type="hidden" id="rv-rating" value="5">
                            </div>
                            <div class="form-row">
                                <label class="form-label">YOUR REVIEW</label>
                                <textarea class="form-input" id="rv-text" rows="4" placeholder="Tell us about your experience..." required></textarea>
                            </div>
                            <button type="submit" class="review-submit-btn" id="rv-submit">Submit Review</button>
                        </form>
                        <div class="review-success" id="review-success" style="display:none;">
                            <div class="review-success-icon">&#10003;</div>
                            <div class="review-success-text">Thank you! Your review will appear after approval.</div>
                        </div>
                        <div class="review-error" id="review-error" style="display:none;"></div>
                    </div>
                </div>

                <!-- How It Works -->
                <div class="how-section">
                    <div class="how-title">How It Works</div>
                    <div class="how-steps">
                        <div class="how-step">
                            <div class="how-step-num">01</div>
                            <div class="how-step-icon">💬</div>
                            <div class="how-step-label">Reach Out</div>
                            <div class="how-step-desc">Tell me about your event via WhatsApp or call</div>
                        </div>
                        <div class="how-step">
                            <div class="how-step-num">02</div>
                            <div class="how-step-icon">📋</div>
                            <div class="how-step-label">Plan</div>
                            <div class="how-step-desc">We lock in date, location, and coverage details</div>
                        </div>
                        <div class="how-step">
                            <div class="how-step-num">03</div>
                            <div class="how-step-icon">📸</div>
                            <div class="how-step-label">Shoot</div>
                            <div class="how-step-desc">I capture every moment &mdash; candids, portraits, all of it</div>
                        </div>
                        <div class="how-step">
                            <div class="how-step-num">04</div>
                            <div class="how-step-icon">🎨</div>
                            <div class="how-step-label">Deliver</div>
                            <div class="how-step-desc">Edited photos in 12&ndash;15 days, video in 3&ndash;4 weeks</div>
                        </div>
                    </div>
                </div>

                <!-- My Gear -->
                <div class="gear-section">
                    <div class="gear-card" id="gear-toggle">
                        <div class="gear-icon">🎥</div>
                        <div class="gear-info">
                            <div class="gear-title">My Gear</div>
                            <div class="gear-desc">Curious what cameras, lenses, and lighting I use? Tap to see the full kit.</div>
                        </div>
                        <div class="gear-arrow">&rarr;</div>
                    </div>
                    <div class="gear-body" id="gear-body">
{gear_categories_html}
                    </div>
                </div>
            </div>

            <!-- PORTFOLIO HOME -->
            <div class="page" id="portfolio-home">
                <div class="page-breadcrumb">Portfolio</div>
                <h1 class="page-title">Portfolio</h1>
                <div class="page-meta">{total_galleries} galleries &middot; Tap any category to browse</div>
                <div class="cat-grid">
                    {"".join(f'''
                    <div class="cat-tile" data-section="portfolio-{cat}">
                        <div class="cat-tile-img" style="background-image:url('{info['cover']}');background-position:{info['cover_pos']}"></div>
                        <div class="cat-tile-content">
                            <div class="cat-name">{info['label']}</div>
                            <div class="cat-count">{info['count']} galleries</div>
                        </div>
                    </div>''' for cat, info in gallery_cards.items())}
                </div>
            </div>

            <!-- PORTFOLIO CATEGORIES -->
            {portfolio_pages}

            <!-- VIDEOS -->
            <div class="page" id="videos">
                <a class="back-link" href="#" data-section="portfolio-home">&larr; Back to Portfolio</a>
                <div class="page-breadcrumb">Portfolio</div>
                <h1 class="page-title">Videos</h1>
                <div class="page-meta">Highlight reels and cinematic teasers from our events</div>
                <div class="video-grid">
                    <a href="https://www.youtube.com/watch?v=ATyq7m_gLtY" target="_blank" rel="noreferrer noopener" class="video-card">
                        <div class="video-thumb" style="background-image:url('https://img.youtube.com/vi/ATyq7m_gLtY/hqdefault.jpg')">
                            <div class="video-play">&#9654;</div>
                            <div class="video-duration">3:25</div>
                        </div>
                        <div class="video-title">Rashmi Baby Shower</div>
                    </a>
                    <a href="https://www.youtube.com/watch?v=B4WH92E3ov4" target="_blank" rel="noreferrer noopener" class="video-card">
                        <div class="video-thumb" style="background-image:url('https://img.youtube.com/vi/B4WH92E3ov4/hqdefault.jpg')">
                            <div class="video-play">&#9654;</div>
                            <div class="video-duration">6:39</div>
                        </div>
                        <div class="video-title">ShravArt's Housewarming</div>
                    </a>
                    <a href="https://www.youtube.com/watch?v=oZSifwJn6MI" target="_blank" rel="noreferrer noopener" class="video-card">
                        <div class="video-thumb" style="background-image:url('https://img.youtube.com/vi/oZSifwJn6MI/hqdefault.jpg')">
                            <div class="video-play">&#9654;</div>
                            <div class="video-duration">3:42</div>
                        </div>
                        <div class="video-title">Mounika Baby Shower</div>
                    </a>
                    <a href="https://www.youtube.com/watch?v=7IqxKNLrtaI" target="_blank" rel="noreferrer noopener" class="video-card">
                        <div class="video-thumb" style="background-image:url('https://img.youtube.com/vi/7IqxKNLrtaI/hqdefault.jpg')">
                            <div class="video-play">&#9654;</div>
                            <div class="video-duration">4:59</div>
                        </div>
                        <div class="video-title">Andrilla Sweet 16 Birthday</div>
                    </a>
                    <a href="https://www.youtube.com/watch?v=XksmtJX71Ao" target="_blank" rel="noreferrer noopener" class="video-card">
                        <div class="video-thumb" style="background-image:url('https://img.youtube.com/vi/XksmtJX71Ao/hqdefault.jpg')">
                            <div class="video-play">&#9654;</div>
                            <div class="video-duration">6:08</div>
                        </div>
                        <div class="video-title">Krithi Half Saree Ceremony</div>
                    </a>
                    <a href="https://www.youtube.com/watch?v=iNklzAP3JNo" target="_blank" rel="noreferrer noopener" class="video-card">
                        <div class="video-thumb" style="background-image:url('https://img.youtube.com/vi/iNklzAP3JNo/hqdefault.jpg')">
                            <div class="video-play">&#9654;</div>
                            <div class="video-duration">1:36</div>
                        </div>
                        <div class="video-title">Ranjith Pinky Gender Reveal</div>
                    </a>
                    <a href="https://www.youtube.com/watch?v=lS1BdiEk3Pg" target="_blank" rel="noreferrer noopener" class="video-card">
                        <div class="video-thumb" style="background-image:url('https://img.youtube.com/vi/lS1BdiEk3Pg/hqdefault.jpg')">
                            <div class="video-play">&#9654;</div>
                            <div class="video-duration">4:43</div>
                        </div>
                        <div class="video-title">Vasundhra Baby Shower</div>
                    </a>
                    <a href="https://www.youtube.com/watch?v=vuSREP1Srgc" target="_blank" rel="noreferrer noopener" class="video-card">
                        <div class="video-thumb" style="background-image:url('https://img.youtube.com/vi/vuSREP1Srgc/hqdefault.jpg')">
                            <div class="video-play">&#9654;</div>
                            <div class="video-duration">6:34</div>
                        </div>
                        <div class="video-title">Sarayu Mihira's Sweet 16</div>
                    </a>
                    <a href="https://www.youtube.com/watch?v=1g4y62tnHqQ" target="_blank" rel="noreferrer noopener" class="video-card">
                        <div class="video-thumb" style="background-image:url('https://img.youtube.com/vi/1g4y62tnHqQ/hqdefault.jpg')">
                            <div class="video-play">&#9654;</div>
                            <div class="video-duration">4:07</div>
                        </div>
                        <div class="video-title">Our Little Miracle Is On The Way</div>
                    </a>
                    <a href="https://www.youtube.com/watch?v=7OuNc5YJh48" target="_blank" rel="noreferrer noopener" class="video-card">
                        <div class="video-thumb" style="background-image:url('https://img.youtube.com/vi/7OuNc5YJh48/hqdefault.jpg')">
                            <div class="video-play">&#9654;</div>
                            <div class="video-duration">3:12</div>
                        </div>
                        <div class="video-title">Keerthi's Half Saree Ceremony</div>
                    </a>
                    <a href="https://www.youtube.com/watch?v=AbwBEGaop8k" target="_blank" rel="noreferrer noopener" class="video-card">
                        <div class="video-thumb" style="background-image:url('https://img.youtube.com/vi/AbwBEGaop8k/hqdefault.jpg')">
                            <div class="video-play">&#9654;</div>
                            <div class="video-duration">3:21</div>
                        </div>
                        <div class="video-title">Laya Half Saree</div>
                    </a>
                    <a href="https://www.youtube.com/watch?v=Nk5upRtUf9M" target="_blank" rel="noreferrer noopener" class="video-card">
                        <div class="video-thumb" style="background-image:url('https://img.youtube.com/vi/Nk5upRtUf9M/hqdefault.jpg')">
                            <div class="video-play">&#9654;</div>
                            <div class="video-duration">5:06</div>
                        </div>
                        <div class="video-title">Ratna &amp; Janu Wedding</div>
                    </a>
                    <a href="https://www.youtube.com/watch?v=NIFPgrPOYCo" target="_blank" rel="noreferrer noopener" class="video-card">
                        <div class="video-thumb" style="background-image:url('https://img.youtube.com/vi/NIFPgrPOYCo/hqdefault.jpg')">
                            <div class="video-play">&#9654;</div>
                            <div class="video-duration">3:34</div>
                        </div>
                        <div class="video-title">Anurag &amp; Madhu Gender Reveal</div>
                    </a>
                    <a href="https://www.youtube.com/watch?v=QMzq-VSBhzQ" target="_blank" rel="noreferrer noopener" class="video-card">
                        <div class="video-thumb" style="background-image:url('https://img.youtube.com/vi/QMzq-VSBhzQ/hqdefault.jpg')">
                            <div class="video-play">&#9654;</div>
                            <div class="video-duration">1:24</div>
                        </div>
                        <div class="video-title">Nyshitha Saree Ceremony</div>
                    </a>
                    <a href="https://www.youtube.com/watch?v=2GwQNMeU4Hs" target="_blank" rel="noreferrer noopener" class="video-card">
                        <div class="video-thumb" style="background-image:url('https://img.youtube.com/vi/2GwQNMeU4Hs/hqdefault.jpg')">
                            <div class="video-play">&#9654;</div>
                            <div class="video-duration">2:29</div>
                        </div>
                        <div class="video-title">Tarun's Birthday</div>
                    </a>
                    <a href="https://www.youtube.com/watch?v=j56qe0hx7iA" target="_blank" rel="noreferrer noopener" class="video-card">
                        <div class="video-thumb" style="background-image:url('https://img.youtube.com/vi/j56qe0hx7iA/hqdefault.jpg')">
                            <div class="video-play">&#9654;</div>
                            <div class="video-duration">5:00</div>
                        </div>
                        <div class="video-title">Keerthi &amp; Prawin Gender Reveal</div>
                    </a>
                    <a href="https://www.youtube.com/watch?v=6f0IUSxVThM" target="_blank" rel="noreferrer noopener" class="video-card">
                        <div class="video-thumb" style="background-image:url('https://img.youtube.com/vi/6f0IUSxVThM/hqdefault.jpg')">
                            <div class="video-play">&#9654;</div>
                            <div class="video-duration">1:23</div>
                        </div>
                        <div class="video-title">Ratna &amp; Janu Pre-Wedding Teaser</div>
                    </a>
                    <a href="https://www.youtube.com/watch?v=LrS4f_ZqWNE" target="_blank" rel="noreferrer noopener" class="video-card">
                        <div class="video-thumb" style="background-image:url('https://img.youtube.com/vi/LrS4f_ZqWNE/hqdefault.jpg')">
                            <div class="video-play">&#9654;</div>
                            <div class="video-duration">3:39</div>
                        </div>
                        <div class="video-title">Swetha Housewarming</div>
                    </a>
                    <a href="https://www.youtube.com/watch?v=-gkBScX8YsY" target="_blank" rel="noreferrer noopener" class="video-card">
                        <div class="video-thumb" style="background-image:url('https://img.youtube.com/vi/-gkBScX8YsY/hqdefault.jpg')">
                            <div class="video-play">&#9654;</div>
                            <div class="video-duration">1:03</div>
                        </div>
                        <div class="video-title">Radhika &amp; Praveen Teaser</div>
                    </a>
                    <a href="https://www.youtube.com/watch?v=nEPyewr1uA4" target="_blank" rel="noreferrer noopener" class="video-card">
                        <div class="video-thumb" style="background-image:url('https://img.youtube.com/vi/nEPyewr1uA4/hqdefault.jpg')">
                            <div class="video-play">&#9654;</div>
                            <div class="video-duration">1:55</div>
                        </div>
                        <div class="video-title">Vinod &amp; Sunitha</div>
                    </a>
                    <a href="https://www.youtube.com/watch?v=8Q7MyyYxf3k" target="_blank" rel="noreferrer noopener" class="video-card">
                        <div class="video-thumb" style="background-image:url('https://img.youtube.com/vi/8Q7MyyYxf3k/hqdefault.jpg')">
                            <div class="video-play">&#9654;</div>
                            <div class="video-duration">3:17</div>
                        </div>
                        <div class="video-title">Avyukh's 1st Birthday</div>
                    </a>
                </div>
                <div style="margin-top:20px; text-align:center;">
                    <a href="https://www.youtube.com/@rsquarestudios" target="_blank" rel="noreferrer noopener" style="color:#8b5cf6; text-decoration:none; font-size:14px;">View all on YouTube &rarr;</a>
                </div>
            </div>

            <!-- PRICING (encrypted) -->
            <div class="page" id="pricing">
                <div class="encrypted-placeholder">This content is encrypted. Enter the password to view pricing.</div>
            </div>

            <!-- BOOKING (encrypted) -->
            <div class="page" id="booking">
                <div class="encrypted-placeholder">This content is encrypted. Enter the password to view booking.</div>
            </div>

            <!-- LOGOUT BUTTON (visible when unlocked) -->
            <button id="logout-btn" class="logout-btn">Log out</button>

            <!-- PASSWORD GATE -->
            <div class="page" id="pw-gate">
                <div class="pw-gate">
                    <h2>📷 Rsquare Studios</h2>
                    <p>This section is password-protected.</p>
                    <div>
                        <div class="pw-input-wrap">
                            <input type="password" class="pw-input" id="pw-input" placeholder="Enter password" autocomplete="off" inputmode="text">
                            <button type="button" class="pw-eye-btn" id="pw-eye-btn" aria-label="Toggle password visibility">
                                <span id="eye-icon">👁</span>
                            </button>
                        </div>
                        <button class="pw-btn" id="pw-btn">Enter</button>
                    </div>
                    <div class="pw-hint">Hint: shared via WhatsApp when you inquired</div>
                    <div class="pw-error" id="pw-error">Wrong password. Try again.</div>
                    <div class="pw-lockout" id="pw-lockout"></div>
                    <p class="pw-reminder">Please don't share passwords outside authorized contacts</p>
                </div>
            </div>

            <!-- WORKFLOW HOME (encrypted) -->
            <div class="page" id="workflow-home">
                <div class="encrypted-placeholder">This content is encrypted. Enter the password to view workflow.</div>
            </div>

            <!-- CHECKLISTS (encrypted) -->
            <div class="page" id="checklists">
                <div class="encrypted-placeholder">This content is encrypted. Enter the password to view checklists.</div>
            </div>

            <!-- WORKFLOW REFERENCE (encrypted) -->
            <div class="page" id="workflow-ref">
                <div class="encrypted-placeholder">This content is encrypted. Enter the password to view workflow reference.</div>
            </div>

            <!-- EDITING PROJECTS (encrypted) -->
            <div class="page" id="editing-projects">
                <div class="encrypted-placeholder">This content is encrypted. Enter the password to view editing projects.</div>
            </div>

            <!-- VIDEO PROJECTS (encrypted) -->
            <div class="page" id="video-projects">
                <div class="encrypted-placeholder">This content is encrypted. Enter the password to view video projects.</div>
            </div>

            <!-- CLIENT FEEDBACK (encrypted, live data) -->
            <div class="page" id="client-feedback">
                <div class="encrypted-placeholder">This content is encrypted. Enter the password to view client feedback.</div>
            </div>

            <!-- BOOKING CONFIRM (encrypted) -->
            <div class="page" id="booking-confirm">
                <div class="encrypted-placeholder">This content is encrypted. Enter the password to view booking confirmation.</div>
            </div>

            <!-- POSING GUIDES (encrypted — shells injected dynamically) -->
            {posing_shells}


            <!-- CONTACT -->
            <div class="page" id="contact">
                <div class="page-breadcrumb">Contact</div>
                <h1 class="page-title">Get in Touch</h1>
                <div class="page-meta">WhatsApp is the easiest way to reach me. Just say hi!</div>

                <div class="gallery-grid" style="max-width:400px;">
                    <a id="contact-wa" class="gallery-card" style="border-color:#25D366;display:none" target="_blank" rel="noreferrer noopener">
                        <div class="gallery-icon" style="font-size:28px;">💬</div>
                        <div class="gallery-info">
                            <div class="gallery-name">WhatsApp</div>
                            <div class="gallery-meta">Quickest way to reach me</div>
                        </div>
                        <div class="gallery-arrow">&#8599;</div>
                    </a>
                    <a id="contact-phone" class="gallery-card" style="display:none">
                        <div class="gallery-icon" style="font-size:28px;">📞</div>
                        <div class="gallery-info">
                            <div class="gallery-name" id="contact-phone-number"></div>
                            <div class="gallery-meta">Call or text</div>
                        </div>
                        <div class="gallery-arrow">&#8599;</div>
                    </a>
                    <a href="https://www.rsquarestudios.com" target="_blank" rel="noreferrer noopener" class="gallery-card">
                        <div class="gallery-icon" style="font-size:28px;">🌐</div>
                        <div class="gallery-info">
                            <div class="gallery-name">rsquarestudios.com</div>
                            <div class="gallery-meta">Full portfolio on SmugMug</div>
                        </div>
                        <div class="gallery-arrow">&#8599;</div>
                    </a>
                    <a href="https://www.instagram.com/rsquare_studios/" target="_blank" rel="noreferrer noopener" class="gallery-card">
                        <div class="gallery-icon" style="font-size:28px;">📷</div>
                        <div class="gallery-info">
                            <div class="gallery-name">@rsquare_studios</div>
                            <div class="gallery-meta">Follow on Instagram</div>
                        </div>
                        <div class="gallery-arrow">&#8599;</div>
                    </a>
                </div>

                <div class="includes-box" style="max-width:400px; margin-top:28px;">
                    <h3>Based in Dallas&ndash;Fort Worth, TX</h3>
                    <div style="font-size:14px; color:#c4b5fd; line-height:1.7;">
                        We photograph weddings, maternity sessions, newborns, birthdays, and cradle ceremonies across the DFW metroplex.<br><br>
                        We take a limited number of sessions each month to ensure every client receives our full attention. Dates are reserved on a first-come, first-served basis &mdash; we recommend booking 4&ndash;6 weeks in advance.
                    </div>
                </div>
            </div>

        </div>
    </div>

    <div class="toast" id="toast"></div>

    <script nonce="{csp_nonce}">
        // Frame-buster: prevent clickjacking (can't set X-Frame-Options on GitHub Pages)
        if (top !== self) {{ top.location = self.location; }}

        const ENCRYPTED_CLIENT = "{encrypted_client_blob}";
        const ENCRYPTED_INTERNAL = "{encrypted_internal_blob}";
        const ENCRYPTED_CLIENT_ADMIN = "{encrypted_client_admin_blob}";
        const PBKDF2_ITERATIONS = {PBKDF2_ITERATIONS};
        let clientUnlocked = false;
        let internalUnlocked = false;
        let _appConfig = null;

        // URL allowlist — only these hosts are permitted in dynamic links
        const ALLOWED_HOSTS = [
            'www.rsquarestudios.com', 'rsquarestudios.com',
            'www.smugmug.com', 'photos.smugmug.com',
            'www.youtube.com', 'youtube.com', 'youtu.be',
            'wa.me', 'api.whatsapp.com',
            'www.instagram.com', 'instagram.com',
            'we.tl', 'mega.nz',
            'cal.com', 'app.cal.com',
            'calendar.google.com', 'outlook.live.com',
            'literate-basketball-b5e.notion.site',
            'script.google.com', 'script.googleusercontent.com',
        ];
        function isAllowedUrl(url) {{
            try {{
                const parsed = new URL(url);
                if (parsed.protocol !== 'https:') return false;
                return ALLOWED_HOSTS.some(h => parsed.hostname === h || parsed.hostname.endsWith('.' + h));
            }} catch {{ return false; }}
        }}

        function toggleGear() {{
            const toggle = document.getElementById('gear-toggle');
            const body = document.getElementById('gear-body');
            toggle.classList.toggle('expanded');
            body.classList.toggle('open');
            if (body.classList.contains('open')) {{
                setTimeout(() => body.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }}), 50);
            }}
        }}

        function showSection(id) {{
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            const target = document.getElementById(id);
            if (target) target.classList.add('active');
            document.querySelectorAll('.sidebar-link').forEach(a => a.classList.remove('active'));
            const mc = document.getElementById('main-content');
            if (mc) mc.scrollTop = 0;
            window.scrollTo(0, 0);
            closeSidebar();
        }}

        // Client sections need client password; internal sections need internal password
        const CLIENT_SECTIONS = ['pricing', 'booking'];
        const INTERNAL_SECTIONS = ['workflow-home', 'checklists', 'workflow-ref', 'editing-projects', 'video-projects', 'client-feedback', 'booking-confirm', 'posing-couples', 'posing-families', 'posing-weddings'];

        function showPrivateGate() {{
            // If both unlocked, go to pricing (client) or workflow (internal)
            if (clientUnlocked && internalUnlocked) {{
                showSection('pricing');
                return;
            }}
            // If only client unlocked, show gate for internal access
            if (clientUnlocked && !internalUnlocked) {{
                window._pendingSection = 'workflow-home';
                showSection('pw-gate');
                return;
            }}
            // If nothing unlocked, show gate targeting pricing
            window._pendingSection = 'pricing';
            showSection('pw-gate');
        }}

        function accessWorkflow(sectionId) {{
            if (CLIENT_SECTIONS.includes(sectionId) && clientUnlocked) {{
                showSection(sectionId);
                return;
            }}
            if (INTERNAL_SECTIONS.includes(sectionId) && internalUnlocked) {{
                showSection(sectionId);
                return;
            }}
            window._pendingSection = sectionId;
            showSection('pw-gate');
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

        /* ── DOM builder helpers (no innerHTML — all content set via textContent/createElement) ── */
        function makeEl(tag, cls, text) {{
            const el = document.createElement(tag);
            if (cls) el.className = cls;
            if (text !== undefined && text !== null) el.textContent = text;
            return el;
        }}
        function makeLink(url, text, cls) {{
            const a = document.createElement('a');
            a.href = isAllowedUrl(url) ? url : '#';
            a.target = '_blank';
            a.rel = 'noreferrer noopener';
            if (cls) a.className = cls;
            if (text) a.textContent = text;
            return a;
        }}
        function setStyle(el, styles) {{
            Object.assign(el.style, styles);
            return el;
        }}

        /* ── Safe markdown renderer (textContent only, no innerHTML) ── */
        function renderMarkdown(md) {{
            const container = document.createDocumentFragment();
            const lines = (md || '').split('\\n');
            let i = 0;
            let currentList = null;

            function flushList() {{
                if (currentList) {{ container.appendChild(currentList); currentList = null; }}
            }}

            while (i < lines.length) {{
                const line = lines[i];
                const trimmed = line.trim();

                // Code blocks
                if (trimmed.startsWith('```')) {{
                    flushList();
                    const codeLines = [];
                    i++;
                    while (i < lines.length && !lines[i].trim().startsWith('```')) {{
                        codeLines.push(lines[i]);
                        i++;
                    }}
                    i++; // skip closing ```
                    const wrapper = makeEl('div', 'wf-code');
                    const pre = makeEl('pre', null, codeLines.join('\\n'));
                    wrapper.appendChild(pre);
                    container.appendChild(wrapper);
                    continue;
                }}

                // Horizontal rule
                if (['---', '***', '___'].includes(trimmed)) {{
                    flushList();
                    container.appendChild(document.createElement('hr'));
                    i++; continue;
                }}

                // Headers
                if (trimmed.startsWith('### ')) {{
                    flushList();
                    container.appendChild(makeEl('h4', 'wf-h4', trimmed.slice(4)));
                    i++; continue;
                }}
                if (trimmed.startsWith('## ')) {{
                    flushList();
                    container.appendChild(makeEl('h3', 'wf-h3', trimmed.slice(3)));
                    i++; continue;
                }}
                if (trimmed.startsWith('# ')) {{
                    flushList();
                    container.appendChild(makeEl('h2', 'wf-h2', trimmed.slice(2)));
                    i++; continue;
                }}

                // Table rows
                if (trimmed.startsWith('|') && trimmed.includes('|')) {{
                    flushList();
                    const tableRows = [];
                    while (i < lines.length && lines[i].trim().startsWith('|')) {{
                        const row = lines[i].trim();
                        const cells = row.slice(1, -1).split('|').map(c => c.trim());
                        // Skip separator rows (---|---)
                        if (!cells.every(c => /^[-: ]+$/.test(c))) {{
                            tableRows.push(cells);
                        }}
                        i++;
                    }}
                    if (tableRows.length > 0) {{
                        const table = makeEl('table', 'wf-table');
                        tableRows.forEach((cells, idx) => {{
                            const tr = document.createElement('tr');
                            cells.forEach(c => {{
                                const cell = document.createElement(idx === 0 ? 'th' : 'td');
                                cell.textContent = c;
                                tr.appendChild(cell);
                            }});
                            table.appendChild(tr);
                        }});
                        container.appendChild(table);
                    }}
                    continue;
                }}

                // Numbered lists
                if (/^\\d+\\.\\s/.test(trimmed)) {{
                    flushList();
                    container.appendChild(makeEl('p', 'wf-step', trimmed.replace(/^\\d+\\.\\s/, '')));
                    i++; continue;
                }}

                // Unordered lists
                if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {{
                    if (!currentList) currentList = document.createElement('ul');
                    const indent = line.search(/\\S/);
                    const li = makeEl('li', null, trimmed.slice(2));
                    if (indent >= 2) setStyle(li, {{ marginLeft: '20px' }});
                    currentList.appendChild(li);
                    i++; continue;
                }}

                // Empty line ends list
                if (trimmed === '') {{
                    flushList();
                    i++; continue;
                }}

                // Paragraph
                flushList();
                container.appendChild(makeEl('p', null, trimmed));
                i++;
            }}
            flushList();
            return container;
        }}

        /* ── Section builders ── */
        function buildSection(el, id, data) {{
            // Common: back link
            if (data.has_back) {{
                const back = makeEl('a', 'back-link', '\u2190 Back to Workflow');
                back.href = '#';
                back.dataset.section = data.back_section || 'workflow-home';
                el.appendChild(back);
            }}
            // Common: breadcrumb, title, subtitle
            if (data.breadcrumb) el.appendChild(makeEl('div', 'page-breadcrumb', data.breadcrumb));
            if (data.title) el.appendChild(makeEl('h1', 'page-title', data.title));
            if (data.subtitle) el.appendChild(makeEl('div', 'page-meta', data.subtitle));

            // Dispatch to specific builder
            if (id === 'pricing') buildPricing(el, data);
            else if (id === 'booking') buildBooking(el, data);
            else if (id === 'workflow-home') buildWorkflowHome(el, data);
            else if (id === 'checklists') buildChecklists(el, data);
            else if (id === 'editing-projects') buildEditingProjects(el, data);
            else if (id === 'video-projects') buildVideoProjects(el, data);
            else if (id === 'client-feedback') buildClientFeedback(el, data);
            else if (id === 'booking-confirm') buildBookingConfirm(el, data);
            else if (data.markdown !== undefined) {{
                const wfContent = makeEl('div', 'wf-content');
                wfContent.appendChild(renderMarkdown(data.markdown));
                el.appendChild(wfContent);
            }}
        }}

        function buildPricing(el, data) {{
            // Pricing cards grid
            const grid = makeEl('div', 'pricing-grid');
            (data.packages || []).forEach(pkg => {{
                const card = makeEl('div', 'pricing-card');
                card.style.setProperty('--accent', pkg.accent);

                const header = makeEl('div', 'pricing-header');
                header.appendChild(makeEl('span', 'pricing-icon', pkg.icon));
                header.appendChild(makeEl('span', 'pricing-name', pkg.name));
                card.appendChild(header);

                if (pkg.desc) {{
                    const desc = makeEl('div', 'tier-details', pkg.desc);
                    desc.style.marginBottom = '12px';
                    card.appendChild(desc);
                }}

                (pkg.tiers || []).forEach(tier => {{
                    const tierDiv = makeEl('div', 'price-tier');
                    const tierHeader = makeEl('div', 'tier-header');
                    tierHeader.appendChild(makeEl('span', 'tier-name', tier.name));
                    const priceSpan = makeEl('span', 'tier-price', tier.price);
                    if (tier.price_sub) {{
                        const sub = makeEl('span', null, tier.price_sub);
                        Object.assign(sub.style, {{ fontSize: '13px', fontWeight: '400', color: '#6b7280' }});
                        priceSpan.appendChild(sub);
                    }}
                    tierHeader.appendChild(priceSpan);
                    tierDiv.appendChild(tierHeader);
                    tierDiv.appendChild(makeEl('div', 'tier-details', tier.desc));
                    card.appendChild(tierDiv);
                }});

                grid.appendChild(card);
            }});
            el.appendChild(grid);

            // Includes box
            const includesBox = makeEl('div', 'includes-box');
            includesBox.appendChild(makeEl('h3', null, "What's Included"));
            const includesList = makeEl('div', 'includes-list');
            (data.includes || []).forEach(item => {{
                includesList.appendChild(makeEl('span', null, '\u2713 ' + item));
            }});
            includesBox.appendChild(includesList);
            el.appendChild(includesBox);

            // Solo vs Dual comparison
            if (data.comparison) {{
                const compWrap = document.createElement('div');
                compWrap.style.marginTop = '28px';
                const compTitle = makeEl('h3', null, data.comparison.title);
                Object.assign(compTitle.style, {{ fontSize: '16px', fontWeight: '700', color: '#fff', marginBottom: '4px' }});
                compWrap.appendChild(compTitle);

                const proscons = makeEl('div', 'proscons');
                ['solo', 'dual'].forEach(key => {{
                    const side = data.comparison[key];
                    if (!side) return;
                    const col = makeEl('div', 'proscons-col');
                    col.style.border = '1px solid ' + side.border;
                    const h4 = makeEl('h4', null, side.label);
                    h4.style.color = side.color;
                    col.appendChild(h4);
                    const ul = document.createElement('ul');
                    (side.pros || []).forEach(pro => {{
                        const li = makeEl('li', null, '\u2713 ' + pro);
                        ul.appendChild(li);
                    }});
                    if (side.note) {{
                        const noteLi = makeEl('li', null, side.note);
                        Object.assign(noteLi.style, {{ color: '#6b7280', fontStyle: 'italic', marginTop: '6px' }});
                        ul.appendChild(noteLi);
                    }}
                    col.appendChild(ul);
                    proscons.appendChild(col);
                }});
                compWrap.appendChild(proscons);
                el.appendChild(compWrap);
            }}

            // Request a Quote button
            const btnWrap = document.createElement('div');
            Object.assign(btnWrap.style, {{ marginTop: '24px', textAlign: 'center' }});
            const quoteBtn = makeEl('button', 'copy-btn', 'Request a Quote');
            quoteBtn.dataset.section = 'booking';
            quoteBtn.style.background = '#8b5cf6';
            btnWrap.appendChild(quoteBtn);
            el.appendChild(btnWrap);

            // Testimonials near pricing
            if (data.reviews && data.reviews.length) {{
                const testWrap = document.createElement('div');
                testWrap.style.marginTop = '32px';
                testWrap.appendChild(makeEl('div', 'testimonials-title', 'What Clients Say'));
                const testGrid = makeEl('div', 'testimonials-grid');
                data.reviews.forEach(r => {{
                    const card = makeEl('div', 'testimonial-card');
                    const stars = '\u2605'.repeat(r.rating) + '\u2606'.repeat(5 - r.rating);
                    card.appendChild(makeEl('div', 'testimonial-stars', stars));
                    card.appendChild(makeEl('div', 'testimonial-quote', r.text));
                    card.appendChild(makeEl('div', 'testimonial-name', r.name));
                    card.appendChild(makeEl('div', 'testimonial-event', r.event_type));
                    testGrid.appendChild(card);
                }});
                testWrap.appendChild(testGrid);
                el.appendChild(testWrap);
            }}
        }}

        function buildBooking(el, data) {{
            const form = makeEl('div', 'book-form');
            form.id = 'book-form';

            function addFormRow(parent, label, inputEl) {{
                const row = makeEl('div', 'form-row');
                row.appendChild(makeEl('label', 'form-label', label));
                row.appendChild(inputEl);
                parent.appendChild(row);
                return row;
            }}
            function makeInput(id, type, placeholder, attrs) {{
                const inp = document.createElement('input');
                inp.className = 'form-input';
                inp.id = id;
                inp.type = type || 'text';
                if (placeholder) inp.placeholder = placeholder;
                inp.dataset.quoteInput = '';
                if (attrs) Object.entries(attrs).forEach(([k,v]) => inp.setAttribute(k, v));
                return inp;
            }}
            function makeSelect(id, options, cls) {{
                const sel = document.createElement('select');
                sel.className = cls || 'form-select';
                sel.id = id;
                sel.dataset.quoteInput = '';
                options.forEach(opt => {{
                    const o = document.createElement('option');
                    if (typeof opt === 'string') {{ o.value = opt; o.textContent = opt; }}
                    else {{ o.value = opt.value; o.textContent = opt.label; }}
                    sel.appendChild(o);
                }});
                return sel;
            }}

            // Name
            addFormRow(form, 'CLIENT NAME', makeInput('q-name', 'text', 'Full name'));

            // Event
            const eventOpts = [{{ value: '', label: 'Select event type' }}, ...(data.event_types || []).map(e => ({{ value: e, label: e }}))];
            addFormRow(form, 'EVENT', makeSelect('q-event', eventOpts));

            // Location
            addFormRow(form, 'LOCATION', makeInput('q-location', 'text', 'Venue name or city'));

            // Date + Hours (inline)
            const inline1 = makeEl('div', 'form-row-inline');
            const dateRow = makeEl('div', 'form-row');
            dateRow.appendChild(makeEl('label', 'form-label', 'DATE'));
            dateRow.appendChild(makeInput('q-date', 'date', ''));
            inline1.appendChild(dateRow);
            const hoursRow = makeEl('div', 'form-row');
            hoursRow.appendChild(makeEl('label', 'form-label', 'HOURS OF COVERAGE'));
            hoursRow.appendChild(makeInput('q-hours', 'number', 'Hours', {{ min: '1' }}));
            inline1.appendChild(hoursRow);
            form.appendChild(inline1);

            // Setting + Coverage (inline)
            const inline2 = makeEl('div', 'form-row-inline');
            const settingRow = makeEl('div', 'form-row');
            settingRow.appendChild(makeEl('label', 'form-label', 'SETTING'));
            settingRow.appendChild(makeSelect('q-shoottype', data.settings || []));
            inline2.appendChild(settingRow);
            const covRow = makeEl('div', 'form-row');
            covRow.appendChild(makeEl('label', 'form-label', 'COVERAGE TYPE'));
            covRow.appendChild(makeSelect('q-services', data.coverage_types || []));
            inline2.appendChild(covRow);
            form.appendChild(inline2);

            // Live streaming checkbox
            const liveRow = makeEl('div', 'form-row');
            liveRow.style.marginTop = '4px';
            const liveLabel = document.createElement('label');
            Object.assign(liveLabel.style, {{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '14px', color: '#d1d5db' }});
            const liveCb = document.createElement('input');
            liveCb.type = 'checkbox';
            liveCb.id = 'q-live';
            liveCb.dataset.quoteInput = '';
            Object.assign(liveCb.style, {{ width: '18px', height: '18px', accentColor: '#10b981' }});
            liveLabel.appendChild(liveCb);
            liveLabel.appendChild(document.createTextNode(data.live_streaming_label || 'Add Live Streaming (+$100)'));
            liveRow.appendChild(liveLabel);
            form.appendChild(liveRow);

            // Estimate + Retainer (inline)
            const inline3 = makeEl('div', 'form-row-inline');
            const estRow = makeEl('div', 'form-row');
            estRow.appendChild(makeEl('label', 'form-label', 'ESTIMATED INVESTMENT'));
            const quoteInput = document.createElement('input');
            quoteInput.className = 'form-input';
            quoteInput.id = 'q-quote';
            quoteInput.readOnly = true;
            Object.assign(quoteInput.style, {{ color: '#8b5cf6', fontWeight: '700' }});
            estRow.appendChild(quoteInput);
            inline3.appendChild(estRow);
            const retRow = makeEl('div', 'form-row');
            retRow.appendChild(makeEl('label', 'form-label', 'RETAINER'));
            retRow.appendChild(makeInput('q-deposit', 'text', 'e.g. $100'));
            inline3.appendChild(retRow);
            form.appendChild(inline3);

            el.appendChild(form);

            // Quote preview
            const preview = makeEl('div', 'quote-preview');
            preview.id = 'quote-preview';
            preview.style.marginTop = '20px';
            el.appendChild(preview);

            // Buttons
            const btnRow = makeEl('div', 'btn-row');
            const copyBtn = makeEl('button', 'copy-btn', '\U0001f4cb Copy to Clipboard');
            copyBtn.id = 'copy-quote-btn';
            btnRow.appendChild(copyBtn);
            const waBtn = makeEl('a', 'share-wa-btn', '\U0001f4ac Share via WhatsApp');
            waBtn.id = 'wa-share-btn';
            waBtn.href = '#';
            waBtn.target = '_blank';
            waBtn.rel = 'noreferrer noopener';
            btnRow.appendChild(waBtn);
            el.appendChild(btnRow);

            // Confirmation
            const conf = document.createElement('div');
            conf.id = 'booking-confirmation';
            Object.assign(conf.style, {{ display: 'none', marginTop: '20px', padding: '20px', background: '#1a2e1a', border: '1px solid #2d4a2d', borderRadius: '12px', textAlign: 'center' }});
            conf.appendChild(setStyle(makeEl('div', null, '\u2713'), {{ fontSize: '24px', marginBottom: '8px' }}));
            conf.appendChild(setStyle(makeEl('div', null, 'Quote sent!'), {{ fontSize: '16px', fontWeight: '600', color: '#10b981', marginBottom: '6px' }}));
            const confMsg = makeEl('div');
            Object.assign(confMsg.style, {{ fontSize: '14px', color: '#9ca3af', lineHeight: '1.6' }});
            confMsg.appendChild(document.createTextNode("I'll confirm availability and get back to you within 24 hours."));
            confMsg.appendChild(document.createElement('br'));
            confMsg.appendChild(document.createTextNode('Feel free to message me on WhatsApp if you have any questions.'));
            conf.appendChild(confMsg);
            el.appendChild(conf);
        }}

        function buildWorkflowHome(el, data) {{
            // Pipeline row
            const pipeRow = makeEl('div', 'pipeline-row');
            (data.pipeline || []).forEach(stage => {{
                const s = makeEl('div', 'pipeline-stage', stage.label);
                s.style.background = stage.color;
                pipeRow.appendChild(s);
            }});
            el.appendChild(pipeRow);

            // Tile grid
            const tileGrid = makeEl('div', 'wf-tile-grid');
            (data.tiles || []).forEach(tile => {{
                let tileEl;
                if (tile.url) {{
                    tileEl = document.createElement('a');
                    tileEl.href = isAllowedUrl(tile.url) ? tile.url : '#';
                    tileEl.target = '_blank';
                    tileEl.rel = 'noreferrer noopener';
                    tileEl.style.textDecoration = 'none';
                    tileEl.style.color = 'inherit';
                }} else {{
                    tileEl = document.createElement('div');
                    if (tile.section) tileEl.dataset.section = tile.section;
                }}
                tileEl.className = 'wf-tile';
                tileEl.appendChild(makeEl('div', 'wf-tile-icon', tile.icon));
                tileEl.appendChild(makeEl('div', 'wf-tile-label', tile.label));
                tileGrid.appendChild(tileEl);
            }});
            el.appendChild(tileGrid);
        }}

        function buildChecklists(el, data) {{
            (data.groups || []).forEach(group => {{
                const grp = makeEl('div', 'checklist-group');
                grp.appendChild(makeEl('div', 'checklist-title', group.title));
                (group.items || []).forEach((item, idx) => {{
                    const label = document.createElement('label');
                    label.className = 'check-item';
                    const cbId = group.prefix + '-' + idx;
                    label.setAttribute('for', cbId);
                    const cb = document.createElement('input');
                    cb.type = 'checkbox';
                    cb.id = cbId;
                    cb.dataset.checklist = '';
                    label.appendChild(cb);
                    label.appendChild(makeEl('span', null, item));
                    grp.appendChild(label);
                }});
                el.appendChild(grp);
            }});
            const resetWrap = document.createElement('div');
            resetWrap.style.marginTop = '20px';
            const resetBtn = makeEl('button', 'pw-btn', 'Reset All Checklists');
            resetBtn.id = 'reset-checklists-btn';
            resetBtn.style.background = '#374151';
            resetWrap.appendChild(resetBtn);
            el.appendChild(resetWrap);
        }}

        function buildEditingProjects(el, data) {{
            const wrap = makeEl('div', 'editing-table-wrap');
            const table = makeEl('table', 'editing-table');
            const thead = document.createElement('thead');
            const headRow = document.createElement('tr');
            (data.columns || []).forEach(col => {{
                headRow.appendChild(makeEl('th', null, col));
            }});
            thead.appendChild(headRow);
            table.appendChild(thead);
            const tbody = document.createElement('tbody');
            (data.rows || []).forEach(row => {{
                const tr = document.createElement('tr');
                // Project
                tr.appendChild(makeEl('td', null, row.task));
                // Priority
                const priTd = document.createElement('td');
                priTd.appendChild(makeEl('span', 'priority-badge priority-' + row.priority.toLowerCase(), row.priority));
                tr.appendChild(priTd);
                // Sent
                tr.appendChild(makeEl('td', null, row.date_sent));
                // Days
                tr.appendChild(makeEl('td', null, row.days + 'd'));
                // Status
                const statusTd = document.createElement('td');
                const badgeMap = {{ 'OVERDUE': 'badge-overdue', 'COMPLETED': 'badge-completed', 'SENT': 'badge-sent' }};
                statusTd.appendChild(makeEl('span', 'status-badge ' + (badgeMap[row.status] || 'badge-progress'), row.status));
                tr.appendChild(statusTd);
                // Completed
                tr.appendChild(makeEl('td', null, row.completed));
                // Files (delivery link)
                const filesTd = document.createElement('td');
                if (row.delivery_link) {{
                    filesTd.appendChild(makeLink(row.delivery_link, 'View', 'delivery-link'));
                }} else {{
                    const dash = makeEl('span', null, '\u2014');
                    dash.style.color = '#6b7280';
                    filesTd.appendChild(dash);
                }}
                tr.appendChild(filesTd);
                tbody.appendChild(tr);
            }});
            table.appendChild(tbody);
            wrap.appendChild(table);
            el.appendChild(wrap);
        }}

        function buildVideoProjects(el, data) {{
            const wrap = makeEl('div', 'editing-table-wrap');
            const table = makeEl('table', 'editing-table');
            const thead = document.createElement('thead');
            const headRow = document.createElement('tr');
            (data.columns || []).forEach(col => {{
                headRow.appendChild(makeEl('th', null, col));
            }});
            thead.appendChild(headRow);
            table.appendChild(thead);
            const tbody = document.createElement('tbody');
            (data.rows || []).forEach(row => {{
                const tr = document.createElement('tr');
                // Project
                tr.appendChild(makeEl('td', null, row.task));
                // Editor
                tr.appendChild(makeEl('td', null, row.editor));
                // Priority
                const priTd = document.createElement('td');
                priTd.appendChild(makeEl('span', 'priority-badge priority-' + row.priority.toLowerCase(), row.priority));
                tr.appendChild(priTd);
                // Sent
                tr.appendChild(makeEl('td', null, row.date_sent));
                // Days
                tr.appendChild(makeEl('td', null, row.days + 'd'));
                // Status
                const statusTd = document.createElement('td');
                const badgeMap = {{ 'OVERDUE': 'badge-overdue', 'COMPLETED': 'badge-completed', 'SENT': 'badge-sent', '1ST CUT DONE': 'badge-progress' }};
                statusTd.appendChild(makeEl('span', 'status-badge ' + (badgeMap[row.status] || 'badge-progress'), row.status));
                tr.appendChild(statusTd);
                // Completed
                tr.appendChild(makeEl('td', null, row.completed));
                // Files (delivery link)
                const filesTd = document.createElement('td');
                if (row.delivery_link) {{
                    filesTd.appendChild(makeLink(row.delivery_link, 'View', 'delivery-link'));
                }} else {{
                    const dash = makeEl('span', null, '\u2014');
                    dash.style.color = '#6b7280';
                    filesTd.appendChild(dash);
                }}
                tr.appendChild(filesTd);
                tbody.appendChild(tr);
            }});
            table.appendChild(tbody);
            wrap.appendChild(table);
            el.appendChild(wrap);
        }}

        /* ── Client Feedback Admin ── */
        var _fbConfig = null;
        var _fbLastCooldown = 0;

        function fbGetStatus(proj, side) {{
            if (proj.type === 'both') {{
                if (side === 'photo') return proj.photo_status || 'editing';
                if (side === 'video') return proj.video_status || 'editing';
            }}
            return proj.status || 'editing';
        }}

        function fbBuildTracker(status) {{
            var stages = [
                {{key: 'shoot_done', label: 'Shoot Done'}},
                {{key: 'sent', label: 'Sent'}},
                {{key: 'editing', label: 'Editing'}},
                {{key: 'review', label: 'Edits Done'}},
                {{key: 'delivered', label: 'Delivered'}}
            ];
            var wrap = makeEl('div', 'fb-tracker');
            var steps = makeEl('div', 'fb-tracker-steps');
            var reached = false;
            stages.forEach(function(stage, idx) {{
                var step = makeEl('div', 'fb-tracker-step');
                if (!reached) {{
                    if (stage.key === status) {{
                        step.className += ' active completed';
                        reached = true;
                    }} else {{
                        step.className += ' completed';
                    }}
                }}
                var dot = makeEl('div', 'fb-tracker-dot', String(idx + 1));
                step.appendChild(dot);
                step.appendChild(makeEl('div', 'fb-tracker-label', stage.label));
                steps.appendChild(step);
            }});
            wrap.appendChild(steps);
            return wrap;
        }}

        function fbPostUpdate(action, body) {{
            var now = Date.now();
            if (now - _fbLastCooldown < 5000) return Promise.resolve(null);
            _fbLastCooldown = now;
            if (!_fbConfig || !_fbConfig.script_url) return Promise.resolve(null);
            return fetch(_fbConfig.script_url, {{
                method: 'POST',
                headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
                body: new URLSearchParams(Object.assign({{type: action}}, body)).toString(),
                redirect: 'follow'
            }}).then(function(r) {{ return r.json(); }}).catch(function() {{ return null; }});
        }}

        function fbRenderProjects(container, projects, entries) {{
            // Clear container
            while (container.firstChild) container.removeChild(container.firstChild);

            var slugs = Object.keys(projects);
            if (slugs.length === 0) {{
                container.appendChild(makeEl('div', 'fb-empty', 'No feedback projects configured.'));
                return;
            }}

            // Filter tabs
            var filterWrap = makeEl('div', 'fb-filter-tabs');
            var filters = [{{'key': 'all', 'label': 'All'}}, {{'key': 'photo', 'label': '\\uD83D\\uDCF7 Photo'}}, {{'key': 'video', 'label': '\\uD83C\\uDFAC Video'}}];
            var editors = [];
            slugs.forEach(function(s) {{
                var p = projects[s];
                if (p.editor && editors.indexOf(p.editor) === -1) editors.push(p.editor);
                if (p.photo_editor && editors.indexOf(p.photo_editor) === -1) editors.push(p.photo_editor);
            }});
            editors.forEach(function(e) {{ filters.push({{key: 'editor:' + e, label: e}}); }});
            var activeFilter = 'all';

            function renderFiltered() {{
                // Remove existing cards
                var cards = container.querySelectorAll('.fb-project-card, .fb-empty');
                cards.forEach(function(c) {{ c.remove(); }});

                var shown = 0;
                slugs.forEach(function(slug) {{
                    var proj = projects[slug];
                    var show = false;
                    if (activeFilter === 'all') show = true;
                    else if (activeFilter === 'photo' && (proj.type === 'photo' || proj.type === 'both')) show = true;
                    else if (activeFilter === 'video' && (proj.type === 'video' || proj.type === 'both')) show = true;
                    else if (activeFilter.indexOf('editor:') === 0) {{
                        var ed = activeFilter.substring(7);
                        if (proj.editor === ed || proj.photo_editor === ed) show = true;
                    }}
                    if (!show) return;
                    shown++;

                    var card = makeEl('div', 'fb-project-card');

                    // Header: name + type badge + editor badges
                    var header = makeEl('div', 'fb-project-header');
                    header.appendChild(makeEl('div', 'fb-project-name', proj.name));
                    var typeBadge = makeEl('span', 'fb-type-badge fb-type-' + proj.type, proj.type);
                    header.appendChild(typeBadge);
                    if (proj.editor) header.appendChild(makeEl('span', 'fb-editor-badge', proj.editor));
                    if (proj.photo_editor) header.appendChild(makeEl('span', 'fb-editor-badge', proj.photo_editor));
                    card.appendChild(header);

                    // Version links
                    if (proj.versions && proj.versions.length > 0) {{
                        var verWrap = makeEl('div', null);
                        verWrap.style.marginBottom = '8px';
                        proj.versions.forEach(function(v) {{
                            var vLink = makeLink(v.url, v.label, 'fb-version-link');
                            verWrap.appendChild(vLink);
                        }});
                        card.appendChild(verWrap);
                    }}

                    // Tracker(s)
                    if (proj.type === 'both') {{
                        var pLabel = makeEl('div', null, '\\uD83D\\uDCF7 Photo');
                        pLabel.style.cssText = 'font-size:11px;color:#9ca3af;margin-top:8px;';
                        card.appendChild(pLabel);
                        card.appendChild(fbBuildTracker(fbGetStatus(proj, 'photo')));
                        var vLabel = makeEl('div', null, '\\uD83C\\uDFAC Video');
                        vLabel.style.cssText = 'font-size:11px;color:#9ca3af;margin-top:8px;';
                        card.appendChild(vLabel);
                        card.appendChild(fbBuildTracker(fbGetStatus(proj, 'video')));
                    }} else {{
                        card.appendChild(fbBuildTracker(fbGetStatus(proj)));
                    }}

                    // Filter entries for this project
                    var projEntries = entries.filter(function(e) {{ return e.project === proj.name; }});
                    var songs = projEntries.filter(function(e) {{ return e.type === 'song'; }});
                    var corrections = projEntries.filter(function(e) {{ return e.type === 'correction'; }});

                    // Songs
                    if (songs.length > 0) {{
                        card.appendChild(makeEl('div', 'fb-section-title', 'Song Choices (' + songs.length + ')'));
                        songs.forEach(function(s) {{
                            var songDiv = makeEl('div', 'fb-song');
                            songDiv.appendChild(makeEl('span', 'fb-song-icon', '\\uD83C\\uDFB5'));
                            songDiv.appendChild(makeEl('span', 'fb-song-text', s.content));
                            card.appendChild(songDiv);
                        }});
                    }}

                    // Corrections
                    if (corrections.length > 0) {{
                        card.appendChild(makeEl('div', 'fb-section-title', 'Corrections (' + corrections.length + ')'));
                        corrections.forEach(function(c) {{
                            var corDiv = makeEl('div', 'fb-correction');
                            var corHeader = makeEl('div', 'fb-correction-header');
                            if (c.timestamp) corHeader.appendChild(makeEl('span', 'fb-correction-ts', c.timestamp));
                            if (c.priority) {{
                                var priCls = 'fb-correction-pri fb-pri-' + (c.priority || 'low').toLowerCase();
                                corHeader.appendChild(makeEl('span', priCls, c.priority));
                            }}
                            // Fixed status icon
                            if (c.fixed === 'yes') {{
                                corHeader.appendChild(makeEl('span', 'fb-status-icon', '\\u2705'));
                            }} else if (c.fixed && c.fixed.indexOf('cant_fix') === 0) {{
                                corHeader.appendChild(makeEl('span', 'fb-status-icon', '\\u274C'));
                            }}
                            corDiv.appendChild(corHeader);
                            corDiv.appendChild(makeEl('div', 'fb-correction-text', c.content));

                            // Fix buttons (only if not already fixed)
                            if (!c.fixed || c.fixed === '') {{
                                var actions = makeEl('div', 'fb-correction-actions');
                                var fixBtn = makeEl('button', 'fb-fix-btn', '\\u2705 Fixed');
                                var cantFixBtn = makeEl('button', 'fb-fix-btn', '\\u274C Can\\u0027t Fix');

                                fixBtn.addEventListener('click', (function(entry, btn1, btn2) {{
                                    return function() {{
                                        btn1.disabled = true;
                                        btn2.disabled = true;
                                        var pin = _fbConfig.project_pins[entry.project] || '';
                                        fbPostUpdate('feedback_update', {{
                                            project: entry.project,
                                            row: entry.row || '',
                                            fixed: 'yes',
                                            pin: pin
                                        }}).then(function() {{
                                            btn1.className = 'fb-fix-btn fixed';
                                            btn1.textContent = '\\u2705 Fixed';
                                        }});
                                    }};
                                }})(c, fixBtn, cantFixBtn));

                                cantFixBtn.addEventListener('click', (function(entry, btn1, btn2) {{
                                    return function() {{
                                        btn1.disabled = true;
                                        btn2.disabled = true;
                                        var pin = _fbConfig.project_pins[entry.project] || '';
                                        fbPostUpdate('feedback_update', {{
                                            project: entry.project,
                                            row: entry.row || '',
                                            fixed: 'cant_fix',
                                            pin: pin
                                        }}).then(function() {{
                                            btn2.className = 'fb-fix-btn cant-fix';
                                            btn2.textContent = '\\u274C Can\\u0027t Fix';
                                        }});
                                    }};
                                }})(c, fixBtn, cantFixBtn));

                                actions.appendChild(fixBtn);
                                actions.appendChild(cantFixBtn);
                                corDiv.appendChild(actions);
                            }}

                            card.appendChild(corDiv);
                        }});
                    }}

                    // No feedback yet
                    if (songs.length === 0 && corrections.length === 0) {{
                        var noData = makeEl('div', 'fb-empty');
                        noData.textContent = 'No feedback submitted yet';
                        noData.style.padding = '16px 0';
                        card.appendChild(noData);
                    }}

                    // Notify editor button (only if corrections exist)
                    if (corrections.length > 0 && proj.editor_phone) {{
                        var notifyBtn = makeEl('button', 'fb-notify-btn', '\\uD83D\\uDCE9 Notify ' + proj.editor);
                        notifyBtn.addEventListener('click', (function(project, editorPhone, pin) {{
                            return function() {{
                                notifyBtn.disabled = true;
                                notifyBtn.textContent = 'Sending...';
                                fbPostUpdate('feedback_notify', {{
                                    project: project.name,
                                    editor_phone: editorPhone,
                                    pin: pin
                                }}).then(function() {{
                                    notifyBtn.textContent = '\\u2705 Notified';
                                    setTimeout(function() {{
                                        notifyBtn.disabled = false;
                                        notifyBtn.textContent = '\\uD83D\\uDCE9 Notify ' + project.editor;
                                    }}, 5000);
                                }});
                            }};
                        }})(proj, proj.editor_phone, _fbConfig.project_pins[proj.name] || ''));
                        card.appendChild(notifyBtn);
                    }}

                    container.appendChild(card);
                }});

                if (shown === 0) {{
                    container.appendChild(makeEl('div', 'fb-empty', 'No projects match this filter.'));
                }}
            }}

            filters.forEach(function(f) {{
                var tab = makeEl('button', 'fb-filter-tab' + (f.key === 'all' ? ' active' : ''), f.label);
                tab.addEventListener('click', function() {{
                    filterWrap.querySelectorAll('.fb-filter-tab').forEach(function(t) {{ t.classList.remove('active'); }});
                    tab.classList.add('active');
                    activeFilter = f.key;
                    renderFiltered();
                }});
                filterWrap.appendChild(tab);
            }});
            container.appendChild(filterWrap);
            renderFiltered();
        }}

        function buildClientFeedback(el, data) {{
            _fbConfig = {{ script_url: data.script_url, ram_phone: data.ram_phone, project_pins: data.project_pins }};

            // Toolbar: refresh button
            var toolbar = makeEl('div', 'fb-toolbar');
            var refreshBtn = makeEl('button', 'fb-refresh', '\\u21BB Refresh');
            toolbar.appendChild(refreshBtn);
            el.appendChild(toolbar);

            // Loading state
            var loadingEl = makeEl('div', 'fb-loading', 'Loading corrections...');
            el.appendChild(loadingEl);

            function doFetch() {{
                // Show loading
                var existing = el.querySelector('.fb-loading');
                if (!existing) {{
                    existing = makeEl('div', 'fb-loading', 'Loading corrections...');
                    el.appendChild(existing);
                }}

                var fetchUrl = data.script_url + '?action=feedback_read';
                if (!isAllowedUrl(fetchUrl)) {{
                    existing.textContent = 'Script URL not in allowlist.';
                    return;
                }}
                fetch(fetchUrl)
                    .then(function(r) {{ return r.json(); }})
                    .then(function(result) {{
                        var ld = el.querySelector('.fb-loading');
                        if (ld) ld.remove();
                        var ents = result.entries || [];
                        fbRenderProjects(el, data.projects, ents);
                    }})
                    .catch(function() {{
                        var ld = el.querySelector('.fb-loading');
                        if (ld) ld.textContent = 'Failed to load. Check your connection.';
                    }});
            }}

            refreshBtn.addEventListener('click', function() {{
                // Remove cards + filters
                var cards = el.querySelectorAll('.fb-project-card, .fb-filter-tabs, .fb-empty');
                cards.forEach(function(c) {{ c.remove(); }});
                doFetch();
            }});

            doFetch();
        }}

        function buildBookingConfirm(el, data) {{
            // Quick-fill buttons
            const qfWrap = makeEl('div', 'bc-quickfill');
            const qfLabel = makeEl('div', 'form-label', 'QUICK FILL');
            qfLabel.style.marginBottom = '8px';
            qfWrap.appendChild(qfLabel);
            const qfGrid = makeEl('div', 'bc-qf-grid');
            (data.quick_fills || []).forEach(qf => {{
                const btn = makeEl('button', 'bc-qf-btn', qf.label);
                btn.addEventListener('click', () => {{
                    const evSel = document.getElementById('bc-event');
                    if (evSel) evSel.value = qf.event;
                    const locInp = document.getElementById('bc-location');
                    if (locInp) locInp.value = qf.location;
                }});
                qfGrid.appendChild(btn);
            }});
            qfWrap.appendChild(qfGrid);
            el.appendChild(qfWrap);

            // Form
            const form = makeEl('div', 'bc-form');

            function addRow(parent, label, inputEl) {{
                const row = makeEl('div', 'form-row');
                row.appendChild(makeEl('label', 'form-label', label));
                row.appendChild(inputEl);
                parent.appendChild(row);
            }}
            function mkInput(id, type, placeholder, attrs) {{
                const inp = document.createElement('input');
                inp.className = 'form-input';
                inp.id = id;
                inp.type = type || 'text';
                if (placeholder) inp.placeholder = placeholder;
                if (attrs) Object.entries(attrs).forEach(([k,v]) => inp.setAttribute(k, v));
                return inp;
            }}
            function mkSelect(id, options) {{
                const sel = document.createElement('select');
                sel.className = 'form-select';
                sel.id = id;
                options.forEach(opt => {{
                    const o = document.createElement('option');
                    if (typeof opt === 'string') {{ o.value = opt; o.textContent = opt; }}
                    else {{ o.value = opt.value; o.textContent = opt.label; }}
                    sel.appendChild(o);
                }});
                return sel;
            }}

            // Client Name
            addRow(form, 'CLIENT NAME', mkInput('bc-name', 'text', 'Full name'));

            // Client Phone
            addRow(form, 'CLIENT PHONE', mkInput('bc-phone', 'tel', '10-digit phone number'));

            // Event Type dropdown
            const evOpts = [{{ value: '', label: 'Select event type' }}, ...(data.event_types || []).map(e => ({{ value: e + ' Photography', label: e }}))];
            addRow(form, 'EVENT TYPE', mkSelect('bc-event', evOpts));

            // Date
            addRow(form, 'DATE', mkInput('bc-date', 'date', ''));

            // Start / End time inline
            const timeRow = makeEl('div', 'form-row-inline');
            const startDiv = makeEl('div', 'form-row');
            startDiv.appendChild(makeEl('label', 'form-label', 'START TIME'));
            const startInp = mkInput('bc-start', 'time', '');
            startInp.value = (data.defaults || {{}}).start_time || '18:00';
            startDiv.appendChild(startInp);
            timeRow.appendChild(startDiv);
            const endDiv = makeEl('div', 'form-row');
            endDiv.appendChild(makeEl('label', 'form-label', 'END TIME'));
            const endInp = mkInput('bc-end', 'time', '');
            endInp.value = (data.defaults || {{}}).end_time || '22:00';
            endDiv.appendChild(endInp);
            timeRow.appendChild(endDiv);
            form.appendChild(timeRow);

            // Location
            addRow(form, 'LOCATION', mkInput('bc-location', 'text', 'Venue name or city'));

            el.appendChild(form);

            // Action buttons
            const actions = makeEl('div', 'bc-actions');
            const sendBtn = makeEl('button', 'bc-send-btn', 'Send via WhatsApp');
            const copyBtn = makeEl('button', 'bc-copy-btn', 'Copy Message');
            actions.appendChild(sendBtn);
            actions.appendChild(copyBtn);
            el.appendChild(actions);

            // Preview area
            const preview = makeEl('div', 'bc-preview');
            preview.id = 'bc-preview';
            preview.style.display = 'none';
            el.appendChild(preview);

            // Helper: build the message text
            function buildMessage() {{
                const name = (document.getElementById('bc-name') || {{}}).value || '';
                const phone = (document.getElementById('bc-phone') || {{}}).value || '';
                const event = (document.getElementById('bc-event') || {{}}).value || '';
                const dateVal = (document.getElementById('bc-date') || {{}}).value || '';
                const start = (document.getElementById('bc-start') || {{}}).value || '';
                const end = (document.getElementById('bc-end') || {{}}).value || '';
                const location = (document.getElementById('bc-location') || {{}}).value || '';

                if (!name || !phone || !event || !dateVal || !start || !end || !location) {{
                    return null;
                }}

                // Format date nicely
                const dObj = new Date(dateVal + 'T00:00:00');
                const dateStr = dObj.toLocaleDateString('en-US', {{ weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }});

                // Format times
                function fmtTime(t) {{
                    const [h, m] = t.split(':').map(Number);
                    const suffix = h >= 12 ? 'PM' : 'AM';
                    const h12 = h % 12 || 12;
                    return h12 + ':' + String(m).padStart(2, '0') + ' ' + suffix;
                }}
                const startStr = fmtTime(start);
                const endStr = fmtTime(end);

                // Calendar links
                const calStart = dateVal.replace(/-/g, '') + 'T' + start.replace(':', '') + '00';
                const calEnd = dateVal.replace(/-/g, '') + 'T' + end.replace(':', '') + '00';
                const calTitle = encodeURIComponent(event + ' - ' + name);
                const calLoc = encodeURIComponent(location);
                const calDetails = encodeURIComponent('Photography session with Rsquare Photography');

                const googleUrl = 'https://calendar.google.com/calendar/render?action=TEMPLATE&text=' + calTitle + '&dates=' + calStart + '/' + calEnd + '&location=' + calLoc + '&details=' + calDetails;

                // Outlook — ISO format
                const olStart = dateVal + 'T' + start + ':00';
                const olEnd = dateVal + 'T' + end + ':00';
                const outlookUrl = 'https://outlook.live.com/calendar/0/deeplink/compose?subject=' + calTitle + '&startdt=' + encodeURIComponent(olStart) + '&enddt=' + encodeURIComponent(olEnd) + '&location=' + calLoc + '&body=' + calDetails;

                const msg = [
                    '🎉 *Booking Confirmed!*',
                    '',
                    event,
                    name,
                    '',
                    '📅 ' + dateStr,
                    '⏰ ' + startStr + ' - ' + endStr,
                    '📍 ' + location,
                    '',
                    'Looking forward to capturing your special moments!',
                    '- ' + (data.photographer_name || 'Ram') + ', Rsquare Photography',
                    '',
                    '📅 *Add to your calendar:*',
                    'iPhone/Apple Calendar:',
                    googleUrl,
                    '',
                    'Outlook Calendar:',
                    outlookUrl,
                ].join('\\n');

                return {{ msg, phone, googleUrl, outlookUrl }};
            }}

            // Show preview
            function showPreview(msgObj) {{
                const prev = document.getElementById('bc-preview');
                if (!prev) return;
                while (prev.firstChild) prev.removeChild(prev.firstChild);
                prev.appendChild(makeEl('div', 'bc-preview-label', 'MESSAGE PREVIEW'));
                const pre = makeEl('div', 'bc-preview-text', msgObj.msg);
                pre.style.whiteSpace = 'pre-wrap';
                prev.appendChild(pre);
                prev.style.display = 'block';
            }}

            // Send button
            sendBtn.addEventListener('click', () => {{
                const result = buildMessage();
                if (!result) {{
                    const prev = document.getElementById('bc-preview');
                    if (prev) {{
                        while (prev.firstChild) prev.removeChild(prev.firstChild);
                        prev.appendChild(makeEl('div', 'bc-preview-label bc-error', 'Please fill in all fields'));
                        prev.style.display = 'block';
                    }}
                    return;
                }}
                showPreview(result);
                const waUrl = 'https://wa.me/' + result.phone + '?text=' + encodeURIComponent(result.msg);
                if (isAllowedUrl(waUrl)) {{
                    window.open(waUrl, '_blank', 'noopener,noreferrer');
                }}
            }});

            // Copy button
            copyBtn.addEventListener('click', () => {{
                const result = buildMessage();
                if (!result) {{
                    const prev = document.getElementById('bc-preview');
                    if (prev) {{
                        while (prev.firstChild) prev.removeChild(prev.firstChild);
                        prev.appendChild(makeEl('div', 'bc-preview-label bc-error', 'Please fill in all fields'));
                        prev.style.display = 'block';
                    }}
                    return;
                }}
                showPreview(result);
                if (navigator.clipboard) {{
                    navigator.clipboard.writeText(result.msg).then(() => {{
                        copyBtn.textContent = 'Copied!';
                        setTimeout(() => {{ copyBtn.textContent = 'Copy Message'; }}, 2000);
                    }});
                }}
            }});
        }}

        function injectDecryptedContent(sections) {{
            delete sections['v'];
            if (sections['__config__']) {{
                _appConfig = sections['__config__'];
                delete sections['__config__'];
                if (_appConfig.ramPhone) {{
                    var waMsg = encodeURIComponent("Hi Ram! I'm interested in a photography session.");
                    var waUrl = 'https://wa.me/' + _appConfig.ramPhone + '?text=' + waMsg;
                    var floatBtn = document.getElementById('wa-float-btn');
                    if (floatBtn) {{ floatBtn.href = waUrl; floatBtn.style.display = ''; }}
                    var contactWa = document.getElementById('contact-wa');
                    if (contactWa) {{ contactWa.href = waUrl; contactWa.style.display = ''; }}
                    var contactPhone = document.getElementById('contact-phone');
                    if (contactPhone) {{
                        contactPhone.href = 'tel:+' + _appConfig.ramPhone;
                        contactPhone.style.display = '';
                        var phoneLabel = document.getElementById('contact-phone-number');
                        if (phoneLabel) {{
                            var p = _appConfig.ramPhone;
                            phoneLabel.textContent = '(' + p.slice(0,3) + ') ' + p.slice(3,6) + '-' + p.slice(6);
                        }}
                    }}
                }}
            }}
            for (const [id, data] of Object.entries(sections)) {{
                const el = document.getElementById(id);
                if (!el) continue;
                while (el.firstChild) el.removeChild(el.firstChild);
                buildSection(el, id, data);
            }}
            loadChecklist();
            if (sections['booking'] && typeof updateQuote === 'function') {{
                updateQuote();
            }}
        }}

        let _failCount = 0;
        let _lockedOut = false;

        async function checkPassword() {{
            if (_lockedOut) return;
            const input = document.getElementById('pw-input').value;
            if (!input) return;
            const btn = document.getElementById('pw-btn');
            btn.disabled = true;
            btn.textContent = 'Checking...';
            let matched = false;

            // Try client blob
            if (!clientUnlocked) {{
                try {{
                    const plaintext = await decryptContent(input, ENCRYPTED_CLIENT);
                    const sections = JSON.parse(plaintext);
                    injectDecryptedContent(sections);
                    clientUnlocked = true;
                    matched = true;
                    updateClientLinks();
                }} catch(e) {{ /* not this password */ }}
            }}

            // Try internal blob — also unlocks client sections (admin access)
            if (!internalUnlocked) {{
                try {{
                    const plaintext = await decryptContent(input, ENCRYPTED_INTERNAL);
                    const sections = JSON.parse(plaintext);
                    injectDecryptedContent(sections);
                    internalUnlocked = true;
                    matched = true;
                    updateInternalLinks();
                    // Admin: also unlock client sections
                    if (!clientUnlocked) {{
                        try {{
                            const clientPlain = await decryptContent(input, ENCRYPTED_CLIENT_ADMIN);
                            const clientSections = JSON.parse(clientPlain);
                            injectDecryptedContent(clientSections);
                            clientUnlocked = true;
                            updateClientLinks();
                        }} catch(e2) {{ /* ok */ }}
                    }}
                }} catch(e) {{ /* not internal password */ }}
            }}

            if (matched) {{
                _failCount = 0;
                updateLockIcon();
                showToast('Unlocked!');
                document.getElementById('logout-btn').style.display = 'block';
                const target = window._pendingSection || (clientUnlocked ? 'pricing' : 'workflow-home');
                const targetEl = document.getElementById(target);
                if (targetEl) targetEl.classList.add('unlocked');
                showSection(target);
            }} else {{
                _failCount++;
                btn.disabled = false;
                btn.textContent = 'Enter';
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

        function startLockout() {{
            _lockedOut = true;
            const btn = document.getElementById('pw-btn');
            const input = document.getElementById('pw-input');
            const lockoutEl = document.getElementById('pw-lockout');
            const errorEl = document.getElementById('pw-error');
            btn.disabled = true;
            input.disabled = true;
            errorEl.style.display = 'none';
            lockoutEl.style.display = 'block';
            let remaining = 15;
            lockoutEl.textContent = `Too many attempts. Try again in ${{remaining}}s`;
            const timer = setInterval(() => {{
                remaining--;
                if (remaining <= 0) {{
                    clearInterval(timer);
                    _lockedOut = false;
                    _failCount = 0;
                    btn.disabled = false;
                    input.disabled = false;
                    lockoutEl.style.display = 'none';
                    input.focus();
                }} else {{
                    lockoutEl.textContent = `Too many attempts. Try again in ${{remaining}}s`;
                }}
            }}, 1000);
        }}

        function togglePasswordVisibility() {{
            const input = document.getElementById('pw-input');
            const icon = document.getElementById('eye-icon');
            if (input.type === 'password') {{
                input.type = 'text';
                icon.textContent = '🙈';
            }} else {{
                input.type = 'password';
                icon.textContent = '👁';
            }}
        }}

        function logout() {{
            // Clear all decrypted content from DOM
            [...CLIENT_SECTIONS, ...INTERNAL_SECTIONS].forEach(id => {{
                const el = document.getElementById(id);
                if (el) el.replaceChildren();
            }});
            location.reload();
        }}

        function updateClientLinks() {{
            // Show pricing/booking in sidebar
            document.querySelectorAll('.sidebar-link.client-link').forEach(link => {{
                link.style.display = 'block';
            }});
        }}

        function updateInternalLinks() {{
            // Show workflow block in sidebar
            const wfBlock = document.getElementById('wf-sidebar-block');
            if (wfBlock) wfBlock.style.display = 'block';
            document.querySelectorAll('.sidebar-link.internal-link').forEach(link => {{
                link.style.display = 'block';
            }});
        }}

        function updateLockIcon() {{
            const icon = document.getElementById('lock-icon');
            if (icon && (clientUnlocked || internalUnlocked)) {{
                icon.textContent = '🔓';
                icon.classList.add('unlocked');
            }}
        }}

        // Checklists - save/load from localStorage
        function saveChecklist() {{
            try {{
                const checks = {{}};
                document.querySelectorAll('#checklists input[type="checkbox"]').forEach(cb => {{
                    checks[cb.id] = cb.checked;
                }});
                localStorage.setItem('rsquare_checklists', JSON.stringify(checks));
            }} catch(e) {{ /* localStorage unavailable */ }}
        }}

        function loadChecklist() {{
            try {{
                const saved = localStorage.getItem('rsquare_checklists');
                if (saved) {{
                    const checks = JSON.parse(saved);
                    Object.entries(checks).forEach(([id, val]) => {{
                        const cb = document.getElementById(id);
                        if (cb) cb.checked = val;
                    }});
                }}
            }} catch(e) {{ /* localStorage unavailable */ }}
        }}

        function resetChecklists() {{
            try {{
                document.querySelectorAll('#checklists input[type="checkbox"]').forEach(cb => cb.checked = false);
                localStorage.removeItem('rsquare_checklists');
            }} catch(e) {{ /* localStorage unavailable */ }}
            showToast('Checklists reset!');
        }}

        function showToast(msg) {{
            const t = document.getElementById('toast');
            t.textContent = msg;
            t.classList.add('show');
            setTimeout(() => t.classList.remove('show'), 2500);
        }}

        function toggleSidebar() {{
            const sb = document.getElementById('sidebar');
            const ov = document.getElementById('sidebar-overlay');
            sb.classList.toggle('open');
            ov.classList.toggle('show');
        }}

        function closeSidebar() {{
            document.getElementById('sidebar').classList.remove('open');
            document.getElementById('sidebar-overlay').classList.remove('show');
        }}

        // Bottom nav handler
        function mobileNav(sectionId) {{
            showSection(sectionId);
            updateBottomNav(sectionId);
        }}

        function mobileNavProtected(sectionId) {{
            accessWorkflow(sectionId);
            if (clientUnlocked || internalUnlocked) {{
                updateBottomNav(sectionId);
            }}
        }}

        function updateBottomNav(sectionId) {{
            document.querySelectorAll('.bnav-item').forEach(b => b.classList.remove('active'));
            const tabMap = {{
                'home': 'bnav-home',
                'portfolio-home': 'bnav-portfolio',
                'pricing': 'bnav-pricing',
                'booking': 'bnav-booking',
                'contact': 'bnav-contact',
            }};
            const tabId = tabMap[sectionId];
            if (tabId) document.getElementById(tabId)?.classList.add('active');
        }}

        function updateQuote() {{
            const svcEl = document.getElementById('q-services');
            if (!svcEl || !_appConfig) return;
            const svcKey = svcEl.value;
            const svcText = (_appConfig.labelMap && _appConfig.labelMap[svcKey]) || svcKey;
            const hours = parseInt(document.getElementById('q-hours').value) || 0;
            const rate = (_appConfig.rateMap && _appConfig.rateMap[svcKey]) || 0;
            const liveCost = _appConfig.liveStreamingCost || 0;
            const live = document.getElementById('q-live').checked ? liveCost : 0;
            const total = (rate * hours) + live;
            document.getElementById('q-quote').value = total > 0 ? '$' + total.toLocaleString() : '';

            const name = document.getElementById('q-name').value || '___';
            const event = document.getElementById('q-event').value || '___';
            const location = document.getElementById('q-location').value || '___';
            const dateVal = document.getElementById('q-date').value;
            const shootType = document.getElementById('q-shoottype').value;
            const deposit = document.getElementById('q-deposit').value || '___';
            const hasLive = document.getElementById('q-live').checked;

            let dateDisplay = '___';
            if (dateVal) {{
                const d = new Date(dateVal + 'T12:00:00');
                dateDisplay = d.toLocaleDateString('en-US', {{ weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' }});
            }}

            const quote = total > 0 ? '$' + total.toLocaleString() : '___';

            // DOM-based quote builder (no innerHTML — safe from XSS)
            function qEl(tag, cls, text) {{
                const el = document.createElement(tag);
                if (cls) el.className = cls;
                if (text) el.textContent = text;
                return el;
            }}
            function qRow(label, value, style) {{
                const row = qEl('div', 'quote-row');
                row.appendChild(qEl('span', 'qlabel', label));
                const val = qEl('span', 'qvalue', value);
                if (style) val.style.color = style;
                row.appendChild(val);
                return row;
            }}
            function qSection(children) {{
                const sec = qEl('div', 'quote-section');
                children.forEach(c => sec.appendChild(c));
                return sec;
            }}

            const preview = document.getElementById('quote-preview');
            preview.replaceChildren();

            // Greeting
            const greetLine1 = document.createTextNode('Hey ' + name + '! 👋');
            const greetLine2 = document.createTextNode("Thanks for reaching out \u2014 here's the quote for your " + event.toLowerCase() + ":");
            const greetDiv = qEl('div', 'quote-greeting');
            greetDiv.appendChild(greetLine1);
            greetDiv.appendChild(document.createElement('br'));
            greetDiv.appendChild(greetLine2);
            preview.appendChild(qSection([greetDiv]));

            // Details
            const detailRows = [
                qEl('div', 'quote-section-title', 'Details'),
                qRow('Client', name),
                qRow('Event', event),
                qRow('Location', location),
                qRow('Date', dateDisplay),
                qRow('Setting', shootType),
                qRow('Coverage', svcText),
                qRow('Hours', String(hours || '___')),
            ];
            if (hasLive) detailRows.push(qRow('Live Streaming', 'Included', '#10b981'));
            preview.appendChild(qSection(detailRows));

            // Pricing
            const totalRow = qRow('Total', quote);
            totalRow.querySelector('.qvalue').classList.add('quote-total');
            preview.appendChild(qSection([
                qEl('div', 'quote-section-title', 'Pricing'),
                totalRow,
                qRow('Retainer', deposit),
                qEl('div', 'quote-note', 'Rest due on event day'),
            ]));

            // What You Get
            const whatNote = qEl('div', 'quote-note');
            whatNote.appendChild(document.createTextNode('\u2022 All edited pictures \u2014 ready in 12\u201315 days'));
            whatNote.appendChild(document.createElement('br'));
            whatNote.appendChild(document.createTextNode('\u2022 Cinematic teaser (4\u20136 min) \u2014 ready in 3\u20134 weeks'));
            preview.appendChild(qSection([qEl('div', 'quote-section-title', 'What You Get'), whatNote]));

            // How You Get Your Photos
            preview.appendChild(qSection([
                qEl('div', 'quote-section-title', 'How You Get Your Photos'),
                qEl('div', 'quote-note', "You'll get a private gallery link. Download all pics at once from desktop \u2014 email with the download link usually takes 15\u201330 min. Link works for 3 months so grab them soon!"),
            ]));

            // Signoff
            const signoff = qEl('div', 'quote-signoff');
            signoff.appendChild(document.createTextNode('Looking forward to it! 🙌'));
            signoff.appendChild(document.createElement('br'));
            signoff.appendChild(document.createTextNode('\u2014 Ram, Rsquare Studios'));
            preview.appendChild(qSection([signoff]));

            const text = `Hey ${{name}}! 👋
Thanks for reaching out — here's the quote for your ${{event.toLowerCase()}}:

*Details*
Client: ${{name}}
Event: ${{event}}
Location: ${{location}}
Date: ${{dateDisplay}}
Setting: ${{shootType}}
Coverage: ${{svcText}}
Hours: ${{hours || '___'}}${{hasLive ? '\\nLive Streaming: Yes (+$' + liveCost + ')' : ''}}

*Pricing*
Total: ${{quote}}
Retainer: ${{deposit}}
Rest due on event day

*What You Get*
• All edited pictures — ready in 12–15 days
• Cinematic teaser (4–6 min) — ready in 3–4 weeks

*How You Get Your Photos*
You'll get a private gallery link. Download all pics at once from desktop — email with the download link usually takes 15–30 min. Link works for 3 months so grab them soon!

Looking forward to it! 🙌
— Ram, Rsquare Studios`;

            document.getElementById('quote-preview').dataset.plaintext = text;
        }}

        function getQuoteText() {{
            const el = document.getElementById('quote-preview');
            return el ? (el.dataset.plaintext || el.textContent) : '';
        }}

        function copyQuote() {{
            const text = getQuoteText();
            navigator.clipboard.writeText(text).then(() => {{
                showToast('Quote copied to clipboard!');
            }}).catch(() => {{
                const ta = document.createElement('textarea');
                ta.value = text;
                document.body.appendChild(ta);
                ta.select();
                document.execCommand('copy');
                document.body.removeChild(ta);
                showToast('Quote copied!');
            }});
        }}

        function shareQuoteWA(e) {{
            e.preventDefault();
            const text = getQuoteText();
            const encoded = encodeURIComponent(text);
            const waUrl = 'https://wa.me/?text=' + encoded;
            if (isAllowedUrl(waUrl)) window.open(waUrl, '_blank');
            const conf = document.getElementById('booking-confirmation');
            if (conf) conf.style.display = 'block';
        }}

        /* Review form submission */
        function submitReview(e) {{
            e.preventDefault();
            const url = _appConfig ? _appConfig.reviewFormUrl : '';
            if (!url) {{
                document.getElementById('review-error').textContent = 'Review submissions are not yet configured.';
                document.getElementById('review-error').style.display = 'block';
                return;
            }}
            const btn = document.getElementById('rv-submit');
            const errEl = document.getElementById('review-error');
            errEl.style.display = 'none';
            btn.disabled = true;
            btn.textContent = 'Submitting...';

            const data = {{
                name: document.getElementById('rv-name').value.trim(),
                event_type: document.getElementById('rv-event').value,
                rating: document.getElementById('rv-rating').value,
                review: document.getElementById('rv-text').value.trim()
            }};

            var formBody = new URLSearchParams();
            formBody.append('name', data.name);
            formBody.append('event_type', data.event_type);
            formBody.append('rating', data.rating);
            formBody.append('review', data.review);

            fetch(url, {{
                method: 'POST',
                body: formBody
            }}).then(function(resp) {{
                document.getElementById('review-form').style.display = 'none';
                document.getElementById('review-success').style.display = 'block';
            }}).catch(function(err) {{
                errEl.textContent = 'Something went wrong. Please try again.';
                errEl.style.display = 'block';
                btn.disabled = false;
                btn.textContent = 'Submit Review';
            }});
        }}

        /* ── Event listeners (CSP-compliant — no inline handlers) ── */
        /* Registered BEFORE loadChecklist/star-rating to ensure clicks work
           even if localStorage throws SecurityError in strict browsers */

        // Group 1: Static buttons with IDs
        document.getElementById('logout-btn').addEventListener('click', logout);
        document.getElementById('pw-btn').addEventListener('click', checkPassword);
        document.getElementById('pw-eye-btn').addEventListener('click', togglePasswordVisibility);
        document.getElementById('mobile-toggle').addEventListener('click', toggleSidebar);
        document.getElementById('sidebar-overlay').addEventListener('click', closeSidebar);
        document.getElementById('gear-toggle').addEventListener('click', toggleGear);
        document.getElementById('private-gate-link').addEventListener('click', function(e) {{
            e.preventDefault();
            showPrivateGate();
        }});
        document.getElementById('pw-input').addEventListener('keydown', function(e) {{
            if (e.key === 'Enter') checkPassword();
        }});

        // Review form
        var reviewForm = document.getElementById('review-form');
        if (reviewForm) reviewForm.addEventListener('submit', submitReview);

        // Reset checklists (inside encrypted content — bind after decryption too)
        var resetBtn = document.getElementById('reset-checklists-btn');
        if (resetBtn) resetBtn.addEventListener('click', resetChecklists);

        // Group 2: Navigation via data-section (delegated)
        document.addEventListener('click', function(e) {{
            var target = e.target.closest('[data-section]');
            if (target) {{
                e.preventDefault();
                showSection(target.getAttribute('data-section'));
            }}
        }});

        // Group 3: Protected nav via data-access (delegated)
        document.addEventListener('click', function(e) {{
            var target = e.target.closest('[data-access]');
            if (target) {{
                e.preventDefault();
                accessWorkflow(target.getAttribute('data-access'));
            }}
        }});

        // Group 4: Bottom nav via data-nav / data-nav-protected (delegated)
        document.addEventListener('click', function(e) {{
            var target = e.target.closest('[data-nav]');
            if (target) {{
                mobileNav(target.getAttribute('data-nav'));
                return;
            }}
            target = e.target.closest('[data-nav-protected]');
            if (target) {{
                mobileNavProtected(target.getAttribute('data-nav-protected'));
            }}
        }});

        // Group 5: Quote builder inputs
        document.querySelectorAll('[data-quote-input]').forEach(function(el) {{
            var eventType = (el.tagName === 'SELECT' || el.type === 'checkbox') ? 'change' : 'input';
            el.addEventListener(eventType, updateQuote);
        }});

        // Group 6: Copy quote + Share WA (inside encrypted content — bind after decryption too)
        var copyBtn = document.getElementById('copy-quote-btn');
        if (copyBtn) copyBtn.addEventListener('click', copyQuote);
        var waBtn = document.getElementById('wa-share-btn');
        if (waBtn) waBtn.addEventListener('click', function(e) {{ shareQuoteWA(e); }});

        // Group 7: Checklist checkboxes (delegated — works after decryption injects them)
        document.addEventListener('change', function(e) {{
            if (e.target.matches && e.target.matches('input[data-checklist]')) saveChecklist();
        }});

        // Re-bind listeners after encrypted content injection
        var _origInject = injectDecryptedContent;
        injectDecryptedContent = function(sections) {{
            _origInject(sections);
            // Re-bind elements that may have been injected
            var resetBtn2 = document.getElementById('reset-checklists-btn');
            if (resetBtn2) resetBtn2.addEventListener('click', resetChecklists);
            var copyBtn2 = document.getElementById('copy-quote-btn');
            if (copyBtn2) copyBtn2.addEventListener('click', copyQuote);
            var waBtn2 = document.getElementById('wa-share-btn');
            if (waBtn2) waBtn2.addEventListener('click', function(e) {{ shareQuoteWA(e); }});
            // Re-bind quote builder inputs
            document.querySelectorAll('[data-quote-input]').forEach(function(el) {{
                var eventType = (el.tagName === 'SELECT' || el.type === 'checkbox') ? 'change' : 'input';
                el.addEventListener(eventType, updateQuote);
            }});
        }};

        /* ── Post-listener initialization ── */

        // Auto-unlock via query params: ?k=<password>&t=<unix_timestamp>
        // Link expires after 10 minutes from the timestamp
        // Uses query params (not hash) so Slack/WhatsApp preserve the full URL
        (function() {{
            var params = new URLSearchParams(window.location.search);
            var key = params.get('k');
            if (!key) return;
            // Check expiry
            var t = params.get('t');
            if (t) {{
                var created = parseInt(t, 10);
                var now = Math.floor(Date.now() / 1000);
                if (now - created > 48 * 3600) {{
                    // Clear params and show expired message
                    history.replaceState(null, '', window.location.pathname);
                    showToast('This link has expired. Please request a new one.');
                    return;
                }}
            }}
            // Clear query params from URL bar (keeps it clean, no password visible)
            history.replaceState(null, '', window.location.pathname);
            // Auto-decrypt with the provided key
            (async function() {{
                // Try client blob
                if (!clientUnlocked) {{
                    try {{
                        var plaintext = await decryptContent(key, ENCRYPTED_CLIENT);
                        var sections = JSON.parse(plaintext);
                        injectDecryptedContent(sections);
                        clientUnlocked = true;
                        updateClientLinks();
                    }} catch(e) {{ /* not client password */ }}
                }}
                // Try internal blob (also unlocks client via admin blob)
                if (!internalUnlocked) {{
                    try {{
                        var plaintext = await decryptContent(key, ENCRYPTED_INTERNAL);
                        var sections = JSON.parse(plaintext);
                        injectDecryptedContent(sections);
                        internalUnlocked = true;
                        updateInternalLinks();
                        if (!clientUnlocked) {{
                            try {{
                                var clientPlain = await decryptContent(key, ENCRYPTED_CLIENT_ADMIN);
                                var clientSections = JSON.parse(clientPlain);
                                injectDecryptedContent(clientSections);
                                clientUnlocked = true;
                                updateClientLinks();
                            }} catch(e2) {{ /* ok */ }}
                        }}
                    }} catch(e) {{ /* not internal password */ }}
                }}
                if (clientUnlocked || internalUnlocked) {{
                    updateLockIcon();
                    document.getElementById('logout-btn').style.display = 'block';
                    var landing = params.get('s') || 'pricing';
                    showSection(landing);
                }}
            }})();
        }})();

        // Load checklists (after event listeners, safe if localStorage unavailable)
        loadChecklist();

        /* Star rating widget */
        (function() {{
            const container = document.getElementById('star-rating');
            if (!container) return;
            const stars = container.querySelectorAll('.star');
            const input = document.getElementById('rv-rating');
            function setRating(val) {{
                input.value = val;
                stars.forEach(function(s) {{
                    s.classList.toggle('active', parseInt(s.dataset.value) === val);
                }});
            }}
            stars.forEach(function(s) {{
                s.addEventListener('click', function() {{
                    setRating(parseInt(s.dataset.value));
                }});
            }});
            setRating(5);
        }})();

    </script>
</body>
</html>"""
    return html


def main():
    print(f"\n{'='*60}")
    print("  📷 Rsquare Studios Dashboard Generator")
    print(f"{'='*60}\n")

    print("📸 Loading galleries...")
    galleries = load_galleries()
    total = sum(len(v) for v in galleries.values())
    print(f"   Found {total} galleries across {len(galleries)} categories")

    print("📖 Loading posing guides...")
    guides = load_posing_guides()
    print(f"   Found {len(guides)} guides")

    print("📋 Loading workflow reference...")
    workflow = load_workflow()
    print(f"   {'Loaded' if workflow else 'Not found'}")

    print("\n🔨 Generating Notion-style dashboard...")
    html = generate_html()

    print(f"💾 Saving to {OUTPUT_FILE.name}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n🌐 Opening in browser...")
    webbrowser.open(f"file://{OUTPUT_FILE}")

    print(f"\n{'='*60}")
    print("  ✅ Dashboard Ready!")
    print(f"{'='*60}")
    print(f"\n  📄 File: {OUTPUT_FILE}")
    print(f"  🌐 Run `python3 generate_dashboard.py` to regenerate")
    print(f"  🔑 Passwords loaded from .secret file\n")


if __name__ == "__main__":
    main()
