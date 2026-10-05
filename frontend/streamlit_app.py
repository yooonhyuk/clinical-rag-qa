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
st.caption("Local-first 의료문서 RAG + DICOM Tag Analyzer — 가상 샘플 데이터 전용 데모")

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
    path = st.text_input("인덱싱할 폴더 (비우면 RAW_DOCS_PATH)", value="")
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
    top_k = st.slider("top-k", 1, 10, 5)
    if st.button("질문하기", type="primary") and question.strip():
        with st.spinner("검색 및 답변 생성 중..."):
            result = api("POST", "/api/ask", json={"question": question, "topK": top_k})
            retrieved = api("POST", "/api/retrieve", json={"question": question, "topK": top_k})
        if result:
            if result["refused"]:
                st.warning(f"거절됨 ({result['refusalReason']})")
            st.markdown(result["answer"])
            st.subheader("출처")
            for s in result["sources"]:
                loc = f"p.{s['pageNumber']}" if s.get("pageNumber") else s.get("sectionTitle") or ""
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
            left, right = st.columns(2)
            left.subheader("태그 요약")
            left.json(result["tagSummary"])
            qa = result["qaResult"]
            right.subheader("통과")
            right.write(", ".join(qa["passed"]) or "-")
            right.subheader("주의 (개인정보)")
            for w in qa["warnings"]:
                right.warning(w)
            right.subheader("누락")
            for m in qa["missing"]:
                right.error(m)
            if not qa["missing"]:
                right.write("없음")
