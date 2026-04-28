# Mean Average Precision (MAP)

Mean Average Precision (MAP) is often considered the **"Gold Standard"** for general search engines.

---

## How MAP Differs from MRR

- **MRR** only cares about the **first hit**. It asks: *"Where is the very first relevant document?"*
- **MAP** cares about **every hit**. It asks: *"Across all relevant documents, how well did we rank each one?"*

---

## How MAP Works

MAP works in two layers:

1. **Average Precision (AP)** for a *single query*:
   - Calculate **Precision@K** at the **exact moment** every correct document is found (i.e., at each relevant item's rank position).
   - Then **average those precisions**.

2. **Mean Average Precision (MAP)** across *all queries*:
   - Take the **AP** for each query.
   - Compute the **mean** of those AP values.

---

## The Formula (Single Query)

For a given query with **N relevant documents**, appearing at ranks *r₁, r₂, ..., rₙ*:

```
AP = (1 / N) * Σ Precision@rᵢ   for i = 1 to N
```

Where:
- `N` = total number of relevant documents for that query
- `Precision@rᵢ` = precision calculated at rank `rᵢ` (the position where the *i*-th relevant document appears)

---

## Concrete Example

### Query: "Classic sci-fi movies from the 1980s"

**Ground truth** (relevant items):
- Blade Runner
- The Terminator
- Back to the Future
- Aliens

Total relevant = **4**

### System Rankings (Top 10):

| Rank | Document                  | Relevant? | Precision@K |
|------|---------------------------|-----------|-------------|
| 1    | Blade Runner              | ✅ Yes    | 1/1 = 1.00  |
| 2    | Star Trek II              | ❌ No     | —           |
| 3    | The Terminator            | ✅ Yes    | 2/3 ≈ 0.67  |
| 4    | E.T.                      | ❌ No     | —           |
| 5    | Back to the Future        | ✅ Yes    | 3/5 = 0.60  |
| 6    | Ghostbusters              | ❌ No     | —           |
| 7    | Aliens                    | ✅ Yes    | 4/7 ≈ 0.57  |
| 8    | The Fly                   | ❌ No     | —           |
| 9    | RoboCop                   | ❌ No     | —           |
| 10   | The Running Man           | ❌ No     | —           |

### Step-by-step Calculation:

We compute precision **only** at ranks where a relevant item is found:

- Rank 1 (Blade Runner): Precision@1 = **1.00**
- Rank 3 (The Terminator): Precision@3 = **0.67**
- Rank 5 (Back to the Future): Precision@5 = **0.60**
- Rank 7 (Aliens): Precision@7 = **0.57**

**AP** = (1.00 + 0.67 + 0.60 + 0.57) / 4 = **2.84 / 4 = 0.71**

---

## From AP to MAP

If we have **Q queries**, each with its own AP:

| Query | AP   |
|-------|------|
| Q1    | 0.71 |
| Q2    | 0.85 |
| Q3    | 0.62 |

```
MAP = (AP₁ + AP₂ + AP₃) / 3 = (0.71 + 0.85 + 0.62) / 3 = 0.727
```

A **MAP of 1.0** means every query returned perfect rankings (all relevant items at the very top).  
A **MAP of 0.0** means no relevant items were retrieved.

---

## Key Properties of MAP

- **Penalizes missing relevant items**: If a relevant document is not retrieved, AP drops because `N` stays the same but one relevant item is missing.
- **Penalizes late relevant items**: Retrieving a relevant document at Rank 100 hurts AP more than retrieving it at Rank 10.
- **Graded quality**: Considers precision at *every* relevant hit, not just the first.
- **Query-level averaging**: Treats each query equally, regardless of how many relevant items it has.

---

## When to Use MAP

- **General web search**: Where multiple relevant results are valuable and order matters.
- **Document retrieval**: Legal, academic, or patent search where users want to discover many relevant items.
- **Benchmarks**: Classic IR benchmarks (like TREC) often report MAP as a primary metric.

---

## MAP vs. Other Metrics

| Metric | Focus | Graded Relevance | All Hits |
|--------|-------|------------------|----------|
| **MRR** | First hit only | ❌ Binary | ❌ No |
| **MAP** | All hits | ❌ Binary | ✅ Yes |
| **NDCG** | All hits | ✅ Yes | ✅ Yes |

MAP is stricter than MRR but less expressive than NDCG (since it uses binary relevance). Use MAP when you want a single, interpretable score that rewards *both* finding *all* relevant items *and* ranking them highly.