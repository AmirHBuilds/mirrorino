#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${ROOT_DIR}/public/fonts"
TMP_DIR="$(mktemp -d)"
CSS_FILE="${TMP_DIR}/google-fonts.css"

CSS_URL='https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Syne:wght@400;500;600;700;800&display=swap'
USER_AGENT='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'

cleanup() {
  rm -rf "${TMP_DIR}"
}
trap cleanup EXIT

mkdir -p "${OUT_DIR}"

echo "Fetching font stylesheet..."
curl -fsSL -A "${USER_AGENT}" "${CSS_URL}" -o "${CSS_FILE}"

declare -A EXPECTED_NAMES=(
  ["Syne:400"]="syne-400.woff2"
  ["Syne:500"]="syne-500.woff2"
  ["Syne:600"]="syne-600.woff2"
  ["Syne:700"]="syne-700.woff2"
  ["Syne:800"]="syne-800.woff2"
  ["IBM Plex Mono:400"]="ibm-plex-mono-400.woff2"
  ["IBM Plex Mono:500"]="ibm-plex-mono-500.woff2"
)

# Parse CSS blocks and emit: key|is_latin|url
mapfile -t PARSED_ROWS < <(
  awk '
    function trim(s) { gsub(/^[ \t]+|[ \t]+$/, "", s); return s }
    
    # Extract font family name (handles both single and double quotes using \x27)
    /font-family:/ {
      if (match($0, /font-family:[[:space:]]*[\x27"]([^\x27"]+)[\x27"]/, m)) family=trim(m[1])
    }
    /font-weight:/ {
      if (match($0, /font-weight:[[:space:]]*([0-9]+)/, m)) weight=m[1]
    }
    /src:/ {
      if (match($0, /url\((https:\/\/fonts\.gstatic\.com[^)]*\.woff2)\)/, m)) url=m[1]
    }
    /unicode-range:/ {
      if (index($0, "U+0000-00FF") > 0) latin=1
    }
    /}/ {
      if (family != "" && weight != "" && url != "") {
        printf "%s:%s|%d|%s\n", family, weight, latin, url
      }
      family=""; weight=""; url=""; latin=0
    }
  ' "${CSS_FILE}"
)

if [[ ${#PARSED_ROWS[@]} -eq 0 ]]; then
  echo "No .woff2 URLs found in Google Fonts CSS." >&2
  exit 1
fi

declare -A LATIN_URLS
declare -A FALLBACK_URLS

for row in "${PARSED_ROWS[@]}"; do
  IFS='|' read -r key is_latin url <<<"${row}"
  [[ -n "${EXPECTED_NAMES[$key]:-}" ]] || continue

  if [[ "$is_latin" == "1" ]]; then
    LATIN_URLS["$key"]="$url"
  elif [[ -z "${FALLBACK_URLS[$key]:-}" ]]; then
    FALLBACK_URLS["$key"]="$url"
  fi
done

for key in "${!EXPECTED_NAMES[@]}"; do
  selected_url="${LATIN_URLS[$key]:-${FALLBACK_URLS[$key]:-}}"
  if [[ -z "${selected_url}" ]]; then
    echo "Missing URL for ${key} in stylesheet." >&2
    exit 1
  fi

  out_file="${OUT_DIR}/${EXPECTED_NAMES[$key]}"
  echo "Downloading ${EXPECTED_NAMES[$key]}"
  curl -fsSL -A "${USER_AGENT}" "${selected_url}" -o "${out_file}"
done

echo "Done. Downloaded local fonts to ${OUT_DIR}"