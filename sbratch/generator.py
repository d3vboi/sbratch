"""
workspace format:
    {"variables": ["x", ...],
     "stacks": [{"x": 0, "y": 0, "blocks": [node, ...]}, ...]}
node format:
    {"id": str, "type": str,
     "fields": {name: str},            # inline values, dropdowns, text fields
     "inputs": {name: node | null},    # blocks plugged into sockets
     "slots":  {name: [node, ...]},    # nested statement stacks
     "counts": {name: int}}            # item counts of variadic inputs
"""
from __future__ import annotations

import re

from .lang import IDENT, NUMBER, RESERVED, operand, sb_string, strip_outer
from .registry import BLOCKS

INDENT = "    "
MAX_DEPTH = 60
MAX_NODES = 4000

_PH = re.compile(r"\{(\$?\w+)(?:\|(\w+))?\}")
_SLOT_LINE = re.compile(r"\s*\{(\w+)\}\s*")


class BlockError(Exception):
    pass


class LimitError(Exception):
    pass


def _d(x):
    return x if isinstance(x, dict) else {}


def _l(x):
    return x if isinstance(x, list) else []


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


class Ctx:
    # what a blocks code template/callable sees while being generated

    def __init__(self, gen: Generator, node: dict, bdef, depth: int):
        self.gen = gen
        self.node = node
        self.bdef = bdef
        self.depth = depth
        self.parts = {p["name"]: p for p in bdef.parts if "name" in p}
        self._temps: dict = {}

    def problem(self, msg: str) -> str:
        # record an error against this block and return a placeholder
        self.gen.error(msg, self.node.get("id"))
        return "?"

    def _expr(self, name: str, key: str | None = None) -> str:
        part = self.parts[name]
        key = key or name
        child = _d(self.node.get("inputs")).get(key)
        if isinstance(child, dict):
            return self.gen.gen_value(child, self.depth + 1)
        inline = part.get("inline")
        raw = _d(self.node.get("fields")).get(key, part.get("default", ""))
        raw = "" if raw is None else str(raw)
        nice = name.replace("_", " ")
        if inline is None:
            return self.problem(f"the '{nice}' slot is empty - drop a block into it.")
        if inline == "number":
            raw = raw.strip()
            if not NUMBER.match(raw):
                return self.problem(f"'{nice}' needs a number (or a block that gives one), got {raw}")
            return raw
        if inline == "text":
            return sb_string(raw)
        # 'any' numbers stay numbers, everything else becomes text
        s = raw.strip()
        return s if NUMBER.match(s) else sb_string(raw)

    def input(self, name: str, key: str | None = None) -> str:
        return strip_outer(self._expr(name, key))

    def operand(self, name: str, key: str | None = None) -> str:
        return operand(self._expr(name, key))

    def count(self, name: str) -> int:
        part = self.parts[name]
        raw = _d(self.node.get("counts")).get(name, part["count"])
        try:
            n = int(raw)
        except (TypeError, ValueError):
            n = part["count"]
        return max(part["min"], min(part["max"], n))

    def items(self, name: str) -> list:
        return [self.input(name, "%s_%d" % (name, i)) for i in range(self.count(name))]

    def field(self, name: str, mod: str | None = None) -> str:
        part = self.parts[name]
        t = part["t"]
        val = _d(self.node.get("fields")).get(name, part.get("default", ""))
        val = "" if val is None else str(val)
        if t == "dropdown":
            if val not in {o["value"] for o in part["options"]}:
                return self.problem(f"'{name}' has an invalid choice {val}.")
            return val
        if t == "variable":
            return self.gen.use_var(val, bool(part.get("writes")), self)
        if t == "number":
            val = val.strip()
            if not NUMBER.match(val):
                return self.problem(f"{val} is not a valid number.")
            return val
        if t == "text":
            if mod == "comment":
                return " ".join(val.split())
            return sb_string(val)
        return self.problem(f"internal: cannot read part {name}")

    def slot(self, name: str) -> list:
        nodes = _l(_d(self.node.get("slots")).get(name))
        return self.gen.gen_list(nodes, self.depth + 1)

    def temp(self, prefix: str) -> str:
        if prefix not in self._temps:
            self._temps[prefix] = self.gen.new_temp(prefix)
        return self._temps[prefix]

    def expand(self, template: str) -> list:
        out = []
        for line in template.split("\n"):
            m = _SLOT_LINE.fullmatch(line)
            if m and self.parts.get(m.group(1), {}).get("t") == "slot":
                out.extend((INDENT + l) if l else l for l in self.slot(m.group(1)))
            else:
                out.append(_PH.sub(self._sub, line))
        return [l for l in out if l.strip()]

    def _sub(self, m) -> str:
        name, mod = m.group(1), m.group(2)
        if name.startswith("$"):
            return self.temp(name[1:])
        part = self.parts.get(name)
        if part is None:
            raise BlockError("internal: unknown placeholder {%s}" % name)
        t = part["t"]
        if t == "input":
            return self.operand(name) if mod == "op" else self.input(name)
        if t in ("slot", "label", "variadic"):
            raise BlockError("internal: {%s} cannot be used inline" % name)
        return self.field(name, mod)


class Generator:
    def __init__(self, workspace):
        self.ws = _d(workspace)
        self.diags: list = []
        self.vars: dict = {}      # lowercase -> name
        self.reads: dict = {}     # lowercase -> (name, block id)
        self.writes: set = set()
        self.used_temps: set = set()
        self.temp_n: dict = {}
        self.nodes = 0

    def _diag(self, level, msg, block=None):
        self.diags.append({"level": level, "message": msg, "block": block})

    def error(self, msg, block=None):
        self._diag("error", msg, block)

    def warn(self, msg, block=None):
        self._diag("warning", msg, block)

    def info(self, msg, block=None):
        self._diag("info", msg, block)

    def _load_variables(self):
        for raw in _l(self.ws.get("variables")):
            if not isinstance(raw, str):
                continue
            name = raw.strip()
            low = name.lower()
            if not IDENT.match(name):
                self.error(f"variable name {name} is not valid (letters, digits and _, starting with a letter)")
            elif low in RESERVED:
                self.error(f"variable name {name} is reserved by Small Basic")
            elif low in self.vars:
                self.error(f"variable {name} is declared twice (names are not case sensitive)")
            else:
                self.vars[low] = name

    def use_var(self, val: str, writes: bool, ctx: Ctx) -> str:
        if not val:
            return ctx.problem("choose a variable")
        low = val.lower()
        if low not in self.vars:
            return ctx.problem(f"variable {val} has not been created (or its name is invalid)")
        if writes:
            self.writes.add(low)
        else:
            self.reads.setdefault(low, (self.vars[low], ctx.node.get("id")))
        return self.vars[low]

    def new_temp(self, prefix: str) -> str:
        n = self.temp_n.get(prefix, 0)
        while True:
            n += 1
            cand = "%s%d" % (prefix, n)
            if cand.lower() not in self.vars and cand.lower() not in self.used_temps:
                break
        self.temp_n[prefix] = n
        self.used_temps.add(cand.lower())
        return cand

    def _tick(self, depth: int):
        self.nodes += 1
        if self.nodes > MAX_NODES or depth > MAX_DEPTH:
            raise LimitError()

    def _def(self, node: dict):
        d = BLOCKS.get(node.get("type"))
        if d is None:
            raise BlockError(f"unknown block type {(node.get("type"),)}" )
        return d

    def gen_value(self, node: dict, depth: int) -> str:
        self._tick(depth)
        try:
            d = self._def(node)
            if d.kind != "value":
                raise BlockError("this block can't be plugged into a socket")
            ctx = Ctx(self, node, d, depth)
            return d.code(ctx) if callable(d.code) else "".join(ctx.expand(d.code))
        except BlockError as e:
            self.error(str(e), node.get("id"))
            return "?"

    def gen_stmt(self, node: dict, depth: int, is_top: bool) -> list:
        d = self._def(node)
        if d.kind == "value":
            raise BlockError("a value block must be plugged into another block")
        if d.kind == "hat" and not is_top:
            raise BlockError("this block can only be at the top of a stack")
        ctx = Ctx(self, node, d, depth)
        res = d.code(ctx) if callable(d.code) else ctx.expand(d.code)
        if isinstance(res, str):
            res = res.split("\n")
        return [l for l in res if l.strip()]

    def gen_list(self, nodes, depth: int, is_top: bool = False) -> list:
        lines: list = []
        for i, node in enumerate(_l(nodes)):
            if not isinstance(node, dict):
                continue
            self._tick(depth)
            try:
                lines.extend(self.gen_stmt(node, depth, is_top and i == 0))
            except BlockError as e:
                self.error(str(e), node.get("id"))
                lines.append(f"' [incomplete block: {e}]")
        return lines

    def run(self) -> dict:
        self._load_variables()
        stacks = [s for s in _l(self.ws.get("stacks")) if isinstance(s, dict)]
        stacks.sort(key=lambda s: (_num(s.get("y")), _num(s.get("x"))))
        lines: list = []
        started = False
        try:
            for st in stacks:
                blocks = [b for b in _l(st.get("blocks")) if isinstance(b, dict)]
                if not blocks:
                    continue
                first = blocks[0]
                d = BLOCKS.get(first.get("type"))
                if d is not None and d.kind == "hat":
                    if started:
                        self.warn("only one 'when program starts' block can be used, extra one is left out", first.get("id"))
                        continue
                    started = True
                    lines.extend(self.gen_list(blocks, 0, is_top=True))
                else:
                    self.warn("these blocks aren't attached to 'when program starts', so they are not executed",
                              first.get("id"))
        except LimitError:
            self.error("the program is too large or too deeply nested to generate.")
        if not started:
            self.info("add a 'when program starts' block and attach your blocks to it.")
        for low, (name, bid) in self.reads.items():
            if low not in self.writes:
                self.warn("variable %r is used but never given a value" % name, bid)
        code = "\n".join(lines) + ("\n" if lines else "")
        ok = not any(d["level"] == "error" for d in self.diags)
        return {"ok": ok, "code": code, "diagnostics": self.diags}


def generate(workspace) -> dict:
    try:
        return Generator(workspace).run()
    except Exception:  # dont leak internals
        return {"ok": False, "code": "", "diagnostics": [
            {"level": "error", "message": "the workspace could not be read", "block": None}]}
