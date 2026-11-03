# Architecture

```text
Tauri v2 window
  └── static SOVRIVA dashboard
       └── http://127.0.0.1:8765
            ├── FastAPI local API
            ├── import adapters + intelligence engine
            └── SQLite (source records, observations, settings)

Chrome/Edge MV3 extension
  ├── webRequest observation (metadata only)
  ├── declarativeNetRequest enforcement
  ├── content-script cosmetic filtering
  └── authenticated batched loopback sync
```

The desktop sidecar is started by Tauri. In development, `run.py` starts the same service directly. A one-time pairing code becomes a hashed, revocable extension token. The extension never receives imported platform records or user interests.
