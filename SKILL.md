---
name: html-poster-to-png
description: "Render a self-contained HTML layout into a crisp forwardable PNG (think-flow diagram, proposal overview, architecture sketch, report page) via MCP. Use when the user says make a diagram/poster I can forward, 做成图片我要转发, 方案可视化, render this layout as an image. Not for interactive content (build a web page instead) or multi-page documents (use a PDF tool)."
display_name: HTML Poster to PNG
license: MIT
metadata:
  author: html-poster-to-png
  input_formats: ["html"]
  output_format: png
---

# HTML Poster to PNG (MCP)

One tool: `render_poster(html, width=1000, scale_factor=2, ...)` -> base64 PNG.

The HTML you pass MUST be self-contained and forwardable-designed:

- fixed pixel width on body (width:1000px), NOT responsive
- pure white #ffffff background (trailing-whitespace crop relies on it)
- all CSS inline in a single <style> block; zero external fonts/images
- CJK-safe font stack: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif
- light background + dark text (it will be read in IM, on phones, in dark mode off)

After receiving the PNG: actually LOOK at it before forwarding - headless
rendering fails silently (tofu CJK glyphs, overflow, misaligned columns never
raise an error). Deliver PNG first, HTML source second.

Preflight with `chrome_available()` if the first render fails.
