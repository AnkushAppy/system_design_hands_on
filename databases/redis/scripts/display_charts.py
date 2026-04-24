#!/usr/bin/env python3
"""
Build SVG charts from metrics/exports/latest.json (from export_metrics.py).
No third-party dependencies — output goes to metrics/charts/ by default.
Open .svg files in a browser, or use ImageMagick/Preview on macOS.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DEFAULT_IN = BASE / "metrics" / "exports" / "latest.json"
CHARTS = BASE / "metrics" / "charts"

WIDTH, HEIGHT, PAD = 900, 320, 48


def _series_from_range(data: dict) -> list[tuple[list[float], list[float], str]]:
    out: list[tuple[list[float], list[float], str]] = []
    if data.get("status") != "success":
        return out
    for res in data.get("data", {}).get("result", []):
        m = res.get("metric", {}) or {}
        label_parts = [f"{k}={m[k]}" for k in sorted(m)]
        leg = ", ".join(label_parts) if label_parts else "value"
        values = res.get("values", [])
        xs: list[float] = []
        ys: list[float] = []
        for t, v in values:
            xs.append(float(t))
            try:
                ys.append(float(v))
            except (TypeError, ValueError):
                ys.append(float("nan"))
        if xs:
            out.append((xs, ys, leg))
    return out


def _escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _to_svg(
    name: str,
    series: list[tuple[list[float], list[float], str]],
) -> str:
    all_y = [y for _, ys, _ in series for y in ys if not math.isnan(y)]
    if not all_y:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}">'
            f'<text x="20" y="40" font-size="14">{_escape(name)}: no data</text></svg>'
        )

    t0 = min(xs[0] for xs, _, _ in series)
    t1 = max(xs[-1] for xs, _, _ in series)
    y_min = min(all_y)
    y_max = max(all_y)
    if y_max == y_min:
        y_min, y_max = y_min - 1.0, y_max + 1.0

    def x_scale(t: float) -> float:
        if t1 == t0:
            return PAD
        return PAD + (t - t0) / (t1 - t0) * (WIDTH - 2 * PAD)

    def y_scale(v: float) -> float:
        return HEIGHT - PAD - (v - y_min) / (y_max - y_min) * (HEIGHT - 2 * PAD)

    colors = ["#3b82f6", "#22c55e", "#f97316", "#a855f7", "#e11d48", "#14b8a6"]
    paths: list[str] = []
    for i, (xs, ys, _leg) in enumerate(series):
        pts = []
        for t, y in zip(xs, ys):
            if math.isnan(y):
                continue
            pts.append(f"{x_scale(t):.2f},{y_scale(y):.2f}")
        if len(pts) < 2:
            continue
        d = "M " + " L ".join(pts)
        c = colors[i % len(colors)]
        paths.append(
            f'<path d="{d}" fill="none" stroke="{c}" stroke-width="1.6" opacity="0.9"/>'
        )

    title = f'<text x="{PAD}" y="28" font-size="15" font-family="ui-sans-serif,system-ui,sans-serif" fill="#e5e5e5">{_escape(name)}</text>'
    axis = (
        f'<line x1="{PAD}" y1="{HEIGHT - PAD}" x2="{WIDTH - PAD}" y2="{HEIGHT - PAD}" stroke="#666"/>'
        f'<line x1="{PAD}" y1="{PAD}" x2="{PAD}" y2="{HEIGHT - PAD}" stroke="#666"/>'
    )
    ylbl = f'<text x="8" y="{HEIGHT // 2}" font-size="11" fill="#999" transform="rotate(-90 8 {HEIGHT // 2})">value</text>'
    tlbl = f'<text x="{WIDTH // 2}" y="{HEIGHT - 12}" text-anchor="middle" font-size="11" fill="#999">time (unix)</text>'

    legend_y = 44
    legend_items: list[str] = []
    for i, (_xs, _ys, leg) in enumerate(series):
        c = colors[i % len(colors)]
        legend_items.append(
            f'<text x="{WIDTH - 280}" y="{legend_y + i * 16}" font-size="11" fill="{c}" font-family="monospace">'
            f"{_escape(leg[:60])}{'…' if len(leg) > 60 else ''}</text>"
        )

    bg = f'<rect width="100%" height="100%" fill="#0b0f14"/>'
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">'
        f"{bg}{title}{axis}{ylbl}{tlbl}{''.join(paths)}{''.join(legend_items)}</svg>"
    )


def main() -> None:
    in_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_IN
    if not in_path.is_file():
        print(f"Missing {in_path} — run scripts/export_metrics.py first.", file=sys.stderr)
        raise SystemExit(1)

    doc = json.loads(in_path.read_text(encoding="utf-8"))
    rng = doc.get("range", {})

    written = 0
    for key, res in sorted(rng.items()):
        if isinstance(res, dict) and res.get("error"):
            print(f"skip {key}: {res['error']}")
            continue
        if not isinstance(res, dict) or "data" not in res:
            continue
        se = _series_from_range(res)
        if not se:
            print(f"skip {key}: no series")
            continue
        p = CHARTS / f"{key}.svg"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(_to_svg(key, se), encoding="utf-8")
        print(f"Wrote {p}")
        written += 1

    if written == 0:
        print("No time series to plot. Check Prometheus is up and re-run export.")
        raise SystemExit(2)


if __name__ == "__main__":
    main()
