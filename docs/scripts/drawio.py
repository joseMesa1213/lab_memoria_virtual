import html
import math
import os
import subprocess

BLUE = ("#dae8fc", "#6c8ebf")
GREEN = ("#d5e8d4", "#82b366")
YELLOW = ("#fff2cc", "#d6b656")
ORANGE = ("#ffe6cc", "#d79b00")
RED = ("#f8cecc", "#b85450")
PURPLE = ("#e1d5e7", "#9673a6")
GRAY = ("#f5f5f5", "#666666")
WHITE = ("#ffffff", "#000000")
NONE = ("none", "none")

FONT = "Helvetica"
MONO = "Courier New"
EDGE = "#333333"


class Line:
    def __init__(self, text, bold=False, mono=False, italic=False, size=None, color=None, underline=False):
        self.text = text
        self.bold = bold
        self.mono = mono
        self.italic = italic
        self.size = size
        self.color = color
        self.underline = underline


def B(text, **kw):
    return Line(text, bold=True, **kw)


def M(text, **kw):
    return Line(text, mono=True, **kw)


def I(text, **kw):
    return Line(text, italic=True, **kw)


def lines_of(label):
    if label is None:
        return []
    if isinstance(label, (str, Line)):
        label = [label]
    result = []
    for item in label:
        if isinstance(item, Line):
            result.append(item)
        else:
            for part in str(item).split("\n"):
                result.append(Line(part))
    return result


class Node:
    def __init__(self, cid, kind, x, y, w, h, label, colors, **opts):
        self.id = cid
        self.kind = kind
        self.x, self.y, self.w, self.h = x, y, w, h
        self.lines = lines_of(label)
        self.fill, self.stroke = colors
        self.opts = opts

    def point(self, side):
        if isinstance(side, tuple):
            fx, fy = side
        else:
            fx, fy = {"t": (0.5, 0), "b": (0.5, 1), "l": (0, 0.5), "r": (1, 0.5)}[side]
        return self.x + fx * self.w, self.y + fy * self.h, fx, fy


class Edge:
    def __init__(self, cid, points, source=None, target=None, exit=None, entry=None, label=None, dashed=False,
                 end="classic", start="none", label_at=None, color=EDGE, width=1, font_size=11):
        self.id = cid
        self.points = points
        self.source, self.target = source, target
        self.exit, self.entry = exit, entry
        self.lines = lines_of(label)
        self.dashed = dashed
        self.end, self.start = end, start
        self.label_at = label_at
        self.color = color
        self.width = width
        self.font_size = font_size


class Diagram:
    def __init__(self, name, width, height, title=None, subtitle=None):
        self.name = name
        self.width, self.height = width, height
        self.items = []
        self.nodes = {}
        self.counter = 0
        if title:
            self.text(20, 16, width - 40, 28, B(title, size=18), align="left")
        if subtitle:
            self.text(20, 44, width - 40, 20, Line(subtitle, size=12, color="#555555"), align="left")

    def _id(self, prefix):
        self.counter += 1
        return f"{prefix}{self.counter}"

    def add(self, kind, x, y, w, h, label=None, colors=BLUE, cid=None, **opts):
        node = Node(cid or self._id("n"), kind, x, y, w, h, label, colors, **opts)
        self.items.append(node)
        self.nodes[node.id] = node
        return node

    def box(self, x, y, w, h, label=None, colors=BLUE, **opts):
        return self.add("rounded", x, y, w, h, label, colors, **opts)

    def rect(self, x, y, w, h, label=None, colors=BLUE, **opts):
        return self.add("rect", x, y, w, h, label, colors, **opts)

    def ellipse(self, x, y, w, h, label=None, colors=BLUE, **opts):
        return self.add("ellipse", x, y, w, h, label, colors, **opts)

    def rhombus(self, x, y, w, h, label=None, colors=YELLOW, **opts):
        return self.add("rhombus", x, y, w, h, label, colors, **opts)

    def cylinder(self, x, y, w, h, label=None, colors=GRAY, **opts):
        return self.add("cylinder", x, y, w, h, label, colors, **opts)

    def text(self, x, y, w, h, label, align="center", valign="middle", **opts):
        return self.add("text", x, y, w, h, label, NONE, align=align, valign=valign, **opts)

    def container(self, x, y, w, h, label, colors=GRAY, header=28, **opts):
        return self.add("swimlane", x, y, w, h, label, colors, header=header, **opts)

    def frame(self, x, y, w, h, label, colors=("none", "#666666"), **opts):
        return self.add("frame", x, y, w, h, label, colors, **opts)

    def uml_class(self, x, y, w, name, attrs, methods, colors=BLUE, stereotype=None):
        header = 40 if stereotype else 26
        attr_h = 8 + 15 * max(1, len(attrs))
        meth_h = 8 + 15 * max(1, len(methods))
        h = header + attr_h + meth_h
        title = [I(f"«{stereotype}»", size=11), B(name)] if stereotype else [B(name)]
        node = self.add("swimlane", x, y, w, h, title, colors, header=header)
        self.add("text", x, y + header, w, attr_h, [M(a, size=11) for a in attrs] or [Line("")], NONE,
                 align="left", valign="top")
        self.add("hline", x, y + header + attr_h, w, 1, None, ("none", colors[1]))
        self.add("text", x, y + header + attr_h, w, meth_h, [M(m, size=11) for m in methods] or [Line("")], NONE,
                 align="left", valign="top")
        return node

    def edge(self, src, dst, exit="r", entry="l", via=None, label=None, **kw):
        sx, sy, efx, efy = src.point(exit)
        tx, ty, nfx, nfy = dst.point(entry)
        points = [(sx, sy)]
        if via:
            points.extend(via)
        else:
            if abs(sx - tx) > 0.5 and abs(sy - ty) > 0.5:
                horizontal = efx in (0, 1) and efy not in (0, 1)
                if horizontal:
                    mx = (sx + tx) / 2
                    points.extend([(mx, sy), (mx, ty)])
                else:
                    my = (sy + ty) / 2
                    points.extend([(sx, my), (tx, my)])
        points.append((tx, ty))
        e = Edge(self._id("e"), points, src.id, dst.id, (efx, efy), (nfx, nfy), label, **kw)
        self.items.append(e)
        return e

    def line(self, points, label=None, **kw):
        e = Edge(self._id("e"), points, label=label, **kw)
        self.items.append(e)
        return e

    def save(self, directory):
        os.makedirs(directory, exist_ok=True)
        base = os.path.join(directory, self.name)
        with open(base + ".drawio", "w") as handle:
            handle.write(self.to_drawio())
        with open(base + ".svg", "w") as handle:
            handle.write(self.to_svg())
        subprocess.run(["rsvg-convert", "-z", "2", base + ".svg", "-o", base + ".png"], check=True)

    def html_label(self, lines):
        parts = []
        for line in lines:
            content = html.escape(line.text)
            if line.mono:
                content = f'<font face="{MONO}">{content}</font>'
            if line.size:
                content = f'<font style="font-size:{line.size}px">{content}</font>'
            if line.color:
                content = f'<font color="{line.color}">{content}</font>'
            if line.bold:
                content = f"<b>{content}</b>"
            if line.italic:
                content = f"<i>{content}</i>"
            if line.underline:
                content = f"<u>{content}</u>"
            parts.append(content)
        return "<br>".join(parts)

    def node_style(self, node):
        base = f"html=1;whiteSpace=wrap;fontFamily={FONT};fontSize=12;"
        colors = f"fillColor={node.fill};strokeColor={node.stroke};"
        align = node.opts.get("align", "center")
        valign = node.opts.get("valign", "middle")
        text_pos = f"align={align};verticalAlign={valign};spacingLeft=6;spacingRight=6;"
        dashed = "dashed=1;" if node.opts.get("dashed") else ""
        stroke_w = f"strokeWidth={node.opts['stroke_width']};" if node.opts.get("stroke_width") else ""
        kinds = {
            "rounded": "rounded=1;absoluteArcSize=1;arcSize=12;",
            "rect": "rounded=0;",
            "ellipse": "ellipse;",
            "rhombus": "rhombus;",
            "cylinder": "shape=cylinder3;boundedLbl=1;backgroundOutline=1;size=12;",
            "text": "text;fillColor=none;strokeColor=none;",
            "swimlane": f"swimlane;startSize={node.opts.get('header', 28)};rounded=0;fontStyle=0;horizontal=1;"
                        "collapsible=0;swimlaneFillColor=#ffffff;",
            "frame": "shape=umlFrame;width=120;height=26;boundedLbl=1;verticalAlign=top;align=left;spacingLeft=6;",
            "hline": "line;strokeWidth=1;fillColor=none;align=left;verticalAlign=middle;spacingTop=-1;"
                     "spacingLeft=3;spacingRight=3;rotatable=0;labelPosition=right;points=[];portConstraint=eastwest;",
        }
        if node.kind == "text":
            return base + kinds["text"] + text_pos
        if node.kind == "hline":
            return kinds["hline"] + f"strokeColor={node.stroke};"
        if node.kind == "frame":
            return base + kinds["frame"] + f"strokeColor={node.stroke};fillColor=none;" + dashed
        return base + kinds[node.kind] + colors + text_pos + dashed + stroke_w

    def edge_style(self, e):
        arrows = {"classic": "classic;{}Fill=1", "open": "block;{}Fill=0", "diamond": "diamondThin;{}Fill=1",
                  "odiamond": "diamondThin;{}Fill=0", "none": "none", "openthin": "open;{}Fill=0"}
        end = arrows[e.end].format("end")
        start = arrows[e.start].format("start")
        style = (f"edgeStyle=none;html=1;rounded=0;fontFamily={FONT};fontSize={e.font_size};endArrow={end};"
                 f"startArrow={start};strokeColor={e.color};strokeWidth={e.width};labelBackgroundColor=#ffffff;")
        if e.dashed:
            style += "dashed=1;"
        if e.exit:
            style += f"exitX={e.exit[0]:.4f};exitY={e.exit[1]:.4f};exitDx=0;exitDy=0;"
        if e.entry:
            style += f"entryX={e.entry[0]:.4f};entryY={e.entry[1]:.4f};entryDx=0;entryDy=0;"
        return style

    def to_drawio(self):
        cells = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']
        for item in self.items:
            if isinstance(item, Node):
                value = html.escape(self.html_label(item.lines), quote=True)
                cells.append(
                    f'<mxCell id="{item.id}" value="{value}" style="{self.node_style(item)}" vertex="1" parent="1">'
                    f'<mxGeometry x="{item.x:.1f}" y="{item.y:.1f}" width="{item.w:.1f}" height="{item.h:.1f}" '
                    f'as="geometry"/></mxCell>')
            else:
                attrs = ""
                if item.source:
                    attrs += f' source="{item.source}"'
                if item.target:
                    attrs += f' target="{item.target}"'
                inner = "".join(f'<mxPoint x="{x:.1f}" y="{y:.1f}"/>' for x, y in item.points[1:-1])
                value = html.escape(self.html_label(item.lines), quote=True) if not item.label_at else ""
                sx, sy = item.points[0]
                tx, ty = item.points[-1]
                cells.append(
                    f'<mxCell id="{item.id}" value="{value}" style="{self.edge_style(item)}" edge="1" parent="1"{attrs}>'
                    f'<mxGeometry relative="1" as="geometry">'
                    f'<mxPoint x="{sx:.1f}" y="{sy:.1f}" as="sourcePoint"/>'
                    f'<mxPoint x="{tx:.1f}" y="{ty:.1f}" as="targetPoint"/>'
                    f'{"<Array as=" + chr(34) + "points" + chr(34) + ">" + inner + "</Array>" if inner else ""}'
                    f'</mxGeometry></mxCell>')
                if item.label_at and item.lines:
                    lx, ly = item.label_at
                    value = html.escape(self.html_label(item.lines), quote=True)
                    w, h = self.measure(item.lines, item.font_size)
                    cells.append(
                        f'<mxCell id="{item.id}l" value="{value}" style="text;html=1;fontFamily={FONT};'
                        f'fontSize={item.font_size};align=center;verticalAlign=middle;labelBackgroundColor=#ffffff;'
                        f'fillColor=none;strokeColor=none;" vertex="1" parent="1">'
                        f'<mxGeometry x="{lx - w / 2 - 4:.1f}" y="{ly - h / 2:.1f}" width="{w + 8:.1f}" '
                        f'height="{h:.1f}" as="geometry"/></mxCell>')
        model = (f'<mxGraphModel dx="{self.width}" dy="{self.height}" grid="1" gridSize="10" guides="1" tooltips="1" '
                 f'connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{self.width}" '
                 f'pageHeight="{self.height}" math="0" shadow="0"><root>{"".join(cells)}</root></mxGraphModel>')
        return (f'<mxfile host="app.diagrams.net" type="device">'
                f'<diagram id="{self.name}" name="{self.name}">{model}</diagram></mxfile>\n')

    def measure(self, lines, default_size=12):
        width = 0
        for line in lines:
            size = line.size or default_size
            factor = 0.6 if line.mono else (0.58 if line.bold else 0.53)
            width = max(width, len(line.text) * size * factor)
        height = sum((line.size or default_size) * 1.25 for line in lines)
        return width, height

    def svg_text(self, lines, x, y, w, h, align="center", valign="middle", default_size=12, pad=6):
        if not lines:
            return ""
        heights = [(l.size or default_size) * 1.25 for l in lines]
        total = sum(heights)
        if valign == "top":
            cursor = y + 4
        elif valign == "bottom":
            cursor = y + h - total - 4
        else:
            cursor = y + (h - total) / 2
        out = []
        for line, lh in zip(lines, heights):
            size = line.size or default_size
            baseline = cursor + lh / 2 + size * 0.35
            cursor += lh
            if align == "left":
                tx, anchor = x + pad, "start"
            elif align == "right":
                tx, anchor = x + w - pad, "end"
            else:
                tx, anchor = x + w / 2, "middle"
            family = f"{MONO}, monospace" if line.mono else f"{FONT}, Arial, sans-serif"
            attrs = (f'x="{tx:.1f}" y="{baseline:.1f}" font-family="{family}" font-size="{size}" '
                     f'fill="{line.color or "#000000"}" text-anchor="{anchor}"')
            if line.bold:
                attrs += ' font-weight="bold"'
            if line.italic:
                attrs += ' font-style="italic"'
            if line.underline:
                attrs += ' text-decoration="underline"'
            out.append(f'<text {attrs} xml:space="preserve">{html.escape(line.text)}</text>')
        return "".join(out)

    def svg_node(self, n):
        fill = n.fill if n.fill != "none" else "none"
        stroke = n.stroke if n.stroke != "none" else "none"
        dash = ' stroke-dasharray="6 4"' if n.opts.get("dashed") else ""
        sw = n.opts.get("stroke_width", 1)
        common = f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash}'
        out = []
        x, y, w, h = n.x, n.y, n.w, n.h
        align = n.opts.get("align", "center")
        valign = n.opts.get("valign", "middle")
        if n.kind == "rounded":
            out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" ry="6" {common}/>')
        elif n.kind == "rect":
            out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" {common}/>')
        elif n.kind == "ellipse":
            out.append(f'<ellipse cx="{x + w / 2}" cy="{y + h / 2}" rx="{w / 2}" ry="{h / 2}" {common}/>')
        elif n.kind == "rhombus":
            out.append(f'<path d="M{x + w / 2},{y} L{x + w},{y + h / 2} L{x + w / 2},{y + h} L{x},{y + h / 2} Z" {common}/>')
        elif n.kind == "cylinder":
            s = 12
            out.append(f'<path d="M{x},{y + s} C{x},{y - s / 3} {x + w},{y - s / 3} {x + w},{y + s} L{x + w},{y + h - s} '
                       f'C{x + w},{y + h + s / 3} {x},{y + h + s / 3} {x},{y + h - s} Z" {common}/>')
            out.append(f'<path d="M{x},{y + s} C{x},{y + 2 * s + s / 3} {x + w},{y + 2 * s + s / 3} {x + w},{y + s}" '
                       f'fill="none" stroke="{stroke}"/>')
            return "".join(out) + self.svg_text(n.lines, x, y + 2 * s, w, h - 2 * s)
        elif n.kind == "swimlane":
            hh = n.opts.get("header", 28)
            out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#ffffff" stroke="{stroke}"{dash}/>')
            out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{hh}" {common}/>')
            return "".join(out) + self.svg_text(n.lines, x, y, w, hh)
        elif n.kind == "frame":
            tab_w = self.measure(n.lines)[0] + 24
            out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="{stroke}"{dash}/>')
            out.append(f'<path d="M{x},{y + 26} L{x + tab_w},{y + 26} L{x + tab_w + 10},{y + 16} L{x + tab_w + 10},{y}" '
                       f'fill="#ffffff" stroke="{stroke}"/>')
            return "".join(out) + self.svg_text(n.lines, x, y, tab_w, 26, align="left")
        elif n.kind == "hline":
            return f'<line x1="{x}" y1="{y}" x2="{x + w}" y2="{y}" stroke="{stroke}"/>'
        return "".join(out) + self.svg_text(n.lines, x, y, w, h, align, valign)

    def arrow_head(self, kind, tip, prev, color):
        if kind == "none":
            return ""
        dx, dy = tip[0] - prev[0], tip[1] - prev[1]
        length = math.hypot(dx, dy) or 1
        ux, uy = dx / length, dy / length
        px, py = -uy, ux
        if kind in ("diamond", "odiamond"):
            size, half = 16, 5
            a = (tip[0] - ux * size / 2 + px * half, tip[1] - uy * size / 2 + py * half)
            b = (tip[0] - ux * size, tip[1] - uy * size)
            c = (tip[0] - ux * size / 2 - px * half, tip[1] - uy * size / 2 - py * half)
            fill = color if kind == "diamond" else "#ffffff"
            return (f'<path d="M{tip[0]:.1f},{tip[1]:.1f} L{a[0]:.1f},{a[1]:.1f} L{b[0]:.1f},{b[1]:.1f} '
                    f'L{c[0]:.1f},{c[1]:.1f} Z" fill="{fill}" stroke="{color}"/>')
        if kind == "openthin":
            size, half = 10, 5
            a = (tip[0] - ux * size + px * half, tip[1] - uy * size + py * half)
            c = (tip[0] - ux * size - px * half, tip[1] - uy * size - py * half)
            return (f'<path d="M{a[0]:.1f},{a[1]:.1f} L{tip[0]:.1f},{tip[1]:.1f} L{c[0]:.1f},{c[1]:.1f}" '
                    f'fill="none" stroke="{color}"/>')
        size, half = (10, 5) if kind == "classic" else (13, 7)
        a = (tip[0] - ux * size + px * half, tip[1] - uy * size + py * half)
        c = (tip[0] - ux * size - px * half, tip[1] - uy * size - py * half)
        if kind == "classic":
            m = (tip[0] - ux * size * 0.7, tip[1] - uy * size * 0.7)
            return (f'<path d="M{tip[0]:.1f},{tip[1]:.1f} L{a[0]:.1f},{a[1]:.1f} L{m[0]:.1f},{m[1]:.1f} '
                    f'L{c[0]:.1f},{c[1]:.1f} Z" fill="{color}" stroke="{color}"/>')
        return (f'<path d="M{tip[0]:.1f},{tip[1]:.1f} L{a[0]:.1f},{a[1]:.1f} L{c[0]:.1f},{c[1]:.1f} Z" '
                f'fill="#ffffff" stroke="{color}"/>')

    def svg_edge(self, e):
        pts = list(e.points)
        trimmed = list(pts)
        if e.end in ("classic", "open"):
            trimmed[-1] = self.shorten(pts[-1], pts[-2], 7 if e.end == "classic" else 12)
        if e.start in ("diamond", "odiamond"):
            trimmed[0] = self.shorten(pts[0], pts[1], 16)
        dash = ' stroke-dasharray="6 4"' if e.dashed else ""
        path = " ".join(f"{x:.1f},{y:.1f}" for x, y in trimmed)
        out = [f'<polyline points="{path}" fill="none" stroke="{e.color}" stroke-width="{e.width}"{dash}/>']
        out.append(self.arrow_head(e.end, pts[-1], pts[-2], e.color))
        out.append(self.arrow_head(e.start, pts[0], pts[1], e.color))
        if e.lines:
            lx, ly = e.label_at if e.label_at else self.midpoint(pts)
            w, h = self.measure(e.lines, e.font_size)
            out.append(f'<rect x="{lx - w / 2 - 3:.1f}" y="{ly - h / 2:.1f}" width="{w + 6:.1f}" height="{h:.1f}" '
                       f'fill="#ffffff"/>')
            out.append(self.svg_text(e.lines, lx - w / 2 - 3, ly - h / 2, w + 6, h, default_size=e.font_size))
        return "".join(out)

    @staticmethod
    def shorten(tip, prev, amount):
        dx, dy = tip[0] - prev[0], tip[1] - prev[1]
        length = math.hypot(dx, dy) or 1
        return tip[0] - dx / length * amount, tip[1] - dy / length * amount

    @staticmethod
    def midpoint(points):
        segments = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(points, points[1:])]
        half = sum(segments) / 2
        for (a, b), length in zip(zip(points, points[1:]), segments):
            if half <= length and length > 0:
                t = half / length
                return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            half -= length
        return points[-1]

    def to_svg(self):
        body = []
        for item in self.items:
            if isinstance(item, Node) and item.kind in ("swimlane", "frame"):
                body.append(self.svg_node(item))
        for item in self.items:
            if isinstance(item, Node) and item.kind not in ("swimlane", "frame"):
                body.append(self.svg_node(item))
        for item in self.items:
            if isinstance(item, Edge):
                body.append(self.svg_edge(item))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" '
                f'viewBox="0 0 {self.width} {self.height}"><rect width="100%" height="100%" fill="#ffffff"/>'
                f'{"".join(body)}</svg>\n')
