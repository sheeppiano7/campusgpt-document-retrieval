import hashlib
import os

import streamlit as st

from rag.answer_engine import AnswerEngine, LLMConfig
from rag.pdf_loader import parse_pdf_bytes
from rag.simple_search import SearchIndex
from rag.text_splitter import split_text_by_page

MAX_FILE_SIZE = 20 * 1024 * 1024

st.set_page_config(page_title="CampusGPT 课程资料问答", page_icon="📚", layout="wide")
st.title("📚 CampusGPT 课程资料问答助手")
st.caption("上传课程 PDF，基于检索内容回答问题，并显示文件名、页码和原文证据。")

with st.sidebar:
    st.header("回答设置")
    provider_label = st.selectbox(
        "回答模式",
        ["本地证据摘要（无需 API）", "OpenAI 兼容接口", "Ollama 本地模型"],
    )
    provider = {
        "本地证据摘要（无需 API）": "extractive",
        "OpenAI 兼容接口": "openai_compatible",
        "Ollama 本地模型": "ollama",
    }[provider_label]
    model = base_url = api_key = ""
    if provider == "openai_compatible":
        base_url = st.text_input("接口地址", value=os.getenv("CAMPUSGPT_BASE_URL", "https://api.openai.com/v1"))
        model = st.text_input("模型名称", value=os.getenv("CAMPUSGPT_MODEL", "gpt-4.1-mini"))
        api_key = st.text_input("API Key", value=os.getenv("CAMPUSGPT_API_KEY", ""), type="password")
        st.caption("密钥只保存在当前进程和会话中，不写入项目文件。")
    elif provider == "ollama":
        base_url = st.text_input("Ollama 地址", value=os.getenv("CAMPUSGPT_OLLAMA_URL", "http://127.0.0.1:11434"))
        model = st.text_input("本地模型", value=os.getenv("CAMPUSGPT_OLLAMA_MODEL", "qwen2.5:3b"))
    top_k = st.slider("检索片段数量", 1, 6, 3)
    min_score = st.slider("最低匹配分数", 0.0, 0.5, 0.05, 0.01)

uploaded_files = st.file_uploader(
    "上传文本型课程 PDF（可多选，每个不超过 20 MB）",
    type=["pdf"],
    accept_multiple_files=True,
)
fingerprint = tuple((f.name, hashlib.sha256(f.getvalue()).hexdigest()) for f in uploaded_files)
if st.session_state.get("selected_files") != fingerprint:
    st.session_state["selected_files"] = fingerprint
    for key in ("index", "document_stats", "last_answer"):
        st.session_state.pop(key, None)

if st.button("解析并建立索引", disabled=not uploaded_files, type="primary"):
    all_pages, errors = [], []
    for uploaded in uploaded_files:
        data = uploaded.getvalue()
        if len(data) > MAX_FILE_SIZE:
            errors.append(f"{uploaded.name}：文件超过 20 MB")
            continue
        try:
            pages = parse_pdf_bytes(data, source_name=uploaded.name)
            if not pages:
                errors.append(f"{uploaded.name}：未提取到文字，扫描件需要先做 OCR")
            else:
                all_pages.extend(pages)
        except ValueError as exc:
            errors.append(f"{uploaded.name}：{exc}")
    for error in errors:
        st.warning(error)
    chunks = split_text_by_page(all_pages)
    if chunks:
        st.session_state["index"] = SearchIndex(chunks)
        st.session_state["document_stats"] = {
            "files": len({p["source"] for p in all_pages}),
            "pages": len(all_pages),
            "chunks": len(chunks),
        }
        stats = st.session_state["document_stats"]
        st.success(f"索引建立完成：{stats['files']} 个文件，{stats['pages']} 个含文字页面，{stats['chunks']} 个文本块")
    else:
        st.session_state.pop("index", None)

stats = st.session_state.get("document_stats")
if stats:
    col1, col2, col3 = st.columns(3)
    col1.metric("资料文件", stats["files"])
    col2.metric("含文字页面", stats["pages"])
    col3.metric("检索文本块", stats["chunks"])

question = st.text_input("请输入问题", placeholder="例如：死锁产生的四个必要条件是什么？")
if st.button("检索并回答"):
    index = st.session_state.get("index")
    if index is None:
        st.warning("请先上传 PDF 并建立索引")
    elif not question.strip():
        st.warning("请输入问题")
    elif provider == "openai_compatible" and (not api_key.strip() or not model.strip()):
        st.warning("请填写模型名称和 API Key，或切换到本地证据摘要模式")
    elif provider == "ollama" and not model.strip():
        st.warning("请填写 Ollama 模型名称")
    else:
        results = index.search(question, top_k=top_k, min_score=min_score)
        config = LLMConfig(provider=provider, model=model, base_url=base_url, api_key=api_key)
        try:
            st.session_state["last_answer"] = AnswerEngine(config).answer(question, results)
        except RuntimeError as exc:
            st.error(str(exc))

answer = st.session_state.get("last_answer")
if answer:
    st.subheader("回答")
    st.write(answer["answer"])
    st.caption(f"回答模式：{answer['provider']}。回答仅依据下列检索证据。")
    st.subheader("来源证据")
    for ref in answer["references"]:
        with st.expander(f"[{ref['id']}] {ref['source']} · 第 {ref['page']} 页 · 匹配分数 {ref['score']:.3f}", expanded=ref["id"] == 1):
            st.write(ref["text"])
