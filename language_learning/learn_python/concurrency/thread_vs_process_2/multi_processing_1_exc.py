# cpu_bound_task.py
import time
from concurrent.futures import ProcessPoolExecutor

def heavy_calculation(n):
    """A function that simulates a CPU-bound task."""
    # print(f"Starting calculation with {n} iterations")
    total = 0
    for i in range(n):
        total += i * i
    
    # print(f"Calculation completed with total: {total}")

def main():
    num_threads = 4
    calculations_per_thread = 20_000_000
    threads = []

    start_time = time.time()

    with ProcessPoolExecutor(max_workers=4) as executor:
        results = executor.map(heavy_calculation, [calculations_per_thread for i in range(4)])

    end_time = time.time()
    print(f"Execution time: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    main()