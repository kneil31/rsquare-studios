#!/usr/bin/env python3
"""Fetch representative cover images from SmugMug for 5 photography categories."""

import json
from requests_oauthlib import OAuth1Session

API_KEY = "nxtxC83BMVxbcJKJ8b89HLV2CBPHpSTD"
API_SECRET = "4F8Vm8LKxFZ8sKFD369PKhZmGcFxM7VTWRMH8QzMdMvWFstdkCgF4Lkpgj4wQxXD"

with open("/Users/ram/.smugmug_config.json") as f:
    config = json.load(f)

sm = OAuth1Session(
    API_KEY,
    client_secret=API_SECRET,
    resource_owner_key=config["access_token"],
    resource_owner_secret=config["access_token_secret"],
)
HEADERS = {"Accept": "application/json"}
BASE = "https://api.smugmug.com"


def api_get(path, params=None):
    url = path if path.startswith("http") else BASE + path
    resp = sm.get(url, headers=HEADERS, params=params)
    if resp.status_code != 200:
        print(f"  ERROR {resp.status_code}: {url}")
        return None
    return resp.json()


def get_image_urls(image_key):
    """Get X3Large and XLarge URLs via the !sizes endpoint."""
    data = api_get(f"/api/v2/image/{image_key}!sizes")
    result = {"image_key": image_key, "x3large_url": None, "xlarge_url": None}
    if data and "Response" in data:
        sizes = data["Response"].get("ImageSizes", {})
        result["x3large_url"] = sizes.get("X3LargeImageUrl")
        result["xlarge_url"] = sizes.get("XLargeImageUrl")
    return result


def get_highlight_or_first_image(node_id):
    """Get highlight image key, or fall back to first album image."""
    # Get node details
    data = api_get(f"/api/v2/node/{node_id}")
    if not data:
        return None
    node = data["Response"]["Node"]
    print(f"  Album: {node['Name']} (NodeID: {node_id})")

    # Try highlight image
    highlight_uri = node.get("Uris", {}).get("HighlightImage", {}).get("Uri")
    if highlight_uri:
        hdata = api_get(highlight_uri)
        if hdata and "Response" in hdata:
            img = hdata["Response"].get("Image", {})
            key = img.get("ImageKey")
            if key:
                print(f"  Highlight image: {key}")
                return key

    # Fall back to first image in album
    album_uri = node.get("Uris", {}).get("Album", {}).get("Uri")
    if album_uri:
        idata = api_get(album_uri + "!images", params={"count": 1})
        if idata and "Response" in idata:
            images = idata["Response"].get("AlbumImage", [])
            if isinstance(images, list) and images:
                key = images[0].get("ImageKey")
                print(f"  First image (fallback): {key}")
                return key
            elif isinstance(images, dict):
                key = images.get("ImageKey")
                print(f"  First image (fallback): {key}")
                return key

    print("  FAILED: no image found")
    return None


# All node IDs resolved
ALBUMS = {
    "wedding":     "PJgsmh",   # 2025-05-10 | Vishnu-Varsha Wedding
    "baby_shower": "H2r9JC",   # 2025-09-24 | Niveditha Baby shower
    "birthday":    "hhFGRP",   # 2025-10-18 | Sri Aadhya Birthday
    "cradle":      "Qxb5Fj",   # 2025-11-01 | Vayu Skanda Cradle
}

# Pre-filled maternity (already known)
results = {
    "maternity": {
        "image_key": "VqnMPLz",
        "x3large_url": "https://photos.smugmug.com/photos/i-VqnMPLz/0/KG7kc3wMPKBWdFkVhTsWfp4LJQCNzQkxK4ww4DZJv/X3/i-VqnMPLz-X3.jpg",
        "xlarge_url": "https://photos.smugmug.com/photos/i-VqnMPLz/0/Kd2nZQ6mNq7gxWCvG9bnXfk4xpp9JSX64npLRHHNV/XL/i-VqnMPLz-XL.jpg",
    }
}

for category, node_id in ALBUMS.items():
    print(f"\n{'='*60}")
    print(f"Category: {category}")
    print(f"{'='*60}")
    image_key = get_highlight_or_first_image(node_id)
    if image_key:
        urls = get_image_urls(image_key)
        results[category] = urls
        print(f"  X3Large: {urls['x3large_url']}")
        print(f"  XLarge:  {urls['xlarge_url']}")
    else:
        results[category] = None

print(f"\n\n{'='*60}")
print("FINAL RESULTS")
print(f"{'='*60}")
print(json.dumps(results, indent=2))
