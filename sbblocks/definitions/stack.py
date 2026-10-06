from ..registry import category, inp
from ._helpers import call

category("stack", "Stack", "#8A8A99", 80)

_name = inp("text", "myStack")

call("stack_push", "stack", "Stack.PushValue {stack} value {value}", "Stack.PushValue", ["stack", "value"],
     kind="statement", specs={"stack": _name, "value": inp("any", "1")})
call("stack_pop", "stack", "Stack.PopValue {stack}", "Stack.PopValue", ["stack"], specs={"stack": _name})
call("stack_count", "stack", "Stack.GetCount {stack}", "Stack.GetCount", ["stack"], specs={"stack": _name})
