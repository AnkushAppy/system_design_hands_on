def calculate_average_precision_verbose(recommended_items, ground_truth_items):
    print(f"\n--- Calculating Average Precision (AP) ---")
    
    hits = 0
    sum_precisions = 0
    relevant_count = len(ground_truth_items)
    
    for i, item in enumerate(recommended_items):
        rank = i + 1
        if item in ground_truth_items:
            hits += 1
            precision_at_rank = hits / rank
            sum_precisions += precision_at_rank
            print(f"Rank {rank}: [HIT] '{item}' -> Precision@{rank} is {hits}/{rank} = {precision_at_rank:.4f}")
        else:
            print(f"Rank {rank}: [MISS] '{item}'")
            
    ap = sum_precisions / relevant_count
    print(f"Average Precision (AP): Sum({sum_precisions:.4f}) / Total Relevant({relevant_count}) = {ap:.4f}")
    return ap

# Query: "Python Tutorials"
# 3 relevant tutorials exist in DB.
db_relevance = ["Tutorial 1", "Tutorial 2", "Tutorial 3"]
# System returns 5 results
results = ["Tutorial 1", "Blog Post", "Tutorial 2", "Ad", "Tutorial 3"]

calculate_average_precision_verbose(results, db_relevance)