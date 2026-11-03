"""Run the local SOVRIVA API and dashboard."""

import os
import socket

import uvicorn
from sovriva.api import app


if __name__ == "__main__":
    port = int(os.getenv("SOVRIVA_PORT", "8765"))
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        probe.bind(("127.0.0.1", port))
    except OSError as exc:
        raise SystemExit(
            f"SOVRIVA cannot start: 127.0.0.1:{port} is already in use. "
            "Stop the other local service or choose SOVRIVA_PORT explicitly."
        ) from exc
    finally:
        probe.close()
    config = uvicorn.Config(
        app=app,
        host="127.0.0.1",
        port=port,
        reload=False,
    )
    uvicorn.Server(config).run()
