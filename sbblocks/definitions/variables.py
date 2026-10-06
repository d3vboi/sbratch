from ..registry import category, define, inp, variable

category("variables", "Variables", "#E8602C", 20)

# palette="variables": the palette shows one copy of this block per user variable.
define("var_get", "variables", "value", "{name}",
       specs={"name": variable()}, code="{name}", palette="variables",
       tooltip="The value stored in a variable")

define("var_set", "variables", "statement", "set {name} to {value}",
       specs={"name": variable(writes=True), "value": inp("any", "0")},
       code="{name} = {value}",
       tooltip="name = value")

define("var_change", "variables", "statement", "change {name} by {value}",
       specs={"name": variable(), "value": inp("number", "1")},
       code="{name} = {name} + {value|op}",
       tooltip="name = name + value")
