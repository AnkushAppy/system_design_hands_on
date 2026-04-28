import math

def calculate_ndcg_verbose(query_name, actual_relevance, k):
    """
    actual_relevance: List of relevance scores in the order the system returned them.
                      e.g., [3, 1, 0, 2] (3 is 'highly relevant', 0 is 'not relevant')
    k: The cutoff point (NDCG@k)
    """
    print(f"\n--- Calculating NDCG@{k} for: {query_name} ---")
    
    # 1. Slice to K
    relevance_at_k = actual_relevance[:k]
    print(f"Top {k} Relevance Scores: {relevance_at_k}")

    # 2. Calculate DCG
    dcg = 0
    print(f"\nStep 1: Calculate DCG (Discounted Cumulative Gain)")
    print(f"{'Rank':<6} | {'Rel':<6} | {'Numerator (2^rel - 1)':<22} | {'Log Discount':<15} | {'Contribution'}")
    
    for i, rel in enumerate(relevance_at_k):
        rank = i + 1
        numerator = (2**rel) - 1
        # Log base 2 of (rank + 1) is the standard discounting factor
        discount = math.log2(rank + 1)
        contribution = numerator / discount
        dcg += contribution
        print(f"{rank:<6} | {rel:<6} | {numerator:<22.0f} | {discount:<15.4f} | {contribution:.4f}")
    
    print(f"TOTAL DCG: {dcg:.4f}")

    # 3. Calculate IDCG (Ideal DCG)
    # To get IDCG, we take all known relevance scores and sort them in descending order
    ideal_relevance = sorted(actual_relevance, reverse=True)[:k]
    idcg = 0
    print(f"\nStep 2: Calculate IDCG (Ideal Ranking: {ideal_relevance})")
    
    for i, rel in enumerate(ideal_relevance):
        rank = i + 1
        idcg += ((2**rel) - 1) / math.log2(rank + 1)
    
    print(f"TOTAL IDCG: {idcg:.4f}")

    # 4. Final NDCG
    ndcg = dcg / idcg if idcg > 0 else 0
    print(f"\nStep 3: Normalize")
    print(f"NDCG = DCG / IDCG = {dcg:.4f} / {idcg:.4f} = {ndcg:.4f}")
    
    return ndcg

# ---------------------------------------------------------
# EXAMPLES
# ---------------------------------------------------------

# Relevance scale: 3=Perfect, 2=Good, 1=Okay, 0=Irrelevant

# Example 1: A great ranking (High relevance at the top)
res1 = [3, 2, 1, 0, 0]
calculate_ndcg_verbose("Good Search Engine", res1, k=5)

# Example 2: A bad ranking (The system found good results, but put them at the bottom)
res2 = [0, 0, 1, 2, 3]
calculate_ndcg_verbose("Bad Search Engine", res2, k=5)

# Example 3: Comparing NDCG@3 vs NDCG@5 for the same result
# Note how the score changes when we change our "window" of interest
res3 = [3, 0, 0, 2, 2]
calculate_ndcg_verbose("Window Test @3", res3, k=3)
calculate_ndcg_verbose("Window Test @5", res3, k=5)