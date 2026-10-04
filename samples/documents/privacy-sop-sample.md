# Privacy SOP (가상 샘플 문서)

> 데모용 가상 표준운영절차서. 실제 기관의 SOP가 아니다. 문서 번호: DEMO-SOP-PRV-003

## Purpose

이 SOP는 가상의 임상시험에서 의료영상을 중앙 저장소로 전송하기 전에 개인정보를 제거(비식별화)하는 절차를
정의한다. 원칙은 "사이트 밖으로 나가는 영상에는 직접 식별자가 없어야 한다"이다.

## De-identification Policy

비식별화는 사이트에서 업로드 전에 수행하는 것을 원칙으로 한다. 아래 태그는 처리 방법을 따른다.

| 태그 | 처리 |
|---|---|
| PatientName | 삭제하거나 Subject ID로 치환 |
| PatientID | EDC Subject ID(DEMO-xxx-xxxx)로 치환 |
| PatientBirthDate | 삭제 (연령이 필요하면 PatientAge만 유지) |
| PatientSex | 프로토콜이 요구하는 경우에만 유지 |
| AccessionNumber | 삭제 또는 무작위 값으로 치환 |
| InstitutionName | 삭제 |
| ReferringPhysicianName | 삭제 |
| PerformingPhysicianName | 삭제 |
| OperatorsName | 삭제 |
| StudyDate | 프로토콜 정책에 따라 날짜 이동(date shift) 또는 유지 |

StudyDate는 직접 식별자는 아니지만 다른 정보와 결합하면 재식별 위험이 있어 민감 정보 가능 항목으로 관리한다.
UID(StudyInstanceUID 등)는 추적을 위해 유지하되, 원본 UID를 연구용 UID로 재발급하는 것을 권장한다.

## Burned-in Annotation

영상 픽셀에 이름 등이 새겨진(burned-in) 경우 태그 비식별화로는 제거되지 않는다.
BurnedInAnnotation 태그가 YES이거나 육안 확인 시 글자가 보이면 해당 영상은 업로드하지 않고
사이트에 마스킹 처리를 요청한다.

## Incident Response

비식별화되지 않은 영상(PHI 포함)이 업로드된 것을 발견하면 다음 순서로 대응한다.

1. 즉시 해당 업로드를 격리(quarantine)하고 열람 권한을 차단한다.
2. 24시간 이내에 개인정보 보호 담당자(Privacy Officer)에게 보고한다.
3. 사이트에 비식별화된 영상 재업로드를 요청한다.
4. 원본 PHI 포함 파일은 확인 후 7일 이내에 영구 삭제하고 삭제 기록을 남긴다.

## Retention

비식별화된 연구 영상은 시험 종료 후 15년간 보관한다(가상 정책).
접근 로그는 3년간 보관한다.
