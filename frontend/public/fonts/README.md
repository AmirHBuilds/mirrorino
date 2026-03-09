# Local web fonts (offline / localhost-safe)

Your app is configured to load fonts from local files in this folder (`/fonts/*.woff2`).

## Why this works

Google Fonts usually needs these external hosts:

- `fonts.googleapis.com` (CSS)
- `fonts.gstatic.com` (font files)

If your server cannot access those domains, font loading fails. Local files avoid that dependency.

## Required files

Place these exact filenames in `frontend/public/fonts/`:

- `syne-400.woff2`
- `syne-500.woff2`
- `syne-600.woff2`
- `syne-700.woff2`
- `syne-800.woff2`
- `ibm-plex-mono-400.woff2`
- `ibm-plex-mono-500.woff2`
- `vazir-400.woff2`
- `vazir-500.woff2`
- `vazir-700.woff2`

## Exact setup steps

### 1) Download once on any machine that has internet

From project root:

```bash
bash frontend/scripts/download-google-fonts.sh
```

This script fetches the Google Fonts CSS and downloads the required `.woff2` files with the exact names above.

### 2) Move/copy the files to your offline server

Copy the whole folder:

```bash
frontend/public/fonts/
```

into the same path on your server/project.

### 3) Build/restart frontend

```bash
docker compose up -d --build frontend
```

(or your normal Nuxt deploy/restart command)

### 4) Verify in browser

Open DevTools → Network and confirm:

- font requests are `/fonts/*.woff2`
- no requests go to `fonts.googleapis.com` or `fonts.gstatic.com`

## Optional server check (Nginx)

Ensure `.woff2` is served with a font MIME type. For Nginx:

```nginx
types {
  font/woff2 woff2;
}
```

Most modern Nginx images already include this in `mime.types`, so this step is usually not required.


## Persian font (Vazir) setup

To use Vazir for Persian text across the website, put these files in this same folder:

- `frontend/public/fonts/vazir-400.woff2`
- `frontend/public/fonts/vazir-500.woff2`
- `frontend/public/fonts/vazir-700.woff2`

The frontend CSS is already configured to load these files. Once copied, rebuild/restart the frontend.
