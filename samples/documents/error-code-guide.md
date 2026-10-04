# Error Code Guide (가상 샘플 문서)

> 데모용 가상 문서. 실제 시스템의 오류 코드와 무관하다. 문서 번호: DEMO-EC-002

## Upload Failure

업로드 실패 오류는 E1xx 계열 코드로 표시된다. 오류 메시지에는 항상 오류 코드, 파일명, 발생 시각이 포함된다.

| 코드 | 메시지 | 의미 |
|---|---|---|
| E101 | File extension mismatch | 확장자와 실제 파일 형식이 다름 (예: .dcm이지만 DICOM이 아님) |
| E102 | Required tag missing | 필수 DICOM 태그 누락 |
| E103 | Subject ID not matched | PatientID 값이 EDC Subject ID와 불일치 |
| E104 | Duplicate instance | 같은 SOPInstanceUID가 이미 존재 |
| E105 | File size exceeded | 업로드 1회 최대 용량 2GB 초과 |
| E201 | Retry count exceeded | 자동 재처리 3회 초과로 중단 |
| E301 | PHI detected | 비식별화되지 않은 개인정보 태그 발견 |

## Operator Checklist

운영자(사이트 코디네이터, 데이터 매니저)는 오류 발생 시 다음을 확인한다.

- E101: 원본 장비에서 DICOM으로 다시 내보내기(export)한다. 화면 캡처나 JPG 변환본을 올리지 않는다.
- E102: 장비 export 설정에서 태그가 제거되지 않았는지 확인하고, 누락 태그 목록을 개발팀에 전달한다.
- E103: EDC에서 Subject ID를 확인하고, 사이트 번호-대상자 번호 형식(DEMO-001-0001)이 맞는지 확인한다.
- E104: 같은 Series를 두 번 업로드했는지 업로드 이력을 확인한다. 의도한 재업로드라면 기존 업로드를 취소 요청한다.
- E105: Series 단위로 나누어 다시 업로드한다.
- E201: 재처리를 기다리지 말고 헬프데스크에 티켓을 등록한다.
- E301: 업로드를 중단하고 Privacy SOP의 사고 대응 절차를 따른다.

## Developer Checklist

개발자(시스템 운영팀)는 다음을 확인한다.

- 애플리케이션 로그에서 요청 ID(request id)로 해당 업로드의 전체 처리 흐름을 추적한다.
- E102 반복 발생 시 특정 장비 제조사(Manufacturer)·모델에서만 발생하는지 집계한다.
- E201 발생 시 메시지 큐 적체 여부와 저장소(Object Storage) 응답 지연을 확인한다.
- E103 다발 시 EDC 연동 배치가 최신 Subject 목록을 동기화했는지 확인한다.
- 오류 로그는 최소 1년간 보관한다.

## Log Levels

로그 레벨은 ERROR, WARN, INFO를 사용한다.
ERROR는 업로드가 거부된 경우, WARN은 업로드는 되었지만 QC 확인이 필요한 경우(예: 권장 태그 누락),
INFO는 정상 처리 이벤트(예: 재시도 시작)에 사용한다.
