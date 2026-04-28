# Mean Reciprocal Rank (MRR)

Mean Reciprocal Rank (MRR) is a standard information retrieval metric that evaluates a model by calculating the average of the reciprocals of the ranks at which the first relevant document is found across multiple queries. It focuses on how quickly a user finds the first correct answer.

## Why MRR is a "Good" Metric

Mean Reciprocal Rank (MRR) is one of the most popular metrics in Search Engines, Recommendation Systems, and Information Retrieval because it aligns very closely with how humans actually use technology.

### 1. It Reflects User Impatience (Top-Heavy)
Most users only care about the first few results. They rarely scroll to the second page of Google or the bottom of a recommendation list.

- **The Penalty**: MRR penalizes a system heavily if the correct answer drops from Rank 1 to Rank 2.
  - Rank 1 gives a score of **1.0**.
  - Rank 2 gives a score of **0.5**.

This 50% drop in score for being just one position off reflects the reality that a user is much less likely to click the second item than the first.

### 2. Perfect for "Factoid" or "Navigational" Search
MRR is the gold standard when there is only one right answer or when the user is looking for a specific target.

**Example**: "What is the capital of Japan?" or "Login to Netflix."

The user isn't looking for a list of relevant documents; they want the one correct link. MRR measures exactly how high that one link is.

### 3. Simplicity and Interpretability
Unlike more complex metrics like NDCG (Normalized Discounted Cumulative Gain), MRR is very easy to explain to stakeholders:

- An MRR of **0.5** roughly means "On average, our correct answer is at Rank 2."
- An MRR of **0.2** means "On average, the answer is at Rank 5."

It is always between 0 and 1, making it easy to track improvement over time.

### 4. Requires Less Data Labeling
To calculate other metrics (like MAP or NDCG), you often need to know the relevance of every item in your list (e.g., "This is a 5/5 match, this is a 3/5 match").

For MRR, you only need to identify the first relevant item. This makes it much cheaper and faster to evaluate your system because you don't need to grade the entire list of results.

### 5. Highly Sensitive to Improvements at the Top
If you improve your algorithm and an item moves from Rank 100 to Rank 50, the MRR barely changes (0.01 vs 0.02).
However, if an item moves from Rank 3 to Rank 1, the score jumps significantly (0.33 to 1.0). This forces developers to focus on the **"Top 10" experience**, which is what impacts the user most.

### When is MRR NOT a good metric?

While it is "good," it isn't perfect for every situation. You should be careful using it if:

- **The user needs multiple results**: If a user searches for "Best running shoes," they want to compare 10 different pairs. MRR only cares about the first one it finds and ignores the quality of the other 9.
- **The order of multiple relevant items matters**: If there are 5 relevant documents, MRR doesn't care if the other 4 are at the bottom of the list or the top.

## Overview

This video explains the concept of Mean Reciprocal Rank (MRR) and how it's calculated:

[![Related video thumbnail](https://img.youtube.com/vi/VIDEO_ID/0.jpg)](https://www.youtube.com/watch?v=VIDEO_ID)

**Computing For All** • YouTube • 29 Sept 2024 • 37s

## Key Aspects of MRR

### Formula

```
MRR = (1 / |Q|) * Σ(1 / rank_i)
```

Where:
- `|Q|` is the total number of queries
- `rank_i` is the position of the first relevant result for query `i`

### Interpretation

- A higher MRR (closer to 1) means the system consistently places relevant results at the top.
- An MRR of 0.5 implies that, on average, the first relevant document is in the second position.

### Use Cases

MRR is ideal for:
- **Known-item searches** — When you know the specific item you're looking for and need to find it quickly
- **Voice assistants** — Where users expect the top result to be correct immediately
- **Retrieval-Augmented Generation (RAG) systems** — Where only the top-ranked relevant result matters for downstream processing

### Limitations

- **Ignores subsequent relevant items**: MRR only considers the rank of the first relevant document and disregards the ranking of other relevant items that appear after it.
- **Binary relevance**: It treats the first relevant item the same regardless of how many relevant items exist in the results.

### Example

If the first relevant results are at positions **3**, **1**, and **2** for three queries:

- Reciprocal ranks: `1/3`, `1/1`, `1/2`
- MRR = `(1/3 + 1/1 + 1/2) / 3` = `(0.33 + 1.0 + 0.5) / 3` = `1.83 / 3` = **0.61**

This means, on average, the system places the first relevant result at approximately rank 1.63 across all queries.