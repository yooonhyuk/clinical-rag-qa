#!/usr/bin/env bash
# Verify the 폐쇄망 (closed-network) deployment started with docker-compose.offline.yml.
# Run in the extracted bundle (after ./install.sh) or from the repository root (`make
# verify-offline`) while the offline stack is up. Exit code 0 only if every check passes.
#
#   1. topology  db/ollama/api are only on internal networks and publish no ports;
#                ui publishes 8501 on 127.0.0.1 only
#   2. routes    no container (ui included) has an IPv4 default route
#   3. egress    from every container: 1.1.1.1:443, 8.8.8.8:53, pypi.org:443,
#                registry.ollama.ai:443, api.anthropic.com:443, host.docker.internal:11434
#                must all fail
#   4. ui        Streamlit runs as a non-root uid with no capabilities; the host reaches it on
#                127.0.0.1:8501
#   5. internal  api -> db, api -> ollama, ui -> api work
#   6. app       index the sample documents, answer a Korean question with a citation, refuse
#                an out-of-scope question, analyze a sample DICOM file (all on the internal net)
set -uo pipefail
cd "$(dirname "$0")"
[ -f docker-compose.offline.yml ] || cd ..
COMPOSE=(docker compose -f docker-compose.yml -f docker-compose.offline.yml)
SERVICES=(db ollama api ui)
UI_PORT="${UI_PORT:-8501}"
EGRESS_TARGETS=(1.1.1.1:443 8.8.8.8:53 pypi.org:443 registry.ollama.ai:443
                api.anthropic.com:443 host.docker.internal:11434)
ASK_QUESTION="${ASK_QUESTION:-업로드할 수 있는 파일 형식은 무엇인가요?}"
REFUSE_QUESTION="${REFUSE_QUESTION:-항암제 용량을 어떻게 조절해야 하나요?}"

fail=0
pass() { printf '  PASS  %s\n' "$*"; }
bad() { printf '  FAIL  %s\n' "$*"; fail=1; }
section() { printf '\n[%s]\n' "$*"; }
cid() { "${COMPOSE[@]}" ps -q "$1"; }

for svc in "${SERVICES[@]}"; do
  if [ -z "$(cid "$svc")" ]; then
    echo "service '$svc' is not running; start it with ./install.sh or make offline-up" >&2
    exit 2
  fi
done

section "1. topology"
for svc in "${SERVICES[@]}"; do
  id=$(cid "$svc")
  nets=$(docker inspect -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}' "$id")
  ports=$(docker port "$id" | tr '\n' ' ')
  for net in $nets; do
    internal=$(docker network inspect -f '{{.Internal}}' "$net")
    if [ "$internal" = "true" ]; then
      pass "$svc on $net (internal)"
    elif [ "$svc" = ui ]; then
      pass "$svc on $net (non-internal; egress closed by route removal, checked below)"
    else
      bad "$svc on non-internal network $net"
    fi
  done
  if [ "$svc" = ui ]; then
    if [ -n "$ports" ] && ! grep -qvE "^127\.0\.0\.1:" <<<"$(docker port "$id" | sed 's/.* -> //')"; then
      pass "ui ports bound to loopback only: $ports"
    else
      bad "ui ports must be 127.0.0.1 only: '${ports:-none}'"
    fi
  elif [ -z "$ports" ]; then
    pass "$svc publishes no ports"
  else
    bad "$svc publishes ports: $ports"
  fi
done

section "2. routes (no IPv4 default route in any container)"
for svc in "${SERVICES[@]}"; do
  routes=$(docker exec "$(cid "$svc")" cat /proc/net/route)
  if awk 'NR > 1 && $2 == "00000000" && $8 == "00000000" { found = 1 } END { exit !found }' <<<"$routes"; then
    bad "$svc has a default route"
  else
    pass "$svc has no default route"
  fi
done

section "3. egress (every attempt must fail)"
for svc in "${SERVICES[@]}"; do
  for target in "${EGRESS_TARGETS[@]}"; do
    host=${target%:*} port=${target##*:}
    if docker exec "$(cid "$svc")" timeout 6 bash -c "exec 3<>/dev/tcp/$host/$port" 2>/dev/null; then
      bad "$svc -> $target REACHABLE"
    else
      pass "$svc -> $target blocked"
    fi
  done
done

section "4. ui process and host access"
status=$(docker exec "$(cid ui)" sh -c 'grep -E "^(Uid|CapEff):" /proc/1/status' | tr -s '\t ' ' ')
uid=$(awk '/^Uid:/ {print $2}' <<<"$status")
capeff=$(awk '/^CapEff:/ {print $2}' <<<"$status")
if [ -n "$uid" ] && [ "$uid" != 0 ] && [ "$capeff" = 0000000000000000 ]; then
  pass "streamlit runs as uid $uid with CapEff=$capeff"
else
  bad "streamlit uid=$uid CapEff=$capeff (want non-root, no capabilities)"
fi
code=$(curl -s -o /dev/null -m 10 -w '%{http_code}' "http://127.0.0.1:$UI_PORT/_stcore/health" || true)
if [ "$code" = 200 ]; then pass "host -> 127.0.0.1:$UI_PORT ui health 200"; else bad "host -> ui health: '$code'"; fi

section "5. internal connectivity"
probe_ok() {  # $1=service $2=host:port
  docker exec "$(cid "$1")" timeout 6 bash -c "exec 3<>/dev/tcp/${2%:*}/${2##*:}" 2>/dev/null
}
for pair in api:db:5432 api:ollama:11434 ui:api:8000; do
  svc=${pair%%:*} target=${pair#*:}
  if probe_ok "$svc" "$target"; then pass "$svc -> $target"; else bad "$svc -> $target unreachable"; fi
done

section "6. app answers on the internal network"
# Runs inside the ui container as the app user, i.e. along the same path the UI uses.
docker exec -i -u 10001 -e ASK_QUESTION="$ASK_QUESTION" -e REFUSE_QUESTION="$REFUSE_QUESTION" \
  "$(cid ui)" python - <<'PY' || fail=1
import os
import sys

import httpx

api = httpx.Client(base_url=os.environ.get("API_BASE_URL", "http://api:8000"), timeout=600)
ok = True


def check(cond: bool, label: str) -> None:
    global ok
    print(f"  {'PASS' if cond else 'FAIL'}  {label}")
    ok &= cond


health = api.get("/api/health").json()
check(health["status"] == "ok", f"health status={health['status']} llm={health['llmModel']['detail']}")

idx = api.post("/api/index", json={}).json()
chunks = sum(d["chunkCount"] for d in idx["details"])
check(idx["failed"] == 0 and idx["indexed"] + idx["skippedDuplicate"] == idx["total"] > 0,
      f"index total={idx['total']} indexed={idx['indexed']} "
      f"duplicate={idx['skippedDuplicate']} failed={idx['failed']} new_chunks={chunks}")

ans = api.post("/api/ask", json={"question": os.environ["ASK_QUESTION"]}).json()
cites = [f"{s['fileName']}#{s.get('sectionTitle') or s.get('pageNumber')}" for s in ans["sources"]]
check(not ans["refused"] and ans["answer"].strip() != "" and len(cites) > 0,
      f"answered with citation {cites} in {ans['latencyMs']}")
print(f"        Q: {os.environ['ASK_QUESTION']}\n        A: {ans['answer'][:200]!r}")

ref = api.post("/api/ask", json={"question": os.environ["REFUSE_QUESTION"]}).json()
check(ref["refused"], f"refused out-of-scope question ({ref['refusalReason']})")

dcm = api.post("/api/dicom/analyze",
               json={"filePath": "sample-phi-nested-private.dcm", "explain": False}).json()
check(dcm.get("counts") is not None and dcm["privacyWarnings"] != [],
      f"DICOM analyze: iod={dcm['layer1']['iod']} privacy_warnings={len(dcm['privacyWarnings'])}")
sys.exit(0 if ok else 1)
PY

echo
if [ $fail -eq 0 ]; then echo "verify-offline: PASS"; else echo "verify-offline: FAIL"; fi
exit $fail
