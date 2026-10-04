"""Generate the fictional `clinical-trial-protocol-sample.pdf` (text PDF, 3 pages).

Usage: uv run --project backend python scripts/generate_sample_pdf.py
"""

from pathlib import Path

import pymupdf

OUT = Path(__file__).resolve().parents[1] / "samples" / "documents"

PAGES: list[tuple[str, list[str]]] = [
    (
        "DEMO-ONC-01 Clinical Trial Protocol (Fictional Sample)",
        [
            "이 문서는 데모용 가상 임상시험 프로토콜이다. 실제 시험, 약물, 기관과 무관하다.",
            "",
            "1. Study Overview",
            "시험명: DEMO-ONC-01, 가상의 고형암 대상 2상 시험.",
            "목표 등록 대상자 수: 120명, 참여 사이트 수: 8개(가상).",
            "영상 평가는 독립 중앙 판독(가상 위원회)에서 수행하며, 사이트는 영상 수집과",
            "업로드만 담당한다.",
            "",
            "2. Study Contacts",
            "의뢰자 스터디 매니저: Demo Study Manager (가상)",
            "영상 운영 담당: Demo Imaging Ops (가상)",
        ],
    ),
    (
        "3. Imaging Schedule",
        [
            "영상 촬영 시점은 다음과 같다.",
            "- Screening: 첫 투여 전 28일 이내",
            "- Week 6, Week 12: 이후 12주 간격으로 반복",
            "- End of Treatment: 치료 종료 후 30일 이내",
            "각 시점의 허용 범위(visit window)는 예정일 기준 +/-7일이다.",
            "",
            "4. Imaging Modalities",
            "기본 검사는 흉부/복부/골반 조영증강 CT이다.",
            "CT 조영제 사용이 불가능한 대상자는 MR로 대체할 수 있으며,",
            "대체 시 사유를 업로드 코멘트에 기재한다.",
        ],
    ),
    (
        "5. Imaging Acquisition Parameters",
        [
            "CT 권장 촬영 조건:",
            "- SliceThickness 5mm 이하 (권장 1.25mm~2.5mm)",
            "- 동일 대상자는 모든 시점에서 같은 장비와 같은 프로토콜 사용을 권장",
            "MR 권장 촬영 조건:",
            "- SliceThickness 5mm 이하, T1 조영 전/후 및 T2 시퀀스 포함",
            "",
            "6. Data Transfer",
            "영상은 비식별화 후 중앙 저장소로 업로드한다(Privacy SOP DEMO-SOP-PRV-003 참조).",
            "업로드 기한: 촬영일로부터 영업일 기준 5일 이내.",
        ],
    ),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open()
    for title, lines in PAGES:
        page = doc.new_page()
        y = 72
        page.insert_text((60, y), title, fontname="korea", fontsize=14)
        y += 30
        for line in lines:
            page.insert_text((60, y), line, fontname="korea", fontsize=10.5)
            y += 18
    path = OUT / "clinical-trial-protocol-sample.pdf"
    doc.save(path)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
