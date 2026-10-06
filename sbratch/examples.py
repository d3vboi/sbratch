# example programs for learners, built with a tiny node-builder DSL."""
import itertools

_ids = itertools.count(1)

def node(type, fields=None, inputs=None, slots=None, counts=None):
    return {"id": "ex%d" % next(_ids), "type": type, "fields": fields or {}, "inputs": inputs or {},
            "slots": slots or {}, "counts": counts or {}}

def num(v):
    return node("num_literal", {"value": str(v)})

def txt(s):
    return node("text_literal", {"value": s})

def var(n):
    return node("var_get", {"name": n})

def arith(a, sym, b):
    return node("math_arith", {"sym": sym}, {"a": a, "b": b})

def cmp(a, sym, b):
    return node("compare", {"sym": sym}, {"a": a, "b": b})

def join(a, b):
    return node("text_join", inputs={"a": a, "b": b})

def say(value):
    return node("tw_writeline", inputs={"value": value})

def workspace(variables, *blocks):
    return {"version": 1, "variables": list(variables),
            "stacks": [{"id": "s1", "x": 30, "y": 30, "blocks": [node("start"), *blocks]}]}

EXAMPLES = {
    "hello": {"title": "Hello, World!", "workspace": _hello()},
    "greeting": {"title": "Ask for a name", "workspace": _greeting()},
    "times_table": {"title": "Times table (for loop)", "workspace": _times_table()},
    "fruit_list": {"title": "Lists and for each", "workspace": _fruit_list()},
}
