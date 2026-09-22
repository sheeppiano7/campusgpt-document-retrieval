"""Run a real local Ollama verification for the cited-answer flow.

Prerequisites:
    ollama pull qwen2.5:1.5b
    Ollama service available at http://127.0.0.1:11434
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag.answer_engine import AnswerEngine, LLMConfig
from rag.simple_search import SearchIndex


def main():
    chunks = [
        {
            "source": "operating_systems.pdf",
            "page": 7,
            "text": "Deadlock requires mutual exclusion, hold and wait, no preemption, and circular wait.",
        }
    ]
    question = "What conditions are required for deadlock?"
    results = SearchIndex(chunks).search(question, top_k=2, min_score=0.01)
    answer = AnswerEngine(
        LLMConfig(
            provider="ollama",
            model="qwen2.5:1.5b",
            base_url="http://127.0.0.1:11434",
            timeout=120,
        )
    ).answer(question, results)
    result = {
        "scenario": "local_ollama_cited_answer",
        "model": "qwen2.5:1.5b",
        "question": question,
        "retrieved_references": [
            {"source": item["source"], "page": item["page"], "score": round(item["score"], 3)}
            for item in results
        ],
        "answer": answer["answer"],
        "citation_present": "[资料1]" in answer["answer"],
    }
    root = Path(__file__).resolve().parents[1]
    output = root / "evaluation" / "ollama_real_verification.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
