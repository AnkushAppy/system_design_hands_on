"""
Here all function will be async.
But we will use blocking calls inside them.
"""

import asyncio
import time

async def blocking_call():
    await asyncio.sleep(1)
    return "Blocking call complete"

async def blocking_call_time():
    time.sleep(1)
    return "Blocking call time complete"

def blocking_call_time_sync():
    time.sleep(1)
    return "Blocking call time complete"

async def main():
    start_time = time.time() 
    print(start_time)
    result = await blocking_call_time()
    print(result, time.time())
    result = await blocking_call()
    print(result, time.time())
    result = blocking_call_time_sync()
    print(result, time.time())

if __name__ == "__main__":
    asyncio.run(main())