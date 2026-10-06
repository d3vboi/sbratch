from ..registry import category, inp
from ._helpers import call, prop

category("math", "Math", "#14B8A6", 70)

# (member, label) - all take one number
_ONE_ARG = ["Abs", "Ceiling", "Floor", "Round", "SquareRoot", "Sin", "Cos", "Tan",
            "ArcSin", "ArcCos", "ArcTan", "GetDegrees", "GetRadians", "Log", "NaturalLog"]
_DEFAULTS = {"SquareRoot": "16", "Round": "3.6", "Ceiling": "3.2", "Floor": "3.8", "Abs": "-5",
             "GetDegrees": "3.14159", "GetRadians": "180", "Log": "100", "NaturalLog": "10"}

for _n in _ONE_ARG:
    call("math_" + _n.lower(), "math", "Math.%s {number}" % _n, "Math." + _n, ["number"],
         specs={"number": inp("number", _DEFAULTS.get(_n, "0"))})

call("math_power", "math", "Math.Power {base} to the power {exponent}", "Math.Power", ["base", "exponent"],
     specs={"base": inp("number", "2"), "exponent": inp("number", "8")})
call("math_remainder", "math", "Math.Remainder {dividend} divided by {divisor}", "Math.Remainder",
     ["dividend", "divisor"], specs={"dividend": inp("number", "10"), "divisor": inp("number", "3")})
call("math_max", "math", "Math.Max {a} {b}", "Math.Max", ["a", "b"],
     specs={"a": inp("number", "1"), "b": inp("number", "2")})
call("math_min", "math", "Math.Min {a} {b}", "Math.Min", ["a", "b"],
     specs={"a": inp("number", "1"), "b": inp("number", "2")})
call("math_random", "math", "Math.GetRandomNumber 1 to {max}", "Math.GetRandomNumber", ["max"],
     specs={"max": inp("number", "10")}, tooltip="Random whole number from 1 to max")
prop("math_pi", "math", "Math.Pi", "Math.Pi")
