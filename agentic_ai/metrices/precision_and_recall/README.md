# Precision@K and Recall@K

## The Core Concepts

### Precision@K
Out of the top **K** results I showed the user, what percentage are actually good?

- **Focuses on quality** — How clean/curated is my top-K list?
- High Precision@K means: "When I show you results, they are trustworthy."

### Recall@K
Out of **all** the good results that exist in my database, what percentage did I manage to show in the top **K**?

- **Focuses on quantity/coverage** — How complete is my top-K list compared to everything relevant that exists?
- High Recall@K means: "I didn't bury the good stuff; I surfaced most of what exists."

---

## Why "Per Query" Matters for Recall

Yes, exactly — when calculating Recall, the **"Relevant Items that exist"** (the denominator) is specific to that particular query. This set is often called the **"Ground Truth"** for that query.

### Why does it have to be per query?

**Relevance is not a property of the document alone; it is a property of the relationship between a query and a document.**

- If the query is **"Red apples"**, then **"Red Apple A"** is relevant.
- If the query is **"Yellow bananas"**, then **"Red Apple A"** is not relevant.

---

## The Recall Formula (Per Query)

For Query **i**:

```
Recall_i = (Number of relevant items the system FOUND for Query i)
           ------------------------------------------------------
           (Total number of relevant items that EXIST in the database for Query i)
```

---

## A Verbose Example to Illustrate

Imagine your database has **1,000 items total**.

### Query 1: "Movies by Christopher Nolan"

- **Total Relevant in DB**: **12** (There are only 12 Nolan movies in your database).
- **System Results (Top 5)**: `["Inception", "Batman", "Interstellar", "Shrek", "Titanic"]`
- **Hits**: 3 (`"Inception"`, `"Batman"`, `"Interstellar"`)

**Recall@5** = `3 / 12 = 0.25`

The system found **25%** of his movies. Even though 3 out of 5 results were good (Precision@5 = 60%), the Recall is low because there are 9 other Nolan movies completely missing from the top 5.

---

### Query 2: "Movies about Talking Animals"

- **Total Relevant in DB**: **200** (There are many such movies in your database).
- **System Results (Top 5)**: `["The Lion King", "Finding Nemo", "Zootopia", "Babe", "Bolt"]`
- **Hits**: 5 (All five are about talking animals)

**Recall@5** = `5 / 200 = 0.025`

Even though the system got a **"perfect"** top-5 list (Precision@5 = 100%), the Recall is very low (**2.5%**) because it missed 195 other talking-animal movies somewhere deeper in the results.

---

## The Challenge: "How do we know all relevant items?"

In a small learning project, you know exactly what is in your list. But in the real world (like Google or Amazon), this is the hardest part of evaluation.

### Small Datasets
Humans manually tag **every single document** for every query.  
→ *Very expensive, but accurate.*

### Large Datasets (Pooling)
You take the top results from **10 different search engines**, mix them together, and have humans grade only those.  
→ You assume anything **no one found** is "irrelevant."

### Synthetic Datasets
You use **AI to generate queries** for specific documents, so you "know" the answer because you created the test.  
→ Good for controlled experiments, but risks bias.