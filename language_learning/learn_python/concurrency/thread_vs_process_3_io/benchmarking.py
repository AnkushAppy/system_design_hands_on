import time
import requests
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

URL = "http://127.0.0.1:8000"
NUM_REQUESTS = 5

def call_api_blocking_io(i):
    response = requests.get(f"{URL}/block")
    return response.json()

def call_api_blocking_io_async(i):
    response = requests.get(f"{URL}/block_async")
    return response.json()

def call_api_sync_pool(i):
    response = requests.get(f"{URL}/sync-pool")
    return response.json()

def call_api_manual_pool(i):
    response = requests.get(f"{URL}/manual-pool")
    return response.json()

def run_benchmark(executor_class, label, func):
    print(f"--- Starting {func.__name__} Benchmark ---")
    start_time = time.time()
    
    with executor_class(max_workers=NUM_REQUESTS) as executor:
        results = list(executor.map(func, range(NUM_REQUESTS)))
        
    duration = time.time() - start_time
    print(f"{func.__name__} took: {duration:.2f} seconds\n")

if __name__ == "__main__":
    # Ensure your FastAPI server is running before executing this
    run_benchmark(ThreadPoolExecutor, "Multi-Threading", call_api_blocking_io)
    run_benchmark(ThreadPoolExecutor, "Multi-Threading", call_api_blocking_io_async)
    run_benchmark(ThreadPoolExecutor, "Multi-Threading", call_api_sync_pool)
    run_benchmark(ThreadPoolExecutor, "Manual ThreadPool", call_api_manual_pool)
    run_benchmark(ProcessPoolExecutor, "Multi-Processing", call_api_blocking_io)
    run_benchmark(ProcessPoolExecutor, "Multi-Processing", call_api_blocking_io_async)
    run_benchmark(ProcessPoolExecutor, "Multi-Processing", call_api_sync_pool)
    run_benchmark(ProcessPoolExecutor, "Multi-Processing", call_api_manual_pool)
    run_benchmark(ProcessPoolExecutor, "Manual ThreadPool", call_api_blocking_io)
    run_benchmark(ProcessPoolExecutor, "Manual ThreadPool", call_api_blocking_io_async)
    run_benchmark(ProcessPoolExecutor, "Manual ThreadPool", call_api_sync_pool)
    run_benchmark(ProcessPoolExecutor, "Manual ThreadPool", call_api_manual_pool)
