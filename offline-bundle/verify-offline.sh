#!/usr/bin/env bash
# Verify the 폐쇄망 setup: api / ollama must NOT reach the internet, but must reach each other.
set -uo pipefail
cd "$(dirname "$0")"
[ -f docker-compose.offline.yml ] || cd ..
COMPOSE=(docker compose -f docker-compose.yml -f docker-compose.offline.yml)

probe() {  # $1=url ; prints REACHABLE / BLOCKED (...) as seen from the api container
  "${COMPOSE[@]}" exec -T api python - "$1" <<'PY'
import sys, urllib.request
try:
    urllib.request.urlopen(sys.argv[1], timeout=5)
    print("REACHABLE")
except Exception as exc:
    print(f"BLOCKED ({type(exc).__name__})")
PY
}

fail=0
for url in https://pypi.org https://api.anthropic.com https://registry.ollama.ai; do
  result=$(probe "$url")
  echo "api -> $url : $result"
  [[ "$result" == BLOCKED* ]] || fail=1
done
result=$(probe http://ollama:11434/api/tags)
echo "api -> ollama (internal) : $result"
[[ "$result" == REACHABLE ]] || fail=1

if [ $fail -eq 0 ]; then echo "verify-offline: PASS"; else echo "verify-offline: FAIL"; fi
exit $fail
