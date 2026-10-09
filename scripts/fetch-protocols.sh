#!/usr/bin/env bash
# Fetch sponsor protocols / SAPs posted on ClinicalTrials.gov for LOCAL-ONLY evaluation.
#
# These PDFs are copyrighted sponsor documents: readable on ClinicalTrials.gov, NOT
# redistributable. This script refuses to write inside a git work tree so they can never be
# committed by accident. Mark the parent folder local-only before indexing:
#   cp corpus/private.corpus.yaml.example ~/clinical-rag-private/.corpus.yaml
#
# For each NCT id it asks the ClinicalTrials.gov API v2 for the study's large documents
# (documentSection.largeDocumentModule.largeDocs[].filename, e.g. Prot_000.pdf, SAP_001.pdf,
# Prot_SAP_000.pdf) and downloads them from the CDN:
#   https://cdn.clinicaltrials.gov/large-docs/<last 2 digits>/<NCT id>/<filename>
# saved as <NCT id>_<filename>. Results: manifest.txt (NCT id + filename) and SHA256SUMS.
#
# Usage: scripts/fetch-protocols.sh [OUT_DIR] [NCT...]
#   default OUT_DIR ~/clinical-rag-private/protocols, default NCT list = the 14 trials below
set -euo pipefail

OUT="${1:-$HOME/clinical-rag-private/protocols}"
shift || true
# Check the nearest existing ancestor BEFORE creating anything, so a refused run leaves no
# empty directory behind inside a repo.
probe="$OUT"
while [[ ! -d "$probe" ]]; do probe="$(dirname "$probe")"; done
if git -C "$probe" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "refusing: $OUT is inside a git work tree; pick a directory outside any repo" >&2
  exit 1
fi
command -v python3 >/dev/null || { echo "python3 is required to read the API JSON" >&2; exit 1; }
mkdir -p "$OUT"

# Oncology imaging-endpoint trials used in docs/journey.md section 13 (2026-10-09).
DEFAULT_TRIALS=(
  NCT04494425  # DESTINY-Breast06
  NCT03785964  # DeFi
  NCT04427072  # GeoMETry-III
  NCT03375320  # CABINET
  NCT03820986  # LEAP-003
  NCT04698187  # CMP-001
  NCT04236141  # Pola-BR (China)
  NCT03568461  # ELARA
  NCT01712490  # ECHELON-1
  NCT03517137  # COBRA
  NCT02667587  # CheckMate 548
  NCT03345095  # MIRAGE
  NCT02987543  # PROfound
  NCT03739684  # CONDOR
)
if (($#)); then TRIALS=("$@"); else TRIALS=("${DEFAULT_TRIALS[@]}"); fi

UA="clinical-rag-qa fetch-protocols (local evaluation)"
API="https://clinicaltrials.gov/api/v2/studies"
CDN="https://cdn.clinicaltrials.gov/large-docs"
ok=0; failed=()
: > "$OUT/manifest.txt.part"

for nct in "${TRIALS[@]}"; do
  if [[ ! "$nct" =~ ^NCT[0-9]{8}$ ]]; then echo "skip  $nct (not an NCT id)"; continue; fi
  json="$(curl -sSf -A "$UA" --max-time 60 "$API/$nct?fields=DocumentSection" || true)"
  files="$(printf '%s' "$json" | python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
except ValueError:
    sys.exit(0)
docs = data.get("documentSection", {}).get("largeDocumentModule", {}).get("largeDocs", [])
for doc in docs:
    name = doc.get("filename", "")
    if (doc.get("hasProtocol") or doc.get("hasSap")) and name.lower().endswith(".pdf"):
        print(name)
')"
  if [[ -z "$files" ]]; then failed+=("$nct (no protocol/SAP in the API response)"); continue; fi
  while IFS= read -r name; do
    [[ "$name" =~ ^[A-Za-z0-9_.-]+$ ]] || { failed+=("$nct/$name (unexpected filename)"); continue; }
    dest="$OUT/${nct}_${name}"
    echo "$nct $name" >> "$OUT/manifest.txt.part"
    if [[ -s "$dest" ]] && file -b "$dest" | grep -q '^PDF'; then
      echo "skip  ${nct}_${name} (already present)"; ok=$((ok+1)); continue
    fi
    if curl -sSfL -A "$UA" --max-time 300 -o "$dest.part" "$CDN/${nct: -2}/$nct/$name" \
       && file -b "$dest.part" | grep -q '^PDF'; then
      mv "$dest.part" "$dest"
      echo "ok    ${nct}_${name} ($(stat -f%z "$dest" 2>/dev/null || stat -c%s "$dest") B)"
      ok=$((ok+1))
    else
      rm -f "$dest.part"; failed+=("$nct/$name  <-  https://clinicaltrials.gov/study/$nct")
    fi
  done <<<"$files"
done

mv "$OUT/manifest.txt.part" "$OUT/manifest.txt"
( cd "$OUT" && shasum -a 256 ./*.pdf > SHA256SUMS 2>/dev/null || true )
echo "fetched: $ok documents -> $OUT"
if ((${#failed[@]})); then
  echo "not fetched (download manually from the study page's Documents tab):"
  printf '  %s\n' "${failed[@]}"
fi
