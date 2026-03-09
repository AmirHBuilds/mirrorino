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

mapfile -t FONT_URLS < <(sed -n "s/.*url(\(https:\/\/fonts\.gstatic\.com[^)]*\.woff2\)).*/\1/p" "${CSS_FILE}")

if [[ ${#FONT_URLS[@]} -eq 0 ]]; then
  echo "No .woff2 URLs found in Google Fonts CSS." >&2
  exit 1
fi

declare -A EXPECTED_NAMES=(
  ["Syne:400"]="syne-400.woff2"
  ["Syne:500"]="syne-500.woff2"
  ["Syne:600"]="syne-600.woff2"
  ["Syne:700"]="syne-700.woff2"
  ["Syne:800"]="syne-800.woff2"
  ["IBM Plex Mono:400"]="ibm-plex-mono-400.woff2"
  ["IBM Plex Mono:500"]="ibm-plex-mono-500.woff2"
)

current_family=""
current_weight=""

declare -A SELECTED_URLS

comment_re="^[[:space:]]*/\*[[:space:]]([^*]+)[[:space:]]\*/[[:space:]]*$"
weight_re="font-weight:[[:space:]]*([0-9]+)"
url_re="url\((https://fonts\.gstatic\.com[^)]*\.woff2)\)"

while IFS= read -r line; do
  if [[ "$line" =~ $comment_re ]]; then
    current_family="${BASH_REMATCH[1]}"
    current_weight=""
  elif [[ "$line" =~ $weight_re ]]; then
    current_weight="${BASH_REMATCH[1]}"
  elif [[ "$line" =~ $url_re ]]; then
    if [[ "$line" == *"latin"* ]] && [[ -n "$current_family" ]] && [[ -n "$current_weight" ]]; then
      key="${current_family}:${current_weight}"
      if [[ -n "${EXPECTED_NAMES[$key]:-}" ]]; then
        SELECTED_URLS["$key"]="${BASH_REMATCH[1]}"
      fi
    fi
  fi
done < "${CSS_FILE}"

for key in "${!EXPECTED_NAMES[@]}"; do
  if [[ -z "${SELECTED_URLS[$key]:-}" ]]; then
    echo "Missing URL for ${key} in stylesheet." >&2
    exit 1
  fi

  out_file="${OUT_DIR}/${EXPECTED_NAMES[$key]}"
  echo "Downloading ${EXPECTED_NAMES[$key]}"
  curl -fsSL -A "${USER_AGENT}" "${SELECTED_URLS[$key]}" -o "${out_file}"
done

echo "Done. Downloaded local fonts to ${OUT_DIR}"
