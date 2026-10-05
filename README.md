# html-poster-to-png-mcp

Render a self-contained HTML layout into a crisp PNG that can be forwarded in
WeChat / WeCom / Slack — think-flow diagrams, proposal overviews,
architecture sketches, report pages.

## Why this exists — the traps it removes

| Trap | Symptom | Handled by |
|---|---|---|
| Host sandbox blocks Chrome's own sandbox | `sandbox initialization failed: Operation not permitted` + `GPU process isn't usable. Goodbye.` | `--no-sandbox` + `--disable-dev-shm-usage` baked in |
| 1x screenshot looks blurry on phones | fuzzy text when zoomed | `scale_factor=2` default (2x resolution) |
| CJK/space filenames break `file://` URLs | percent-encoding errors, empty screenshot | temp files are always ASCII-named |
| Estimated window height leaves a white band | ugly bottom whitespace | sampled whitespace auto-crop (keep `bottom_padding`) |
| Headless render "succeeds" with tofu boxes | silently wrong output, no error | server returns dimensions; agent should vision-check before forwarding |

## Install & run

```bash
pip install -e .        # mcp + pillow
python server.py        # stdio transport
```

```json
{
  "mcpServers": {
    "html-poster-to-png": {
      "command": "python",
      "args": ["/path/to/html-poster-to-png-mcp/server.py"]
    }
  }
}
```

Optional env: `CHROME_PATH` (any Chromium binary), `POSTER_TIMEOUT` (default 60s).

## Smoke test

```bash
python test_smoke.py    # live render of a tiny HTML -> asserts PNG signature
```

License: MIT.
