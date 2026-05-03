import time
import asyncio

from fastapi import FastAPI
from starlette.concurrency import run_in_threadpool

app = FastAPI()

def heavy_io_task():
    time.sleep(5)
    return "Task Complete"

async def async_heavy_io_task():
    await asyncio.sleep(5)
    return "Task Complete"

# 1. BLOCKING (The "Don't Do This" Case)
# This blocks the event loop. If one person hits this, 
# the whole server stops for 5 seconds for everyone.
@app.get("/block")
async def blocking_io():
    heavy_io_task()
    return {"message": "I blocked the whole server!"}

@app.get("/block_async")
async def blocking_io_async():
    await async_heavy_io_task()
    return {"message": "I blocked the whole server!"}

# 2. SYNC DEF (FastAPI's Automatic ThreadPool)
# FastAPI sees 'def' and automatically runs this in its 
# internal ThreadPoolExecutor. It won't block other requests.
@app.get("/sync-pool")
def sync_io_in_pool():
    heavy_io_task()
    return {"message": "I ran in a separate thread automatically."}

# 3. MANUAL THREADPOOL (Using run_in_threadpool)
# Useful if you need to run a blocking function inside 
# an existing async function without stalling the loop.
@app.get("/manual-pool")
async def manual_threadpool():
    # Offloads the blocking function to the thread pool
    result = await run_in_threadpool(heavy_io_task)
    return {"message": result}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)