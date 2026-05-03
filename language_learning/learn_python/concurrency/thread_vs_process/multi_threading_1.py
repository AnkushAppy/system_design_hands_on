# cpu_bound_task.py
import time
import threading

def heavy_calculation(n):
    """A function that simulates a CPU-bound task."""
    print(f"Starting calculation with {n} iterations")
    total = 0
    for i in range(n):
        total += i * i
    
    print(f"Calculation completed with total: {total}")

def main():
    num_threads = 4
    calculations_per_thread = 20_000_000
    threads = []

    start_time = time.time()

    for _ in range(num_threads):
        thread = threading.Thread(target=heavy_calculation, args=(calculations_per_thread,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    end_time = time.time()
    print(f"Execution time: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    main()