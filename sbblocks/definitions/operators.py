from ..registry import category, define, inp, dropdown, number, text

category("operators", "Operators", "#59C059", 30)

# --- literals ---
define("num_literal", "operators", "value", "{value}", specs={"value": number("0")}, code="{value}",
       tooltip="A number")
define("text_literal", "operators", "value", '" {value} "', specs={"value": text("hello")}, code="{value}",
       tooltip="Text. Double quotes and line breaks are handled for you.")
define("bool_true", "operators", "value", "true", code="True", shape="bool")
define("bool_false", "operators", "value", "false", code="False", shape="bool")
define("text_newline", "operators", "value", "new line", code="Text.GetCharacter(10)",
       tooltip="Text.GetCharacter(10)")
define("text_tab", "operators", "value", "tab", code="Text.GetCharacter(9)",
       tooltip="Text.GetCharacter(9)")

# --- arithmetic / comparison / logic ---
define("math_arith", "operators", "value", "{a} {sym} {b}",
       specs={"a": inp("number", "0"), "sym": dropdown(["+", "-", "*", "/"]), "b": inp("number", "0")},
       code="({a|op} {sym} {b|op})",
       tooltip="Arithmetic")

define("compare", "operators", "value", "{a} {sym} {b}", shape="bool",
       specs={"a": inp("any", ""),
              "sym": dropdown([("=", "="), ("≠", "<>"), ("<", "<"), (">", ">"), ("≤", "<="), ("≥", ">=")]),
              "b": inp("any", "0")},
       code="({a|op} {sym} {b|op})",
       tooltip="Comparison (gives True or False)")

define("logic", "operators", "value", "{a} {sym} {b}", shape="bool",
       specs={"a": inp(None), "sym": dropdown(["And", "Or"]), "b": inp(None)},
       code="({a|op} {sym} {b|op})",
       tooltip="And / Or")

define("not", "operators", "value", "not {a}", shape="bool",
       specs={"a": inp(None)},
       code="({a|op} = False)",
       tooltip="Small Basic has no Not operator, so this compares with False")
