#!/usr/bin/env python3
"""Live smoke test: spawn over stdio, render a tiny HTML poster, assert PNG."""
import asyncio
import base64
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parent
HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
body{width:1000px;background:#fff;font-family:-apple-system,"PingFang SC",sans-serif;padding:48px 56px}
h1{font-size:30px;margin:0 0 12px}.box{background:#EEEDFE;border:1px solid #AFA9EC;
color:#26215C;border-radius:10px;padding:16px;font-size:13px}
</style></head><body><h1>Smoke Test 海报</h1><div class="box">如果看到中文方块，字体栈有问题。</div></body></html>"""


async def main() -> int:
    params = StdioServerParameters(command=sys.executable, args=[str(ROOT / "server.py")])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            avail = await session.call_tool("chrome_available", {})
            info = json.loads(avail.content[0].text)
            assert info.get("ok"), info
            print(f"[1] chrome ok: {info.get('version')}")

            r = await session.call_tool("render_poster", {"html": HTML})
            res = json.loads(r.content[0].text)
            assert res.get("ok") is True, res
            png = base64.b64decode(res["png_base64"])
            assert png[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
            assert res["width_px"] == 2000, f"width {res['width_px']} != 2000 (1000*2)"
            print(f"[2] render ok: {res['width_px']}x{res['height_px']} px, "
                  f"{len(png)} bytes")

    print("SMOKE OK")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
