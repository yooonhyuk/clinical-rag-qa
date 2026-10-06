# 004. compose가 호스트 Ollama 설정을 무시하고 포트를 모든 인터페이스에 공개

- 상태: 해결
- GitHub: https://github.com/yooonhyuk/clinical-rag-qa/issues/5
- 발견: 2026-10-06, 전체 `docker compose build/up` 첫 실행
- 영향 범위: `docker-compose.yml`, `Makefile`
- 관련 코드: `docker-compose.yml`, `docker-compose.host-ollama.yml`(신규), `tests/unit/test_offline_bundle.py`

## 증상

1. README는 Mac에서 `.env`에 `OLLAMA_BASE_URL=http://host.docker.internal:11434`를 두라고 안내했습니다. 하지만 `docker-compose.yml`의 api 환경변수가 `OLLAMA_BASE_URL: http://ollama:11434`로 고정되어 있어 이 값이 적용되지 않았습니다. 또 api가 `ollama` 컨테이너의 healthy 상태에 의존했기 때문에, 호스트 Ollama만으로 스택을 띄울 수 없었습니다. 결국 ollama 이미지를 받고, 컨테이너 안에서 모델을 다시 pull해야 했습니다.
2. `5432`, `11434`, `8000`, `8501`이 `0.0.0.0`에 공개되었습니다. 같은 LAN에서 기본 비밀번호(`clinical`/`clinical`)인 PostgreSQL, 인증 없는 Ollama와 API에 접속할 수 있었습니다.
3. `OLLAMA_TIMEOUT_SEC`가 컨테이너에 전달되지 않았습니다. 모델 로딩과 생성이 느린 CPU 전용 환경에서도 60초 제한을 바꿀 수 없었습니다.

## 해결

- `OLLAMA_BASE_URL`, `OLLAMA_TIMEOUT_SEC`를 환경변수(`.env`)로 받습니다. 기본값은 이전과 같습니다.
- `docker-compose.host-ollama.yml`을 추가했습니다. ollama 서비스를 profile 뒤로 숨기고, api의 `depends_on`에서 ollama를 빼고, `host.docker.internal`(Linux는 `host-gateway`)을 가리킵니다. `make up-host-ollama`로 실행하며, 아무것도 pull하지 않습니다.
- 공개 포트는 모두 `127.0.0.1`에 바인딩합니다. 단위 테스트가 이를 확인합니다.
- 폐쇄망 프로필은 api의 `OLLAMA_BASE_URL`을 `http://ollama:11434`로 고정하고, `OLLAMA_TIMEOUT_SEC` 기본값을 300초로 둡니다(`OFFLINE_OLLAMA_TIMEOUT_SEC`로 변경 가능).

## 검증 (2026-10-06, Docker Desktop 29.5.2, macOS arm64, 호스트 Ollama 0.24)

새 DB 볼륨으로 `make up-host-ollama`를 실행해 다음을 확인했습니다.

- api가 시작하면서 alembic을 head(0004)까지 적용했고, `/api/health`가 `ok`를 반환
- `/api/index`: 문서 6개, 28 chunk 인덱싱, 실패 0
- "업로드할 수 있는 파일 형식은 무엇인가요?": `dicom-upload-guide.md#Supported File Formats`를 인용해 답변(생성 약 12초, gemma4:e4b)
- "항암제 용량을 어떻게 조절해야 하나요?": `OUT_OF_SCOPE`로 거절. "이 시스템의 월 구독 요금은 얼마인가요?": `MODEL_REFUSED`로 거절
- `/api/dicom/analyze`(`sample-ct-anonymized.dcm`, `sample-phi-nested-private.dcm`): Layer 1/2 결과와 LLM 설명 반환
- ui: 호스트에서 `127.0.0.1:8501/_stcore/health` 200, ui 컨테이너에서 api `/api/health` 호출 성공
