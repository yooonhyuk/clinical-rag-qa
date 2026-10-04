# DICOM Upload Guide (가상 샘플 문서)

> 이 문서는 ClinicalRAG QA 데모를 위해 작성한 **가상 문서**다. 실제 기관·시험·제품과 무관하다.
> 문서 번호: DEMO-UG-001 / 버전 1.2

## Scope

이 가이드는 가상의 임상시험 "DEMO-ONC-01"에서 사이트(병원)가 의료영상(DICOM)을 중앙 영상 저장소로
업로드할 때 지켜야 할 기준을 정의한다. 대상 Modality는 CT, MR, CR이다.
영상 판독, 진단, 병변 평가는 이 가이드의 범위가 아니며 독립 판독 위원회(가상)의 별도 절차를 따른다.

## Supported File Formats

- 업로드 가능한 파일 형식은 DICOM Part 10 파일(.dcm)과 DICOM 파일을 묶은 ZIP 파일이다.
- JPG, PNG, PDF 등 일반 이미지·문서 파일은 영상 데이터로 업로드할 수 없다.
- 한 번에 업로드할 수 있는 최대 용량은 2GB이며, 이를 넘으면 Series 단위로 나누어 업로드한다.
- 파일명은 확장자와 실제 형식이 일치해야 한다. 확장자가 .dcm이지만 DICOM preamble("DICM")이 없으면
  E101 오류로 거부된다.

## Required DICOM Tags

모든 영상은 아래 필수 태그를 포함해야 한다. 하나라도 없으면 업로드 검증 단계에서 E102 오류가 발생한다.

- StudyInstanceUID
- SeriesInstanceUID
- SOPInstanceUID
- Modality
- Rows
- Columns

## Recommended Tags by Modality

CT와 MR 영상은 공간 정보 확인을 위해 아래 태그를 추가로 확인한다.
누락되면 업로드는 가능하지만 QC 단계에서 "주의(Warning)"로 표시된다.

- PixelSpacing
- SliceThickness
- ImagePositionPatient
- ImageOrientationPatient

CR(일반 촬영) 영상은 PixelSpacing 또는 ImagerPixelSpacing 중 하나가 있으면 된다.

## Upload Validation

업로드 후 시스템은 다음 순서로 자동 검증을 수행한다.

1. 파일 형식 검증: DICOM Part 10 형식인지, 확장자와 형식이 일치하는지 확인한다.
2. 필수 태그 검증: Required DICOM Tags가 모두 존재하는지 확인한다.
3. Subject ID 매핑 검증: PatientID 태그 값이 EDC에 등록된 Subject ID(예: DEMO-001-0001)와 일치하는지 확인한다.
4. 개인정보 태그 검증: 비식별화되지 않은 개인정보 가능 태그가 남아 있는지 확인한다.
5. 중복 검증: 같은 SOPInstanceUID가 이미 업로드되었는지 확인한다.

DICOM 업로드가 실패하면 운영자는 먼저 다음 항목을 확인한다.

- 파일 형식이 DICOM Part 10인지
- 필수 태그가 모두 존재하는지
- Subject ID 매핑이 올바른지 (사이트 번호와 대상자 번호 조합)
- 재처리(재업로드) 가능 상태인지 — 재시도 횟수 3회를 넘으면 자동 재처리가 중단된다.

## Visit and Timepoint

각 업로드는 하나의 방문(Visit)에 연결된다. 방문 명칭은 Screening, Week 6, Week 12, End of Treatment를
사용한다. 방문 창(visit window)은 예정일 기준 ±7일이며, 창을 벗어난 영상은 "Out of Window"로 표시되어
데이터 매니저의 확인을 받는다.

## Upload Deadline

사이트는 촬영일로부터 영업일 기준 5일 이내에 영상을 업로드해야 한다.
기한을 넘긴 업로드는 지연 사유를 업로드 코멘트에 기재한다.
