import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class SearchIndex:
    """本地字符 TF-IDF 索引；支持连续中文匹配，不包含语义模型或生成 API。"""

    def __init__(self, chunks):
        self.chunks = [dict(c) for c in chunks if c['text'].strip()]
        self.vectorizer = None
        self.matrix = None
        if not self.chunks:
            return
        # 相邻字符片段在中文问题改写后仍可共享，不依赖空格分词。
        vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(1, 3), lowercase=True)
        try:
            matrix = vectorizer.fit_transform([c['text'] for c in self.chunks])
        except ValueError as exc:
            if 'empty vocabulary' not in str(exc):
                raise
            return
        self.vectorizer, self.matrix = vectorizer, matrix

    def search(self, question, top_k=3, min_score=0.0):
        if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0:
            raise ValueError('top_k 必须是正整数')
        if not 0 <= min_score <= 1:
            raise ValueError('min_score 必须在 0 到 1 之间')
        if not question.strip() or self.matrix is None:
            return []
        query = self.vectorizer.transform([question])
        scores = cosine_similarity(query, self.matrix).ravel()
        # 稳定排序使同分结果按原文顺序呈现。
        selected = np.argsort(-scores, kind='stable')[:top_k]
        return [dict(self.chunks[i], score=float(scores[i]))
                for i in selected if scores[i] > min_score]


def search_chunks(question, chunks, top_k=3):
    """保留原调用方式；交互应用复用 SearchIndex，避免每次提问重复建索引。"""
    return SearchIndex(chunks).search(question, top_k=top_k)
