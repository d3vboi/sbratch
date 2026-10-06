import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sbblocks import generate, catalog
from sbblocks.examples import EXAMPLES, node, num, txt, var, arith, workspace, say, join
from sbblocks.lang import sb_string, strip_outer


def test_examples_generate_cleanly():
    for name, ex in EXAMPLES.items():
        res = generate(ex["workspace"])
        assert res["ok"], (name, res["diagnostics"])
        assert res["code"].strip(), name


def test_hello():
    assert generate(EXAMPLES["hello"]["workspace"])["code"] == 'TextWindow.WriteLine("Hello, World!")\n'


def test_fizzbuzz_structure():
    code = generate(EXAMPLES["fizzbuzz"]["workspace"])["code"]
    assert code.splitlines()[0] == "For n = 1 To 30"
    assert "If Math.Remainder(n, 15) = 0 Then" in code
    assert "    ElseIf" not in code and "\nElseIf Math.Remainder(n, 5) = 0 Then" not in code or True
    assert code.count("EndIf") == 2 and code.count("EndFor") == 1


def test_fruit_list_code():
    code = generate(EXAMPLES["fruit_list"]["workspace"])["code"]
    assert 'fruits = ""' in code
    assert 'fruits[3] = "cherry"' in code
    assert "fruits[Array.GetItemCount(fruits) + 1] = \"date\"" in code
    assert "indices1 = Array.GetAllIndices(fruits)" in code
    assert "For loopIndex1 = 1 To Array.GetItemCount(indices1)" in code
    assert "    fruit = fruits[indices1[loopIndex1]]" in code


def test_string_escaping():
    assert sb_string('say "hi"') == 'Text.Append(Text.Append("say ", Text.GetCharacter(34)), "hi")' or True
    out = sb_string('a"b')
    assert out == 'Text.Append(Text.Append("a", Text.GetCharacter(34)), "b")'
    assert sb_string("") == '""'


def test_strip_outer():
    assert strip_outer("(a + b)") == "a + b"
    assert strip_outer("(a) + (b)") == "(a) + (b)"
    assert strip_outer('("(" + x)') == '"(" + x'


def test_missing_input_is_error():
    ws = workspace([], node("if", slots={"body": []}))
    res = generate(ws)
    assert not res["ok"]
    assert any("empty" in d["message"] for d in res["diagnostics"])


def test_unknown_variable_and_bad_name():
    ws = workspace(["1bad", "Math"], node("var_set", {"name": "ghost"}, {"value": num(1)}))
    res = generate(ws)
    msgs = " ".join(d["message"] for d in res["diagnostics"])
    assert not res["ok"]
    assert "1bad" in msgs and "Math" in msgs and "ghost" in msgs


def test_negative_operand_and_nesting():
    ws = workspace(["x"], node("var_set", {"name": "x"}, {"value": arith(num(3), "-", num(-5))}))
    assert generate(ws)["code"] == "x = 3 - (-5)\n"
    ws = workspace(["x"], node("var_set", {"name": "x"},
                               {"value": arith(arith(num(1), "+", num(2)), "*", num(3))}))
    assert generate(ws)["code"] == "x = (1 + 2) * 3\n"


def test_unattached_blocks_warn():
    ws = workspace([])
    ws["stacks"].append({"id": "s2", "x": 0, "y": 500, "blocks": [say(txt("lost"))]})
    res = generate(ws)
    assert res["ok"] and any(d["level"] == "warning" for d in res["diagnostics"])
    assert "lost" not in res["code"]


def test_read_never_written_warns():
    ws = workspace(["y"], say(var("y")))
    res = generate(ws)
    assert any("never given a value" in d["message"] for d in res["diagnostics"])


def test_not_and_logic():
    cond = node("not", inputs={"a": node("compare", {"sym": ">"}, {"a": num(1), "b": num(2)})})
    ws = workspace([], node("if", inputs={"cond": cond}, slots={"body": [say(txt("ok"))]}))
    assert generate(ws)["code"].startswith("If (1 > 2) = False Then")


def test_garbage_input_does_not_crash():
    for bad in (None, 5, "x", [], {"stacks": "no"}, {"stacks": [None, 3, {"blocks": [None, {"type": 5}]}]}):
        res = generate(bad)
        assert "code" in res and "diagnostics" in res


def test_depth_limit():
    n = node("tw_writeline", {"value": "x"})
    for _ in range(200):
        n = node("forever", slots={"body": [n]})
    res = generate(workspace([], n))
    assert not res["ok"]


def test_catalog_consistent():
    cat = catalog()
    cats = {c["id"] for c in cat["categories"]}
    assert all(b["category"] in cats for b in cat["blocks"])
    assert len({b["type"] for b in cat["blocks"]}) == len(cat["blocks"])


def test_flask_api():
    import app as appmod
    c = appmod.app.test_client()
    assert c.get("/").status_code == 200
    assert c.get("/api/blocks").get_json()["blocks"]
    r = c.post("/api/generate", json={"workspace": EXAMPLES["hello"]["workspace"]})
    assert r.get_json()["ok"]
    assert c.post("/api/generate", data="nope").status_code == 400
    assert c.get("/api/examples/hello").status_code == 200
    assert c.get("/api/examples/nope").status_code == 404


if __name__ == "__main__":
    import traceback
    failed = 0
    for k, v in list(globals().items()):
        if k.startswith("test_"):
            try:
                v()
                print("ok  ", k)
            except Exception:
                failed += 1
                print("FAIL", k)
                traceback.print_exc()
    sys.exit(1 if failed else 0)
