# 002. DICOM 자유 텍스트 태그 값이 응답과 LLM 프롬프트로 노출됨

- 상태: 해결 (출력 allowlist 도입)
- GitHub: https://github.com/yooonhyuk/clinical-rag-qa/issues/2
- 발견: 2026-10-06, 코드 리뷰
- 영향 범위: `POST /api/dicom/analyze` 응답의 `tagSummary`, DB `dicom_files.tags`, DICOM 설명 LLM 프롬프트
- 관련 코드: `backend/app/services/dicom_safe.py`(신규), `backend/app/services/dicom_service.py`, `tests/unit/test_dicom_phi_boundary.py`

## 증상

`evaluate()`는 `privacy_tags.yaml`에 적힌 태그와 UID만 `"exists"`로 바꾸고, **나머지 태그는 값을 그대로** `tag_summary`에 넣었습니다. 이 `tag_summary`가 API 응답, DB의 `tags` 컬럼, `_explain()`이 만드는 LLM 프롬프트에 그대로 들어갔습니다.

샘플 파일로는 `StudyDescription: "DEMO CT CHEST"`처럼 무해해 보였지만, 실제 병원 데이터에서는 다음 같은 값이 흔합니다.

- `StudyDescription` / `SeriesDescription`: 기사가 입력한 자유 텍스트. 환자 이름, 등록번호, 의뢰 사유가 들어갈 수 있습니다.
- `Manufacturer` 등 LO 속성: 장비 메모나 기관명이 들어간 사례가 있습니다.
- `BodyPartExamined`(CS): 코드 속성이지만 잘못된 장비 설정으로 자유 텍스트가 들어갈 수 있습니다.

기존 테스트는 `PatientName` 같은 denylist 항목만 확인했기 때문에 이 경로를 잡지 못했습니다.

## 원인

출력 정책이 **denylist**("개인정보로 알려진 태그만 숨긴다")였습니다. 목록에 없는 속성은 안전하다고 가정했고, 값의 형식도 확인하지 않았습니다. DICOM에는 수천 개의 표준 속성과 무제한의 private tag가 있으므로 denylist로는 경계를 지킬 수 없습니다.

## 해결

`backend/app/services/dicom_safe.py`에 **출력 allowlist**를 두었습니다. 분석기 밖으로 나가는 모든 DICOM 유래 값(응답, DB, LLM 프롬프트)은 이 모듈을 거칩니다.

| 종류 | 속성 | 출력 조건 |
|---|---|---|
| 코드(CS) | `Modality`, `BodyPartExamined` | CS 문자셋(`A-Z 0-9 _ 공백`)·16자 이하일 때만. 아니면 `exists (value suppressed…)` |
| SOP Class | `SOPClassUID` | pydicom 표준 UID 사전에 등록된 경우 이름(예: `CT Image Storage`)으로 변환. 아니면 숨김 |
| 숫자 | `Rows`, `Columns`, `NumberOfFrames`, `PixelSpacing`, `SliceThickness`, `SpacingBetweenSlices`, `ImagePositionPatient`, `ImageOrientationPatient`, `SeriesNumber`, `InstanceNumber`, `SamplesPerPixel`, `BitsAllocated`, `BitsStored` | 모든 값이 숫자로 해석될 때만 |
| 그 외 전부 | 이름, 날짜, UID, 설명, private tag, sequence | 존재 여부만: `exists` / `empty` / `absent` |

추가로 `DicomService`는 생성자에서 `provider != "ollama"`인 클라이언트를 받으면 버립니다. 지금도 container가 anthropic 모드에서 `None`을 넘기지만, 다른 호출자가 실수로 외부 Provider를 넘겨도 DICOM 정보가 나가지 않게 한 심층 방어입니다.

## 회귀 테스트

`tests/unit/test_dicom_phi_boundary.py`

- `StudyDescription`, `SeriesDescription`, `Manufacturer`, `InstitutionName`, private tag(그룹 0011), 2단계 중첩 sequence(`RequestAttributesSequence` → `RequestedProcedureCodeSequence.CodeMeaning`), 소문자 자유 텍스트를 넣은 `BodyPartExamined`에 PHI 유사 문자열을 넣습니다.
- 확인 대상: `evaluate()` 결과, `DicomService` 결과와 LLM 프롬프트, HTTP 응답 본문 전체, DB에 저장되는 행.
- ollama 경로(프롬프트 1회 생성, PHI 없음)와 anthropic 경로(프롬프트 0회, 템플릿 설명) 모두 확인합니다.

## 남은 한계

- 대문자 이름처럼 CS 형식을 만족하는 자유 텍스트(`BodyPartExamined = "HONG GILDONG"`)는 형식 검사만으로 걸러지지 않습니다. 이후 Layer 1 재구성([#3](https://github.com/yooonhyuk/clinical-rag-qa/issues/3))에서 표준 Defined Terms와 대조하도록 강화합니다.
- 이 수정은 **출력 경계**만 다룹니다. 파일 자체가 비식별화 기준을 만족하는지는 Layer 2(PS3.15 Annex E) 검사의 몫입니다.
