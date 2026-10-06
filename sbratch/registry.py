from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Union

KINDS = ("hat", "statement", "value")
SHAPES = ("round", "bool")

@dataclass
class Category:
    id: str
    name: str
    color: str
    order: int = 100

@dataclass
class BlockDef:
    type: str
    category: str
    kind: str
    parts: List[dict]
    code: Union[str, Callable]
    shape: str = "round"
    tooltip: str = ""
    palette: Optional[str] = None

CATEGORIES: Dict[str, Category] = {}
BLOCKS: Dict[str, BlockDef] = {}

def category(id: str, name: str, color: str, order: int = 100) -> None:
    CATEGORIES[id] = Category(id, name, color, order)

# part specs (used in specs=)

def label(text: str) -> dict:
    return {"t": "label", "text": text}

def inp(inline: Optional[str] = "any", default: str = "") -> dict:
    # input socket. inline: None (must be filled by a block), 'any', 'number', 'text'.
    if inline not in (None, "any", "number", "text"):
        raise ValueError("bad inline kind %r" % (inline,))
    return {"t": "input", "inline": inline, "default": default}

def dropdown(options, default: Optional[str] = None) -> dict:
    # options: list of 'value' strings or (label, value) pairs.
    opts = []
    for o in options:
        lab, val = (o, o) if isinstance(o, str) else o
        opts.append({"label": lab, "value": val})
    return {"t": "dropdown", "options": opts, "default": default if default is not None else opts[0]["value"]}

def text(default: str = "") -> dict:
    return {"t": "text", "default": default}

def number(default: str = "0") -> dict:
    return {"t": "number", "default": default}

def variable(writes: bool = False) -> dict:
    # dropdown of the user's variables. writes=True marks it as assigned by the block.
    return {"t": "variable", "writes": writes}

def sub() -> dict:
    # dropdown of the subroutines defined in the workspace
    return {"t": "sub"}

def slot() -> dict:
    # a C-shaped mouth that holds a stack of statements.
    return {"t": "slot"}

def many(count: int = 2, min: int = 1, max: int = 20, inline: Optional[str] = "any", default: str = "") -> dict:
    # a variable number of input sockets with +/- buttons
    return {"t": "variadic", "count": count, "min": min, "max": max, "inline": inline, "default": default}

# registration

_TOKEN = re.compile(r"\{(\w+)\}")
_PLACEHOLDER = re.compile(r"\{(\$?\w+)(?:\|(\w+))?\}")

def _parse_pattern(pattern: str, specs: dict) -> List[dict]:
    parts: List[dict] = []
    pos = 0
    used = set()
    for m in _TOKEN.finditer(pattern):
        txt = pattern[pos:m.start()].strip()
        if txt:
            parts.append(label(txt))
        name = m.group(1)
        if name not in specs:
            raise ValueError("pattern %r uses {%s} but no spec was given" % (pattern, name))
        if name in used:
            raise ValueError("pattern %r uses {%s} twice" % (pattern, name))
        used.add(name)
        parts.append(dict(specs[name], name=name))
        pos = m.end()
    tail = pattern[pos:].strip()
    if tail:
        parts.append(label(tail))
    extra = set(specs) - used
    if extra:
        raise ValueError("specs not used in pattern %r: %s" % (pattern, sorted(extra)))
    return parts

def define(type: str, category: str, kind: str, pattern: str, code, specs: Optional[dict] = None,
           shape: str = "round", tooltip: str = "", palette: Optional[str] = None) -> BlockDef:
    if type in BLOCKS:
        raise ValueError("duplicate block type %r" % type)
    if category not in CATEGORIES:
        raise ValueError("unknown category %r for block %r" % (category, type))
    if kind not in KINDS:
        raise ValueError("bad kind %r for block %r" % (kind, type))
    if shape not in SHAPES:
        raise ValueError("bad shape %r for block %r" % (shape, type))
    parts = _parse_pattern(pattern, dict(specs or {}))
    names = {p["name"] for p in parts if "name" in p}
    if isinstance(code, str):
        for m in _PLACEHOLDER.finditer(code):
            if not m.group(1).startswith("$") and m.group(1) not in names:
                raise ValueError("code of %r uses unknown placeholder {%s}" % (type, m.group(1)))
    bdef = BlockDef(type, category, kind, parts, code, shape, tooltip, palette)
    BLOCKS[type] = bdef
    return bdef

def catalog() -> dict:
    # JSON-serialisable description of all categories and blocks for the frontend.
    cats = sorted(CATEGORIES.values(), key=lambda c: (c.order, c.name))
    return {
        "categories": [{"id": c.id, "name": c.name, "color": c.color} for c in cats],
        "blocks": [
            {"type": b.type, "category": b.category, "kind": b.kind, "shape": b.shape,
             "parts": b.parts, "tooltip": b.tooltip, "palette": b.palette}
            for b in BLOCKS.values()
        ],
    }
