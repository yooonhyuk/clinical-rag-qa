# 003. 폐쇄망 프로필에서 ui 컨테이너의 외부 접속 경로(ui_edge)

- 상태: 해결 (ui의 default route 제거 + verify-offline.sh 강화)
- GitHub: https://github.com/yooonhyuk/clinical-rag-qa/issues/4
- 발견: 2026-10-06, 오프라인 번들 첫 실제 설치·검증
- 영향 범위: `docker-compose.offline.yml`의 ui 서비스, `offline-bundle/verify-offline.sh`
- 관련 코드: `frontend/no_egress_entrypoint.py`(신규), `frontend/Dockerfile`, `docker-compose.offline.yml`, `offline-bundle/verify-offline.sh`, `tests/unit/test_offline_bundle.py`

## 증상

폐쇄망 프로필은 db·ollama·api를 `internal: true` 네트워크에만 연결합니다. 그런데 Docker는 internal 네트워크에서 호스트 포트를 열지 못하기 때문에 ui만 일반 bridge 네트워크 `ui_edge`에 추가로 연결했습니다. 이 때문에 ui 컨테이너에 default route가 생겼고, 인터넷으로 나갈 수 있었습니다.

Docker Desktop 29.5.2(macOS arm64)에서 이전 설정으로 ui를 띄우고 새 `verify-offline.sh`를 돌린 결과입니다.

```
  FAIL  ui has a default route
  FAIL  ui -> 1.1.1.1:443 REACHABLE
  FAIL  ui -> 8.8.8.8:53 REACHABLE
  FAIL  ui -> pypi.org:443 REACHABLE
  FAIL  ui -> registry.ollama.ai:443 REACHABLE
  FAIL  ui -> api.anthropic.com:443 REACHABLE
  FAIL  ui -> host.docker.internal:11434 REACHABLE
verify-offline: FAIL
```

기존 `verify-offline.sh`는 api 컨테이너에서 HTTP 3곳만 확인했기 때문에 이 경로를 잡지 못했습니다. db·ollama·ui, 포트 바인딩, 앱 응답 여부도 확인하지 않았습니다.

## 시도한 방법 (Docker Desktop 29.5.2에서 직접 확인)

| 방법 | 127.0.0.1 포트 | 외부 접속 |
|---|---|---|
| 일반 bridge (이전 설정) | 열림 | **가능** |
| `internal: true` + `ports` | **열리지 않음** | 차단 |
| bridge + `com.docker.network.bridge.enable_ip_masquerade=false` | 열림 | **가능** (Docker Desktop은 VM 밖 네트워크 스택에서 다시 NAT한다) |
| `com.docker.network.bridge.gateway_mode_ipv4=isolated` | - | internal 네트워크에만 허용되어 생성 실패 |
| internal 네트워크에 `gw-priority`를 높게 | 열림 | **가능** (default route는 여전히 edge 쪽) |
| **edge 연결 + 컨테이너 안에서 default route 삭제** | **열림** | **차단** |

Docker 설정만으로는 "호스트 포트 공개"와 "외부 접속 차단"을 동시에 만족시킬 수 없었습니다.

## 해결

ui 컨테이너가 시작할 때 자기 network namespace의 default route를 직접 지웁니다(`frontend/no_egress_entrypoint.py`).

1. compose가 `user: "0:0"`, `cap_drop: [ALL]`, `cap_add: [NET_ADMIN, SETUID, SETGID]`, `no-new-privileges`로 entrypoint를 실행합니다.
2. entrypoint가 `/proc/net/route`에서 default route를 찾아 `SIOCDELRT` ioctl로 지웁니다. 표준 라이브러리만 쓰므로 이미지에 iproute2를 추가할 필요가 없습니다. 지운 뒤 다시 확인하고, 남아 있으면 시작을 거부합니다.
3. `setgid/setuid(10001)`로 내려갑니다. root가 아닌 uid로 바뀌면 커널이 permitted/effective capability를 모두 비우므로 Streamlit 프로세스는 route를 다시 추가할 수 없습니다(`CapEff: 0000000000000000`).
4. Streamlit을 `exec`합니다.

직접 연결된 서브넷은 그대로 동작합니다. internal 네트워크로 api에 붙고, 공개 포트 트래픽은 `ui_edge` bridge gateway에서 들어옵니다. 외부 DNS 조회도 막기 위해 `dns: [127.0.0.1]`로 Docker 내장 DNS의 상위 서버를 없는 주소로 지정했습니다. 서비스 이름(`api`)은 계속 해석됩니다. Linux 엔진에서 NAT도 끄도록 `ui_edge`에 `enable_ip_masquerade=false`를 함께 두었습니다(Docker Desktop에서는 효과 없음, 이중 방어).

`verify-offline.sh`는 이제 다음을 모두 확인하고, 하나라도 실패하면 종료 코드 1을 냅니다.

1. 토폴로지: db·ollama·api는 internal 네트워크에만 연결되어 있고 포트를 공개하지 않는다. ui는 127.0.0.1에만 공개한다.
2. 모든 컨테이너에 IPv4 default route가 없다.
3. 모든 컨테이너에서 1.1.1.1:443, 8.8.8.8:53, pypi.org:443, registry.ollama.ai:443, api.anthropic.com:443, host.docker.internal:11434 접속이 실패한다.
4. Streamlit이 root가 아닌 uid, capability 0으로 실행되고, 호스트에서 127.0.0.1:8501에 접속된다.
5. api→db, api→ollama, ui→api 내부 통신이 된다.
6. ui 컨테이너에서 api를 통해 샘플 인덱싱, 한국어 질문 답변(출처 포함), 범위 밖 질문 거절, DICOM 분석이 된다.

## 검증 (2026-10-06, Docker Desktop 29.5.2, macOS arm64)

`PLATFORM=linux/arm64 WHEELS=0 LLM_MODEL=medgemma:4b make bundle`로 만든 번들을 임시 폴더에 풀고 `install.sh` → `verify-offline.sh`를 실행했습니다. 47개 항목 모두 PASS였습니다(위 6단계, 질문 답변은 CPU의 medgemma:4b로 약 26초). 이전 ui 설정으로 되돌리면 위 "증상"처럼 ui 관련 7개 항목이 FAIL입니다(음성 대조).

`tests/unit/test_offline_bundle.py`는 route 파싱, `struct rtentry` 배치, entrypoint 실행 순서(route 삭제 → 권한 하강 → exec), compose 하드닝 설정을 고정합니다.

## 남은 한계

- 호스트에서 `docker exec -u 0`으로 들어가면 NET_ADMIN이 bounding set에 남아 있어 route를 다시 추가할 수 있습니다. 이 권한은 Docker를 다룰 수 있는 호스트 관리자에게만 있고, 그 관리자는 어차피 네트워크 설정 전체를 바꿀 수 있습니다.
- ui는 `ui_edge` 서브넷 안의 주소(bridge gateway = Docker 호스트/VM)에는 닿을 수 있습니다. 인터넷 경로는 아니지만, Docker 호스트에 0.0.0.0으로 열린 다른 서비스가 있다면 그쪽으로는 접속할 수 있습니다.
- IPv4만 다룹니다. compose 네트워크는 IPv6가 기본으로 꺼져 있고, 켤 경우 같은 방식으로 IPv6 default route도 지워야 합니다.
