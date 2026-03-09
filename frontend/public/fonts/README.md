# Local web fonts

Your app now loads fonts from local disk via `/fonts/*.woff2` files in this folder.

## What the code used before (external DNS/CDN)

Previously, fonts were loaded from Google Fonts using:

- CSS endpoint DNS: `fonts.googleapis.com`
- Font files DNS/CDN: `fonts.gstatic.com`

The CSS URL used by the app was:

`https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Syne:wght@400;500;600;700;800&display=swap`

## Files you must place here

- `syne-400.woff2`
- `syne-500.woff2`
- `syne-600.woff2`
- `syne-700.woff2`
- `syne-800.woff2`
- `ibm-plex-mono-400.woff2`
- `ibm-plex-mono-500.woff2`

## How to download them

### Option A (easy): from Google Fonts website

1. Open https://fonts.google.com/specimen/Syne and https://fonts.google.com/specimen/IBM+Plex+Mono
2. Download the family files.
3. Convert/pick `.woff2` files for the required weights above.
4. Rename to the exact filenames listed above and copy into this folder.

### Option B (exact same source the code previously used)

On a machine with internet access, fetch the CSS from `fonts.googleapis.com`, then download every `https://fonts.gstatic.com/...woff2` URL found in it.

Example helper flow:

```bash
mkdir -p frontend/public/fonts
curl -L -A "Mozilla/5.0" \
  'https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Syne:wght@400;500;600;700;800&display=swap' \
  -o /tmp/downloadino-fonts.css

# open /tmp/downloadino-fonts.css, copy the .woff2 URLs from fonts.gstatic.com,
# download them, then rename to:
# syne-400.woff2 syne-500.woff2 syne-600.woff2 syne-700.woff2 syne-800.woff2
# ibm-plex-mono-400.woff2 ibm-plex-mono-500.woff2
```

After files are in this folder, rebuild/restart frontend.
