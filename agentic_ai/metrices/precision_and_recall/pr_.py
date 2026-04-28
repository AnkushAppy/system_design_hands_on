def calculate_precision_recall_at_k(recommended_items, ground_truth_items, k):
    """
    recommended_items: List of IDs returned by the search engine
    ground_truth_items: List of IDs that are actually relevant (in the database)
    k: The cutoff
    """
    # 1. Slice to K
    top_k = recommended_items[:k]
    
    # 2. Find intersection (Which ones are in both?)
    hits = [item for item in top_k if item in ground_truth_items]
    num_hits = len(hits)
    
    # 3. Precision: Hits / Total shown
    precision = num_hits / k
    
    # 4. Recall: Hits / Total that EXIST
    recall = num_hits / len(ground_truth_items)
    
    print(f"--- Metrics @ {k} ---")
    print(f"Top {k} Results: {top_k}")
    print(f"Relevant Items that exist: {ground_truth_items}")
    print(f"Hits found: {hits} ({num_hits})")
    print(f"Precision@{k}: {num_hits}/{k} = {precision:.4f}")
    print(f"Recall@{k}:    {num_hits}/{len(ground_truth_items)} = {recall:.4f}")
    
    return precision, recall

# Example: Searching for "Red Apples"
# Database has 5 red apples. The search engine returns 10 items.
returned = ["Red Apple A", "Green Pear", "Red Apple B", "Banana", "Orange", "Red Apple C"]
actual_apples = ["Red Apple A", "Red Apple B", "Red Apple C", "Red Apple D", "Red Apple E"]

calculate_precision_recall_at_k(returned, actual_apples, k=3)