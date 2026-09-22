import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rag.simple_search import SearchIndex


def evaluate(dataset, top_k=3):
    index = SearchIndex(dataset["documents"])
    reciprocal_ranks, hits, details = [], 0, []
    for item in dataset["questions"]:
        results = index.search(item["question"], top_k=top_k, min_score=0.0)
        rank = next((n for n, result in enumerate(results, 1) if result["source"] == item["source"] and result["page"] == item["page"]), None)
        hits += rank is not None
        reciprocal_ranks.append(0 if rank is None else 1 / rank)
        details.append({"question": item["question"], "expected": f"{item['source']}#{item['page']}", "rank": rank})
    count = len(dataset["questions"])
    return {"question_count": count, f"recall_at_{top_k}": hits / count, "mrr": sum(reciprocal_ranks) / count, "details": details}


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    dataset = json.loads((root / "evaluation" / "sample_dataset.json").read_text(encoding="utf-8"))
    result = evaluate(dataset)
    (root / "evaluation" / "latest_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
