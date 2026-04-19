import os
import traceback

import uvicorn


def main() -> None:
    port = int(os.getenv("PORT", "8000"))
    print(f"[deckcreator] starting server on port {port}", flush=True)
    try:
        from main import app
    except Exception:
        print("[deckcreator] failed to import FastAPI app", flush=True)
        traceback.print_exc()
        raise

    print("[deckcreator] FastAPI app import succeeded", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()
