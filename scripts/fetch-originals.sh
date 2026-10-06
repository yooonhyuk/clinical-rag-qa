#!/usr/bin/env bash
# Fetch copyrighted source documents (response criteria papers, QIBA profiles,
# sponsor protocols) for LOCAL-ONLY evaluation.
#
# These files are NOT redistributable (Elsevier / ASCO / ASH / RSNA / sponsor
# copyright). This script refuses to write inside a git work tree so they
# can never be committed by accident. Eval numbers computed on them are
# reported as "local-only, not reproducible from the public repo".
#
# Usage: scripts/fetch-originals.sh [OUT_DIR]   (default: ~/clinical-rag-private/originals)
set -euo pipefail

OUT="${1:-$HOME/clinical-rag-private/originals}"
# Check the nearest existing ancestor BEFORE creating anything, so a refused run leaves no
# empty directory behind inside a repo.
probe="$OUT"
while [[ ! -d "$probe" ]]; do probe="$(dirname "$probe")"; done
if git -C "$probe" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "refusing: $OUT is inside a git work tree; pick a directory outside any repo" >&2
  exit 1
fi
mkdir -p "$OUT"

UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
ok=0; manual=()

# name | url | landing page (for manual download when the url is blocked)
SOURCES=(
  "recist_1.1_eisenhauer_2009.pdf|https://project.eortc.org/recist/wp-content/uploads/sites/4/2015/03/RECISTGuidelines.pdf|https://doi.org/10.1016/j.ejca.2008.10.026"
  "irecist_seymour_2017.pdf|https://europepmc.org/articles/PMC5648544?pdf=render|https://pmc.ncbi.nlm.nih.gov/articles/PMC5648544/"
  "rano_2.0_wen_2023.pdf|https://europepmc.org/articles/PMC10860967?pdf=render|https://pmc.ncbi.nlm.nih.gov/articles/PMC10860967/"
  "lugano_cheson_2014.pdf|https://europepmc.org/articles/PMC4979083?pdf=render|https://pmc.ncbi.nlm.nih.gov/articles/PMC4979083/"
  "lugano_imaging_barrington_2014.pdf|https://europepmc.org/articles/PMC5015423?pdf=render|https://pmc.ncbi.nlm.nih.gov/articles/PMC5015423/"
  "lyric_cheson_2016.pdf||https://doi.org/10.1182/blood-2016-05-718528"
  "qiba_fdg_pet_ct_v1.14_2023.pdf|https://qibawiki.rsna.org/images/c/c7/QIBA_FDG-PET_Profile_v114.pdf|https://qibawiki.rsna.org/index.php/Profiles"
  "qiba_ct_tumor_volume_change_2022.pdf|https://qibawiki.rsna.org/images/3/3c/QIBACTVol_TumorVolumeChange_2022Jul21.pdf|https://qibawiki.rsna.org/index.php/Profiles"
  "protocol_NCT04489771.pdf|https://cdn.clinicaltrials.gov/large-docs/71/NCT04489771/Prot_SAP_000.pdf|https://clinicaltrials.gov/study/NCT04489771"
  "protocol_NCT03761056.pdf|https://cdn.clinicaltrials.gov/large-docs/56/NCT03761056/Prot_000.pdf|https://clinicaltrials.gov/study/NCT03761056"
)

for row in "${SOURCES[@]}"; do
  IFS='|' read -r name url landing <<<"$row"
  dest="$OUT/$name"
  if [[ -s "$dest" ]] && file -b "$dest" | grep -q '^PDF'; then
    echo "skip  $name (already present)"; ok=$((ok+1)); continue
  fi
  if [[ -n "$url" ]] && curl -sSL -A "$UA" --max-time 120 -o "$dest.part" "$url" \
     && file -b "$dest.part" | grep -q '^PDF'; then
    mv "$dest.part" "$dest"; echo "ok    $name ($(stat -f%z "$dest" 2>/dev/null || stat -c%s "$dest") B)"; ok=$((ok+1))
  else
    rm -f "$dest.part"; manual+=("$name  <-  $landing")
  fi
done

( cd "$OUT" && shasum -a 256 ./*.pdf > SHA256SUMS 2>/dev/null || true )
echo "fetched: $ok / ${#SOURCES[@]}  ->  $OUT"
if ((${#manual[@]})); then
  echo "download these manually in a browser and save under $OUT with the given name:"
  printf '  %s\n' "${manual[@]}"
fi
