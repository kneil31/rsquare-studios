# CLAUDE.md — Krithin Neel Family Memories

Subproject of rsquare-studios-dashboard. Family memories page hosted on GitHub Pages.

**Last Updated:** 2026-02-19

## Overview

- **Live URL:** https://kneil31.github.io/krithin-neel/
- **GitHub Repo:** kneil31/krithin-neel (public)
- **Generator:** `generate_krithin_page.py` → `output/index.html`
- **No password protection** (removed for now)

## Design

- Warm pastel baby/family theme (cream #FFF8F0 bg, peach #E8A87C accent)
- Nunito font, photo tiles with gradient overlay (same style as rsquare-studios dashboard)
- 3 tabs: Krithin | Monika | Family
- Mobile-first (shared via WhatsApp)
- Gallery tiles: 3/4 aspect ratio, 2-column mobile, 3-column desktop
- Video tiles: 16/9 aspect ratio, always 2-column grid, YouTube thumbnails as background

## Data

- Image counts from `../album_stats.json` (keyed by SmugMug node_id)
- Cover images from `cover_images.json` (SmugMug highlight images, medium/large/xlarge)
- Older Monika albums (2023) don't have node_ids — show emoji icon fallback tiles
- Gallery URLs, video URLs, and metadata hardcoded in generator

## Content

| Tab | Galleries |
|-----|-----------|
| Krithin | Fresh 48, Cradle Ceremony, Sankranthi 2025, Temple Visit, Cake Smash, Adugulu, Halloween, New Year 2026 |
| Monika | Baby Shower, Maternity 2024, Birthday 2023, Girls Shoot 2023, Maternity 2023 |
| Family | Moniel Housewarming, Sankranthi 2025 |

**Videos:** 9 in Krithin tab, 1 in Monika tab (all with YouTube URLs and thumbnail tiles)

## Workflow

```bash
# Regenerate
cd krithin-neel
python3 generate_krithin_page.py

# Deploy to GitHub Pages
cp output/index.html /tmp/krithin-neel/
cd /tmp/krithin-neel && git add . && git commit -m "description" && git push
```

## Notes

- "Moniel Housewarming" not "Half Saree" (album name: Monika-Neel HW)
- Halloween album is "KAYU Halloween" in album_stats (node_id: K9g7f3)
- Video tile thumbnails use `https://img.youtube.com/vi/{VIDEO_ID}/hqdefault.jpg`
- Skipped video: `dkpibn_N4EM` (Cradle Ceremony review only, may add later)
