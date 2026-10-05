#!/usr/bin/env python3
"""html-poster-to-png MCP server.

Render a self-contained HTML layout (think-flow diagram, proposal overview,
architecture sketch, report page) into a crisp PNG that can be forwarded in
IM (WeChat / WeCom / Slack / ...).

Pipeline: HTML text -> headless Chrome screenshot -> PIL whitespace crop ->
base64 PNG returned inline. The three classic headless-Chrome traps
(--no-sandbox, device scale factor 2, ASCII-only temp filenames) are handled
inside the server so callers never hit them.
"""
import base64
import functools
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

try:  # MCP SDK 1.x
    from mcp.server.fastmcp import FastMCP as _Server
except ModuleNotFoundError:  # 2.x renamed FastMCP to MCPServer
    from mcp.server.mcpserver import MCPServer as _Server

mcp = _Server("html-poster-to-png")

_TIMEOUT = int(os.environ.get("POSTER_TIMEOUT", "60"))

_CHROME_CANDIDATES = [
    os.environ.get("CHROME_PATH", ""),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]


class KnownError(Exception):
    def __init__(self, code: str, msg: str, hint: str = ""):
        super().__init__(msg)
        self.code, self.msg, self.hint = code, msg, hint


def guard(fn):
    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        try:
            return await fn(*args, **kwargs)
        except KnownError as exc:
            return {"ok": False, "errcode": exc.code, "message": exc.msg, "hint": exc.hint}
        except Exception as exc:
            return {"ok": False, "error": type(exc).__name__, "message": str(exc)[:300]}
    return wrapper


def _find_chrome() -> str:
    for cand in _CHROME_CANDIDATES:
        if cand and Path(cand).exists():
            return cand
    raise KnownError(
        "CHROME_NOT_FOUND", "no Chrome/Chromium binary found",
        "set CHROME_PATH env var to your browser binary; any Chromium works")


def _crop_whitespace(src: str, dst: str, bottom_padding: int = 80) -> tuple[int, int]:
    """Find the last non-white row (sampled) and crop; return (w, h)."""
    from PIL import Image
    im = Image.open(src).convert("RGB")
    w, h = im.size
    px = im.load()
    last = h - 1
    for y in range(h - 1, -1, -1):
        if any(px[x, y] != (255, 255, 255) for x in range(0, w, 6)):
            last = y
            break
    im.crop((0, 0, w, min(h, last + bottom_padding))).save(dst, optimize=True)
    return w, min(h, last + bottom_padding)


@mcp.tool()
@guard
async def chrome_available() -> dict:
    """Preflight: report the Chrome binary path this server will use."""
    path = _find_chrome()
    version = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=15)
    return {"ok": True, "chrome": path, "version": version.stdout.strip()}


@mcp.tool()
@guard
async def render_poster(html: str, width: int = 1000, scale_factor: int = 2,
                        window_height: int = 6000, bottom_padding: int = 80,
                        full_page: bool = True) -> dict:
    """Render self-contained HTML into a crisp PNG, returned as base64.

    Design rules for the HTML you pass (the server cannot fix these):
    - fixed pixel width on body (e.g. width:1000px), NOT responsive
    - pure white #ffffff background (whitespace cropping relies on it)
    - all CSS inline in one <style> block; no external fonts/images
    - CJK text: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif

    Args:
        html: complete self-contained HTML document
        width: CSS layout width in px; screenshot is width * scale_factor
        scale_factor: 2 gives 2x resolution (2000px wide) - readable on phones
        window_height: viewport height; overestimate, excess is cropped away
        bottom_padding: px of breathing room kept below the last content row
        full_page: crop trailing whitespace (set False to keep window_height)
    """
    if not html or "<" not in html:
        raise KnownError("BAD_HTML", "html looks empty or is not markup")
    chrome = _find_chrome()
    workdir = Path(tempfile.mkdtemp(prefix="poster_"))
    html_path = workdir / "poster.html"          # ASCII-only: file:// URLs break on CJK names
    shot_path = workdir / "shot.png"
    final_path = workdir / "final.png"
    html_path.write_text(html, encoding="utf-8")

    proc = subprocess.run(
        [chrome, "--headless=new", "--no-sandbox", "--disable-gpu",
         "--disable-dev-shm-usage", "--disable-software-rasterizer",
         "--hide-scrollbars", f"--force-device-scale-factor={scale_factor}",
         f"--screenshot={shot_path}", f"--window-size={width},{window_height}",
         html_path.as_uri()],
        capture_output=True, text=True, timeout=_TIMEOUT)
    if not shot_path.exists() or shot_path.stat().st_size == 0:
        raise KnownError("SHOT_FAILED", f"chrome exited rc={proc.returncode} with no screenshot",
                         (proc.stderr or proc.stdout).strip()[-400:] or
                         "try chrome_available(); on locked-down hosts --no-sandbox is required")

    out_w, out_h = (width * scale_factor, window_height * scale_factor)
    if full_page:
        out_w, out_h = _crop_whitespace(str(shot_path), str(final_path), bottom_padding)
    else:
        shutil.copyfile(shot_path, final_path)

    png_b64 = base64.b64encode(final_path.read_bytes()).decode()
    return {"ok": True, "png_base64": png_b64,
            "width_px": out_w, "height_px": out_h,
            "layout_width": width, "scale_factor": scale_factor}


def main():
    mcp.run()


if __name__ == "__main__":
    main()
