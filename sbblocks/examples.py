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


def _hello():
    return workspace([], node("tw_writeline", {"value": "Hello, World!"}))


def _greeting():
    return workspace(
        ["name"],
        node("tw_write", {"value": "What is your name? "}),
        node("var_set", {"name": "name"}, {"value": node("tw_read")}),
        say(join(txt("Nice to meet you, "), var("name"))),
    )


def _times_table():
    return workspace(
        ["i"],
        node("for", {"var": "i", "start": "1", "end": "10"}, slots={"body": [
            say(join(join(var("i"), txt(" x 7 = ")), arith(var("i"), "*", num(7)))),
        ]}),
    )


def _fizzbuzz():
    inner = node("if_elseif", inputs={
        "c1": cmp(node("math_remainder", inputs={"dividend": var("n"), "divisor": num(3)}), "=", num(0)),
        "c2": cmp(node("math_remainder", inputs={"dividend": var("n"), "divisor": num(5)}), "=", num(0)),
    }, slots={"b1": [node("tw_writeline", {"value": "Fizz"})],
              "b2": [node("tw_writeline", {"value": "Buzz"})],
              "b3": [say(var("n"))]})
    outer = node("if_else",
                 inputs={"cond": cmp(node("math_remainder", inputs={"dividend": var("n"), "divisor": num(15)}), "=", num(0))},
                 slots={"then": [node("tw_writeline", {"value": "FizzBuzz"})], "otherwise": [inner]})
    return workspace(["n"], node("for", {"var": "n", "start": "1", "end": "30"}, slots={"body": [outer]}))


def _fruit_list():
    return workspace(
        ["fruits", "fruit"],
        node("list_make",
             {"list": "fruits", "items_0": "apple", "items_1": "banana", "items_2": "cherry"},
             counts={"items": 3}),
        node("list_add", {"list": "fruits", "value": "date"}),
        say(join(txt("I have this many fruits: "), node("list_count", {"list": "fruits"}))),
        node("foreach", {"item": "fruit", "list": "fruits"}, slots={"body": [say(var("fruit"))]}),
    )


EXAMPLES = {
    "hello": {"title": "Hello, World!", "workspace": _hello()},
    "greeting": {"title": "Ask for a name", "workspace": _greeting()},
    "times_table": {"title": "Times table (for loop)", "workspace": _times_table()},
    "fizzbuzz": {"title": "FizzBuzz (if / else)", "workspace": _fizzbuzz()},
    "fruit_list": {"title": "Lists and for each", "workspace": _fruit_list()},
}
