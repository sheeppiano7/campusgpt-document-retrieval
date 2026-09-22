import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class SearchIndex:
    """可复用的字符 TF-IDF 索引，适合无分词依赖的中英文课程资料。"""

    def __init__(self, chunks):
        self.chunks = [dict(c) for c in chunks if c.get("text", "").strip()]
        self.vectorizer = self.matrix = None
        if not self.chunks:
            return
        vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(1, 3), lowercase=True, sublinear_tf=True)
        try:
            matrix = vectorizer.fit_transform([c["text"] for c in self.chunks])
        except ValueError as exc:
            if "empty vocabulary" not in str(exc):
                raise
            return
        self.vectorizer, self.matrix = vectorizer, matrix

    def search(self, question, top_k=3, min_score=0.05):
        if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0:
            raise ValueError("top_k 必须是正整数")
        if not isinstance(min_score, (int, float)) or isinstance(min_score, bool) or not 0 <= min_score <= 1:
            raise ValueError("min_score 必须在 0 到 1 之间")
        if not isinstance(question, str) or not question.strip() or self.matrix is None:
            return []
        query = self.vectorizer.transform([question.strip()])
        scores = cosine_similarity(query, self.matrix).ravel()
        selected = np.argsort(-scores, kind="stable")[:top_k]
        return [dict(self.chunks[i], score=float(scores[i])) for i in selected if scores[i] >= min_score and scores[i] > 0]


def search_chunks(question, chunks, top_k=3, min_score=0.05):
    return SearchIndex(chunks).search(question, top_k=top_k, min_score=min_score)
