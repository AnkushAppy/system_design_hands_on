# NDCG (Normalized Discounted Cumulative Gain)

NDCG (Normalized Discounted Cumulative Gain) is more sophisticated than MRR. While MRR only cares about the first relevant result, NDCG cares about **multiple relevant results** and **how relevant each one is**.

It answers the question: **"Did we put the most important items at the very top, and the less important items slightly below them?"**

---

## The Three Components of NDCG

To understand NDCG, you must understand these three steps:

1. **CG (Cumulative Gain)**: The sum of relevance scores. It doesn't care about order.
2. **DCG (Discounted Cumulative Gain)**: The sum of relevance scores penalized (discounted) based on their position. A good result at Rank 10 is worth much less than at Rank 1.
3. **IDCG (Ideal DCG)**: This is the DCG of a "perfect" world where the results are sorted from most relevant to least relevant.

**NDCG**:

```
NDCG = DCG / IDCG
```

This gives a score between **0 and 1**.

---

## What Does "Discounted" Mean?

In the context of NDCG, the word **"Discounted"** refers to a reduction in value based on position.

Think of it like a **"late penalty."** If a student turns in a perfect paper on time, they get 100%. If they turn in that same perfect paper a week late, the teacher "discounts" the grade (maybe they only get 70%).

In search results, **Rank 1 is "on time," and Rank 10 is "late."**

### 1. The Intuition

The **"Gain"** is how relevant a document is. The **"Discount"** is how much we stop caring about that relevance as the user has to scroll further down.

- **Gain**: "This document is a perfect match! (Score: 3)"
- **Discount**: "But it's at the bottom of the page, so the user probably won't see it. Let's reduce its value."

### 2. The Math of the Discount

In the formula for DCG, we calculate the value of a result like this:

```
Value = Gain / Discount Factor
```

The standard discount factor used is **log₂(rank + 1)**.

| Rank | Log Discount (log₂(rank+1)) | Effect on Score |
|------|-----------------------------|----------------|
| 1    | log₂(2) = 1.0               | No discount. You get 100% of the gain. |
| 2    | log₂(3) ≈ 1.58              | Divided by 1.58. The value drops significantly. |
| 3    | log₂(4) = 2.0               | Divided by 2. A perfect result here is worth half as much as at Rank 1. |
| 10   | log₂(11) ≈ 3.45             | Divided by 3.45. The value is heavily penalized. |

### 3. Why use a Logarithm for the discount?

You might ask: *"Why not just divide by the rank? (e.g., divide by 1, 2, 3...)"*

Researchers found that a simple linear discount (1, 2, 3) is too harsh. Users do look at the first few results. A logarithmic discount is **"gentler."**

- It penalizes the first few drops (from Rank 1 to 2 to 3) quite a bit.
- But the difference between Rank 100 and Rank 101 is almost nothing, because by that point, the user has already stopped looking. The log curve flattens out, reflecting this human behavior.

### 4. A Concrete Example

Imagine you have a **Perfect Result (Relevance = 7)**.

- At Rank 1:
  ```
  7 / log₂(2) = 7 / 1 = 7.0
  ```

- At Rank 3:
  ```
  7 / log₂(4) = 7 / 2 = 3.5
  ```

The **"Discount"** has cut the value of that perfect result in half just because it moved down two spots.

### Summary

- **Gain**: The raw quality of the result.
- **Discount**: A penalty based on how far down the list the result is.
- **Discounted Gain**: The "actual value" the user gets from that result, considering they have to work (scroll/read) to find it.

---

## Comparison Breakdown (Why use NDCG?)

Let's use a sample query: **"Best Smartphones 2024"**

| Result Pos | Relevance (0-3) | Why?                          |
|------------|-----------------|-------------------------------|
| 1          | 3               | iPhone 15 Pro (Perfect match) |
| 2          | 2               | Samsung S24 (Very relevant)   |
| 3          | 0               | A link to a recipe for pie (Irrelevant) |
| 4          | 1               | A phone from 2022 (Somewhat relevant) |

### Why MRR would be insufficient here:

MRR only asks: **"Where is the first relevant item?"**

- In this case, the first relevant item is at Rank 1.
- MRR = **1.0**.
- MRR doesn't care that Rank 3 is a recipe for pie. It doesn't care that Rank 2 is also very good. It gives this list a "Perfect" score.

### How NDCG sees it:

**DCG** calculates:

```
DCG = (2^3 - 1) / log(2)  +  (2^2 - 1) / log(3)  +  (2^0 - 1) / log(4)  +  (2^1 - 1) / log(5)
```

It notices that the **0 at Rank 3** hurts the score.

It compares this to the **Ideal (IDCG)**, which would have put the **3, 2, 1, 0** in that exact order.

If your system returned **[0, 1, 2, 3]**, NDCG would give you a very low score because your best content (**3**) was heavily discounted by being at the bottom.

---

## Summary: MRR vs. NDCG

| Feature          | MRR                          | NDCG                                   |
|------------------|------------------------------|----------------------------------------|
| Relevance        | Binary (Yes/No)              | Graded (0, 1, 2, 3...)                 |
| Focus            | First relevant item only     | The whole list (up to K)               |
| Use Case         | Navigational (Find "The" page) | Discovery (Find "many" good things) |
| Complexity       | Very Simple                  | Mathematical / Logarithmic             |
| Interpretation   | Average Rank                 | How close to "Perfectly Sorted"        |

---

## When to use NDCG?

Use it for **E-commerce (Amazon)**, **Streaming (Netflix)**, or **Web Search (Google)**, where you want to show a variety of relevant items and the specific order of the top 10 items matters immensely.