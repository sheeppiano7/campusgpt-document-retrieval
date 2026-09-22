def split_text_by_page(pages, chunk_size=500, overlap=80):
    """按页切分并传递文件名和页码，参数保证窗口持续前移。"""
    if not isinstance(chunk_size, int) or isinstance(chunk_size, bool) or chunk_size <= 0:
        raise ValueError("chunk_size 必须是正整数")
    if not isinstance(overlap, int) or isinstance(overlap, bool) or not 0 <= overlap < chunk_size:
        raise ValueError("overlap 必须满足 0 <= overlap < chunk_size")
    chunks = []
    for page in pages:
        text = page["text"].strip()
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            content = text[start:end].strip()
            if content:
                chunks.append({"source": page.get("source", "unknown.pdf"), "page": page["page"], "text": content})
            if end == len(text):
                break
            start = end - overlap
    return chunks
