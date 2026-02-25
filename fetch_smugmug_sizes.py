#!/usr/bin/env python3
"""Fetch SmugMug image size URLs for given image keys using OAuth1."""

import json
from requests_oauthlib import OAuth1Session

with open("/Users/ram/.smugmug_config.json") as f:
    config = json.load(f)

session = OAuth1Session(
    client_key=config["api_key"],
    client_secret=config["api_secret"],
    resource_owner_key=config["access_token"],
    resource_owner_secret=config["access_token_secret"],
)

IMAGE_KEYS = {
    "ZqWs3n5": "maternity",
    "BvTChsc": "wedding",
    "Xq8BHgp": "birthday",
}

for key, label in IMAGE_KEYS.items():
    url = f"https://api.smugmug.com/api/v2/image/{key}!sizes"
    resp = session.get(url, headers={"Accept": "application/json"})

    print(f"\n--- {label.upper()} (ImageKey: {key}) ---")
    print(f"Status: {resp.status_code}")

    if resp.status_code == 200:
        data = resp.json()
        sizes = data.get("Response", {}).get("ImageSizes", {})
        x3large = sizes.get("X3LargeImageUrl", "N/A")
        xlarge = sizes.get("XLargeImageUrl", "N/A")
        print(f"X3LargeImageUrl: {x3large}")
        print(f"XLargeImageUrl:  {xlarge}")
    else:
        print(f"Error: {resp.text[:300]}")
