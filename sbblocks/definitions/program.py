from ..registry import category, inp
from ._helpers import call, prop

category("program", "Program", "#E0457B", 100)

call("prog_delay", "program", "Program.Delay {ms} milliseconds", "Program.Delay", ["ms"], kind="statement",
     specs={"ms": inp("number", "1000")})
call("prog_end", "program", "Program.End", "Program.End", [], kind="statement",
     tooltip="Stops the program immediately")
prop("prog_arg_count", "program", "Program.ArgumentCount", "Program.ArgumentCount")
call("prog_arg", "program", "Program.GetArgument {index}", "Program.GetArgument", ["index"],
     specs={"index": inp("number", "1")})
