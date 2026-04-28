def calculate_mrr_at_k(queries_data, k_value):
    """
    Calculates MRR@k with a detailed breakdown of each query.
    """
    print(f"\n{'='*80}")
    print(f" CALCULATING MRR@{k_value}")
    print(f"{'='*80}")
    
    total_rr = 0
    num_queries = len(queries_data)

    for i, item in enumerate(queries_data, 1):
        query = item['query']
        results = item['results']
        target = item['target']
        
        # Consider only the top k results
        top_k_results = results[:k_value]
        
        rank = 0
        rr = 0
        
        print(f"Query {i}: '{query}'")
        print(f"  Target: '{target}'")
        print(f"  Top {k_value} results:")
        
        # Visualize the results and find the target
        for idx, res in enumerate(top_k_results):
            pos = idx + 1
            if res == target:
                print(f"    {pos}. {res}  <-- [RELEVANT FOUND]")
                rank = pos
                rr = 1 / rank
                # We stop at the FIRST relevant result found
                break 
            else:
                print(f"    {pos}. {res}")
        
        if rr == 0:
            if target in results:
                # Target exists in the full list, but outside the top K
                full_rank = results.index(target) + 1
                print(f"  Result: Found at Rank {full_rank}, but since {full_rank} > {k_value}, RR = 0")
            else:
                print(f"  Result: Not found in any results. RR = 0")
        else:
            print(f"  Result: Found at Rank {rank}. RR = 1/{rank} = {rr:.4f}")
            
        total_rr += rr
        print("-" * 40)

    mrr = total_rr / num_queries
    print(f"SUM OF RECIPROCAL RANKS: {total_rr:.4f}")
    print(f"MRR@{k_value} (Sum / {num_queries}): {mrr:.4f}")
    return mrr

# ---------------------------------------------------------
# SAMPLE DATASET
# ---------------------------------------------------------
# We have 5 queries. We provide the top 5 predictions for each.
dataset = [
    {
        "query": "Who wrote Hamlet?",
        "results": ["Shakespeare", "Marlowe", "Bacon", "Jonson", "Greene"],
        "target": "Shakespeare"  # Rank 1
    },
    {
        "query": "Capital of France",
        "results": ["Lyon", "Marseille", "Paris", "Nice", "Bordeaux"],
        "target": "Paris"        # Rank 3
    },
    {
        "query": "Largest Planet",
        "results": ["Earth", "Mars", "Saturn", "Neptune", "Jupiter"],
        "target": "Jupiter"      # Rank 5
    },
    {
        "query": "Python Creator",
        "results": ["Bill Gates", "Guido van Rossum", "Steve Jobs", "Elon Musk", "Zuckerberg"],
        "target": "Guido van Rossum" # Rank 2
    },
    {
        "query": "Moon of Mars",
        "results": ["Titan", "Europa", "Ganymede", "Io", "Callisto"],
        "target": "Phobos"       # Not in top 5
    }
]

# ---------------------------------------------------------
# RUNNING ANALYSES
# ---------------------------------------------------------

# MRR@1: Extremely strict. Only Rank 1 counts.
mrr_1 = calculate_mrr_at_k(dataset, 1)

# MRR@3: Moderately strict. Only positions 1, 2, and 3 count.
mrr_3 = calculate_mrr_at_k(dataset, 3)

# MRR@5: More lenient. Positions 1 through 5 count.
mrr_5 = calculate_mrr_at_k(dataset, 5)

# Final Comparison Table
print("\n" + "#"*30)
print("FINAL SUMMARY COMPARISON")
print("#"*30)
print(f"MRR @ 1: {mrr_1:.4f}")
print(f"MRR @ 3: {mrr_3:.4f}")
print(f"MRR @ 5: {mrr_5:.4f}")