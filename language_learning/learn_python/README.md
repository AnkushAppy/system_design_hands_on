# Learn Python — hands-on notes

Small, runnable **Python** examples grouped by topic. Each area is independent: use a **virtual environment** in the directory you are working in and install only the dependencies that folder needs.

The repo root [`.gitignore`](../../.gitignore) ignores local **`test.db`** files, SQLite WAL/journal sidecars, **`venv`** / **`.venv`**, and common caches so generated artifacts stay out of git.

---

## Layout

| Path | Topic |
|------|--------|
| [`fastapi/dependency_injection/`](fastapi/dependency_injection/) | FastAPI `Depends` with SQLAlchemy 2.0: sync vs async SQLite |
| [`design_pattern/creational/`](design_pattern/creational/) | Creational patterns with Pydantic-heavy demos |
| [`concurrency/`](concurrency/) | Async I/O, blocking in loops, threads vs processes |
| [`installers/examples/`](installers/examples/) | Packaging / installer-related snippets |

---

## FastAPI — dependency injection

**Location:** [`fastapi/dependency_injection/`](fastapi/dependency_injection/)

| File | What it shows |
|------|----------------|
| [`main.py`](fastapi/dependency_injection/main.py) | Sync SQLAlchemy engine, `sqlite:///./test.db`, `get_db` generator dependency |
| [`async_main.py`](fastapi/dependency_injection/async_main.py) | Async engine (`sqlite+aiosqlite`), `get_async_db`, `GET/POST /users/` |
| [`test_async_main.py`](fastapi/dependency_injection/test_async_main.py) | `pytest` + Starlette `TestClient` against in-memory async SQLite |

**Install (example):**

```bash
cd fastapi/dependency_injection
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install fastapi uvicorn sqlalchemy aiosqlite
# Tests:
pip install pytest
```

**Run** (from `fastapi/dependency_injection/`; both bind **port 8000**):

```bash
python main.py
# or
python async_main.py
```

**Tests:**

```bash
pytest test_async_main.py -q
```

---

## Design patterns — creational

**Location:** [`design_pattern/creational/`](design_pattern/creational/)

| Module | Pattern |
|--------|---------|
| [`factory.py`](design_pattern/creational/factory.py) | Factory-style construction |
| [`abstract_factory.py`](design_pattern/creational/abstract_factory.py) | Abstract factory |
| [`builder.py`](design_pattern/creational/builder.py) | Builder |
| [`prototype.py`](design_pattern/creational/prototype.py) | Prototype / copy-style flows |
| [`singleton.py`](design_pattern/creational/singleton.py) | Singleton (thread-safe sketch) |
| [`intered.py`](design_pattern/creational/intered.py) | Interning / shared immutable instances (`weakref` pool) |

All of these use **Pydantic v2** (`BaseModel`, `Field`, etc.). Each file has an `if __name__ == "__main__":` demo.

```bash
cd design_pattern/creational
python -m venv .venv && source .venv/bin/activate
pip install pydantic
python factory.py    # or any other module name
```

---

## Concurrency

**Location:** [`concurrency/`](concurrency/)

- **`async_workflow/`** — blocking vs async-friendly calls inside loops (`blocking_calls.py`, `blocking_calls_in_loop.py`, `blocking_calls_in_loop_parallel.py`).
- **`thread_vs_process/`** — sequential vs multithreading vs multiprocessing examples.
- **`thread_vs_process_2/`** — threading vs multiprocessing with exception handling.
- **`thread_vs_process_3_io/`** — `benchmarking.py`; [`fastapi_server.py`](concurrency/thread_vs_process_3_io/fastapi_server.py) illustrates blocking routes vs `run_in_threadpool` / async sleep (needs `fastapi`, `uvicorn`).

Open each script for the exact `python …` entrypoint (some are libraries with a `__main__` block, some are servers).

---

## Installers — examples

**Location:** [`installers/examples/`](installers/examples/)

Lightweight scripts (`example.py`, `main.py`) for experimenting with install / entrypoint patterns. Dependencies depend on what you add; start from stdlib unless the file imports otherwise.

---

## Python version

[`fastapi/dependency_injection/.python-version`](fastapi/dependency_injection/.python-version) pins a version for tools like **pyenv** / **uv**. Other folders may run on any recent Python 3 that matches the syntax used (e.g. `typing` features); prefer **3.11+** for the least friction.
