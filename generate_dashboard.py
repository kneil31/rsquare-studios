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
import hashlib
import webbrowser
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
OUTPUT_FILE = SCRIPT_DIR / "index.html"
GALLERIES_FILE = SCRIPT_DIR.parent / "rsqr_whatsapp_api" / "smugmug_galleries.json"
WORKFLOW_FILE = SCRIPT_DIR.parent.parent / "photo_workflow" / "PHOTO_WORKFLOW_CHEATSHEET.md"
POSING_DIR = SCRIPT_DIR.parent.parent.parent / "Upskill" / "Posing_Upskill" / "prompts"
TWOMANN_DIR = SCRIPT_DIR.parent / "TwoMann_Course" / "chapters"

# Password hash for internal section (SHA-256 of the password)
# Default password: "rsquare2026"
PASSWORD_HASH = hashlib.sha256("rsquare2026".encode()).hexdigest()


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
        "wedding": ("https://photos.smugmug.com/photos/i-BvTChsc/0/LwhGTh2B2pCPDgNpjPJp8J3nCSfRNdKwd3j5CVTKN/X3/i-BvTChsc-X3.jpg", "center center"),
        "engagement": ("https://photos.smugmug.com/photos/i-8NfsLKT/0/LVnhsbXXV3JPcX2r2PhvcKfCj9gK9czpWsZ2VXrSH/X3/i-8NfsLKT-X3.jpg", "center center"),
        "pre_wedding": ("https://photos.smugmug.com/photos/i-GfR24FT/0/MHQbxRCTTvn8x7WXCkzHRjCWR96TC6TnBsTfQRFQ7/X3/i-GfR24FT-X3.jpg", "center center"),
        "half_saree": ("https://photos.smugmug.com/photos/i-MCmGphP/0/NZvk2KBMQzVZvJJTQh23xdmRRsvzNzGRdBgx2HX66/X3/i-MCmGphP-X3.jpg", "center center"),
        "maternity": ("https://photos.smugmug.com/photos/i-ZqWs3n5/0/NcPVRqqFJXR3MJfcVn45gshTHXpxkZFvfv655D3mB/X3/i-ZqWs3n5-X3.jpg", "center 15%"),
        "baby_shower": ("https://photos.smugmug.com/photos/i-3MjgbV3/0/NWkJRQPLmfwjxBJ2qLpKLS2RHVpb39NtfssFhZJxp/X3/i-3MjgbV3-X3.jpg", "center 25%"),
        "birthday": ("https://photos.smugmug.com/photos/i-Xq8BHgp/0/NGnrqRVd9gkP3r8gdC8BdwN2WrLPJT4MpQ594MTwF/X3/i-Xq8BHgp-X3.jpg", "center center"),
        "cradle": ("https://photos.smugmug.com/photos/i-R3QTwKk/0/KzsCGkHgZ6HKmVjVtFvwkWF9s9sRzMSTQWKPJfxQb/X3/i-R3QTwKk-X3.jpg", "center center"),
        "celebrations": ("https://photos.smugmug.com/photos/i-MPN69Q3/0/LGSxZbpLfpcb7j3kqQkkTdfwDHcJbV6XdxnGNq6Hb/X3/i-MPN69Q3-X3.jpg", "center center"),
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
            demo_styles = {"wedding": "monogram", "cradle": "monogram", "engagement": "monogram", "half_saree": "monogram", "celebrations": "monogram", "maternity": "date", "birthday": "date", "baby_shower": "line", "pre_wedding": "line"}
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
                <a href="{escape_html(url)}" target="_blank" rel="noopener" class="{card_class}">
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
        }
    return cards_by_category


def build_pricing_section():
    """Build pricing cards with professional photographer language."""
    html = """
            <!-- Solo -->
            <div class="pricing-card" style="--accent: #8b5cf6;">
                <div class="pricing-header">
                    <span class="pricing-icon">📷</span>
                    <span class="pricing-name">Solo</span>
                </div>
                <div class="price-tier">
                    <div class="tier-header">
                        <span class="tier-name">Photo Only</span>
                        <span class="tier-price">$150<span style="font-size:13px;font-weight:400;color:#6b7280;">/hr</span></span>
                    </div>
                    <div class="tier-details">Just me and my camera</div>
                </div>
                <div class="price-tier">
                    <div class="tier-header">
                        <span class="tier-name">Photo + Video</span>
                        <span class="tier-price">$235<span style="font-size:13px;font-weight:400;color:#6b7280;">/hr</span></span>
                    </div>
                    <div class="tier-details">I shoot both photo and video &mdash; great for smaller events</div>
                </div>
            </div>

            <!-- Dual -->
            <div class="pricing-card" style="--accent: #3b82f6;">
                <div class="pricing-header">
                    <span class="pricing-icon">📷&thinsp;📹</span>
                    <span class="pricing-name">Dual</span>
                </div>
                <div class="price-tier">
                    <div class="tier-header">
                        <span class="tier-name">Photo + Video</span>
                        <span class="tier-price">$325<span style="font-size:13px;font-weight:400;color:#6b7280;">/hr</span></span>
                    </div>
                    <div class="tier-details">Me on photos, videographer on video &mdash; nothing gets missed</div>
                </div>
            </div>

            <!-- Live -->
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
                <a class="back-link" href="#" onclick="showSection('workflow-home'); return false;">&larr; Back to Workflow</a>
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
        links += f'<a href="#{section_id}" class="sidebar-link sub-link" onclick="showSection(\'{section_id}\')">{short}</a>\n'
    return links


def build_twomann_pages(chapters):
    html = ""
    for i, ch in enumerate(chapters):
        section_id = f"twomann-{i}"
        converted = md_to_html_simple(ch["content"])
        html += f"""
            <div class="page" id="{section_id}">
                <a class="back-link" href="#" onclick="showSection('workflow-home'); return false;">&larr; Back to Workflow</a>
                <div class="page-breadcrumb">TwoMann Course &middot; Chapter {i + 1} of {len(chapters)}</div>
                <h1 class="page-title">{escape_html(ch['title'])}</h1>
                <div class="wf-content">{converted}</div>
            </div>"""
    return html


def generate_html():
    now = datetime.now().strftime("%b %d, %Y")

    # Load data
    galleries = load_galleries()
    gallery_cards = build_gallery_cards(galleries)
    pricing_html = build_pricing_section()
    posing_guides = load_posing_guides()
    posing_pages = build_posing_html(posing_guides)
    workflow_md = load_workflow()
    workflow_html = md_to_html_simple(workflow_md)
    total_galleries = sum(c["count"] for c in gallery_cards.values())

    # Build sidebar gallery links
    gallery_sidebar = ""
    for cat, info in gallery_cards.items():
        gallery_sidebar += f'<a href="#portfolio-{cat}" class="sidebar-link" onclick="showSection(\'portfolio-{cat}\')">{info["icon"]} {info["label"]} ({info["count"]})</a>\n'

    # Build portfolio category pages
    portfolio_pages = ""
    for cat, info in gallery_cards.items():
        portfolio_pages += f"""
            <div class="page gallery-page-wrap" id="portfolio-{cat}">
                <div class="gallery-backdrop" style="background-image:url('{info['cover']}')"></div>
                <a class="back-link" href="#" onclick="showSection('portfolio-home'); return false;">&larr; Back to Portfolio</a>
                <div class="cat-hero" style="background-image:url('{info['cover']}');background-position:{info['cover_pos']}">
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
        posing_sidebar += f'<a href="#{sid}" class="sidebar-link sub-link" onclick="showSection(\'{sid}\')">{name}</a>\n'

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

    def checklist_html(items, list_id):
        html = ""
        for i, item in enumerate(items):
            html += f"""
                <label class="check-item" for="{list_id}-{i}">
                    <input type="checkbox" id="{list_id}-{i}" onchange="saveChecklist()">
                    <span>{item}</span>
                </label>"""
        return html

    pre_html = checklist_html(pre_shoot_items, "pre")
    dayof_html = checklist_html(day_of_items, "day")
    post_html = checklist_html(post_shoot_items, "post")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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

        /* Hero */
        .hero {{
            position: relative;
            text-align: center;
            padding: 80px 20px 60px;
            background: url('https://photos.smugmug.com/photos/i-VqnMPLz/0/KG7kc3wMPKBWdFkVhTsWfp4LJQCNzQkxK4ww4DZJv/X3/i-VqnMPLz-X3.jpg') center center / cover no-repeat;
            border-radius: 16px;
            margin: 0 16px 24px;
            overflow: hidden;
        }}
        .hero::before {{
            content: '';
            position: absolute;
            inset: 0;
            background: linear-gradient(180deg, rgba(0,0,0,0.4) 0%, rgba(0,0,0,0.65) 100%);
            z-index: 0;
        }}
        .hero > * {{
            position: relative;
            z-index: 1;
        }}
        .hero-logo {{
            font-size: 48px;
            margin-bottom: 12px;
        }}
        .hero h1 {{
            font-size: 36px;
            font-weight: 800;
            color: #fff;
            margin-bottom: 8px;
            letter-spacing: -1px;
            text-shadow: 0 2px 8px rgba(0,0,0,0.4);
        }}
        .hero p {{
            font-size: 16px;
            color: #d1d5db;
            max-width: 500px;
            margin: 0 auto 32px;
            line-height: 1.6;
            text-shadow: 0 1px 4px rgba(0,0,0,0.5);
        }}
        .hero-stats {{
            display: flex;
            justify-content: center;
            gap: 40px;
            margin-bottom: 32px;
        }}
        .hero-stat {{
            text-align: center;
        }}
        .hero-stat .number {{
            font-size: 28px;
            font-weight: 700;
            color: #c4b5fd;
            text-shadow: 0 1px 4px rgba(0,0,0,0.5);
        }}
        .hero-stat .label {{
            font-size: 12px;
            color: #d1d5db;
            letter-spacing: 0.5px;
            margin-top: 4px;
            text-shadow: 0 1px 2px rgba(0,0,0,0.5);
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
            box-shadow: 0 4px 12px rgba(139,92,246,0.4);
        }}
        .hero-cta:hover {{ background: #7c3aed; }}
        .hero-scroll-hint {{
            margin-top: 24px;
            font-size: 12px;
            color: rgba(255,255,255,0.4);
            letter-spacing: 1px;
            text-transform: uppercase;
            animation: bounce 2s infinite;
        }}
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
            position: relative;
            border-radius: 12px;
            padding: 0;
            text-align: center;
            cursor: pointer;
            transition: transform 0.15s, box-shadow 0.2s;
            text-decoration: none;
            color: inherit;
            overflow: hidden;
            aspect-ratio: 3/4;
            display: flex;
            align-items: flex-end;
            background-size: cover;
            background-position: center;
        }}
        .cat-tile::before {{
            content: '';
            position: absolute;
            inset: 0;
            background: linear-gradient(180deg, transparent 30%, rgba(0,0,0,0.75) 100%);
            z-index: 0;
        }}
        .cat-tile:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 24px rgba(139,92,246,0.25);
        }}
        .cat-tile-content {{
            position: relative;
            z-index: 1;
            padding: 16px 20px;
            width: 100%;
            text-align: left;
        }}
        .cat-icon {{ display: none; }}
        .cat-name {{ font-size: 18px; font-weight: 700; color: #fff; margin-bottom: 2px; text-shadow: 0 1px 4px rgba(0,0,0,0.6); }}
        .cat-count {{ font-size: 13px; color: #d1d5db; text-shadow: 0 1px 2px rgba(0,0,0,0.5); }}

        /* Category hero banner */
        .cat-hero {{
            position: relative;
            border-radius: 16px;
            overflow: hidden;
            height: 200px;
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
        .pw-input {{
            padding: 10px 16px;
            background: #202020;
            border: 1px solid #2d2d2d;
            border-radius: 8px;
            color: #e0e0e0;
            font-size: 15px;
            outline: none;
            width: 260px;
            text-align: center;
        }}
        .pw-input:focus {{ border-color: #8b5cf6; }}
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
        .pw-error {{
            color: #ef4444;
            font-size: 13px;
            margin-top: 12px;
            display: none;
        }}

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

            /* Hero mobile — full screen */
            .hero {{
                min-height: calc(100vh - 70px);
                margin: 0;
                border-radius: 0;
                padding: 0 24px;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                background-image: url('https://photos.smugmug.com/photos/i-VqnMPLz/0/Kd2nZQ6mNq7gxWCvG9bnXfk4xpp9JSX64npLRHHNV/XL/i-VqnMPLz-XL.jpg');
            }}
            .hero-logo {{ font-size: 44px; margin-bottom: 16px; }}
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
                gap: 28px;
                margin-bottom: 28px;
            }}
            .hero-stat .number {{ font-size: 26px; }}
            .hero-cta {{
                padding: 16px 40px;
                font-size: 16px;
                border-radius: 10px;
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
            .cat-tile {{
                aspect-ratio: 16/9;
            }}
            .cat-tile-content {{
                padding: 10px 12px;
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

            /* Booking form mobile */
            .form-row-inline {{ grid-template-columns: 1fr; }}
            .btn-row {{ flex-direction: column; }}
            .copy-btn, .share-wa-btn {{ width: 100%; justify-content: center; padding: 14px; }}
            .proscons {{ grid-template-columns: 1fr; }}

            /* Password gate */
            .pw-gate {{ padding: 40px 16px; }}
            .pw-input {{ width: 100%; max-width: 260px; font-size: 16px; padding: 12px 16px; }}
            .pw-btn {{ margin-left: 0; margin-top: 12px; display: block; width: 100%; max-width: 260px; padding: 14px; font-size: 16px; }}
            .pw-gate > div {{ display: flex; flex-direction: column; align-items: center; }}

            /* Workflow content */
            .wf-content {{ font-size: 15px; }}
            .wf-content .wf-table {{ font-size: 12px; display: block; overflow-x: auto; }}
            .wf-code {{ font-size: 12px; }}
            .back-link {{ font-size: 14px; padding: 8px 0; }}
        }}

        /* Small phones */
        @media (max-width: 380px) {{
            .cat-grid {{ grid-template-columns: 1fr; }}
            .hero-stats {{ flex-wrap: wrap; gap: 16px; }}
            .wf-tile-grid {{ grid-template-columns: 1fr; }}
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
    </style>
</head>
<body>
    <button class="mobile-toggle" onclick="toggleSidebar()">&#9776;</button>
    <div class="sidebar-overlay" id="sidebar-overlay" onclick="closeSidebar()"></div>

    <!-- WhatsApp floating button -->
    <a href="https://wa.me/15307278598?text=Hi%20Ram!%20I%27m%20interested%20in%20a%20photography%20session." class="wa-float" target="_blank" rel="noopener" aria-label="Chat on WhatsApp">
        <svg viewBox="0 0 24 24"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
    </a>

    <!-- Bottom nav (mobile) -->
    <nav class="bottom-nav">
        <div class="bottom-nav-inner">
            <div class="bnav-item active" onclick="mobileNav('home')" id="bnav-home">
                <span class="bnav-icon">🏠</span>
                Home
            </div>
            <div class="bnav-item" onclick="mobileNav('portfolio-home')" id="bnav-portfolio">
                <span class="bnav-icon">📸</span>
                Portfolio
            </div>
            <div class="bnav-item" onclick="mobileNavProtected('pricing')" id="bnav-pricing">
                <span class="bnav-icon">💰</span>
                Pricing
            </div>
            <div class="bnav-item" onclick="mobileNavProtected('booking')" id="bnav-booking">
                <span class="bnav-icon">📋</span>
                Book
            </div>
            <div class="bnav-item" onclick="mobileNav('contact')" id="bnav-contact">
                <span class="bnav-icon">📞</span>
                Contact
            </div>
        </div>
    </nav>

    <div class="layout">
        <!-- Sidebar -->
        <div class="sidebar" id="sidebar">
            <div class="sidebar-brand">📷 <span>Rsquare Studios</span></div>

            <a class="sidebar-link" onclick="showSection('home')">🏠 Home</a>

            <div class="sidebar-divider"></div>
            <div class="sidebar-section-label">PORTFOLIO</div>
            <a class="sidebar-link" onclick="showSection('portfolio-home')">📸 All Categories</a>
            <a class="sidebar-link" onclick="showSection('videos')">🎬 Videos</a>
            {gallery_sidebar}

            <div class="sidebar-divider"></div>
            <div class="sidebar-section-label" id="wf-section-label">
                <span class="lock-icon" id="lock-icon">🔒</span> PRIVATE
            </div>
            <a class="sidebar-link wf-link" onclick="accessWorkflow('pricing')">💰 Pricing</a>
            <a class="sidebar-link wf-link" onclick="accessWorkflow('booking')">📋 Book / Get Quote</a>
            <div class="sidebar-section-label wf-link" style="padding-top:8px">WORKFLOW
            </div>
            <a class="sidebar-link wf-link" onclick="accessWorkflow('workflow-home')">📋 Dashboard</a>
            <a class="sidebar-link wf-link" onclick="accessWorkflow('checklists')">✅ Checklists</a>
            <a class="sidebar-link wf-link" onclick="accessWorkflow('workflow-ref')">📖 Workflow Reference</a>

            <div class="sidebar-section-label wf-link" style="padding-top:8px">POSING GUIDES</div>
            {posing_sidebar.replace('class="sidebar-link sub-link"', 'class="sidebar-link sub-link wf-link"')}



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
                    <div class="hero-logo">📷</div>
                    <h1>Rsquare Studios</h1>
                    <p>Wedding &amp; event photography in DFW. Photos and videos that actually look like you.</p>
                    <div class="hero-stats">
                        <div class="hero-stat">
                            <div class="number">{total_galleries}+</div>
                            <div class="label">GALLERIES</div>
                        </div>
                        <div class="hero-stat">
                            <div class="number">5+</div>
                            <div class="label">YEARS</div>
                        </div>
                        <div class="hero-stat">
                            <div class="number">100+</div>
                            <div class="label">WEDDINGS</div>
                        </div>
                    </div>
                    <a href="#" class="hero-cta" onclick="showSection('portfolio-home'); return false;">View Portfolio</a>
                </div>
            </div>

            <!-- PORTFOLIO HOME -->
            <div class="page" id="portfolio-home">
                <div class="page-breadcrumb">Portfolio</div>
                <h1 class="page-title">Portfolio</h1>
                <div class="page-meta">{total_galleries} galleries &middot; Tap any category to browse</div>
                <div class="cat-grid">
                    {"".join(f'''
                    <div class="cat-tile" onclick="showSection('portfolio-{cat}')" style="background-image:url('{info['cover']}');background-position:{info['cover_pos']}">
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
                <a class="back-link" href="#" onclick="showSection('portfolio-home'); return false;">&larr; Back to Portfolio</a>
                <div class="page-breadcrumb">Portfolio</div>
                <h1 class="page-title">Videos</h1>
                <div class="page-meta">Highlight reels and cinematic teasers from our events</div>
                <div class="video-grid">
                    <a href="https://www.youtube.com/watch?v=ATyq7m_gLtY" target="_blank" rel="noopener" class="video-card">
                        <div class="video-thumb" style="background-image:url('https://img.youtube.com/vi/ATyq7m_gLtY/hqdefault.jpg')">
                            <div class="video-play">&#9654;</div>
                            <div class="video-duration">3:25</div>
                        </div>
                        <div class="video-title">Rashmi Baby Shower</div>
                    </a>
                    <a href="https://www.youtube.com/watch?v=B4WH92E3ov4" target="_blank" rel="noopener" class="video-card">
                        <div class="video-thumb" style="background-image:url('https://img.youtube.com/vi/B4WH92E3ov4/hqdefault.jpg')">
                            <div class="video-play">&#9654;</div>
                            <div class="video-duration">6:39</div>
                        </div>
                        <div class="video-title">ShravArt's Housewarming</div>
                    </a>
                    <a href="https://www.youtube.com/watch?v=oZSifwJn6MI" target="_blank" rel="noopener" class="video-card">
                        <div class="video-thumb" style="background-image:url('https://img.youtube.com/vi/oZSifwJn6MI/hqdefault.jpg')">
                            <div class="video-play">&#9654;</div>
                            <div class="video-duration">3:42</div>
                        </div>
                        <div class="video-title">Mounika Baby Shower</div>
                    </a>
                    <a href="https://www.youtube.com/watch?v=7IqxKNLrtaI" target="_blank" rel="noopener" class="video-card">
                        <div class="video-thumb" style="background-image:url('https://img.youtube.com/vi/7IqxKNLrtaI/hqdefault.jpg')">
                            <div class="video-play">&#9654;</div>
                            <div class="video-duration">4:59</div>
                        </div>
                        <div class="video-title">Andrilla Sweet 16 Birthday</div>
                    </a>
                    <a href="https://www.youtube.com/watch?v=XksmtJX71Ao" target="_blank" rel="noopener" class="video-card">
                        <div class="video-thumb" style="background-image:url('https://img.youtube.com/vi/XksmtJX71Ao/hqdefault.jpg')">
                            <div class="video-play">&#9654;</div>
                            <div class="video-duration">6:08</div>
                        </div>
                        <div class="video-title">Krithi Half Saree Ceremony</div>
                    </a>
                    <a href="https://www.youtube.com/watch?v=iNklzAP3JNo" target="_blank" rel="noopener" class="video-card">
                        <div class="video-thumb" style="background-image:url('https://img.youtube.com/vi/iNklzAP3JNo/hqdefault.jpg')">
                            <div class="video-play">&#9654;</div>
                            <div class="video-duration">1:36</div>
                        </div>
                        <div class="video-title">Ranjith Pinky Gender Reveal</div>
                    </a>
                    <a href="https://www.youtube.com/watch?v=lS1BdiEk3Pg" target="_blank" rel="noopener" class="video-card">
                        <div class="video-thumb" style="background-image:url('https://img.youtube.com/vi/lS1BdiEk3Pg/hqdefault.jpg')">
                            <div class="video-play">&#9654;</div>
                            <div class="video-duration">4:43</div>
                        </div>
                        <div class="video-title">Vasundhra Baby Shower</div>
                    </a>
                    <a href="https://www.youtube.com/watch?v=vuSREP1Srgc" target="_blank" rel="noopener" class="video-card">
                        <div class="video-thumb" style="background-image:url('https://img.youtube.com/vi/vuSREP1Srgc/hqdefault.jpg')">
                            <div class="video-play">&#9654;</div>
                            <div class="video-duration">6:34</div>
                        </div>
                        <div class="video-title">Sarayu Mihira's Sweet 16</div>
                    </a>
                    <a href="https://www.youtube.com/watch?v=1g4y62tnHqQ" target="_blank" rel="noopener" class="video-card">
                        <div class="video-thumb" style="background-image:url('https://img.youtube.com/vi/1g4y62tnHqQ/hqdefault.jpg')">
                            <div class="video-play">&#9654;</div>
                            <div class="video-duration">4:07</div>
                        </div>
                        <div class="video-title">Our Little Miracle Is On The Way</div>
                    </a>
                    <a href="https://www.youtube.com/watch?v=7OuNc5YJh48" target="_blank" rel="noopener" class="video-card">
                        <div class="video-thumb" style="background-image:url('https://img.youtube.com/vi/7OuNc5YJh48/hqdefault.jpg')">
                            <div class="video-play">&#9654;</div>
                            <div class="video-duration">3:12</div>
                        </div>
                        <div class="video-title">Keerthi's Half Saree Ceremony</div>
                    </a>
                </div>
                <div style="margin-top:20px; text-align:center;">
                    <a href="https://www.youtube.com/@rsquarestudios" target="_blank" rel="noopener" style="color:#8b5cf6; text-decoration:none; font-size:14px;">View all on YouTube &rarr;</a>
                </div>
            </div>

            <!-- PRICING -->
            <div class="page" id="pricing">
                <div class="page-breadcrumb">Pricing</div>
                <h1 class="page-title">Pricing</h1>
                <div class="page-meta">Hourly rates. No packages, no hidden stuff. You pay for what you need.</div>
                <div class="pricing-grid">
                    {pricing_html}
                </div>

                <div class="includes-box">
                    <h3>What's Included</h3>
                    <div class="includes-list">
                        <span>&#10003; All edited photos &mdash; usually ready in 12&ndash;15 days</span>
                        <span>&#10003; Cinematic highlight video (4&ndash;6 min)</span>
                        <span>&#10003; Online gallery &mdash; download, share, print</span>
                        <span>&#10003; Full print rights &mdash; print anywhere you want</span>
                    </div>
                </div>


                <!-- Solo vs Dual comparison -->
                <div style="margin-top:28px;">
                    <h3 style="font-size:16px; font-weight:700; color:#fff; margin-bottom:4px;">Solo or Dual &mdash; which one do you need?</h3>
                    <div class="proscons">
                        <div class="proscons-col" style="border:1px solid #2d4a2d;">
                            <h4 style="color:#10b981;">Solo</h4>
                            <ul>
                                <li>&#10003; Easier on the budget</li>
                                <li>&#10003; I handle both photo and video &mdash; ceremony, portraits, reception, all covered</li>
                                <li style="color:#6b7280; font-style:italic; margin-top:6px;">Good for: birthdays, baby showers, smaller events</li>
                            </ul>
                        </div>
                        <div class="proscons-col" style="border:1px solid #2d3a5e;">
                            <h4 style="color:#3b82f6;">Dual</h4>
                            <ul>
                                <li>&#10003; Two people, two angles &mdash; nothing gets missed</li>
                                <li>&#10003; Way more candid shots and guest moments</li>
                                <li>&#10003; Better highlight video with dedicated video guy</li>
                                <li style="color:#6b7280; font-style:italic; margin-top:6px;">Go with this for: weddings, 100+ guests, multi-spot events</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <div style="margin-top:24px; text-align:center;">
                    <button class="copy-btn" onclick="showSection('booking')" style="background:#8b5cf6;">Request a Quote</button>
                </div>
            </div>

            <!-- BOOKING -->
            <div class="page" id="booking">
                <div class="page-breadcrumb">Book</div>
                <h1 class="page-title">Request a Quote</h1>
                <div class="page-meta">Fill in your details and I'll send you a quote on WhatsApp.</div>

                <div class="book-form" id="book-form">
                    <div class="form-row">
                        <label class="form-label">CLIENT NAME</label>
                        <input class="form-input" id="q-name" placeholder="Full name" oninput="updateQuote()">
                    </div>
                    <div class="form-row">
                        <label class="form-label">EVENT</label>
                        <input class="form-input" id="q-event" placeholder="e.g. Wedding, Birthday, Maternity" oninput="updateQuote()">
                    </div>
                    <div class="form-row">
                        <label class="form-label">LOCATION</label>
                        <input class="form-input" id="q-location" placeholder="Venue name or city" oninput="updateQuote()">
                    </div>
                    <div class="form-row-inline">
                        <div class="form-row">
                            <label class="form-label">DATE</label>
                            <input class="form-input" id="q-date" type="date" oninput="updateQuote()">
                        </div>
                        <div class="form-row">
                            <label class="form-label">HOURS OF COVERAGE</label>
                            <input class="form-input" id="q-hours" type="number" min="1" placeholder="Hours" oninput="updateQuote()">
                        </div>
                    </div>
                    <div class="form-row-inline">
                        <div class="form-row">
                            <label class="form-label">SETTING</label>
                            <select class="form-select" id="q-shoottype" onchange="updateQuote()">
                                <option value="Outdoor">Outdoor</option>
                                <option value="Indoor">Indoor</option>
                                <option value="Outdoor + Indoor">Outdoor + Indoor</option>
                            </select>
                        </div>
                        <div class="form-row">
                            <label class="form-label">COVERAGE TYPE</label>
                            <select class="form-select" id="q-services" onchange="updateQuote()">
                                <option value="Photography &mdash; Solo ($150/hr)">Photography &mdash; Solo ($150/hr)</option>
                                <option value="Photo &amp; Video &mdash; Solo ($235/hr)">Photo &amp; Video &mdash; Solo ($235/hr)</option>
                                <option value="Photo &amp; Video &mdash; Dual ($325/hr)">Photo &amp; Video &mdash; Dual ($325/hr)</option>
                            </select>
                        </div>
                    </div>
                    <div class="form-row" style="margin-top:4px;">
                        <label style="display:flex; align-items:center; gap:8px; cursor:pointer; font-size:14px; color:#d1d5db;">
                            <input type="checkbox" id="q-live" onchange="updateQuote()" style="width:18px; height:18px; accent-color:#10b981;">
                            Add Live Streaming (+$100)
                        </label>
                    </div>
                    <div class="form-row-inline">
                        <div class="form-row">
                            <label class="form-label">ESTIMATED INVESTMENT</label>
                            <input class="form-input" id="q-quote" readonly style="color:#8b5cf6; font-weight:700;">
                        </div>
                        <div class="form-row">
                            <label class="form-label">RETAINER</label>
                            <input class="form-input" id="q-deposit" placeholder="e.g. $100" oninput="updateQuote()">
                        </div>
                    </div>
                </div>

                <div class="quote-preview" id="quote-preview" style="margin-top:20px;"></div>

                <div class="btn-row">
                    <button class="copy-btn" onclick="copyQuote()">📋 Copy to Clipboard</button>
                    <a class="share-wa-btn" id="wa-share-btn" href="#" target="_blank" rel="noopener" onclick="shareQuoteWA(event)">💬 Share via WhatsApp</a>
                </div>

            </div>

            <!-- PASSWORD GATE -->
            <div class="page" id="pw-gate">
                <div class="pw-gate">
                    <h2>📷 Rsquare Studios</h2>
                    <p>This section is password-protected.</p>
                    <div>
                        <input type="password" class="pw-input" id="pw-input" placeholder="Enter password" onkeydown="if(event.key==='Enter')checkPassword()">
                        <button class="pw-btn" onclick="checkPassword()">Enter</button>
                    </div>
                    <div class="pw-error" id="pw-error">Wrong password. Try again.</div>
                </div>
            </div>

            <!-- WORKFLOW HOME -->
            <div class="page" id="workflow-home">
                <div class="page-breadcrumb">Internal</div>
                <h1 class="page-title">Workflow Dashboard</h1>
                <div class="page-meta">Checklists, posing prompts, course notes &amp; workflow reference</div>

                <div class="pipeline-row">
                    <div class="pipeline-stage" style="background: #3b82f6;">Inquiry</div>
                    <div class="pipeline-stage" style="background: #8b5cf6;">Booked</div>
                    <div class="pipeline-stage" style="background: #f59e0b;">Shot</div>
                    <div class="pipeline-stage" style="background: #ec4899;">Editing</div>
                    <div class="pipeline-stage" style="background: #10b981;">Delivered</div>
                </div>

                <div class="wf-tile-grid">
                    <div class="wf-tile" onclick="showSection('checklists')">
                        <div class="wf-tile-icon">✅</div>
                        <div class="wf-tile-label">Checklists</div>
                    </div>
                    <div class="wf-tile" onclick="showSection('workflow-ref')">
                        <div class="wf-tile-icon">📖</div>
                        <div class="wf-tile-label">Workflow Reference</div>
                    </div>
                    <div class="wf-tile" onclick="showSection('posing-couples')">
                        <div class="wf-tile-icon">💑</div>
                        <div class="wf-tile-label">Couple Poses</div>
                    </div>
                    <div class="wf-tile" onclick="showSection('posing-families')">
                        <div class="wf-tile-icon">👨‍👩‍👧</div>
                        <div class="wf-tile-label">Family Poses</div>
                    </div>
                    <div class="wf-tile" onclick="showSection('posing-weddings')">
                        <div class="wf-tile-icon">💍</div>
                        <div class="wf-tile-label">Wedding Poses</div>
                    </div>
                    <a class="wf-tile" href="https://literate-basketball-b5e.notion.site/PLAN-POSES-13e48bb472084196a825703d7e8a4d10" target="_blank" rel="noopener" style="text-decoration:none;color:inherit;">
                        <div class="wf-tile-icon">📸</div>
                        <div class="wf-tile-label">Pose References</div>
                    </a>
                </div>
            </div>

            <!-- CHECKLISTS -->
            <div class="page" id="checklists">
                <a class="back-link" href="#" onclick="showSection('workflow-home'); return false;">&larr; Back to Workflow</a>
                <div class="page-breadcrumb">Workflow</div>
                <h1 class="page-title">Shoot Checklists</h1>
                <div class="page-meta">Check items off as you go &mdash; state is saved in your browser</div>

                <div class="checklist-group">
                    <div class="checklist-title">PRE-SHOOT</div>
                    {pre_html}
                </div>
                <div class="checklist-group">
                    <div class="checklist-title">DAY-OF GEAR</div>
                    {dayof_html}
                </div>
                <div class="checklist-group">
                    <div class="checklist-title">POST-SHOOT</div>
                    {post_html}
                </div>
                <div style="margin-top: 20px;">
                    <button class="pw-btn" onclick="resetChecklists()" style="background: #374151;">Reset All Checklists</button>
                </div>
            </div>

            <!-- WORKFLOW REFERENCE -->
            <div class="page" id="workflow-ref">
                <a class="back-link" href="#" onclick="showSection('workflow-home'); return false;">&larr; Back to Workflow</a>
                <div class="page-breadcrumb">Workflow</div>
                <h1 class="page-title">Photo Workflow Reference</h1>
                <div class="page-meta">Ingest &rarr; Sort &rarr; Cull &rarr; Edit &rarr; Export &rarr; Deliver</div>
                <div class="wf-content">{workflow_html}</div>
            </div>

            <!-- POSING GUIDES -->
            {posing_pages}


            <!-- CONTACT -->
            <div class="page" id="contact">
                <div class="page-breadcrumb">Contact</div>
                <h1 class="page-title">Get in Touch</h1>
                <div class="page-meta">WhatsApp is the easiest way to reach me. Just say hi!</div>

                <div class="gallery-grid" style="max-width:400px;">
                    <a href="https://wa.me/15307278598?text=Hi%20Ram!%20I%27m%20interested%20in%20a%20photography%20session." target="_blank" rel="noopener" class="gallery-card" style="border-color:#25D366;">
                        <div class="gallery-icon" style="font-size:28px;">💬</div>
                        <div class="gallery-info">
                            <div class="gallery-name">WhatsApp</div>
                            <div class="gallery-meta">Quickest way to reach me</div>
                        </div>
                        <div class="gallery-arrow">&#8599;</div>
                    </a>
                    <a href="tel:+15307278598" class="gallery-card">
                        <div class="gallery-icon" style="font-size:28px;">📞</div>
                        <div class="gallery-info">
                            <div class="gallery-name">(530) 727-8598</div>
                            <div class="gallery-meta">Call or text</div>
                        </div>
                        <div class="gallery-arrow">&#8599;</div>
                    </a>
                    <a href="https://www.rsquarestudios.com" target="_blank" rel="noopener" class="gallery-card">
                        <div class="gallery-icon" style="font-size:28px;">🌐</div>
                        <div class="gallery-info">
                            <div class="gallery-name">rsquarestudios.com</div>
                            <div class="gallery-meta">Full portfolio on SmugMug</div>
                        </div>
                        <div class="gallery-arrow">&#8599;</div>
                    </a>
                    <a href="https://www.instagram.com/rsquare_studios/" target="_blank" rel="noopener" class="gallery-card">
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

    <script>
        const PASSWORD_HASH = "{PASSWORD_HASH}";
        let isUnlocked = false;

        function showSection(id) {{
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            const target = document.getElementById(id);
            if (target) target.classList.add('active');
            // Update sidebar
            document.querySelectorAll('.sidebar-link').forEach(a => a.classList.remove('active'));
            // Scroll to top — both the content div and the window
            const mc = document.getElementById('main-content');
            if (mc) mc.scrollTop = 0;
            window.scrollTo(0, 0);
            // Close mobile sidebar + overlay
            closeSidebar();
        }}

        function accessWorkflow(sectionId) {{
            if (isUnlocked) {{
                showSection(sectionId);
                return;
            }}
            // Check sessionStorage
            if (sessionStorage.getItem('rsquare_unlocked') === 'true') {{
                isUnlocked = true;
                showSection(sectionId);
                updateLockIcon();
                return;
            }}
            // Show password gate, remembering where they wanted to go
            window._pendingSection = sectionId;
            showSection('pw-gate');
        }}

        async function checkPassword() {{
            const input = document.getElementById('pw-input').value;
            const encoder = new TextEncoder();
            const data = encoder.encode(input);
            const hashBuffer = await crypto.subtle.digest('SHA-256', data);
            const hashArray = Array.from(new Uint8Array(hashBuffer));
            const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

            if (hashHex === PASSWORD_HASH) {{
                isUnlocked = true;
                sessionStorage.setItem('rsquare_unlocked', 'true');
                updateLockIcon();
                showToast('Unlocked!');
                const target = window._pendingSection || 'pricing';
                showSection(target);
            }} else {{
                document.getElementById('pw-error').style.display = 'block';
                document.getElementById('pw-input').value = '';
                document.getElementById('pw-input').focus();
            }}
        }}

        function updateLockIcon() {{
            const icon = document.getElementById('lock-icon');
            if (icon) {{
                icon.textContent = '🔓';
                icon.classList.add('unlocked');
            }}
        }}

        // Make all wf-links go through accessWorkflow
        document.querySelectorAll('.sidebar-link.wf-link, .sidebar-link.sub-link').forEach(link => {{
            const originalOnclick = link.getAttribute('onclick');
            if (originalOnclick && originalOnclick.includes('showSection')) {{
                const match = originalOnclick.match(/showSection\\('([^']+)'\\)/);
                if (match) {{
                    const sectionId = match[1];
                    link.setAttribute('onclick', `accessWorkflow('${{sectionId}}')`);
                }}
            }}
        }});

        // Checklists - save/load from localStorage
        function saveChecklist() {{
            const checks = {{}};
            document.querySelectorAll('#checklists input[type="checkbox"]').forEach(cb => {{
                checks[cb.id] = cb.checked;
            }});
            localStorage.setItem('rsquare_checklists', JSON.stringify(checks));
        }}

        function loadChecklist() {{
            const saved = localStorage.getItem('rsquare_checklists');
            if (saved) {{
                const checks = JSON.parse(saved);
                Object.entries(checks).forEach(([id, val]) => {{
                    const cb = document.getElementById(id);
                    if (cb) cb.checked = val;
                }});
            }}
        }}

        function resetChecklists() {{
            document.querySelectorAll('#checklists input[type="checkbox"]').forEach(cb => cb.checked = false);
            localStorage.removeItem('rsquare_checklists');
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
            if (isUnlocked || sessionStorage.getItem('rsquare_unlocked') === 'true') {{
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

        // Check if already unlocked (pricing/workflow access persists in tab)
        if (sessionStorage.getItem('rsquare_unlocked') === 'true') {{
            isUnlocked = true;
            updateLockIcon();
        }}

        // Load checklists on page load
        loadChecklist();

        // Quote form logic
        const rateMap = {{
            'Photography — Solo ($150/hr)': 150,
            'Photo & Video — Solo ($235/hr)': 235,
            'Photo & Video — Dual ($325/hr)': 325,
        }};

        function updateQuote() {{
            const svc = document.getElementById('q-services').value;
            // Decode HTML entities for matching
            const svcText = svc.replace(/&amp;/g, '&').replace(/&mdash;/g, '—');
            const hours = parseInt(document.getElementById('q-hours').value) || 0;
            const rate = rateMap[svcText] || 0;
            const live = document.getElementById('q-live').checked ? 100 : 0;
            const total = (rate * hours) + live;
            document.getElementById('q-quote').value = total > 0 ? '$' + total.toLocaleString() : '';

            const name = document.getElementById('q-name').value || '___';
            const event = document.getElementById('q-event').value || '___';
            const location = document.getElementById('q-location').value || '___';
            const dateVal = document.getElementById('q-date').value;
            const shootType = document.getElementById('q-shoottype').value;
            const deposit = document.getElementById('q-deposit').value || '___';
            const hasLive = document.getElementById('q-live').checked;
            const liveText = hasLive ? 'Yes' : 'No';

            let dateDisplay = '___';
            if (dateVal) {{
                const d = new Date(dateVal + 'T12:00:00');
                dateDisplay = d.toLocaleDateString('en-US', {{ weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' }});
            }}

            const quote = total > 0 ? '$' + total.toLocaleString() : '___';

            // HTML preview (styled)
            const html = `
                <div class="quote-section">
                    <div class="quote-greeting">Hey ${{name}}! 👋<br>Thanks for reaching out — here's the quote for your ${{event.toLowerCase()}}:</div>
                </div>
                <div class="quote-section">
                    <div class="quote-section-title">Details</div>
                    <div class="quote-row"><span class="qlabel">Client</span><span class="qvalue">${{name}}</span></div>
                    <div class="quote-row"><span class="qlabel">Event</span><span class="qvalue">${{event}}</span></div>
                    <div class="quote-row"><span class="qlabel">Location</span><span class="qvalue">${{location}}</span></div>
                    <div class="quote-row"><span class="qlabel">Date</span><span class="qvalue">${{dateDisplay}}</span></div>
                    <div class="quote-row"><span class="qlabel">Setting</span><span class="qvalue">${{shootType}}</span></div>
                    <div class="quote-row"><span class="qlabel">Coverage</span><span class="qvalue">${{svcText}}</span></div>
                    <div class="quote-row"><span class="qlabel">Hours</span><span class="qvalue">${{hours || '___'}}</span></div>
                    ${{hasLive ? '<div class="quote-row"><span class="qlabel">Live Streaming</span><span class="qvalue" style="color:#10b981;">Included</span></div>' : ''}}
                </div>
                <div class="quote-section">
                    <div class="quote-section-title">Pricing</div>
                    <div class="quote-row"><span class="qlabel">Total</span><span class="qvalue quote-total">${{quote}}</span></div>
                    <div class="quote-row"><span class="qlabel">Retainer</span><span class="qvalue">${{deposit}}</span></div>
                    <div class="quote-note">Rest due on event day</div>
                </div>
                <div class="quote-section">
                    <div class="quote-section-title">What You Get</div>
                    <div class="quote-note">• All edited pictures — ready in 12–15 days<br>• Cinematic teaser (4–6 min) — ready in 3–4 weeks</div>
                </div>
                <div class="quote-section">
                    <div class="quote-section-title">How You Get Your Photos</div>
                    <div class="quote-note">You'll get a private gallery link. Download all pics at once from desktop — email with the download link usually takes 15–30 min. Link works for 3 months so grab them soon!</div>
                </div>
                <div class="quote-section">
                    <div class="quote-signoff">Looking forward to it! 🙌<br>— Ram, Rsquare Studios</div>
                </div>
            `;
            document.getElementById('quote-preview').innerHTML = html;

            // Plain text version (for copy/WhatsApp)
            const text = `Hey ${{name}}! 👋
Thanks for reaching out — here's the quote for your ${{event.toLowerCase()}}:

*Details*
Client: ${{name}}
Event: ${{event}}
Location: ${{location}}
Date: ${{dateDisplay}}
Setting: ${{shootType}}
Coverage: ${{svcText}}
Hours: ${{hours || '___'}}${{hasLive ? '\\nLive Streaming: Yes (+$100)' : ''}}

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
            return document.getElementById('quote-preview').dataset.plaintext || document.getElementById('quote-preview').textContent;
        }}

        function copyQuote() {{
            const text = getQuoteText();
            navigator.clipboard.writeText(text).then(() => {{
                showToast('Quote copied to clipboard!');
            }}).catch(() => {{
                // Fallback
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
            window.open('https://wa.me/?text=' + encoded, '_blank');
        }}

        // Initialize quote preview
        updateQuote();

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
    print(f"  🔑 Internal password: rsquare2026\n")


if __name__ == "__main__":
    main()
