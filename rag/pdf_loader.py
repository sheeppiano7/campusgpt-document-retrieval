from pathlib import Path

import pymupdf


def _extract(document, source_name):
    pages = []
    for number, page in enumerate(document, start=1):
        text = " ".join(page.get_text().split())
        if text:
            pages.append({"source": source_name, "page": number, "text": text})
    return pages


def parse_pdf(file_path):
    """读取文本型 PDF，跳过空页并保留原始文件名与页码。"""
    path = Path(file_path)
    try:
        with pymupdf.open(path) as document:
            if document.needs_pass:
                raise ValueError("请先解密 PDF 后再上传")
            return _extract(document, path.name)
    except (pymupdf.FileDataError, pymupdf.EmptyFileError) as exc:
        raise ValueError("无法读取 PDF，请检查文件是否损坏") from exc


def parse_pdf_bytes(data, source_name="uploaded.pdf"):
    """直接处理上传内容，不使用用户文件名拼接磁盘路径。"""
    if not data:
        raise ValueError("PDF 文件为空")
    safe_name = Path(source_name).name or "uploaded.pdf"
    try:
        with pymupdf.open(stream=data, filetype="pdf") as document:
            if document.needs_pass:
                raise ValueError("请先解密 PDF 后再上传")
            return _extract(document, safe_name)
    except (pymupdf.FileDataError, pymupdf.EmptyFileError) as exc:
        raise ValueError("无法读取 PDF，请检查文件是否损坏") from exc
