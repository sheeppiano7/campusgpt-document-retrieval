import fitz


def _extract(document):
    pages = []
    for number, page in enumerate(document, start=1):
        text = page.get_text().strip()
        if text:
            pages.append({'page': number, 'text': text})
    return pages


def parse_pdf(file_path):
    """读取文本型 PDF，跳过空页但保留原始页码，并及时关闭文件。"""
    with fitz.open(file_path) as document:
        if document.needs_pass:
            raise ValueError('请先解密 PDF 后再上传')
        return _extract(document)


def parse_pdf_bytes(data):
    """直接处理上传内容，不使用用户文件名拼接磁盘路径。"""
    if not data:
        raise ValueError('PDF 文件为空')
    try:
        with fitz.open(stream=data, filetype='pdf') as document:
            if document.needs_pass:
                raise ValueError('请先解密 PDF 后再上传')
            return _extract(document)
    except (fitz.FileDataError, fitz.EmptyFileError) as exc:
        raise ValueError('无法读取 PDF，请检查文件是否损坏') from exc
