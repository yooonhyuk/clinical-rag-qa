# Imaging QA Checklist (가상 샘플 문서)

> 데모용 가상 체크리스트. 문서 번호: DEMO-QA-004

## QC Checklist

데이터 매니저는 업로드된 각 Series에 대해 아래 항목을 확인하고 통과/주의/불가 중 하나로 기록한다.

- [ ] Modality가 프로토콜에 정의된 검사 종류(CT 또는 MR)와 일치하는가
- [ ] 필수 태그(Study/Series/SOP Instance UID, Modality, Rows, Columns)가 모두 있는가
- [ ] CT/MR의 경우 PixelSpacing, SliceThickness가 존재하는가
- [ ] CT 흉부 영상의 SliceThickness가 5mm 이하인가 (프로토콜 기준, 가상)
- [ ] 방문(Visit)과 촬영일이 방문 창(±7일) 안에 있는가
- [ ] 개인정보 가능 태그가 비식별화되었는가
- [ ] 이미지 수가 Series 내에서 연속적인가 (InstanceNumber 누락 없음)

## QC Result Codes

- PASS: 모든 항목 충족
- WARNING: 권장 태그 누락 또는 경미한 프로토콜 이탈. 사이트에 확인 요청(Query)을 보내고 판독 대기열에는 올린다.
- FAIL: 필수 태그 누락, 개인정보 미제거, 잘못된 Modality. 판독 대기열에 올리지 않고 재업로드를 요청한다.

## Query Management

QC에서 WARNING 또는 FAIL이 나오면 사이트에 Query를 발행한다.
사이트는 Query 발행 후 영업일 기준 3일 이내에 응답해야 한다.
3일 안에 응답이 없으면 Query는 자동으로 리마인더가 발송되고, 7일이 지나면 스터디 매니저에게 에스컬레이션된다.

## Roles

- 사이트 코디네이터: 업로드, Query 응답
- 데이터 매니저: QC 수행, Query 발행
- 스터디 매니저: 에스컬레이션 처리
- 시스템 운영팀(개발자): 시스템 오류 분석, 로그 확인
