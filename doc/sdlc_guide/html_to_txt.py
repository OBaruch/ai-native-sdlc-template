#!/usr/bin/env python3
"""Convierte las lecciones HTML del AI-Native SDLC Playbook a texto plano (.txt).

Sólo usa la librería estándar (html.parser), no requiere instalar nada.

Uso:
    python html_to_txt.py                    # convierte todo html/ -> txt/
    python html_to_txt.py --width 100        # además envuelve párrafos a 100 columnas
    python html_to_txt.py html/03-plan-mode.html   # sólo algunos archivos
"""

from __future__ import annotations

import argparse
import re
import sys
import textwrap
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

BASE_URL = "https://academy.claude.com/courses/ai-native-sdlc-playbook"

# Configuración por lección: archivo -> (número de lección, etapa, slug en la web).
LESSONS: dict[str, tuple[int, str, str]] = {
    "00-introduction": (1, "Introduction", "introduction"),
    "01-capture-intent": (2, "Stage 1: Plan", "capture-intent"),
    "02-requirements-and-design": (3, "Stage 2: Design", "requirements-and-design"),
    "03-plan-mode": (4, "Stage 3: Build", "plan-mode"),
    "04-claude-md": (5, "Stage 3: Build", "claude-md"),
    "05-skills-as-institutional-knowledge": (6, "Stage 3: Build", "skills-as-institutional-knowledge"),
    "06-parallel-sessions-and-subagents": (7, "Stage 3: Build", "parallel-sessions-and-subagents"),
    "07-give-claude-a-feedback-loop": (8, "Stage 4: Test", "give-claude-a-feedback-loop"),
    "08-continuous-evals-in-ci": (9, "Stage 4: Test", "continuous-evals-in-ci"),
    "09-ai-in-the-pr-review-loop": (10, "Stage 5: Deploy", "ai-in-the-pr-review-loop"),
    "10-hooks-as-approval-gates": (11, "Stage 5: Deploy", "hooks-as-approval-gates"),
    "11-ci-cd-integration-and-deployment": (12, "Stage 5: Deploy", "ci-cd-integration-and-deployment"),
    "12-closing-the-loop-on-metrics": (13, "Stage 6: Maintain", "closing-the-loop-on-metrics"),
    "13-closing-thoughts-and-resources": (14, "Closing", "closing-thoughts-and-resources"),
}

VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
             "meta", "source", "track", "wbr"}
# Nunca aportan contenido legible (botones de copiar/zoom, iconos, scripts).
SKIP_TAGS = {"script", "style", "noscript", "template", "svg", "button", "iframe",
             "form", "input", "select", "textarea"}
BLOCK_TAGS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "table",
              "pre", "figure", "figcaption", "blockquote", "div", "section", "article",
              "header", "footer", "nav", "aside", "main", "hr", "dl", "dt", "dd",
              "details", "summary"}
HEADING_UNDERLINE = {1: "=", 2: "-", 3: "~"}
LONG_CELL = 40  # si alguna celda supera esto, la tabla se renderiza como registros


# ---------------------------------------------------------------- árbol DOM ---

@dataclass
class Node:
    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    children: list["Node | str"] = field(default_factory=list)
    parent: "Node | None" = None

    @property
    def classes(self) -> set[str]:
        return set((self.attrs.get("class") or "").split())

    def iter(self):
        yield self
        for c in self.children:
            if isinstance(c, Node):
                yield from c.iter()

    def find(self, tag: str) -> "Node | None":
        return next((n for n in self.iter() if n.tag == tag), None)

    def find_all(self, tag: str) -> list["Node"]:
        return [n for n in self.iter() if n.tag == tag]


class TreeBuilder(HTMLParser):
    """Construye un árbol tolerante a HTML mal cerrado."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("#root")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, {k: (v or "") for k, v in attrs}, parent=self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(Node(tag, {k: (v or "") for k, v in attrs},
                                            parent=self.stack[-1]))

    def handle_endtag(self, tag):
        # Cierra hasta la etiqueta correspondiente; ignora cierres huérfanos.
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        if data:
            self.stack[-1].children.append(data)


def parse(html: str) -> Node:
    tb = TreeBuilder()
    tb.feed(html)
    tb.close()
    return tb.root


# ------------------------------------------------------------ renderizado ---

def is_heading_anchor(n: Node) -> bool:
    """El <a> de icono "#" que la web pega a cada h2."""
    return n.tag == "a" and "pointer-events-none" in n.classes


def inline_text(node: Node | str, keep_ws: bool = False) -> str:
    if isinstance(node, str):
        return node
    if node.tag in SKIP_TAGS or is_heading_anchor(node):
        return ""
    if node.tag == "br":
        return "\n"
    if node.tag == "img":
        alt = node.attrs.get("alt", "").strip()
        return f"[Imagen: {alt}]" if alt else ""
    return "".join(inline_text(c, keep_ws) for c in node.children)


def clean(text: str) -> str:
    lines = [re.sub(r"[ \t\r\f\v ]+", " ", ln).strip() for ln in text.split("\n")]
    return "\n".join(ln for ln in lines if ln)


def is_block(n: Node | str) -> bool:
    return isinstance(n, Node) and n.tag in BLOCK_TAGS


class Renderer:
    def __init__(self, width: int = 0) -> None:
        self.width = width

    def wrap(self, text: str, indent: str = "", first: str | None = None) -> str:
        first = indent if first is None else first
        if not self.width:
            lines = text.split("\n")
            return "\n".join([first + lines[0]] + [indent + ln for ln in lines[1:]])
        out = []
        for i, para in enumerate(text.split("\n")):
            out.append(textwrap.fill(para, self.width, initial_indent=first if i == 0 else indent,
                                     subsequent_indent=indent, break_long_words=False,
                                     break_on_hyphens=False))
        return "\n".join(out)

    # Devuelve una lista de bloques de texto; se unen con líneas en blanco.
    def blocks(self, node: Node, indent: str = "") -> list[str]:
        tag = node.tag
        if tag in SKIP_TAGS:
            return []
        if re.fullmatch(r"h[1-6]", tag):
            text = clean(inline_text(node)).replace("\n", " ")
            if not text:
                return []
            level = int(tag[1])
            mark = HEADING_UNDERLINE.get(level)
            return [f"{text}\n{mark * len(text)}" if mark else f"{'#' * level} {text}"]
        if tag == "p":
            text = clean(inline_text(node))
            return [self.wrap(text, indent)] if text else []
        if tag in ("ul", "ol"):
            return [self.render_list(node, indent)]
        if tag == "table":
            t = self.render_table(node, indent)
            return [t] if t else []
        if tag == "pre":
            return [self.render_pre(node, indent)]
        if tag == "figure":
            return self.render_figure(node, indent)
        if tag == "blockquote":
            inner = self.children_blocks(node, "")
            return ["\n".join(indent + "> " + ln if ln else indent + ">"
                              for ln in "\n\n".join(inner).split("\n"))]
        if tag == "hr":
            return [indent + "-" * 40]
        if tag == "div" and node.find("pre") and not any(
                c.tag == "pre" for c in node.children if isinstance(c, Node)):
            # Contenedor de bloque de código: cabecera con nombre de archivo + <pre>.
            return self.render_code_card(node, indent)
        return self.children_blocks(node, indent)

    def children_blocks(self, node: Node, indent: str) -> list[str]:
        out: list[str] = []
        buf: list[Node | str] = []

        def flush():
            text = clean("".join(inline_text(x) for x in buf))
            if text:
                out.append(self.wrap(text, indent))
            buf.clear()

        for c in node.children:
            if is_block(c):
                flush()
                out.extend(self.blocks(c, indent))  # type: ignore[arg-type]
            else:
                buf.append(c)
        flush()
        return out

    def render_list(self, node: Node, indent: str) -> str:
        ordered = node.tag == "ol"
        start = int(node.attrs.get("start", "1") or 1) if ordered else 1
        items = [c for c in node.children if isinstance(c, Node) and c.tag == "li"]
        lines = []
        for i, li in enumerate(items):
            marker = f"{start + i}. " if ordered else "- "
            sub_indent = indent + " " * len(marker)
            parts = self.children_blocks(li, sub_indent)
            if not parts:
                continue
            first = parts[0]
            # Sustituye la sangría de la primera línea por el marcador.
            first = indent + marker + first[len(sub_indent):] if first.startswith(sub_indent) \
                else indent + marker + first.lstrip()
            lines.append("\n".join([first] + parts[1:]))
        return "\n".join(lines)

    def render_table(self, node: Node, indent: str) -> str:
        rows: list[list[str]] = []
        header_rows = 0
        for tr in node.find_all("tr"):
            cells = [c for c in tr.children if isinstance(c, Node) and c.tag in ("th", "td")]
            if not cells:
                continue
            row = [clean(inline_text(c)).replace("\n", " ") for c in cells]
            if all(c.tag == "th" for c in cells) and len(rows) == header_rows:
                header_rows += 1
            rows.append(row)
        if not rows:
            return ""
        ncol = max(len(r) for r in rows)
        rows = [r + [""] * (ncol - len(r)) for r in rows]
        header = rows[0] if header_rows else [f"Col {i + 1}" for i in range(ncol)]
        body = rows[header_rows:] if header_rows else rows

        if any(len(c) > LONG_CELL for r in body for c in r):
            # Formato registro: legible aunque las celdas sean largas.
            recs = []
            for r in body:
                rec = [self.wrap(f"{header[0]}: {r[0]}", indent)]
                rec += [self.wrap(f"{h}: {v}", indent + "    ", indent + "  ")
                        for h, v in zip(header[1:], r[1:])]
                recs.append("\n".join(rec))
            return "\n\n".join(recs)

        widths = [max(len(r[i]) for r in [header] + body) for i in range(ncol)]
        fmt = lambda r: indent + " | ".join(c.ljust(w) for c, w in zip(r, widths)).rstrip()
        sep = indent + "-+-".join("-" * w for w in widths)
        return "\n".join([fmt(header), sep] + [fmt(r) for r in body])

    def render_pre(self, node: Node, indent: str, label: str = "") -> str:
        code = inline_text(node, keep_ws=True).strip("\n")
        code = textwrap.dedent(code.replace("\r\n", "\n").replace("\t", "    "))
        body = "\n".join(indent + "    " + ln if ln.strip() else "" for ln in code.split("\n"))
        head = f"{indent}[Código: {label}]" if label else f"{indent}[Código]"
        return f"{head}\n{body}"

    def render_code_card(self, node: Node, indent: str) -> list[str]:
        pre = node.find("pre")
        assert pre is not None
        label_parts = []
        for c in node.children:
            if isinstance(c, Node) and c is not pre and not c.find("pre") and c.tag != "pre":
                label_parts.append(clean(inline_text(c)))
        label = " ".join(p for p in label_parts if p)[:120]
        return [self.render_pre(pre, indent, label)]

    def render_figure(self, node: Node, indent: str) -> list[str]:
        out = []
        for img in node.find_all("img"):
            alt = clean(img.attrs.get("alt", ""))
            if alt:
                out.append(self.wrap(f"[Imagen: {alt}]", indent))
        cap = node.find("figcaption")
        if cap is not None:
            text = clean(inline_text(cap))
            if text:
                out.append(self.wrap(f"Figura: {text}", indent))
        for c in node.children:  # contenido extra (p. ej. un <pre> dentro de figure)
            if isinstance(c, Node) and c.tag not in ("figcaption", "img", "button"):
                out.extend(self.blocks(c, indent))
        return out


# ------------------------------------------------------------- por lección ---

def page_meta(root: Node) -> dict[str, str]:
    meta: dict[str, str] = {}
    for n in root.iter():
        if n.tag == "link" and n.attrs.get("rel") == "canonical":
            meta.setdefault("url", n.attrs.get("href", ""))
        elif n.tag == "meta" and n.attrs.get("property") == "og:url":
            meta.setdefault("url", n.attrs.get("content", ""))
    h1 = root.find("h1")
    if h1 is not None:
        meta["title"] = clean(inline_text(h1)).replace("\n", " ")
    # "Lesson N" y "X min" aparecen en la cabecera de la lección (fuera del <article>).
    main = root.find("main") or root
    article = main.find("article")
    head_text = ""
    for n in main.iter():
        if n is article:
            break
        if n.tag in ("p", "span", "div", "h1") and not n.find("article"):
            head_text += " " + clean(inline_text(n))
    if m := re.search(r"\bLesson\s+\d+(?:\s+of\s+\d+)?", head_text):
        meta["lesson"] = m.group(0)
    if m := re.search(r"\b\d+\s*min\b", head_text):
        meta["duration"] = m.group(0)
    return meta


def convert(src: Path, width: int) -> tuple[str, list[str]]:
    warnings: list[str] = []
    raw = src.read_bytes()
    m = re.search(rb'<meta[^>]+charset=["\']?([\w-]+)', raw[:4096], re.I)
    html = raw.decode(m.group(1).decode() if m else "utf-8", errors="replace")
    root = parse(html)

    stem = src.stem
    num, stage, slug = LESSONS.get(stem, (0, "", stem.split("-", 1)[-1]))
    if stem not in LESSONS:
        warnings.append("archivo no está en LESSONS; se usa configuración genérica")

    meta = page_meta(root)
    article = next((n for n in root.iter() if n.tag == "article" and "mdx-article" in n.classes), None)
    if article is None:
        article = root.find("article") or root.find("main") or root.find("body") or root
        warnings.append(f"no se encontró article.mdx-article; se usó <{article.tag}>")

    title = meta.get("title") or slug.replace("-", " ").title()
    info = [p for p in (meta.get("lesson") or (f"Lesson {num}" if num else ""), stage,
                        meta.get("duration")) if p]
    header = [title, "=" * len(title)]
    if info:
        header.append(" · ".join(info))
    header.append(f"Source: {meta.get('url') or f'{BASE_URL}/{slug}'}")

    body = Renderer(width).blocks(article)
    text = "\n".join(header) + "\n\n" + "\n\n".join(b for b in body if b.strip()) + "\n"
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Validaciones
    words = len(text.split())
    if words < 150:
        warnings.append(f"contenido sospechosamente corto ({words} palabras)")
    # Sólo etiquetas HTML reales y fuera de bloques de código (textos como "<name>" son válidos).
    prose = "\n".join(ln for ln in text.split("\n") if not ln.startswith("    "))
    html_tag = r"</?(?:%s)\b[^>]*>" % "|".join(sorted(BLOCK_TAGS | SKIP_TAGS | {"a", "span", "img", "code", "strong", "em"}))
    if leftover := re.findall(html_tag, prose):
        warnings.append(f"quedaron etiquetas HTML en el texto: {sorted(set(leftover))[:5]}")
    if "�" in text:
        warnings.append("hay caracteres no decodificables (�)")
    n_h2 = len(article.find_all("h2"))
    n_h2_out = sum(1 for b in body if re.search(r"\n-+$", b))
    if n_h2 != n_h2_out:
        warnings.append(f"h2 en HTML={n_h2} vs en txt={n_h2_out}")
    return text, warnings


def main() -> int:
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*", type=Path, help="HTML a convertir (por defecto: todos en --src)")
    ap.add_argument("--src", type=Path, default=here / "html", help="carpeta de HTML (default: html/)")
    ap.add_argument("--out", type=Path, default=here, help="carpeta de salida (default: junto a este script)")
    ap.add_argument("--width", type=int, default=0, help="envolver párrafos a N columnas (0 = no envolver)")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # consola de Windows
    except AttributeError:
        pass

    files = args.files or sorted(args.src.glob("*.html"))
    if not files:
        print(f"No hay archivos .html en {args.src}", file=sys.stderr)
        return 1
    args.out.mkdir(parents=True, exist_ok=True)

    failed = 0
    for f in files:
        try:
            text, warns = convert(f, args.width)
        except Exception as e:  # noqa: BLE001 — seguir con los demás archivos
            failed += 1
            print(f"ERROR  {f.name}: {type(e).__name__}: {e}")
            continue
        dst = args.out / f"{f.stem}.txt"
        dst.write_text(text, encoding="utf-8", newline="\n")
        status = "WARN " if warns else "OK   "
        print(f"{status} {f.name} -> {dst.name}  ({len(text.split())} palabras, {text.count(chr(10))} líneas)")
        for w in warns:
            print(f"       - {w}")

    print(f"\n{len(files) - failed}/{len(files)} convertidos en {args.out}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
