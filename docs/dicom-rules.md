# DICOM 규칙: 2계층 설계 (표준 적합성 + 비식별화)

- 관련 이슈: [#2](https://github.com/yooonhyuk/clinical-rag-qa/issues/2)(출력 allowlist, [문서](issues/002-dicom-free-text-phi-to-llm.md)), [#3](https://github.com/yooonhyuk/clinical-rag-qa/issues/3)(2계층 재구성)
- 코드: `backend/app/services/dicom_{service,conformance,deid,findings,rules,safe}.py`, `backend/app/cli/dicom_scan.py`
- 규칙 데이터: `backend/app/rules/standard/*.yaml`(표준에서 생성, 커밋됨), `backend/app/rules/deid_policy.yaml`(사이트 정책)

MVP-1의 DICOM 규칙은 직접 고른 필수 태그 13개와 개인정보 태그 10개였습니다. 근거 표준이 없었고, Enhanced 멀티프레임 파일에서 거짓 "누락"이 났으며, 중첩 sequence와 private tag를 보지 못했습니다. 지금은 아래 두 계층으로 나눠 **DICOM 표준 원문에서 생성한 규칙**으로 검사합니다.

```text
pydicom.dcmread(stop_before_pixels=True)          픽셀은 읽지 않음
 ├─ Layer 1  표준 적합성   PS3.3 IOD/모듈 Type, PS3.5 값 형식, Defined Terms
 │           + 정량 준비도  PET SUV 계산에 필요한 태그 (경고, 적합성 오류 아님)
 ├─ Layer 2  비식별화      PS3.15 Annex E Table E.1-1 + 사이트 정책(YAML)
 └─ 출력 경계 (dicom_safe)  allowlist 값 + 존재 여부 + finding(코드·키워드·건수·출처)
      └─ LLM 설명          allowlist 요약 + finding 코드/건수만 (로컬 Ollama만, 실패 시 템플릿)
```

이후 계획: **Layer 3**(임상시험별 업로드 기준, 예: "슬라이스 두께 ≤ 2.5mm")은 업로드 가이드 문서를 RAG로 검색해 적용하는 MVP-2 범위이고, **series/study 단위 일관성**(같은 series의 IOP/PixelSpacing 일치, 슬라이스 간격, UID 중복)이 다음 단계입니다. 지금은 파일 단위로만 검사합니다.

---

## 1. 출처와 판(edition)

모든 표준 규칙은 dicom.nema.org의 공식 DocBook XML에서 스크립트로 추출합니다. 표를 손으로 옮기지 않습니다. 네트워크가 안 되면 스크립트는 오류로 멈추고 파일을 쓰지 않습니다.

| 파트 | 판 | 사용한 부분 | 생성 파일 |
|---|---|---|---|
| PS3.3 Information Object Definitions | **2026d** | Annex A IOD 모듈 표, Functional Group 매크로 표, Annex C 모듈/매크로 속성 표(Include 재귀 전개), C.7.3.1.1.1 Modality Defined Terms | `rules/standard/ps3.3_iod.yaml` |
| PS3.15 Security and System Management Profiles | **2026d** | Table E.1-1(657행), Table E.1-1a(조치 코드) | `rules/standard/ps3.15_e1-1_deid.yaml` |
| PS3.16 Content Mapping Resource | **2026d** | CID 7050 De-identification Method, Annex L Body Part Examined Defined Terms(L-1~L-3) | 위 두 파일에 포함 |

- URL: `https://dicom.nema.org/medical/dicom/current/source/docbook/partNN/partNN.xml` (2026d는 아직 판별 경로에 보관되지 않아 `current`로 받고, 문서 부제에서 판을 읽어 기록합니다).
- 수집일: 2026-10-06. 각 YAML 머리말과 `sources` 항목에 판, URL, 수집일, 원본 XML의 SHA-256을 남깁니다.
- 재생성: `make dicom-rules` (= `scripts/build_iod_rules.py` + `scripts/build_deid_rules.py`). 특정 판을 고정하려면 `--edition 2025c`처럼 보관 판을 지정합니다. 내려받은 XML은 `~/.cache/clinical-rag-qa/dicom-standard/`에 캐시합니다.
- 파서 자체는 네트워크 없이 작은 DocBook 조각으로 테스트합니다(`tests/unit/test_dicom_rule_builders.py`).

## 2. Layer 1 — 표준 적합성 (PS3.3 / PS3.5)

### IOD 결정과 범위

SOP Class UID로 IOD를 정하고, 범위 밖이거나 없으면 Modality로 추정합니다(`determinedBy`). 둘 다 안 되면 `L1-IOD-UNKNOWN`(경고)을 내고 모듈 검사를 건너뜁니다.

| IOD (PS3.3 표) | Storage SOP Class UID | Modality 대체 |
|---|---|---|
| CT Image (A.3-1) | 1.2.840.10008.5.1.4.1.1.2 | CT |
| Enhanced CT Image (A.38-1, FG A.38-2) | …1.2.1 | – |
| MR Image (A.4-1) | …1.4 | MR |
| Enhanced MR Image (A.36-1, FG A.36-2) | …1.4.1 | – |
| Positron Emission Tomography Image (A.21.3-1) | …1.128 | PT |
| Enhanced PET Image (A.56-1, FG A.56-2) | …1.130 | – |
| Ultrasound Image (A.6-1) | …1.6.1 | US |
| Ultrasound Multi-frame Image (A.7-1) | …1.3.1 | – |
| Secondary Capture Image (A.8-1) | …1.7 | OT, SC |
| Computed Radiography Image (A.2-1) | …1.1 | CR |
| Digital X-Ray Image (A.26-1) | …1.1.1 (For Presentation), …1.1.1.1 (For Processing) | DX |

(…은 `1.2.840.10008.5.1.4.1`) 11개 IOD, 56개 모듈을 생성합니다. Mammography, NM, XA/RF, RT, SR, Segmentation, Legacy Converted Enhanced, Whole Slide 등은 아직 범위 밖입니다(`L1-IOD-NOT-COVERED` info 후 Modality로 추정).

### Type 의미

| Type | 판정 | finding |
|---|---|---|
| 1 | 존재하고 값이 비어 있지 않아야 함 | `L1-TYPE1-ABSENT` / `L1-TYPE1-EMPTY` (error) |
| 2 | 존재해야 함(빈 값 허용) | `L1-TYPE2-ABSENT` (error) |
| 1C / 2C | 조건 미평가. 없는 속성을 모듈별로 묶어 보고 | `L1-CONDITIONAL-NOT-EVALUATED` (info) |
| 3 | 검사하지 않음 | – |

- **부재와 빈 값을 구분합니다**(`absent` / `empty` / `exists`). MVP-1은 빈 값을 "없음"으로 봐서 Type 2를 잘못 판정했습니다.
- 사용(Usage) **M** 모듈만 검사합니다. **C** 모듈은 조건을 평가하지 않고 목록만 보고합니다(`L1-CONDITIONAL-MODULE-NOT-EVALUATED`). **U** 모듈은 무시합니다.
- 한 속성이 여러 모듈에 나오면 **가장 엄격한 Type** 한 번만 평가합니다. 예: Image Type은 General Image에서 Type 3, CT Image에서 Type 1.
- Pixel Data 계열(그룹 7FE0)은 `stop_before_pixels`로 읽지 않으므로 제외합니다.
- 모듈 속성은 최상위만 검사합니다(sequence 내부의 Type은 Functional Group 매크로 1단계만).

### Enhanced 멀티프레임 (Functional Groups)

Enhanced CT/MR/PET은 PixelSpacing·ImagePositionPatient·ImageOrientationPatient가 최상위가 아니라 **Shared / Per-frame Functional Groups Sequence** 안에 있습니다. IOD의 Functional Group 매크로 표에서 사용 M인 매크로(Pixel Measures, Plane Position, Plane Orientation, Frame Content, Frame Anatomy, 모달리티별 Frame Type 등)를 찾아:

- Shared 항목에 있거나 **모든** Per-frame 항목에 있으면 충족. 아니면 `L1-FG-MISSING`(빠진 프레임 수 포함).
- "May not be used as a Shared Functional Group"인 매크로(Frame Content)가 Shared에 있으면 `L1-FG-SHARED-NOT-ALLOWED`.
- 매크로 내부 Type 1/2 속성은 `L1-FG-TYPE1-*` / `L1-FG-TYPE2-*`.
- `tagSummary`의 공간 값도 Functional Group(1번 프레임)에서 가져오고 `spatialSource`로 표시합니다.

### 값 형식 (PS3.5 6.2)과 Defined Terms

검사한 속성 중 값이 있는 최상위 속성에 대해(값은 출력하지 않음):

| VR | 규칙 | finding |
|---|---|---|
| UI | 64자 이하, `[0-9.]`만, 빈 구성요소·구성요소 선행 0 금지 | `L1-VR-UI` |
| DA | `YYYYMMDD`, 실제 존재하는 날짜 | `L1-VR-DA` |
| TM | `HH[MM[SS[.F{1,6}]]]`, 범위 검사 | `L1-VR-TM` |
| CS | 대문자·숫자·공백·`_`, 16자 이하 | `L1-VR-CS` |
| Modality | PS3.3 C.7.3.1.1.1 Defined Terms(79개) / Retired(18개) | `L1-MODALITY-TERM` / `L1-MODALITY-RETIRED` (warning) |
| Body Part Examined | PS3.16 Annex L Defined Terms(347개) | `L1-BODYPART-TERM` (warning) |

pydicom 자체 값 검증은 꺼 둡니다. pydicom 경고 문구가 원래 값을 그대로 인용해 로그에 PHI가 남기 때문입니다(`test_reading_malformed_values_does_not_log_them`).

### 정량 준비도 (PET SUV) — 적합성과 별도

PET(SOP Class 또는 Modality PT)이면 SUV 계산에 필요한 태그를 확인하고 **경고**로만 보고합니다(`quantitationReadiness`, `QR-*`).

| 항목 | 위치 | 근거 |
|---|---|---|
| PatientWeight (0010,1030) | 최상위 | PS3.3 C.7.2.2 Patient Study Module |
| SeriesTime (0008,0031) | 최상위 | PS3.3 C.7.3.1 General Series Module |
| Units (0054,1001), BQML이 아니면 `QR-UNITS` | 최상위 | PS3.3 C.8.9.1 PET Series Module |
| DecayCorrection (0054,1102) | 최상위 | PS3.3 C.8.9.1 |
| RadiopharmaceuticalInformationSequence → RadionuclideTotalDose, RadionuclideHalfLife, RadiopharmaceuticalStartTime(또는 StartDateTime) | 첫 항목 | PS3.3 C.8.9.2 PET Isotope Module |

Enhanced PET은 이 정보가 Functional Group 구조에 있어 이번 범위에서는 `QR-NOT-EVALUATED`(info)로 둡니다.

> **주의 — SUV와 기본 비식별화 프로파일의 충돌**: PS3.15 Basic Profile은 PatientWeight와 RadiopharmaceuticalStartTime을 **X(삭제)** 로 정합니다. SUV 준비가 된 PET 샘플(`sample-pet-suv-ready.dcm`)은 그래서 Layer 2 오류가 납니다. 정량 분석이 필요한 임상시험은 보통 **Retain Patient Characteristics Option**과 **Retain Longitudinal Temporal Information** 옵션을 씁니다. 이 선택은 `deid_policy.yaml`의 `options`로 표현합니다.

## 3. Layer 2 — 비식별화 (PS3.15 Annex E)

### 프로파일 적용

- Table E.1-1의 657개 항목(속성 653 + 반복 그룹 `50xx,xxxx`/`60xx,3000`/`60xx,4000` + private)을 **모든 속성에, sequence 항목 안까지 재귀적으로** 적용합니다(E.1.1: "whether contained in the top level Data Set or embedded in an Item of a Sequence of Items"). 중첩 위치는 키워드 경로(`RequestAttributesSequence[0].RequestedProcedureDescription`)로 보고합니다.
- 적용 옵션 = 정책 `options` ∪ (파일이 선언한 CID 7050 옵션, `honor_claimed_options: true`일 때). 옵션 열에 값(K/C)이 있으면 기본 조치 대신 그 값을 씁니다.
- 복합 조치는 IOD의 Type으로 풉니다: `X/Z`는 Type 2면 Z, 아니면 X / `X/D`·`Z/D`·`X/Z/D`는 Type 1이면 D, Type 2면 Z, Type 3이면 X / `X/Z/U*`는 Type 1이면 sequence 유지 후 내부 UID를 U로, Type 2면 Z, Type 3이면 X. 중첩 항목이나 필수 모듈 밖 속성처럼 **Type을 모르면 가장 완화된 쪽**을 적용하고 `action`에 그 사실을 적습니다(거짓 오류 방지).

| 조치 | 판정 | finding |
|---|---|---|
| X 삭제 | 값이 있으면 오류, 빈 값으로 남으면 경고. sequence면 내부는 보지 않음 | `DEID-X-PRESENT` (error) / `DEID-X-EMPTY` (warning) |
| Z 빈 값 또는 더미 | 값이 있으면 경고(더미인지 판단 불가) — 가명 정책 대상이면 아래 규칙 | `DEID-Z-NOT-EMPTY` (warning) |
| D 더미 치환 | 값 있음: 치환 여부 확인 불가 / 비어 있음: 경고 | `DEID-D-VERIFY` (info) / `DEID-D-EMPTY` (warning) |
| C 정제 | 텍스트 VR이면 경고, 그 외(날짜 등) info | `DEID-C-VERIFY` |
| U 새 UID | "UID 존재(프로파일: 치환)". 원본인지 치환본인지는 파일 하나로 판단할 수 없음 | `DEID-U-PRESENT` (info) |
| K 유지 | sequence면 내부 검사 | – |

### Private 속성, 선언, 가명, 픽셀, 날짜

- **Private 속성(홀수 그룹)**: 개수와 그룹 번호만 보고합니다. 기본 프로파일은 X라 오류이고, 정책에 `retain_safe_private`가 있으면 info로 낮추되 "안전 private 목록 대조는 미구현"이라고 적습니다(`DEID-PRIVATE-PRESENT`, PS3.15 E.3.10).
- **파일의 비식별화 선언**: PatientIdentityRemoved(0012,0062), DeidentificationMethod(0012,0063, 자유 텍스트라 존재 여부만), DeidentificationMethodCodeSequence(0012,0064). CID 7050에 있는 코드만 이름으로 보여 주고, 모르는 코드는 개수만 셉니다. YES인데 0063·0064가 모두 없으면 `DEID-CLAIM-INCOMPLETE`(PS3.3 C.7.1.1 Type 1C), YES가 아니면 `DEID-NOT-CLAIMED`(info).
- **가명 정책**(`deid_policy.yaml` → `pseudonymization`): PatientID·PatientName이 비어 있거나(허용 시) 정규식과 **완전히 일치**하면 준수(`DEID-PSEUDONYM-OK`, info), 값이 있는데 일치하지 않으면 `DEID-PSEUDONYM-MISMATCH`(error). 기본 형식은 `<STUDY>-<SITE>-<SUBJECT>`(예 `DEMO-001-0001`): `^[A-Z0-9]{2,12}-[0-9]{3}-[0-9]{3,5}$`. 최상위 속성에만 적용합니다.
- **픽셀 내 식별정보**(픽셀은 읽지 않음): BurnedInAnnotation(0028,0301)=YES면 `DEID-BURNED-IN`(error, 고위험). 없고 Modality가 정책의 고위험 목록(기본 US, ES, XC, SC, OT, DX, CR)이면 `DEID-PIXEL-RISK`(warning, "수동/OCR 확인 권장").
- **날짜**: 날짜·시간 속성은 각 행의 조치로 판정하고, 개수와 적용 옵션을 `DEID-DATES`(info)로 요약합니다. 시간축을 유지해야 하면 정책에서 `retain_longitudinal_full_dates`(K) 또는 `retain_longitudinal_modified_dates`(C = 이동된 날짜, "확인 필요")를 켭니다(PS3.15 E.3.6).

### 정책 기본값 (`backend/app/rules/deid_policy.yaml`)

| 키 | 기본값 | 의미 |
|---|---|---|
| `options` | `[]` | Basic Profile만 적용 |
| `honor_claimed_options` | `true` | 파일이 0012,0064로 선언한 옵션도 반영 |
| `pseudonymization.PatientID/PatientName` | 위 정규식, `allow_empty: true` | 가명 형식이면 준수 |
| `burned_in_high_risk_modalities` | `[US, ES, XC, SC, OT, DX, CR]` | BurnedInAnnotation이 없을 때 위험 표시 |

## 4. 출력과 LLM 경계

`POST /api/dicom/analyze` 응답(camelCase):

```text
tagSummary              allowlist 값(Modality, SOP Class 이름, Rows/Columns, PixelSpacing, …) / exists·empty·absent
layer1                  {standard, iod{key,name,determinedBy,source}, passed[], findings[]}
layer2                  {profile, profileEdition, optionsApplied[], claimedDeid{…}, findings[]}
quantitationReadiness   {applicable, ready, label, findings[]}
counts                  {layer1, layer2, quantitationReadiness}: {error, warning, info}
privacyWarnings, missingRequiredTags, qaResult, ruleSource, disclaimer   (MVP-1 호환 필드)
```

finding: `{code, severity, message, source, attribute, tag, action, count, paths, details}`. **값은 어디에도 없습니다.** `source`는 근거 표준 절·표(예: `PS3.15 2026d Table E.1-1`, `PS3.3 C.7.6.2 Image Plane Module (Table C.7-10)`)입니다.

LLM(로컬 Ollama)에는 `tagSummary`, IOD 이름, `counts`, error/warning finding의 `code`/`attribute`(표준 키워드)/`count`, info 코드 목록, 선언된 CID 7050 방법 이름만 보냅니다. message·paths·값은 보내지 않습니다. 외부 Provider(anthropic) 모드에서는 DICOM 설명을 항상 템플릿으로 만듭니다(container와 `DicomService` 양쪽에서 막음).

## 5. 폴더 일괄 검사 (실제 공개 데이터로 시험하기)

```bash
make dicom-scan DIR=/path/to/tcia/download                 # 표 + 빈도 상위 finding
make dicom-scan DIR=/path SCAN_ARGS="--json out.jsonl"      # 파일별 전체 결과(JSONL)
uv run --project backend python -m app.cli.dicom_scan /path --redact-paths --fail-on error
```

- 폴더 아래 모든 파일을 시도하고 DICOM이 아니면 건너뜁니다(확장자 무관). DB·LLM·네트워크를 쓰지 않습니다.
- `--redact-paths`: 파일 이름 자체에 식별자가 있을 때 경로 대신 `#n`을 출력합니다.
- `--fail-on error|warning`: CI나 업로드 전 점검에서 종료 코드로 쓸 수 있습니다.

## 6. 한계

- **조건부 요건**: Type 1C/2C와 C 모듈의 조건은 평가하지 않습니다(목록만 보고). 단, PatientIdentityRemoved=YES일 때 0012,0063/0064 요건은 Layer 2에서 확인합니다.
- **깊이**: 모듈 속성은 최상위, Functional Group 매크로는 1단계까지만 Type을 봅니다.
- **확인 불가 항목**: Z/D 값이 더미인지, UID가 치환됐는지, C 대상이 정제됐는지는 파일 하나로 판단할 수 없어 info/경고로만 보고합니다. 안전 private 속성 목록(E.3.10) 대조는 미구현입니다.
- **픽셀**: 읽지 않습니다. 픽셀 내 텍스트는 BurnedInAnnotation과 Modality로 위험만 표시합니다.
- **사전 버전**: pydicom 3.0.2의 데이터 사전이 2026d보다 오래돼 Table E.1-1의 26개 신규 속성은 키워드가 없습니다(태그로 매칭되므로 판정은 동일).
- **파일 단위**: series/study 일관성, 같은 환자의 UID 일관성(U의 "internally consistent")은 보지 않습니다(다음 단계).
- **커버리지**: 위 11개 IOD만 모듈 검사를 합니다. 합성 샘플로만 테스트했고, 실제 공개 데이터(TCIA 등)는 아직 돌리지 않았습니다.
