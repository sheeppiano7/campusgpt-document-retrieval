import hashlib
import streamlit as st
from rag.pdf_loader import parse_pdf_bytes
from rag.text_splitter import split_text_by_page
from rag.simple_search import SearchIndex

st.set_page_config(page_title='CampusGPT 课程资料检索', layout='wide')
st.title('CampusGPT 课程资料检索助手')
st.caption('上传课程 PDF，查找相关原文和来源页码。当前版本返回资料片段，不生成 AI 答案。')

uploaded = st.file_uploader('上传文本型课程 PDF', type=['pdf'])
data = uploaded.getvalue() if uploaded is not None else None
fingerprint = hashlib.sha256(data).hexdigest() if data is not None else None
if st.session_state.get('selected_file') != fingerprint:
    st.session_state['selected_file'] = fingerprint
    st.session_state.pop('index', None)
    st.session_state.pop('results', None)

if st.button('解析资料', disabled=uploaded is None):
    st.session_state.pop('index', None)
    st.session_state.pop('results', None)
    if len(data) > 20 * 1024 * 1024:
        st.error('请上传不超过 20 MB 的 PDF')
    else:
        try:
            pages = parse_pdf_bytes(data)
            chunks = split_text_by_page(pages)
            if not chunks:
                st.warning('未提取到文字。扫描件需要先进行文字识别，再上传文本型 PDF。')
            else:
                st.session_state['index'] = SearchIndex(chunks)
                st.success(f'已解析 {len(pages)} 个含文字页面，形成 {len(chunks)} 个文本块')
        except ValueError as exc:
            st.error(str(exc))

question = st.text_input('你想查找什么？', placeholder='例如：死锁的必要条件是什么？')
if st.button('开始检索'):
    index = st.session_state.get('index')
    if index is None:
        st.warning('请先上传 PDF 并点击“解析资料”')
    elif not question.strip():
        st.warning('请输入问题')
    else:
        results = index.search(question)
        if not results:
            st.info('没有找到匹配片段，请尝试课程中的关键词。')
        for number, result in enumerate(results, 1):
            st.subheader(f'片段 {number} · 第 {result["page"]} 页')
            st.write(result['text'])
            st.caption(f'文本匹配分数 {result["score"]:.3f}，分数不代表答案正确率')
