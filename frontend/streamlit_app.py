"""ClinicalRAG QA - Streamlit UI (documents, indexing, Q&A, DICOM analysis).

The UI only talks to the FastAPI backend (API_BASE_URL); it never calls an LLM directly.
"""

import os
from typing import Any

import httpx
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
TIMEOUT = httpx.Timeout(float(os.getenv("UI_TIMEOUT_SEC", "300")))


def api(method: str, path: str, **kwargs: Any) -> dict[str, Any] | None:
    try:
        res = httpx.request(method, f"{API_BASE_URL}{path}", timeout=TIMEOUT, **kwargs)
    except httpx.HTTPError as exc:
        st.error(f"API 연결 실패: {exc}")
        return None
    if res.is_error:
        detail = (
            res.json().get("detail")
            if res.headers.get("content-type", "").startswith("application/json")
            else res.text
        )
        st.error(f"API 오류 {res.status_code}: {detail}")
        return None
    return res.json()


st.set_page_config(page_title="ClinicalRAG QA", layout="wide")
st.title("ClinicalRAG QA")
st.caption(
    "Local-first 의료문서 RAG + DICOM Tag Analyzer — toy / public / 로컬 전용(private) 코퍼스"
)


def corpus_label(name: str | None, classification: str | None, external_allowed: bool) -> str:
    scope = "외부 LLM 허용 가능" if external_allowed else "로컬 전용"
    return f"{name or '(이름 없음)'} · {classification or '분류 없음'} · {scope}"


corpora_info = api("GET", "/api/corpora") or {"corpora": [], "folders": [], "llmProvider": "?"}

with st.sidebar:
    st.subheader("System health")
    if st.button("새로고침"):
        st.session_state.pop("health", None)
    health = st.session_state.setdefault("health", api("GET", "/api/health"))
    if health:
        st.write(f"상태: **{health['status']}** · LLM provider: `{health['llmProvider']}`")
        components = (
            "database",
            "pgvector",
            "ollama",
            "llmModel",
            "embeddingModel",
            "embeddingIndex",
        )
        for key in components:
            item = health[key]
            st.write(f"{'✅' if item['ok'] else '⚠️'} {key}: {item.get('detail') or ''}")
        if health["llmProvider"] != "ollama":
            st.warning("외부 LLM(Claude API) 모드입니다. 가상/비민감 샘플 문서만 사용하세요.")

tab_docs, tab_index, tab_ask, tab_dicom = st.tabs(["문서 목록", "인덱싱", "질문하기", "DICOM 분석"])

with tab_docs:
    data = api("GET", "/api/documents")
    if data:
        rows = [
            {
                "파일명": d["fileName"],
                "형식": d["fileType"],
                "상태": d["status"],
                "chunk 수": d["chunkCount"],
                "인덱싱 시각": d.get("indexedAt"),
                "오류 유형": d.get("errorType"),
                "오류 메시지": d.get("errorMessage"),
            }
            for d in data["documents"]
        ]
        if rows:
            st.dataframe(rows, use_container_width=True)
        else:
            st.info("인덱싱된 문서가 없습니다.")

with tab_index:
    folders = corpora_info["folders"]
    presets = {
        corpus_label(f["name"], f["classification"], f["externalAllowed"]): f["path"]
        for f in folders
    }
    choice = st.selectbox("코퍼스 폴더", ["직접 입력", *presets])
    if choice == "직접 입력":
        path = st.text_input("인덱싱할 폴더 (비우면 RAW_DOCS_PATH)", value="")
    else:
        path = presets[choice]
        st.caption(f"`{path}` — 폴더의 .corpus.yaml이 이름·분류·포함할 파일을 정합니다.")
    if st.button("인덱싱 실행", type="primary"):
        with st.spinner("문서 파싱 → chunk → embedding → 저장 중..."):
            job = api("POST", "/api/index", json={"path": path or None})
        if job:
            cols = st.columns(4)
            cols[0].metric("전체", job["total"])
            cols[1].metric("성공", job["indexed"])
            cols[2].metric("실패", job["failed"])
            cols[3].metric("중복 생략", job["skippedDuplicate"])
            failures = [d for d in job["details"] if d["status"] != "INDEXED"]
            if failures:
                st.subheader("실패/생략 사유")
                st.dataframe(failures, use_container_width=True)

with tab_ask:
    question = st.text_area(
        "질문", placeholder="DICOM 업로드 실패 시 운영자가 먼저 확인해야 할 항목은?"
    )
    indexed = {
        corpus_label(c["name"], c["classification"], c["externalAllowed"]): c
        for c in corpora_info["corpora"]
        if c["name"]
    }
    selected_corpus = st.selectbox(
        "코퍼스",
        ["전체", *indexed],
        format_func=lambda k: (
            k
            if k == "전체"
            else f"{k} ({indexed[k]['documents']}개 문서, {indexed[k]['chunks']} chunk)"
        ),
        help="검색을 한 코퍼스로 제한합니다. 로컬 전용 코퍼스는 외부 LLM 모드에서 거부됩니다.",
    )
    corpus = None if selected_corpus == "전체" else indexed[selected_corpus]["name"]
    if corpus and not indexed[selected_corpus]["externalAllowed"]:
        st.caption(
            "로컬 전용 코퍼스: 답변은 로컬 Ollama에서만 생성되고, 외부 LLM 모드에서는 "
            "이 코퍼스의 문서가 검색되지 않습니다."
        )
    top_k = st.slider("top-k", 1, 10, 5)
    if st.button("질문하기", type="primary") and question.strip():
        body = {"question": question, "topK": top_k, "corpus": corpus}
        with st.spinner("검색 및 답변 생성 중..."):
            result = api("POST", "/api/ask", json=body)
            retrieved = api("POST", "/api/retrieve", json=body)
        if result:
            if result["refused"]:
                st.warning(f"거절됨 ({result['refusalReason']})")
            elif result.get("partial"):
                st.info(f"부분 답변: {result.get('caveat') or ''}")
            st.markdown(result["answer"])
            st.subheader("출처")
            for s in result["sources"]:
                loc = " · ".join(
                    x
                    for x in (s.get("sectionTitle"), s.get("pageNumber") and f"p.{s['pageNumber']}")
                    if x
                )
                st.write(f"- {s['fileName']} / {loc} (chunk {s['chunkIndex']}, score {s['score']})")
            if not result["sources"]:
                st.write("- (없음)")
            lat = result["latencyMs"]
            usage = result.get("llm") or {}
            st.caption(
                f"검색 {lat['retrieval']}ms · 생성 {lat['generation']}ms · "
                f"{usage.get('provider', '-')}/{usage.get('model', '-')} · "
                f"tokens in {usage.get('inputTokens', '-')} / out {usage.get('outputTokens', '-')}"
            )
        if retrieved:
            with st.expander("검색된 chunk 미리보기"):
                for c in retrieved["chunks"]:
                    st.markdown(f"**{c['fileName']}** · score `{c['score']}` · {c['metadata']}")
                    st.text(c["text"][:600])

with tab_dicom:
    st.info("이 기능은 DICOM 태그(메타데이터)만 분석합니다. 영상 판독은 수행하지 않습니다.")
    files = (api("GET", "/api/dicom/files") or {}).get("files", [])
    selected = st.selectbox("DICOM 파일", files) if files else st.text_input("DICOM 파일 경로")
    explain = st.checkbox("LLM 설명 생성", value=True)
    if st.button("분석", type="primary") and selected:
        with st.spinner("태그 추출 및 규칙 검사 중..."):
            result = api(
                "POST", "/api/dicom/analyze", json={"filePath": selected, "explain": explain}
            )
        if result:
            st.markdown(result["summary"])
            st.caption(f"설명 생성: {result['summarySource']} · 규칙: {result['ruleSource']}")
            counts = result["counts"]
            iod = result["layer1"]["iod"]
            cols = st.columns(4)
            cols[0].metric("IOD", iod["name"] or "미확인", help=iod.get("source"))
            cols[1].metric(
                "Layer 1 적합성 오류", counts["layer1"]["error"], help=result["layer1"]["standard"]
            )
            cols[2].metric(
                "Layer 2 비식별화 오류/경고",
                f"{counts['layer2']['error']} / {counts['layer2']['warning']}",
                help=result["layer2"]["profileEdition"],
            )
            qr = result["quantitationReadiness"]
            cols[3].metric(
                "PET SUV 준비도",
                "해당 없음" if not qr["applicable"] else ("준비됨" if qr["ready"] else "부족"),
            )

            def show_findings(findings: list[dict[str, Any]]) -> None:
                rows = [
                    {
                        "심각도": f["severity"],
                        "코드": f["code"],
                        "속성": f.get("attribute") or "",
                        "태그": f.get("tag") or "",
                        "조치": f.get("action") or "",
                        "건수": f["count"],
                        "내용": f["message"],
                        "근거": f["source"],
                        "위치": ", ".join(f.get("paths") or []),
                    }
                    for f in findings
                ]
                if rows:
                    st.dataframe(rows, use_container_width=True, hide_index=True)
                else:
                    st.write("없음")

            t1, t2, t3, t4 = st.tabs(
                ["Layer 1 · 표준 적합성", "Layer 2 · 비식별화", "PET 정량 준비도", "태그 요약"]
            )
            with t1:
                st.caption(
                    f"{result['layer1']['standard']} · IOD 결정: {iod.get('determinedBy') or '-'}"
                )
                show_findings(result["layer1"]["findings"])
            with t2:
                claim = result["layer2"]["claimedDeid"]
                methods = ", ".join(m["meaning"] for m in claim["methodCodes"]) or "-"
                options = ", ".join(
                    f"{o['name']} ({o['origin']})" for o in result["layer2"]["optionsApplied"]
                )
                st.caption(
                    f"{result['layer2']['profile']} · {result['layer2']['profileEdition']} · "
                    f"PatientIdentityRemoved: {claim['patientIdentityRemoved']} · "
                    f"선언된 방법: {methods} · 적용 옵션: {options or '없음(기본 프로파일)'}"
                )
                show_findings(result["layer2"]["findings"])
            with t3:
                if qr["applicable"]:
                    st.caption(qr.get("label") or "")
                    show_findings(qr["findings"])
                else:
                    st.write("PET 영상이 아니어서 해당 없음")
            with t4:
                st.caption("허용된 코드/숫자 값만 표시합니다. 그 외 속성은 존재 여부만 표시합니다.")
                st.json(result["tagSummary"])
