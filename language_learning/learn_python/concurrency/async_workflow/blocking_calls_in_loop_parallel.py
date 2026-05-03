"""
Here all function will be async.
But we will use blocking calls inside them.
"""

import asyncio
import time

async def blocking_call():
    await asyncio.sleep(1)
    return "Blocking call complete"


async def main():
    start_time = time.time() 
    print(start_time)
    tasks = [blocking_call() for i in range(10)]
    results = await asyncio.gather(*tasks)
    for result in results:
        print(result)
    end_time = time.time()
    print(end_time - start_time)

if __name__ == "__main__":
    asyncio.run(main())