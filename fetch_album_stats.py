#!/usr/bin/env python3
"""
Fetch SmugMug album stats for Rsquare Studios.
Lists all albums under year folders (2024-2026), gathers engagement metrics,
categorizes by event type, and outputs ranked results.
"""

import json
import time
import sys
from pathlib import Path
from requests_oauthlib import OAuth1Session

# --- Config ---
API_KEY = "nxtxC83BMVxbcJKJ8b89HLV2CBPHpSTD"
API_SECRET = "4F8Vm8LKxFZ8sKFD369PKhZmGcFxM7VTWRMH8QzMdMvWFstdkCgF4Lkpgj4wQxXD"
ROOT_NODE = "sh9H2R"
BASE_URL = "https://api.smugmug.com"
TARGET_YEARS = {"2024", "2025", "2026"}
OUTPUT_PATH = Path("/Users/ram/Documents/2025 - Rsquare/Rsquare-Scripts/Photography/rsquarestudios/rsquare-studios-dashboard/album_stats.json")

# Load OAuth tokens
with open(Path.home() / ".smugmug_config.json") as f:
    config = json.load(f)

session = OAuth1Session(
    client_key=API_KEY,
    client_secret=API_SECRET,
    resource_owner_key=config["access_token"],
    resource_owner_secret=config["access_token_secret"],
)

HEADERS = {"Accept": "application/json"}
CALL_COUNT = 0


def api_get(uri, params=None):
    """Make a rate-limited GET request to SmugMug API."""
    global CALL_COUNT
    url = uri if uri.startswith("http") else BASE_URL + uri
    if params is None:
        params = {}

    for attempt in range(3):
        time.sleep(0.12)
        CALL_COUNT += 1
        resp = session.get(url, headers=HEADERS, params=params)
        if resp.status_code == 429:
            wait = 2 ** (attempt + 1)
            print(f"  [429 rate limited] Backing off {wait}s...")
            time.sleep(wait)
            continue
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

    print(f"  [ERROR] Failed after retries: {url}")
    return None


def get_children(node_id, node_type=None):
    """Get all children of a node with pagination."""
    children = []
    uri = f"/api/v2/node/{node_id}!children"
    params = {"count": 50, "start": 1}
    if node_type:
        params["Type"] = node_type

    while True:
        data = api_get(uri, params)
        if not data or "Response" not in data:
            break
        nodes = data["Response"].get("Node", [])
        if not nodes:
            break
        children.extend(nodes)

        pages = data["Response"].get("Pages", {})
        next_page = pages.get("NextPage")
        if next_page:
            uri = next_page
            params = {}
        else:
            break

    return children


def get_album_stats(album_key):
    """Try to get album stats from the !stats endpoint."""
    data = api_get(f"/api/v2/album/{album_key}!stats")
    if not data or "Response" not in data:
        return {}
    return data["Response"].get("AlbumStats", {})


def categorize(name):
    """Categorize album by keywords in the name."""
    lower = name.lower()
    if any(k in lower for k in ["wedding", "engagement"]):
        return "Wedding"
    if any(k in lower for k in ["maternity"]):
        return "Maternity"
    if any(k in lower for k in ["baby shower", "babyshower"]):
        return "Baby Shower"
    if any(k in lower for k in ["birthday", "bday"]):
        return "Birthday"
    if "cradle" in lower:
        return "Cradle"
    if any(k in lower for k in ["shoot", "session", "portrait", "family"]):
        return "Portrait/Session"
    return "Other"


def main():
    print("=" * 60)
    print("SmugMug Album Stats Fetcher - Rsquare Studios")
    print("=" * 60)

    # Step 1: Get year folders under root node
    print(f"\n[1/4] Fetching children of root node {ROOT_NODE}...")
    root_children = get_children(ROOT_NODE)

    year_folders = []
    other_folders = []
    for node in root_children:
        name = node.get("Name", "")
        ntype = node.get("Type", "")
        if name in TARGET_YEARS and ntype == "Folder":
            year_folders.append(node)
            print(f"  Found year folder: {name} (NodeId: {node['NodeID']})")
        elif ntype == "Folder":
            other_folders.append(node)

    if not year_folders:
        print("  No exact year-name folders found. All root children:")
        for node in root_children:
            print(f"    - {node.get('Name', '?')} (Type: {node.get('Type', '?')}, NodeID: {node.get('NodeID', '?')})")
        # Use all folders as fallback
        year_folders = [n for n in root_children if n.get("Type") == "Folder"]
        print(f"  Using all {len(year_folders)} folders.")
    else:
        if other_folders:
            print(f"  (Skipping {len(other_folders)} non-target folders: {', '.join(n['Name'] for n in other_folders[:5])}...)")

    # Step 2: Get albums under each year folder
    print(f"\n[2/4] Fetching albums from {len(year_folders)} year folders...")
    all_albums_raw = []

    for yf in year_folders:
        year_name = yf["Name"]
        year_node_id = yf["NodeID"]
        print(f"\n  --- {year_name} ---")

        # Get all children (albums might be nested in sub-folders too)
        album_nodes = get_children(year_node_id, node_type="Album")
        print(f"  Found {len(album_nodes)} albums")

        # Also check for sub-folders that might contain albums
        sub_folders = get_children(year_node_id, node_type="Folder")
        if sub_folders:
            print(f"  Found {len(sub_folders)} sub-folders, checking for nested albums...")
            for sf in sub_folders:
                sf_albums = get_children(sf["NodeID"], node_type="Album")
                if sf_albums:
                    print(f"    {sf['Name']}: {len(sf_albums)} albums")
                    for sa in sf_albums:
                        sa["_parent_folder"] = sf["Name"]
                    album_nodes.extend(sf_albums)

        for node in album_nodes:
            all_albums_raw.append({
                "year": year_name,
                "node": node,
            })

    print(f"\n  Total albums to process: {len(all_albums_raw)}")

    # Step 3: Get details and stats for each album
    print(f"\n[3/4] Fetching album details and stats...")

    # Probe first album for available endpoints
    stats_endpoint_works = False
    if all_albums_raw:
        probe = all_albums_raw[0]["node"]
        probe_uris = probe.get("Uris", {})
        print(f"  Probing first album: {probe.get('Name', '?')}")

        # Show available node Uris
        for uri_key, uri_val in probe_uris.items():
            uri_str = uri_val.get("Uri", str(uri_val)) if isinstance(uri_val, dict) else str(uri_val)
            if any(s in uri_key.lower() for s in ["album", "stat", "view", "image"]):
                print(f"    {uri_key}: {uri_str}")

        # Get album detail to see what fields are available
        album_uri = None
        if "Album" in probe_uris:
            au = probe_uris["Album"]
            album_uri = au.get("Uri") if isinstance(au, dict) else au

        if album_uri:
            probe_data = api_get(album_uri)
            if probe_data and "Response" in probe_data:
                pa = probe_data["Response"].get("Album", {})
                # Find stat-related keys
                stat_keys = [k for k in pa.keys() if any(s in k.lower() for s in
                    ["view", "visit", "count", "image", "download", "stat", "hit", "popular", "total"])]
                print(f"  Stat-related fields in Album: {stat_keys}")

                # Show album Uris
                for uk, uv in pa.get("Uris", {}).items():
                    ustr = uv.get("Uri", str(uv)) if isinstance(uv, dict) else str(uv)
                    print(f"    Album.Uri.{uk}: {ustr}")

                # Try !stats endpoint
                akey = pa.get("AlbumKey", "")
                if akey:
                    sd = get_album_stats(akey)
                    if sd:
                        print(f"  !stats endpoint works. Keys: {list(sd.keys())}")
                        print(f"  Sample stats: {json.dumps(sd, indent=2)[:500]}")
                        stats_endpoint_works = True
                    else:
                        print("  !stats endpoint not available.")

    # Process all albums
    albums = []
    for i, entry in enumerate(all_albums_raw):
        node = entry["node"]
        year = entry["year"]
        name = node.get("Name", "Unknown")
        node_id = node.get("NodeID", "")

        if (i + 1) % 10 == 0 or i == 0:
            print(f"  [{i+1}/{len(all_albums_raw)}] {name}")

        # Get album URI from node
        node_uris = node.get("Uris", {})
        album_uri = None
        if "Album" in node_uris:
            au = node_uris["Album"]
            album_uri = au.get("Uri") if isinstance(au, dict) else au

        album_detail = {}
        album_stats = {}
        album_key = ""

        if album_uri:
            ad = api_get(album_uri)
            if ad and "Response" in ad:
                album_detail = ad["Response"].get("Album", {})
                album_key = album_detail.get("AlbumKey", "")

        if stats_endpoint_works and album_key:
            album_stats = get_album_stats(album_key)

        image_count = album_detail.get("ImageCount", 0)
        web_uri = album_detail.get("WebUri", node.get("WebUri", ""))

        # Collect all possible engagement metrics
        views = 0
        downloads = 0

        # From stats endpoint
        if album_stats:
            views = album_stats.get("Views", album_stats.get("Visits", 0)) or 0
            downloads = album_stats.get("Downloads", 0) or 0

        # From album detail (fallback)
        if not views:
            for key in ["ViewCount", "Visits", "TotalViews", "Views"]:
                v = album_detail.get(key, 0)
                if v:
                    views = v
                    break

        category = categorize(name)
        parent_folder = node.get("_parent_folder", "")

        albums.append({
            "name": name,
            "year": year,
            "category": category,
            "parent_folder": parent_folder,
            "image_count": image_count or 0,
            "views": views,
            "downloads": downloads,
            "web_uri": web_uri,
            "node_id": node_id,
            "album_key": album_key,
        })

    # Step 4: Sort and output
    print(f"\n[4/4] Sorting and generating output...")

    # Primary sort: views desc, secondary: image_count desc
    albums.sort(key=lambda a: (a["views"], a["image_count"]), reverse=True)

    # Group by category
    categories = {}
    for a in albums:
        cat = a["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(a)

    output = {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_albums": len(albums),
        "api_calls": CALL_COUNT,
        "stats_endpoint_available": stats_endpoint_works,
        "albums_ranked": albums,
        "by_category": {cat: lst for cat, lst in sorted(categories.items())},
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Saved to: {OUTPUT_PATH}")

    # --- Print Summary ---
    print("\n" + "=" * 75)
    print("ALBUM STATS SUMMARY - Rsquare Studios")
    print(f"Total albums: {len(albums)} | API calls: {CALL_COUNT}")
    print(f"Stats endpoint available: {stats_endpoint_works}")
    print("=" * 75)

    print(f"\n{'TOP 10 ALBUMS OVERALL':^75}")
    print("-" * 75)
    print(f"{'#':<3} {'Album':<38} {'Year':<6} {'Imgs':>5} {'Views':>7} {'Cat':<14}")
    print("-" * 75)
    for i, a in enumerate(albums[:10], 1):
        print(f"{i:<3} {a['name'][:37]:<38} {a['year']:<6} {a['image_count']:>5} {a['views']:>7} {a['category']:<14}")

    for cat in sorted(categories.keys()):
        cat_albums = sorted(categories[cat], key=lambda a: (a["views"], a["image_count"]), reverse=True)
        print(f"\n{'TOP 5: ' + cat.upper():^75}")
        print("-" * 75)
        print(f"{'#':<3} {'Album':<43} {'Year':<6} {'Imgs':>5} {'Views':>7}")
        print("-" * 75)
        for i, a in enumerate(cat_albums[:5], 1):
            print(f"{i:<3} {a['name'][:42]:<43} {a['year']:<6} {a['image_count']:>5} {a['views']:>7}")
        print(f"  ({len(cat_albums)} total in category)")

    print(f"\n{'YEAR SUMMARY':^75}")
    print("-" * 75)
    for year in sorted(TARGET_YEARS):
        ya = [a for a in albums if a["year"] == year]
        ti = sum(a["image_count"] for a in ya)
        tv = sum(a["views"] for a in ya)
        print(f"  {year}: {len(ya):>3} albums | {ti:>6} images | {tv:>6} views")

    print(f"\nDone.")


if __name__ == "__main__":
    main()
