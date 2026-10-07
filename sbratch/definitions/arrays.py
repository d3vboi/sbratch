# arrays = SB arrays, array block takes a variable from the dropdown
from ._helpers import call
from ..registry import category, define, inp, many, variable

category("arrays", "arrays", "#D65CD6", 40)


def _make_array(c):
    name = c.field("array")
    lines = [f'{name} = ""']
    for i, v in enumerate(c.items("items"), start=1):
        lines.append(f"{name}[{i}] = {v}")
    return lines


define("array_make", "arrays", "statement", "set {array} to a array of {items}",
       specs={"array": variable(writes=True), "items": many(3, 1, 20, "any", "")},
       code=_make_array, tooltip='array = "" then array[1] = ..., array[2] = ...')

define("array_clear", "arrays", "statement", "clear array {array}",
       specs={"array": variable(writes=True)}, code='{array} = ""')

define("array_set", "arrays", "statement", "set {array} [ {index} ] to {value}",
       specs={"array": variable(writes=True), "index": inp("any", "1"), "value": inp("any", "")},
       code="{array}[{index}] = {value}", tooltip="Indexes can be numbers or text")

define("array_get", "arrays", "value", "{array} [ {index} ]",
       specs={"array": variable(), "index": inp("any", "1")},
       code="{array}[{index}]")

define("array2_set", "arrays", "statement", "set {array} [ {row} ] [ {col} ] to {value}",
       specs={"array": variable(writes=True), "row": inp("any", "1"), "col": inp("any", "1"), "value": inp("any", "")},
       code="{array}[{row}][{col}] = {value}", tooltip="A array of arrays (2D array)")

define("array2_get", "arrays", "value", "{array} [ {row} ] [ {col} ]",
       specs={"array": variable(), "row": inp("any", "1"), "col": inp("any", "1")},
       code="{array}[{row}][{col}]")

define("array_add", "arrays", "statement", "add {value} to end of {array}",
       specs={"value": inp("any", ""), "array": variable(writes=True)},
       code="{array}[Array.GetItemCount({array}) + 1] = {value}")

define("array_remove", "arrays", "statement", "remove item {index} from {array}",
       specs={"index": inp("any", "1"), "array": variable(writes=True)},
       code='Array.RemoveItem("{array}", {index})',
       tooltip="Array.RemoveItem takes the array's NAME as text")

call("array_count", "arrays", "number of items in {array}", "Array.GetItemCount", ["array"],
     specs={"array": variable()})
call("array_has_index", "arrays", "{array} has index {index}", "Array.ContainsIndex", ["array", "index"],
     shape="bool", specs={"array": variable(), "index": inp("any", "1")})
call("array_has_value", "arrays", "{array} has value {value}", "Array.ContainsValue", ["array", "value"],
     shape="bool", specs={"array": variable(), "value": inp("any", "")})
call("array_indices", "arrays", "all indices of {array}", "Array.GetAllIndices", ["array"],
     specs={"array": variable()})
call("array_is_array", "arrays", "{array} is a array", "Array.IsArray", ["array"],
     shape="bool", specs={"array": variable()})
