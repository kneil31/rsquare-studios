#!/usr/bin/env python3
"""
Detect faces in category cover images and output optimal background-position values.
Uses OpenCV Haar Cascade (same as Instagram AutoPoster's carousel_cover_generator.py).

Usage:
    python3 detect_cover_faces.py          # Analyze all covers, print results
    python3 detect_cover_faces.py --apply  # Analyze and update generate_dashboard.py
"""

import sys
import os
import re
import tempfile
import urllib.request
import cv2
import numpy as np
from PIL import Image

# Category covers from generate_dashboard.py
CATEGORY_COVERS = {
    "wedding": "https://photos.smugmug.com/photos/i-BvTChsc/0/LwhGTh2B2pCPDgNpjPJp8J3nCSfRNdKwd3j5CVTKN/X3/i-BvTChsc-X3.jpg",
    "engagement": "https://photos.smugmug.com/photos/i-8NfsLKT/0/LVnhsbXXV3JPcX2r2PhvcKfCj9gK9czpWsZ2VXrSH/X3/i-8NfsLKT-X3.jpg",
    "pre_wedding": "https://photos.smugmug.com/photos/i-GfR24FT/0/MHQbxRCTTvn8x7WXCkzHRjCWR96TC6TnBsTfQRFQ7/X3/i-GfR24FT-X3.jpg",
    "half_saree": "https://photos.smugmug.com/photos/i-MCmGphP/0/NZvk2KBMQzVZvJJTQh23xdmRRsvzNzGRdBgx2HX66/X3/i-MCmGphP-X3.jpg",
    "maternity": "https://photos.smugmug.com/photos/i-ZqWs3n5/0/NcPVRqqFJXR3MJfcVn45gshTHXpxkZFvfv655D3mB/X3/i-ZqWs3n5-X3.jpg",
    "baby_shower": "https://photos.smugmug.com/photos/i-3MjgbV3/0/NWkJRQPLmfwjxBJ2qLpKLS2RHVpb39NtfssFhZJxp/X3/i-3MjgbV3-X3.jpg",
    "birthday": "https://photos.smugmug.com/photos/i-Xq8BHgp/0/NGnrqRVd9gkP3r8gdC8BdwN2WrLPJT4MpQ594MTwF/X3/i-Xq8BHgp-X3.jpg",
    "cradle": "https://photos.smugmug.com/photos/i-R3QTwKk/0/KzsCGkHgZ6HKmVjVtFvwkWF9s9sRzMSTQWKPJfxQb/X3/i-R3QTwKk-X3.jpg",
    "celebrations": "https://photos.smugmug.com/photos/i-MPN69Q3/0/LGSxZbpLfpcb7j3kqQkkTdfwDHcJbV6XdxnGNq6Hb/X3/i-MPN69Q3-X3.jpg",
}

_face_cascade = None

def get_face_cascade():
    """Load face detection cascade (lazy load)."""
    global _face_cascade
    if _face_cascade is None:
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        _face_cascade = cv2.CascadeClassifier(cascade_path)
    return _face_cascade


def detect_faces(img):
    """
    Detect faces in a PIL Image.

    Returns:
        list of (x, y, w, h) tuples for each detected face
    """
    cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    cascade = get_face_cascade()
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    return faces if len(faces) > 0 else []


def face_position_to_css(faces, img_width, img_height):
    """
    Convert detected face positions to CSS background-position.

    The category tiles are wider than tall (aspect-ratio ~2:1 on desktop, 16:9 on mobile).
    background-position X% Y% means the point at X% of the image aligns with X% of the container.
    For faces, we want the face center to be visible in the tile.

    Returns:
        str: CSS background-position value (e.g., "center 25%")
    """
    if len(faces) == 0:
        return "center center"

    # Find bounding box center of all faces
    min_x = min(x for (x, y, w, h) in faces)
    max_x = max(x + w for (x, y, w, h) in faces)
    min_y = min(y for (x, y, w, h) in faces)
    max_y = max(y + h for (x, y, w, h) in faces)

    face_center_x = (min_x + max_x) / 2
    face_center_y = (min_y + max_y) / 2

    x_pct = round((face_center_x / img_width) * 100)
    y_pct = round((face_center_y / img_height) * 100)

    # Horizontal: if close to center (40-60%), use "center" for cleaner CSS
    h_val = "center" if 40 <= x_pct <= 60 else f"{x_pct}%"
    v_val = f"{y_pct}%"

    return f"{h_val} {v_val}"


def download_image(url):
    """Download image from URL and return as PIL Image."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = resp.read()
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    tmp.write(data)
    tmp.close()
    img = Image.open(tmp.name)
    img.load()
    os.unlink(tmp.name)
    return img


def analyze_covers():
    """Download each cover image, detect faces, return CSS positions."""
    results = {}
    print("Analyzing category cover images for face positions...\n")

    for cat, url in CATEGORY_COVERS.items():
        print(f"  {cat}:")
        try:
            img = download_image(url)
            print(f"    Downloaded: {img.width}x{img.height}")
            faces = detect_faces(img)
            num_faces = len(faces) if hasattr(faces, '__len__') else 0
            css_pos = face_position_to_css(faces, img.width, img.height)

            if num_faces > 0:
                print(f"    Faces found: {num_faces}")
                for i, (x, y, w, h) in enumerate(faces):
                    print(f"      Face {i+1}: ({x},{y}) {w}x{h}")
            else:
                print(f"    No faces detected — using center")

            print(f"    CSS position: {css_pos}")
            results[cat] = css_pos
        except Exception as e:
            print(f"    ERROR: {e}")
            results[cat] = "center center"
        print()

    return results


def apply_to_generator(results):
    """Update category_covers in generate_dashboard.py with face-detected positions."""
    gen_path = os.path.join(os.path.dirname(__file__), "generate_dashboard.py")
    with open(gen_path, "r") as f:
        content = f.read()

    for cat, css_pos in results.items():
        # Match the tuple pattern for this category
        pattern = rf'("{cat}":\s*\("[^"]+",\s*")([^"]+)("\))'
        match = re.search(pattern, content)
        if match:
            old_pos = match.group(2)
            if old_pos != css_pos:
                content = content[:match.start(2)] + css_pos + content[match.end(2):]
                print(f"  {cat}: {old_pos} → {css_pos}")
            else:
                print(f"  {cat}: {css_pos} (unchanged)")
        else:
            print(f"  {cat}: pattern not found in generator")

    with open(gen_path, "w") as f:
        f.write(content)
    print("\nUpdated generate_dashboard.py")


if __name__ == "__main__":
    results = analyze_covers()

    print("\n" + "=" * 50)
    print("Summary — CSS background-position values:")
    print("=" * 50)
    for cat, pos in results.items():
        print(f"  {cat}: {pos}")

    if "--apply" in sys.argv:
        print("\nApplying to generate_dashboard.py...")
        apply_to_generator(results)
    else:
        print("\nRun with --apply to update generate_dashboard.py")
