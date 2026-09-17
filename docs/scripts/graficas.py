import csv
import os
import subprocess
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "graficas")

SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT2 = "#52514e"
MUTED = "#8a8985"
GRID = "#e6e5e1"
AXIS = "#bdbcb6"
FONT = "Helvetica, Arial, sans-serif"
SERIES = {"FIFO": "#2a78d6", "LRU": "#eb6834", "CLOCK": "#1baf7a"}
ORDER = ["FIFO", "LRU", "CLOCK"]


def esc(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, value, size=12, color=TEXT2, anchor="start", weight="normal"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" fill="{color}" '
            f'text-anchor="{anchor}" font-weight="{weight}">{esc(value)}</text>')


def marker(policy, x, y):
    color = SERIES[policy]
    ring = f'stroke="{SURFACE}" stroke-width="2"'
    if policy == "FIFO":
        return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{color}" {ring}/>'
    if policy == "LRU":
        return f'<rect x="{x - 4.5:.1f}" y="{y - 4.5:.1f}" width="9" height="9" rx="1" fill="{color}" {ring}/>'
    return (f'<path d="M{x:.1f},{y - 5.5:.1f} L{x + 5.5:.1f},{y + 4:.1f} L{x - 5.5:.1f},{y + 4:.1f} Z" '
            f'fill="{color}" {ring} stroke-linejoin="round"/>')


def legend(x, y):
    parts = []
    for policy in ORDER:
        parts.append(f'<line x1="{x}" y1="{y}" x2="{x + 22}" y2="{y}" stroke="{SERIES[policy]}" stroke-width="2"/>')
        parts.append(marker(policy, x + 11, y))
        parts.append(text(x + 28, y + 4, policy, 12, TEXT2))
        x += 90
    return "".join(parts)


def nice_ticks(low, high, count=5):
    span = high - low
    raw = span / count
    magnitude = 10 ** len(str(int(raw))) / 10 if raw >= 1 else 1
    for step in (1, 2, 2.5, 5, 10):
        if raw <= step * magnitude:
            size = step * magnitude
            break
    start = int(low // size) * size
    ticks = [start]
    while ticks[-1] < high - 1e-9:
        ticks.append(ticks[-1] + size)
    return ticks


def fmt(value):
    if abs(value - round(value)) < 1e-9:
        return f"{int(round(value)):,}".replace(",", ".")
    return f"{value:.1f}"


def line_panel(x0, y0, width, height, title, xs, series, y_label, y_range=None, x_label="Marcos físicos",
               categorical=False):
    parts = [text(x0, y0 + 14, title, 14, TEXT, weight="bold")]
    top = y0 + 48
    left = x0 + 50
    plot_w = width - 150
    plot_h = height - 84
    values = [v for policy in series for v in series[policy]]
    low, high = y_range if y_range else (min(values), max(values))
    ticks = nice_ticks(low, high)
    low, high = ticks[0], ticks[-1]
    if high == low:
        high = low + 1
    x_min, x_max = min(xs), max(xs)

    def px(v):
        if categorical:
            return left + xs.index(v) / (len(xs) - 1) * plot_w
        return left + (v - x_min) / (x_max - x_min) * plot_w

    def py(v):
        return top + plot_h - (v - low) / (high - low) * plot_h

    for tick in ticks:
        yy = py(tick)
        parts.append(f'<line x1="{left}" y1="{yy:.1f}" x2="{left + plot_w}" y2="{yy:.1f}" stroke="{GRID}" stroke-width="1"/>')
        parts.append(text(left - 8, yy + 4, fmt(tick), 11, MUTED, "end"))
    parts.append(f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="{AXIS}" stroke-width="1"/>')
    for v in xs:
        parts.append(text(px(v), top + plot_h + 16, fmt(v), 11, MUTED, "middle"))
    parts.append(text(left + plot_w / 2, top + plot_h + 34, x_label, 11, TEXT2, "middle"))
    parts.append(text(x0, top - 8, y_label, 11, TEXT2))
    ends = []
    for policy in ORDER:
        points = " ".join(f"{px(x):.1f},{py(y):.1f}" for x, y in zip(xs, series[policy]))
        parts.append(f'<polyline points="{points}" fill="none" stroke="{SERIES[policy]}" stroke-width="2" '
                     f'stroke-linejoin="round" stroke-linecap="round"/>')
        for x, y in zip(xs, series[policy]):
            parts.append(marker(policy, px(x), py(y)))
        ends.append([py(series[policy][-1]), policy, series[policy][-1]])
    ends.sort()
    merged = []
    for yy, policy, value in ends:
        if merged and abs(merged[-1][2] - value) < 0.05 * (1 if isinstance(value, float) else 20):
            merged[-1][1].append(policy)
        else:
            merged.append([yy, [policy], value])
    for i in range(1, len(merged)):
        if merged[i][0] - merged[i - 1][0] < 14:
            merged[i][0] = merged[i - 1][0] + 14
    for yy, policy, value in merged:
        shown = f"{value:.1f}" if isinstance(value, float) else fmt(value)
        names = "Las 3" if len(policy) == 3 else " = ".join(p for p in ORDER if p in policy)
        parts.append(text(left + plot_w + 10, yy + 4, f"{names}  {shown}", 11, TEXT2))
    return "".join(parts)


def column_panel(x0, y0, width, height, title, groups, data, y_label):
    parts = [text(x0, y0 + 14, title, 14, TEXT, weight="bold")]
    top = y0 + 48
    left = x0 + 52
    plot_w = width - 70
    plot_h = height - 84
    high = max(v for g in groups for v in data[g].values())
    ticks = nice_ticks(0, high * 1.08)
    high = ticks[-1]

    def py(v):
        return top + plot_h - v / high * plot_h

    for tick in ticks:
        yy = py(tick)
        parts.append(f'<line x1="{left}" y1="{yy:.1f}" x2="{left + plot_w}" y2="{yy:.1f}" stroke="{GRID}" stroke-width="1"/>')
        parts.append(text(left - 8, yy + 4, fmt(tick), 11, MUTED, "end"))
    band = plot_w / len(groups)
    bar = min(24, (band - 30) / 3 - 2)
    for gi, group in enumerate(groups):
        center = left + band * gi + band / 2
        start = center - (bar * 3 + 4) / 2
        for pi, policy in enumerate(ORDER):
            value = data[group][policy]
            x = start + pi * (bar + 2)
            y = py(value)
            h = top + plot_h - y
            r = min(4, h)
            path = (f"M{x:.1f},{top + plot_h:.1f} L{x:.1f},{y + r:.1f} Q{x:.1f},{y:.1f} {x + r:.1f},{y:.1f} "
                    f"L{x + bar - r:.1f},{y:.1f} Q{x + bar:.1f},{y:.1f} {x + bar:.1f},{y + r:.1f} "
                    f"L{x + bar:.1f},{top + plot_h:.1f} Z")
            parts.append(f'<path d="{path}" fill="{SERIES[policy]}"/>')
            label = f"{value / 1000:.1f}k".replace(".", ",") if value >= 1000 else fmt(value)
            parts.append(text(x + bar / 2, y - 5, label, 10, TEXT2, "middle"))
        parts.append(text(center, top + plot_h + 18, group, 12, TEXT2, "middle"))
    parts.append(f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="{AXIS}" stroke-width="1"/>')
    parts.append(text(x0, top - 8, y_label, 11, TEXT2))
    return "".join(parts)


def swatch_legend(x, y):
    parts = []
    for policy in ORDER:
        parts.append(f'<rect x="{x}" y="{y - 6}" width="12" height="12" rx="2" fill="{SERIES[policy]}"/>')
        parts.append(text(x + 18, y + 4, policy, 12, TEXT2))
        x += 80
    return "".join(parts)


def save(name, width, height, body, title, subtitle):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
           f'<rect width="100%" height="100%" fill="{SURFACE}"/>'
           f'{text(24, 34, title, 18, TEXT, weight="bold")}{text(24, 56, subtitle, 12, TEXT2)}{body}</svg>')
    svg_path = os.path.join(OUT, name + ".svg")
    with open(svg_path, "w") as handle:
        handle.write(svg)
    subprocess.run(["rsvg-convert", "-z", "2", svg_path, "-o", os.path.join(OUT, name + ".png")], check=True)


def load(path):
    with open(path) as handle:
        return list(csv.DictReader(handle))


def main():
    rows = load(os.path.join(OUT, "barrido.csv"))
    table = defaultdict(lambda: defaultdict(dict))
    for row in rows:
        table[row["trace"]][row["policy"]][int(row["frames"])] = row
    frames = sorted({int(r["frames"]) for r in rows})

    titles = {"secuencial": "Secuencial (512 páginas)", "aleatorio": "Aleatorio uniforme (512 páginas)",
              "localidad": "Localidad temporal (1024 páginas)", "matrices": "Multiplicación de matrices (768 páginas)"}
    body = [legend(24, 82)]
    panel_w, panel_h = 470, 310
    for i, trace in enumerate(["localidad", "matrices", "aleatorio", "secuencial"]):
        x0 = 24 + (i % 2) * (panel_w + 20)
        y0 = 100 + (i // 2) * (panel_h + 16)
        series = {p: [float(table[trace][p][f]["hit_rate"]) for f in frames] for p in ORDER}
        body.append(line_panel(x0, y0, panel_w, panel_h, titles[trace], frames, series, "Hit rate (%)",
                               y_range=(0, 100) if trace == "aleatorio" else (60, 100) if trace != "secuencial" else (90, 100)))
    save("hit_rate_vs_marcos", 984, 100 + 2 * (panel_h + 16) + 8, "".join(body),
         "Hit rate según memoria física disponible",
         "Páginas de 4 KB; memoria de 256 KB (64 marcos) a 2 MB (512 marcos). Mismo archivo de trazas para las tres políticas.")

    body = [legend(24, 82)]
    for i, trace in enumerate(["localidad", "matrices"]):
        x0 = 24 + i * (panel_w + 20)
        series = {p: [int(table[trace][p][f]["replacements"]) for f in frames] for p in ORDER}
        body.append(line_panel(x0, 100, panel_w, panel_h, titles[trace], frames, series, "Reemplazos"))
    save("reemplazos_vs_marcos", 984, 100 + panel_h + 8, "".join(body),
         "Número de reemplazos según memoria física",
         "Cada reemplazo expulsa una página; si está sucia además se escribe a swap.")

    body = [swatch_legend(24, 82)]
    groups = ["localidad", "matrices", "aleatorio", "secuencial"]
    data = {titles[g].split(" (")[0]: {p: int(table[g][p][128]["swap_outs"]) for p in ORDER} for g in groups}
    body.append(column_panel(24, 100, 936, 320, "Escrituras a swap con 128 marcos (512 KB)", list(data.keys()), data,
                             "Swap-out (páginas)"))
    save("swap_out_128", 984, 430, "".join(body), "Costo de E/S: páginas sucias escritas a disco",
         "Menos expulsiones de páginas activas implica menos escrituras a swap.")

    belady = {"3 marcos": {"FIFO": 9, "LRU": 10, "CLOCK": 9}, "4 marcos": {"FIFO": 10, "LRU": 8, "CLOCK": 10}}
    body = [swatch_legend(24, 82),
            column_panel(24, 100, 560, 300, "Fallos para 1 2 3 4 1 2 5 1 2 3 4 5", list(belady.keys()), belady,
                         "Fallos de página")]
    save("belady", 610, 410, "".join(body), "Anomalía de Belady",
         "FIFO y CLOCK empeoran con más memoria; LRU (algoritmo de pila) mejora.")

    rows = load(os.path.join(OUT, "pagina.csv"))
    sizes = sorted({int(r["page_size"]) for r in rows})
    by = defaultdict(dict)
    for r in rows:
        by[r["policy"]][int(r["page_size"])] = r
    kb = [s // 1024 for s in sizes]
    body = [legend(24, 82)]
    body.append(line_panel(24, 100, panel_w, panel_h, "Fallos de página", kb,
                           {p: [int(by[p][s]["faults"]) for s in sizes] for p in ORDER}, "Fallos",
                           x_label="Tamaño de página (KB), escala logarítmica", categorical=True))
    body.append(line_panel(24 + panel_w + 20, 100, panel_w, panel_h, "Escrituras a swap", kb,
                           {p: [int(by[p][s]["swap_outs"]) for s in sizes] for p in ORDER}, "Swap-out (páginas)",
                           x_label="Tamaño de página (KB), escala logarítmica", categorical=True))
    save("tamano_pagina", 984, 100 + panel_h + 8, "".join(body),
         "Efecto del tamaño de página (memoria fija de 1 MB, traza de localidad)",
         "Con 1 MB fijo: 4 KB = 256 marcos … 64 KB = 16 marcos. Cada fallo con páginas grandes mueve más bytes.")


if __name__ == "__main__":
    main()
