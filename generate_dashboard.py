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
    category_icons = {
        "wedding": "💍",
        "maternity": "🤰",
        "newborn": "👶",
        "birthday": "🎂",
        "cradle": "🍼",
    }
    category_labels = {
        "wedding": "Wedding",
        "maternity": "Maternity",
        "newborn": "Baby Shower",
        "birthday": "Birthday",
        "cradle": "Cradle Ceremony",
    }

    cards_by_category = {}
    for cat, items in galleries.items():
        cards = ""
        for g in items:
            name = g["name"]
            url = g["url"]
            # Extract short name: remove date prefix and location suffix
            parts = name.split(" | ")
            short_name = parts[1] if len(parts) > 1 else name
            location = parts[2] if len(parts) > 2 else ""
            date_str = parts[0] if len(parts) > 0 else ""

            cards += f"""
                <a href="{escape_html(url)}" target="_blank" rel="noopener" class="gallery-card">
                    <div class="gallery-icon">{category_icons.get(cat, '📷')}</div>
                    <div class="gallery-info">
                        <div class="gallery-name">{escape_html(short_name)}</div>
                        <div class="gallery-meta">{escape_html(location)} &middot; {escape_html(date_str)}</div>
                    </div>
                    <div class="gallery-arrow">&#8599;</div>
                </a>"""
        cards_by_category[cat] = {
            "html": cards,
            "icon": category_icons.get(cat, "📷"),
            "label": category_labels.get(cat, cat.title()),
            "count": len(items),
        }
    return cards_by_category


def build_pricing_section():
    """Build pricing cards from hardcoded data (from photography_info_messages.py)."""
    packages = [
        {
            "name": "Wedding Photography",
            "icon": "💍",
            "color": "#8b5cf6",
            "tiers": [
                {"name": "Full Day", "price": "$2,500", "details": "8-10 hrs, 2 photographers, 500-800 photos, engagement session included"},
                {"name": "Half Day", "price": "$1,500", "details": "4-6 hrs, 1 photographer, 300-500 photos"},
                {"name": "Engagement Only", "price": "$450", "details": "60-90 min, 40-60 edited photos"},
            ],
            "addons": [
                "2nd photographer +$400",
                "Extra hour +$250",
                "Wedding album +$500",
                "Parent albums +$150 ea",
                "Raw files +$300",
            ],
        },
        {
            "name": "Maternity",
            "icon": "🤰",
            "color": "#ec4899",
            "tiers": [
                {"name": "Session", "price": "$450", "details": "60-90 min, 2-3 outfits, 40-60 photos, gown rental included"},
            ],
            "addons": [
                "Album +$150",
                "Canvas print (16x20) +$100",
                "Newborn bundle $900 (save $100)",
            ],
        },
        {
            "name": "Newborn",
            "icon": "👶",
            "color": "#f59e0b",
            "tiers": [
                {"name": "Session", "price": "$550", "details": "2-3 hrs, 3-4 setups, 30-50 photos, props included, best at 5-14 days"},
            ],
            "addons": [
                "Milestone Bundle (newborn+6mo+1yr) $1,200 (save $200)",
                "Album (10x10, 20 pages) +$200",
                "Announcement cards +$75",
            ],
        },
        {
            "name": "Birthday",
            "icon": "🎂",
            "color": "#3b82f6",
            "tiers": [
                {"name": "1st Birthday / Cake Smash", "price": "$400", "details": "1 hr, 50-70 photos, decorations included"},
                {"name": "Party Coverage", "price": "$600", "details": "2-3 hrs, 100-150 photos"},
            ],
            "addons": [],
        },
        {
            "name": "Cradle Ceremony",
            "icon": "🍼",
            "color": "#10b981",
            "tiers": [
                {"name": "Full Coverage", "price": "$700", "details": "3-4 hrs, 150-250 photos"},
            ],
            "addons": [],
        },
    ]

    html = ""
    for pkg in packages:
        tiers_html = ""
        for tier in pkg["tiers"]:
            tiers_html += f"""
                <div class="price-tier">
                    <div class="tier-header">
                        <span class="tier-name">{tier['name']}</span>
                        <span class="tier-price">{tier['price']}</span>
                    </div>
                    <div class="tier-details">{tier['details']}</div>
                </div>"""

        addons_html = ""
        if pkg["addons"]:
            addons_html = '<div class="addons-label">Add-ons</div><ul class="addons-list">'
            for addon in pkg["addons"]:
                addons_html += f"<li>{addon}</li>"
            addons_html += "</ul>"

        html += f"""
            <div class="pricing-card" style="--accent: {pkg['color']};">
                <div class="pricing-header">
                    <span class="pricing-icon">{pkg['icon']}</span>
                    <span class="pricing-name">{pkg['name']}</span>
                </div>
                {tiers_html}
                {addons_html}
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
    chapters = load_twomann_chapters()
    twomann_sidebar = build_twomann_sidebar(chapters)
    twomann_pages = build_twomann_pages(chapters)

    total_galleries = sum(c["count"] for c in gallery_cards.values())

    # Build sidebar gallery links
    gallery_sidebar = ""
    for cat, info in gallery_cards.items():
        gallery_sidebar += f'<a href="#portfolio-{cat}" class="sidebar-link" onclick="showSection(\'portfolio-{cat}\')">{info["icon"]} {info["label"]} ({info["count"]})</a>\n'

    # Build portfolio category pages
    portfolio_pages = ""
    for cat, info in gallery_cards.items():
        portfolio_pages += f"""
            <div class="page" id="portfolio-{cat}">
                <a class="back-link" href="#" onclick="showSection('portfolio-home'); return false;">&larr; Back to Portfolio</a>
                <div class="page-breadcrumb">Portfolio</div>
                <h1 class="page-title">{info['icon']} {info['label']}</h1>
                <div class="page-meta">{info['count']} galleries on SmugMug</div>
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
            display: inline-block;
            font-size: 13px;
            color: #8b5cf6;
            text-decoration: none;
            margin-bottom: 16px;
            padding: 4px 0;
            cursor: pointer;
        }}
        .back-link:hover {{ color: #a78bfa; }}

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
            text-align: center;
            padding: 60px 20px 40px;
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
        }}
        .hero p {{
            font-size: 16px;
            color: #6b7280;
            max-width: 500px;
            margin: 0 auto 32px;
            line-height: 1.6;
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
            color: #8b5cf6;
        }}
        .hero-stat .label {{
            font-size: 12px;
            color: #525252;
            letter-spacing: 0.5px;
            margin-top: 4px;
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
        }}
        .hero-cta:hover {{ background: #7c3aed; }}

        /* Category tiles on portfolio home */
        .cat-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
            gap: 16px;
            margin-top: 24px;
        }}
        .cat-tile {{
            background: #202020;
            border: 1px solid #2d2d2d;
            border-radius: 12px;
            padding: 24px;
            text-align: center;
            cursor: pointer;
            transition: border-color 0.2s, transform 0.15s;
            text-decoration: none;
            color: inherit;
        }}
        .cat-tile:hover {{
            border-color: #8b5cf6;
            transform: translateY(-2px);
        }}
        .cat-icon {{ font-size: 36px; margin-bottom: 10px; }}
        .cat-name {{ font-size: 16px; font-weight: 600; color: #e0e0e0; margin-bottom: 4px; }}
        .cat-count {{ font-size: 13px; color: #525252; }}

        /* Gallery cards */
        .gallery-grid {{
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        .gallery-card {{
            display: flex;
            align-items: center;
            gap: 14px;
            padding: 14px 18px;
            background: #202020;
            border: 1px solid #2d2d2d;
            border-radius: 10px;
            text-decoration: none;
            color: inherit;
            transition: border-color 0.15s, transform 0.15s;
        }}
        .gallery-card:hover {{
            border-color: #3d3d3d;
            transform: translateX(3px);
        }}
        .gallery-icon {{ font-size: 24px; }}
        .gallery-info {{ flex: 1; }}
        .gallery-name {{ font-size: 15px; font-weight: 600; color: #e0e0e0; }}
        .gallery-meta {{ font-size: 12px; color: #525252; margin-top: 2px; }}
        .gallery-arrow {{ font-size: 16px; color: #525252; }}

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

            /* Hero mobile */
            .hero {{
                padding: 32px 8px 24px;
            }}
            .hero-logo {{ font-size: 40px; }}
            .hero h1 {{
                font-size: 26px;
                letter-spacing: -0.5px;
            }}
            .hero p {{
                font-size: 14px;
                margin-bottom: 24px;
            }}
            .hero-stats {{
                gap: 20px;
                margin-bottom: 24px;
            }}
            .hero-stat .number {{ font-size: 24px; }}
            .hero-cta {{
                padding: 14px 32px;
                font-size: 16px;
                width: 100%;
                max-width: 300px;
            }}
            .contact-bar {{
                gap: 12px;
                flex-direction: column;
            }}

            /* Category tiles mobile */
            .cat-grid {{
                grid-template-columns: 1fr 1fr;
                gap: 10px;
            }}
            .cat-tile {{
                padding: 18px 12px;
            }}
            .cat-icon {{ font-size: 30px; margin-bottom: 6px; }}
            .cat-name {{ font-size: 14px; }}

            /* Gallery cards mobile — bigger touch targets */
            .gallery-grid {{ gap: 10px; }}
            .gallery-card {{
                padding: 16px;
                gap: 12px;
                min-height: 64px;
            }}
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
            <div class="bnav-item" onclick="mobileNav('pricing')" id="bnav-pricing">
                <span class="bnav-icon">💰</span>
                Pricing
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
            {gallery_sidebar}

            <div class="sidebar-divider"></div>
            <div class="sidebar-section-label">PRICING</div>
            <a class="sidebar-link" onclick="showSection('pricing')">💰 Packages &amp; Pricing</a>

            <div class="sidebar-divider"></div>
            <div class="sidebar-section-label" id="wf-section-label">
                <span class="lock-icon" id="lock-icon">🔒</span> WORKFLOW
            </div>
            <a class="sidebar-link wf-link" onclick="accessWorkflow('workflow-home')">📋 Dashboard</a>
            <a class="sidebar-link wf-link" onclick="accessWorkflow('checklists')">✅ Checklists</a>
            <a class="sidebar-link wf-link" onclick="accessWorkflow('workflow-ref')">📖 Workflow Reference</a>

            <div class="sidebar-section-label wf-link" style="padding-top:8px">POSING GUIDES</div>
            {posing_sidebar.replace('class="sidebar-link sub-link"', 'class="sidebar-link sub-link wf-link"')}

            <div class="sidebar-section-label wf-link" style="padding-top:8px">TWOMANN COURSE</div>
            {twomann_sidebar.replace('class="sidebar-link sub-link"', 'class="sidebar-link sub-link wf-link"')}

            <div class="sidebar-footer">
                Updated {now}<br>
                {total_galleries} galleries &middot; {len(chapters)} course chapters
            </div>
        </div>

        <!-- Content -->
        <div class="content" id="main-content">

            <!-- HOME -->
            <div class="page active" id="home">
                <div class="hero">
                    <div class="hero-logo">📷</div>
                    <h1>Rsquare Studios</h1>
                    <p>Wedding, Maternity, Newborn, Birthday &amp; Cradle Ceremony Photography in the Dallas-Fort Worth area.</p>
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
                    <div class="contact-bar" style="margin-top: 32px;">
                        <span class="contact-item"><a href="https://www.rsquarestudios.com" target="_blank">rsquarestudios.com</a></span>
                        <span class="contact-item">Dallas, TX</span>
                        <span class="contact-item"><a href="tel:+15307278598">(530) 727-8598</a></span>
                    </div>
                </div>
            </div>

            <!-- PORTFOLIO HOME -->
            <div class="page" id="portfolio-home">
                <div class="page-breadcrumb">Portfolio</div>
                <h1 class="page-title">Portfolio</h1>
                <div class="page-meta">{total_galleries} galleries across 5 categories &middot; Photos hosted on SmugMug</div>
                <div class="cat-grid">
                    {"".join(f'''
                    <div class="cat-tile" onclick="showSection('portfolio-{cat}')">
                        <div class="cat-icon">{info['icon']}</div>
                        <div class="cat-name">{info['label']}</div>
                        <div class="cat-count">{info['count']} galleries</div>
                    </div>''' for cat, info in gallery_cards.items())}
                </div>
            </div>

            <!-- PORTFOLIO CATEGORIES -->
            {portfolio_pages}

            <!-- PRICING -->
            <div class="page" id="pricing">
                <div class="page-breadcrumb">Packages</div>
                <h1 class="page-title">Packages &amp; Pricing</h1>
                <div class="page-meta">Professional photography for life's most important moments</div>
                <div class="pricing-grid">
                    {pricing_html}
                </div>
                <div class="includes-box">
                    <h3>All Packages Include</h3>
                    <div class="includes-list">
                        <span>&#10003; Private SmugMug gallery</span>
                        <span>&#10003; High-resolution downloads</span>
                        <span>&#10003; Print release</span>
                        <span>&#10003; Professional editing</span>
                        <span>&#10003; 48-72hr sneak peek</span>
                        <span>&#10003; Lifetime cloud storage</span>
                    </div>
                </div>
            </div>

            <!-- PASSWORD GATE -->
            <div class="page" id="pw-gate">
                <div class="pw-gate">
                    <h2>🔒 Workflow Dashboard</h2>
                    <p>This section is password-protected. Enter the password to access checklists, posing guides, and course notes.</p>
                    <div>
                        <input type="password" class="pw-input" id="pw-input" placeholder="Enter password" onkeydown="if(event.key==='Enter')checkPassword()">
                        <button class="pw-btn" onclick="checkPassword()">Unlock</button>
                    </div>
                    <div class="pw-error" id="pw-error">Incorrect password. Try again.</div>
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
                    <div class="wf-tile" onclick="showSection('twomann-0')">
                        <div class="wf-tile-icon">📚</div>
                        <div class="wf-tile-label">TwoMann Course</div>
                    </div>
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

            <!-- TWOMANN COURSE PAGES -->
            {twomann_pages}

            <!-- CONTACT -->
            <div class="page" id="contact">
                <div class="page-breadcrumb">Contact</div>
                <h1 class="page-title">Get In Touch</h1>
                <div class="page-meta">Ready to capture your special moments? Reach out anytime!</div>

                <div class="gallery-grid" style="max-width:400px;">
                    <a href="https://wa.me/15307278598?text=Hi%20Ram!%20I%27m%20interested%20in%20a%20photography%20session." target="_blank" rel="noopener" class="gallery-card" style="border-color:#25D366;">
                        <div class="gallery-icon" style="font-size:28px;">💬</div>
                        <div class="gallery-info">
                            <div class="gallery-name">WhatsApp</div>
                            <div class="gallery-meta">Fastest way to reach us</div>
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
                    <h3>Based in Dallas-Fort Worth, TX</h3>
                    <div style="font-size:14px; color:#c4b5fd; line-height:1.7;">
                        Available for weddings, maternity, newborn, birthday, and cradle ceremony photography.<br><br>
                        We typically book 4-6 weeks in advance. Secure your date with a deposit!
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
            // Scroll to top
            document.getElementById('main-content').scrollTop = 0;
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
                showToast('Unlocked! Welcome to the workflow dashboard.');
                const target = window._pendingSection || 'workflow-home';
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
            // Update active state on bottom nav
            document.querySelectorAll('.bnav-item').forEach(b => b.classList.remove('active'));
            // Map section to tab
            const tabMap = {{
                'home': 'bnav-home',
                'portfolio-home': 'bnav-portfolio',
                'pricing': 'bnav-pricing',
                'contact': 'bnav-contact',
            }};
            const tabId = tabMap[sectionId];
            if (tabId) document.getElementById(tabId)?.classList.add('active');
        }}

        // Check if already unlocked
        if (sessionStorage.getItem('rsquare_unlocked') === 'true') {{
            isUnlocked = true;
            updateLockIcon();
        }}

        // Load checklists on page load
        loadChecklist();
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

    print("🎓 Loading TwoMann course chapters...")
    chapters = load_twomann_chapters()
    print(f"   Found {len(chapters)} chapters")

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
