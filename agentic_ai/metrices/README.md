# Search Evaluation Metrics

Hands-on guide to core Information Retrieval metrics with runnable Python demos.

This folder includes both:
- conceptual notes (`README.md` files inside metric folders)
- executable examples (`.py` files) that print step-by-step calculations

---

## Metrics Covered

| Metric | What It Measures | Best Use Case | Example Script |
|--------|-------------------|---------------|----------------|
| **MRR@K** | How quickly the first relevant result appears | QA bots, navigational search, RAG first-hit quality | `mean_reciprocal_rank/mmr.py` |
| **NDCG@K** | Quality of ranking with graded relevance | E-commerce, recommendations, discovery search | `ndcg/ndcg.py` |
| **Precision@K** | Relevance purity in top K | "How clean are top results?" | `precision_and_recall/pr_.py` |
| **Recall@K** | Coverage of relevant items in top K | "How many relevant items did we recover?" | `precision_and_recall/pr_.py` |
| **MAP** | Average ranking quality across all relevant hits | Offline benchmark for search systems | `map/map.py` |

---

## Project Structure

```text
metrices/
├── README.md
├── mean_reciprocal_rank/
│   ├── README.md
│   └── mmr.py
├── ndcg/
│   ├── README.md
│   └── ndcg.py
├── precision_and_recall/
│   ├── README.md
│   └── pr_.py
└── map/
    ├── README.md
    └── map.py
```

---

## Quick Start

Run each metric demo from the `agentic_ai/metrices` directory:

```bash
python mean_reciprocal_rank/mmr.py
python ndcg/ndcg.py
python precision_and_recall/pr_.py
python map/map.py
```

Each script is intentionally verbose and prints intermediate steps to make the math easy to follow.

---

## What Each Script Demonstrates

### 1) `mean_reciprocal_rank/mmr.py`
- Computes **MRR@1**, **MRR@3**, and **MRR@5** on a sample multi-query dataset.
- Shows query-by-query reciprocal rank breakdown.
- Demonstrates the effect of moving the first relevant result lower in ranking.

Formula:
```text
MRR = (1 / |Q|) * Σ(1 / rank_i)
```

---

### 2) `ndcg/ndcg.py`
- Computes **DCG**, **IDCG**, and **NDCG@K** with detailed per-rank contribution tables.
- Uses graded relevance labels (e.g., 0, 1, 2, 3).
- Compares good vs bad ranking orders and K-window effects.

Formula:
```text
NDCG@K = DCG@K / IDCG@K
```

---

### 3) `precision_and_recall/pr_.py`
- Computes **Precision@K** and **Recall@K** for a sample query.
- Prints top-K results, hit set, and both ratios.
- Useful for understanding the quality-vs-coverage tradeoff.

Formulas:
```text
Precision@K = Hits@K / K
Recall@K    = Hits@K / TotalRelevant
```

---

### 4) `map/map.py`
- Computes **Average Precision (AP)** for a ranked list with multiple relevant items.
- Shows "hit" / "miss" at every rank and running precision accumulation.
- Use AP per query, then average AP across queries to get MAP.

Formulas:
```text
AP  = (Σ Precision@rank_of_each_hit) / TotalRelevant
MAP = Average(AP over all queries)
```

---

## Which Metric Should You Pick?

| Scenario | Primary Metric | Why |
|---------|----------------|-----|
| One correct answer must appear immediately | **MRR@K** | Optimizes first relevant rank |
| Order of multiple relevant items matters | **NDCG@K** | Captures graded relevance + rank position |
| Need clean top results | **Precision@K** | Penalizes irrelevant items in top K |
| Need maximum retrieval coverage | **Recall@K** | Measures misses among relevant set |
| Need one stable offline benchmark | **MAP** | Strong aggregate ranking metric |

Recommended pairs:
- `MRR + Precision@K` for assistants/search bars
- `NDCG + MAP` for discovery/recommendation systems
- `Recall@K + Precision@K` for high-recall domains (legal, medical, compliance)

---

## Notes

- `K` should match user behavior (for example: `K=3`, `K=5`, or `K=10`).
- A metric score is only as good as your relevance labels.
- Track multiple metrics together; no single metric tells the full story.