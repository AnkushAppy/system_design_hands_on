import time
from multiprocessing import Pool

def heavy_calculation(n):
    # A function that simulates a CPU-bound task.
    print(f"Starting calculation with {n} iterations")
    total = 0
    for i in range(n):
        total += i * i
    print(f"Calculation completed with total: {total}")
    return total

def main():
    num_processes = 4
    calculations_per_thread = 20_000_000
    
    # Create a list of arguments for each process
    args = [calculations_per_thread] * num_processes
    
    start_time = time.time()
    
    # Use a process pool to run tasks in parallel
    with Pool(processes=num_processes) as pool:
        results = pool.map(heavy_calculation, args)
        
    end_time = time.time()
    print(f"Calculation results: {results}")
    print(f"Execution time: {end_time - start_time:.2f} seconds")

if __name__ == '__main__':
    main()
