# Public corpus sources (retrieved 2026-10-06)

| File | Issuer / version | Source URL | License / basis |
|---|---|---|---|
| 01_fda_imaging_endpoint_2018.pdf | FDA, Clinical Trial Imaging Endpoint Process Standards, final 2018-04 | https://www.fda.gov/media/81172/download (fetched via web.archive.org id_ snapshot; fda.gov blocks scripted fetches) | US Government work, public domain |
| 02_ich_e6r3_2025.pdf | ICH E6(R3) Step 4, 2025-01-06 | https://database.ich.org/sites/default/files/ICH_E6%28R3%29_Step4_FinalGuideline_2025_0106.pdf | ICH legal notice: reproduction allowed with copyright acknowledgement (logo excluded) |
| 03_ema_anticancer_rev6.pdf | EMA/CHMP/205/95 Rev.6 | https://www.ema.europa.eu/en/documents/scientific-guideline/guideline-clinical-evaluation-anticancer-medicinal-products-revision-6_en.pdf | © EMA 2024, reproduction authorised with source acknowledged |
| 04_mfds_anticancer_guideline_ko.pdf | 식약처 항암제 임상시험 가이드라인, 안내서-0235-04 (2024.10) | https://www.mfds.go.kr/brd/m_1060/view.do?seq=15542 | 공공저작물 (저작권법 제24조의2), 출처: 식품의약품안전처 |
| 05_mfds_ich_gcp_ko.pdf | 식약처 ICH GCP 민원인 안내서, 안내서-1035-01 (2020) | https://www.mfds.go.kr/brd/m_1060/view.do?seq=14675 | 공공저작물 (저작권법 제24조의2), 출처: 식품의약품안전처 |
| 06_mfds_ai_device_lung_ko.pdf | 식약처 AI 디지털의료기기 임상시험계획서 가이드라인: 폐암·폐결절, 안내서-0980-03 (2025.10) | https://www.mfds.go.kr/brd/m_1060/view.do?seq=15741 | 공공저작물 (저작권법 제24조의2), 출처: 식품의약품안전처 |
| 07_irecist_how_to_2020.xml | Persigehl et al., Cancer Imaging 2020;20:2 (JATS full text) | https://www.ebi.ac.uk/europepmc/webservices/rest/PMC6942293/fullTextXML | CC BY 4.0 |
| 08_recil_vs_lugano_2019.xml | Cancers (Basel) 2019;12(1):9 (JATS full text) | https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7016710/fullTextXML | CC BY 4.0 |
| 09_rano2_review_2025.xml | RANO 2.0 review, Jpn J Radiol 2025 (JATS full text) | https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12479667/fullTextXML | CC BY 4.0 |
| 10_midi_deid_report_2023.pdf | MIDI Task Group report, arXiv:2303.10473 | https://arxiv.org/pdf/2303.10473 | CC BY 4.0 |
| 11_dicom_ps3.15_annexE_2026d.html | DICOM PS3.15 Annex E, edition 2026d (unmodified) | https://dicom.nema.org/medical/dicom/current/output/chtml/part15/chapter_E.html | © NEMA; unmodified excerpt per NEMA copyright permission |

Integrity: `corpus/SHA256SUMS` (`make corpus-verify`). Copyrighted originals (RECIST 1.1, Lugano, iRECIST, RANO 2.0, LYRIC, QIBA profiles, two ClinicalTrials.gov protocols) are **not** in this repository: `make fetch-originals` downloads them for local-only evaluation into `~/clinical-rag-private/originals` (the script refuses to write inside a git work tree).
